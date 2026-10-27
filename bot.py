import os
import re
import io
import sys
import json
import math
import time
import base64
import html
import glob
import random
import gc
import ctypes
import hashlib
import logging
import threading
import shutil
import subprocess
import requests
import telebot
from telebot import types as tg_types
from google import genai

import storage as db
import phrases as ph
import mascot
from texts import tr
from texts_i18n import LANG_ORDER, LANG_LABEL, LANG_NAME_EN
from catalog import (FILM_STYLES, ANIM_STYLES, ORIG_STYLE, FILM_GENRES, ANIM_GENRES, ORIG_GENRE,
                     SOUND_MODES, MUSIC_GENRES, TIMBRES, VOICE_LANGS, label,
                     DANCE_STYLES, FILM_STYLES_ALL, DANCE_MUSIC)


# ═══════════════════════════════════════════════════════════════
# ЛОГИ БЕЗ СЕКРЕТІВ
# ═══════════════════════════════════════════════════════════════
SECRETS = []


def redact(text) -> str:
    s = str(text)
    for sec in SECRETS:
        if sec and len(sec) > 8:
            s = s.replace(sec, "***")
    s = re.sub(r"\d{6,}:[A-Za-z0-9_-]{20,}", "***", s)
    return s


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {redact(msg)}", flush=True)


# ── Пам'ять: на безкоштовному Render лише 512 МБ ──
try:
    _libc = ctypes.CDLL("libc.so.6")
    _libc.mallopt(-8, 2)   # M_ARENA_MAX=2: потоки не роздувають пам'ять окремими «купами»
except Exception:
    _libc = None


def mem_mb():
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except Exception:
        pass
    return 0


def mem_log(stage: str):
    log(f"🧠 Пам'ять: {mem_mb()} МБ · {stage}")


def free_memory():
    gc.collect()
    try:
        if _libc:
            _libc.malloc_trim(0)   # повернути звільнену пам'ять системі
    except Exception:
        pass


class RedactFilter(logging.Filter):
    def filter(self, record):
        try:
            record.msg = redact(record.getMessage())
            record.args = ()
        except Exception:
            pass
        return True


for _name in ("TeleBot", "urllib3", "requests", "httpx", "google_genai"):
    logging.getLogger(_name).addFilter(RedactFilter())
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


# ═══════════════════════════════════════════════════════════════
# НАЛАШТУВАННЯ (змінні оточення на Render; або config.json на комп'ютері)
# ═══════════════════════════════════════════════════════════════
def _split_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value).split(",") if v.strip()]


_FILE_CFG = {}
if os.path.exists("config.json"):
    try:
        with open("config.json", "r", encoding="utf-8") as _f:
            _FILE_CFG = json.load(_f)
    except Exception:
        log("⚠️ config.json не вдалося прочитати (перевірте коми та лапки).")


def cfg(name, default=None):
    v = os.environ.get(name)
    if v:
        return v
    v = _FILE_CFG.get(name)
    return v if v not in (None, "") else default


def cfg_num(name, default):
    try:
        return type(default)(float(cfg(name, default)))
    except (TypeError, ValueError):
        return default


def _ids(name):
    out = []
    for v in _split_list(cfg(name)):
        try:
            out.append(int(v))
        except ValueError:
            log(f"⚠️ {name}: '{v}' — не число, пропускаю.")
    return out


TELEGRAM_TOKEN = (cfg("TELEGRAM_BOT_TOKEN") or "").strip()
api_keys = _split_list(cfg("GEMINI_API_KEYS") or cfg("GEMINI_API_KEY"))
GROQ_API_KEY = (cfg("GROQ_API_KEY") or "").strip()
FAL_KEY = (cfg("FAL_KEY") or "").strip()            # fal.ai: LTX і Kling (платно)
OMNI_API_KEY = (cfg("OMNI_API_KEY") or "").strip()  # окремий ключ Google з увімкненою оплатою (Omni)

ADMIN_IDS = _ids("ADMIN_IDS")
TESTER_IDS = _ids("TESTER_IDS")
# Хто може користуватися ботом: admins — тільки адмін; testers — адмін + TESTER_IDS; public — усі
ACCESS_MODE = (cfg("ACCESS_MODE", "admins") or "admins").strip().lower()

SECRETS.extend([TELEGRAM_TOKEN, GROQ_API_KEY, FAL_KEY, OMNI_API_KEY, *api_keys])

if not TELEGRAM_TOKEN:
    log("❌ Немає TELEGRAM_BOT_TOKEN. Додайте його в змінні оточення або config.json.")
    sys.exit(1)
if not api_keys:
    log("❌ Немає GEMINI_API_KEYS. Додайте ключ(і) Gemini.")
    sys.exit(1)

# ── ШІ для аналізу і промптів ──
DEFAULT_ANALYSIS_MODELS = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]
ANALYSIS_MODELS = _split_list(cfg("ANALYSIS_MODELS")) or DEFAULT_ANALYSIS_MODELS
GROQ_MODELS = _split_list(cfg("GROQ_MODELS")) or ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]

# ── Продукт ──
FREE_PER_DAY = cfg_num("FREE_PROMPTS_PER_DAY", 2)
PACK_SIZE = 10
REF_BONUS = cfg_num("REF_BONUS", 2)
PAID_DAILY_CAP = cfg_num("PAID_DAILY_CAP", 20)          # запобіжник: максимум відео на добу для всіх разом
PRICE_TEST_MODE = (cfg("PRICE_TEST_MODE", "0") or "0").strip() == "1"  # усі ціни = 1 ⭐ для перевірки оплати
STAR_USD = 0.013                                          # скільки $ отримуємо з 1 зірки
PROMPT_COST_USD = 0.02

# ── Моделі готового відео (від дешевшої до найкращої). Ціни в зірках можна змінити командою /setprice ──
VIDEO_MODELS = {
    "ltx": {"name": "LTX-2.3", "emoji": "💰", "provider": "fal",
            "endpoint": cfg("FAL_LTX_MODEL", "fal-ai/ltx-2.3/text-to-video/fast"),
            "usd_sec": 0.06, "stars": 45,
            "params": {"resolution": "1080p", "fps": 25, "generate_audio": True}},
    "omni": {"name": "Omni 1.1", "emoji": "⭐", "provider": "gemini",
             "endpoint": cfg("OMNI_MODEL", "gemini-omni-1.1-flash"),
             "usd_sec": 0.10, "stars": 75, "params": {}},
    "kling": {"name": "Kling 4.0", "emoji": "💎", "provider": "fal",
              "endpoint": cfg("FAL_KLING_MODEL", "kling/v4/text-to-video"),
              "usd_sec": 0.157, "stars": 115, "params": {"resolution": "720p"}},
}
DEFAULT_PRICES = {"ltx": 45, "omni": 75, "kling": 115, "kling30": 420, "pack": 20}
CLIP_SECONDS = 8
MAX_FULL_SECONDS = 30
SHORT_VIDEO_SEC = 10  # відео до 10 с у режимі «Хук» береться цілком

if (cfg("TELEGRAM_TEST_ENV", "0") or "0").strip() == "1":
    # Тестовий сервер Telegram: окремий бот, тестові зірки без реальних грошей
    telebot.apihelper.API_URL = "https://api.telegram.org/bot{0}/test/{1}"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_sessions = {}     # chat_id -> поточне налаштування ролика
pending_orders = {}    # order_id -> сесія, яка чекає оплату
last_analysis = {}     # chat_id -> текст розбору (кнопка «🔍»)
_bot_username = [None]

ALL_CONTENT_TYPES = [
    "text", "audio", "document", "photo", "sticker", "video", "video_note",
    "voice", "location", "contact", "animation", "poll", "dice"
]


# ═══════════════════════════════════════════════════════════════
# ЦІНИ
# ═══════════════════════════════════════════════════════════════
def price(key):
    if PRICE_TEST_MODE:
        return 1
    try:
        return int(db.get_setting(f"price_{key}", DEFAULT_PRICES[key]))
    except (TypeError, ValueError):
        return DEFAULT_PRICES[key]


def model_ready(key):
    m = VIDEO_MODELS[key]
    return bool(FAL_KEY) if m["provider"] == "fal" else bool(OMNI_API_KEY)


def full_seconds(s):
    d = float(s.get("duration") or MAX_FULL_SECONDS)
    return int(max(CLIP_SECONDS, min(MAX_FULL_SECONDS, round(d))))


def v30_price(seconds):
    p = math.ceil(price("kling30") * seconds / MAX_FULL_SECONDS / 5) * 5
    return 1 if PRICE_TEST_MODE else max(price("kling"), p)


def price_range(lo, hi):
    return f"{lo}" if lo == hi else f"{lo}–{hi}"


def range8():
    """Ціна відео 8 с до вибору моделі: від найдешевшої до найдорожчої моделі."""
    ps = [price(k) for k in VIDEO_MODELS]
    return price_range(min(ps), max(ps))


def range30():
    """Ціна відео до 30 с до аналізу ролика: залежить від довжини."""
    return price_range(v30_price(CLIP_SECONDS), v30_price(MAX_FULL_SECONDS))


def order_info(s):
    """(ціна в зірках, собівартість $, секунд, ключ моделі) для поточного замовлення."""
    if s.get("gen_mode") == "v30":
        sec = s.get("v30_sec") or full_seconds(s)  # після рахунку тривалість зафіксована
        return v30_price(sec), sec * VIDEO_MODELS["kling"]["usd_sec"] + PROMPT_COST_USD, sec, "kling"
    key = s.get("model", "ltx")
    sec = CLIP_SECONDS
    return price(key), sec * VIDEO_MODELS[key]["usd_sec"] + PROMPT_COST_USD, sec, key


# ═══════════════════════════════════════════════════════════════
# ДОСТУП І МОВА
# ═══════════════════════════════════════════════════════════════
def is_admin(uid):
    return uid in ADMIN_IDS


def is_allowed(user) -> bool:
    if user is None:
        return False
    if user.id in ADMIN_IDS or ACCESS_MODE == "public":
        return True
    return ACCESS_MODE == "testers" and user.id in TESTER_IDS


def lang_code(user):
    return (getattr(user, "language_code", "") or "").lower().split("-")[0]


def guess_lang(user):
    code = lang_code(user)
    if code in ("ru", "be"):
        return "uk"   # поки мову не обрано — українська; російську можна вибрати в меню
    return code if code in LANG_ORDER else "en"


def tl_name(L):
    """Мова другого блоку промпту (перекладу)."""
    return LANG_NAME_EN.get(L, "Ukrainian") if L != "en" else "Ukrainian"


def user_lang(user):
    u, _ = db.ensure_user(user.id, guess_lang(user))
    return u.get("lang") or "en"


# ═══════════════════════════════════════════════════════════════
# ЗАВДАННЯ ДЛЯ ШІ
# ═══════════════════════════════════════════════════════════════
ANALYSIS_SYSTEM_PROMPT = """
You are a senior film director, cinematographer and sound designer.
Watch the WHOLE video and LISTEN to its audio carefully. Your breakdown is the ONLY source for another
AI that cannot see or hear the video and must recreate it faithfully for a video generator.
Anything you do not write down is lost; anything you get wrong will be copied. Be exact, never guess
extra actions. Write in English (speech/lyrics stay in the original language). Plain concrete words,
no technical codes. Directions are from the CAMERA's point of view (screen-left, screen-right,
toward camera, away from camera).

Answer strictly in this structure:

## 1. SUBJECTS
List EVERYTHING that matters in the frame — people, animals, vehicles, objects, crowds, natural
elements (water, waves, fire, smoke, wind, clouds) — with IDs S1, S2, ... and exact counts
("3 people", "1 dog", "a crowd of about 40 people", "one huge wave").
For each person: gender (decide carefully even under hoods or loose clothes: look at face, hair, body
shape, hands, voice; if unsure write "gender unclear, most likely ..."), approximate age as a number range
("about 20-24 years old"; adults are never "girl"/"boy"), skin tone,
body type, face, hair, every clothing item with color and material, shoes, accessories, props.
Describe people ONLY by what is visible. Never label anyone's religion, ethnicity, nationality or race;
describe religious or national items neutrally by shape and color as clothing or jewelry
("black wide-brim fur hat", "small six-pointed gold pendant"), without naming a faith or a people.
For animals/objects/elements: size, color, material, shape, behavior. Position in frame.

## 2. LOCATION
Place, indoor/outdoor, time of day, weather, background details, ground surface, lighting
(direction, warm/cold, hard/soft).

## 3. CAMERA
Shot size, height, angle, lens feel, every camera move with timing, cuts.

## 4. ACTIONS
Before writing this section, re-watch the main action moment frame by frame and verify:
how many times each action happens, which objects are involved and how many of them there are,
where the subject takes off and lands, and any slow motion or speed change. Report only what you see.
A) SUMMARY: every distinct action or event exactly ONCE with its count and time, e.g.
   "S1 does 1 backflip from the right stump onto the grass, 1.0-5.5s". Never count one
   slowed-down action as two.
B) PLAYBACK SPEED: normal, slow motion, speed ramp (slow -> normal or normal -> slow), fast motion,
   reverse or freeze frames — with exact seconds where each starts and ends.
C) TIMELINE: in beats of about 1 second, describe how each subject moves: start pose -> movement ->
   end pose, body parts, direction, speed, contact with ground/objects; for elements and crowds how
   they move (wave rises and crashes left to right, crowd walks toward camera...). Plain physical words.

## 5. KEY MOMENT
The most important 8 seconds of the video (what the video is about). If the video is 10 seconds
or shorter, use the whole video.
[HOOK_START]
start_sec=<number>; end_sec=<number>; reason=<one sentence>
[HOOK_END]

## 6. AUDIO
MUSIC: genre, tempo (BPM estimate), mood, instruments, accents with timestamps, which actions land on beats.
VOICE: speech, singing, rap or none; who; delivery, emotion, pace, pitch, texture, breaths and pauses.
SOUND EFFECTS with timestamps and sources. AMBIENCE. What is loudest.
Listen to the whole audio several times and transcribe EVERY word — do not skip or merge words.
Speech/lyrics strictly in tags, word for word in the original language. For Cyrillic-script languages
mark the stressed vowel with an acute accent in every word of 2+ syllables (e.g. моло́ко).
[TRANSCRIPT_START]
<timestamped lines with speaker ID and delivery note, or: no speech>
[TRANSCRIPT_END]
[VOICE_PROFILE_START]
<for each voice: gender, age, pitch, timbre, emotion, pace, singing or speaking; or: no voice>
[VOICE_PROFILE_END]

## 7. DURATION
[DURATION_START]<total video length in seconds, number only>[DURATION_END]

## 8. CONTENT CHECK
One word for the whole video: ok, nudity (exposed genitals, bare female breasts or buttocks, sexual acts),
sexual (strongly sexualized or pornographic content even without nudity), gore (graphic violence, blood,
injuries, killing) or minor_risk (a person who looks under 18 shown in a sexualized way).
Swimwear, dancing, kissing, fitness, fashion, fights in sport or action movies without gore = ok.
Flag only clear cases; when in doubt write ok.
[SAFETY_START]<one word>[SAFETY_END]
"""

PROMPT_RULES = """
You write prompts for AI video generators (Google Veo / Omni, Kling, Sora, LTX).
One clip = EXACTLY {clip} seconds, vertical 9:16, with native audio.
Your job is FAITHFUL RECREATION of the given source window, re-skinned in the chosen style and genre.

THE GOLDEN RULES
1. INVENT NOTHING. Recreate only what happens in the source window. Do not add actions, events,
   people, objects or effects "to make it better".
2. SAME COUNTS: the same number of people, animals, objects and the same number of each action
   (one flip stays one flip). Merge the parts of one movement into one beat.
3. SAME PACE AND TIMING: keep the source speed. Copy the breakdown's timecodes exactly, shifted so the
   window starts at 0s. Copy playback effects explicitly with seconds: say when slow motion begins and
   say when the speed returns to normal. A complex movement keeps its full duration.
4. If the source window is shorter than the clip, the scene simply continues naturally to fill the
   time (people keep doing what they were doing, water keeps flowing, the camera keeps moving).
   No new events.
5. STYLE = how the frame is filmed or rendered (color, light, lens, medium and texture, wardrobe,
   emotion, sound treatment). GENRE = the world and mood around the subjects (location, weather,
   background life, music feel). Combine both. They NEVER change actions, choreography, body
   proportions, anatomy or physics of the source. Visual distortions of the world and textures are
   allowed only if the style asks for them.
6. APPLY THE STYLE AND GENRE STRONGLY. Use every layer of both recipes with concrete details: the
   style sentence must contain at least 6 concrete visual details from the style recipe (color and
   light, lens, medium/texture, world details, wardrobe, emotion), the setting must show the genre's
   world and background life, and the audio must follow the recipe's sound. The look must be
   unmistakable from the first frame and stay through the whole clip.
7. AUDIO follows the style (arrangement, instruments, texture, room sound) but WORDS NEVER CHANGE:
   spoken or sung lines are copied word for word (with their stress accents) unless the settings give
   you an exact custom line. Voice is always a natural human performance.
8. SELF-CONTAINED: the video generator has NEVER seen the source video or this breakdown.
   In prompt_en never write "original", "source", "as described", "passport", "same as above",
   "described earlier" or internal IDs like S1/S2/C1. Refer to subjects by short descriptions
   ("the woman in her early 20s", "the black SUV"). Write every appearance out in full.
9. NO IDENTITY LABELS: never describe a person by religion, ethnicity, nationality or race and never
   name religious or national symbols. Describe only visible clothing, hair, accessories, age and build
   in neutral words ("man in a black wide-brim fur hat and long black coat").
10. AGE IS ALWAYS EXPLICIT (video safety filters reject unclear ages). For every adult write a clear
   adult age: "a woman in her early 20s", "a 20-year-old woman", "a man in his 30s". Never use "girl",
   "boy", "kid", "teen", "petite", "little" or a bare "young woman/young man" for adults (always add the
   age). Never describe an adult's skin, lips, eyes or body shape in detail — clothing, hair, accessories
   and actions are enough. Do not put childish things (fairies, talking animals, toys, music boxes,
   nursery or storybook decor, "cute/innocent") into the same scene as a person; for fairy-tale or
   cartoon styles use grown-up versions (palace, magic light, orchestra). If a person in the source looks
   under 18, call them only "a child"/"a teenager" with clothing and actions, no looks at all.
11. STYLE AND GENRE STAY CONCRETE: style and genre must stay fully concrete — exact colors, light,
   drawing/render technique, line and texture, character design traits (e.g. "yellow skin, big round
   white eyes, overbite"), wardrobe, world details and sound. Never write vague phrases like "in the
   style of a famous show", "something similar to" or "iconic cartoon look" — describe what is seen.
12. DANCE STYLE (only when the STYLE recipe starts with "DANCE:"): this is the one exception to rules 1, 2,
   3 and 5. Do NOT describe or copy the source movements at all. The people dance the named dance from the
   first to the last second: write the timeline as concrete named dance moves with seconds (e.g. "0-2s: deep
   squat kicks; 2-4s: split leap; 4-6s: fast spin"), a new move every 1-2 seconds, on the music beat. Keep
   only the number of people, the camera framing and the tempo. The title line names the dance.

PROMPT FORMAT (plain English, {words} words, no technical codes, no brand/film/artist names):
- Title line naming the main action, e.g. "A woman in her early 20s performs a single slow-motion backflip."
- Style sentence (concrete visual description, see rule 6).
- Subjects: full appearance of each written out in full. CROWD RULE: if there are more than 3 people (or
  animals), describe only the 2-3 main ones in full and all the others in ONE short group phrase
  (e.g. "five more men in similar bright suits"). The whole prompt_en must stay under 2000 characters.
- Timed beats, max {beats}: "0-2s: ...", each a clear physical action with direction and end pose;
  state the pose at 0s and at the last second.
- Setting (genre world), camera (with timing), lighting and color.
- Audio: music, sound effects with times, voice description, exact line in quotes and when it is said
  or sung; or "No dialogue." Copy lyric/speech lines EXACTLY as in the transcript, in normal lowercase
  letters WITH the acute stress marks (e.g. "твої́ о́чі ліхтари́ки"). Never write whole words in capitals.

OUTPUT: valid JSON only (no markdown, no comments):
{{
  "hook_reason_ua": "one short sentence in {tl}: what this clip shows",
  "characters": [{{"id": "S1", "short_name": "the woman in her early 20s", "short_name_ua": "the same short name in {tl}", "passport": "..."}}],
  "segments": [
    {{
      "index": 1,
      "source_range": "e.g. 0-8s",
      "prompt_en": "...",
      "prompt_ua": "complete natural {tl} translation of prompt_en (lines in quotes stay as they are)",
      "negative": "comma list: on-screen text, subtitles, watermark, logos, extra people, extra or broken limbs, distorted body, distorted faces, flicker, robotic voice"
    }}
  ]
}}
"""

NATURAL_VOICE = "natural human voice, real performance with breathing and natural intonation, not robotic, not text-to-speech"


def style_info(s):
    cat = s.get("style_cat")
    if cat == "orig" or s.get("style") == "orig":
        return ORIG_STYLE
    table = {"anim": ANIM_STYLES, "dance": DANCE_STYLES}.get(cat, FILM_STYLES_ALL)
    return table.get(s.get("style"), ("", "—", "—", ""))


def genre_info(s):
    g = s.get("genre")
    if g == "orig":
        return ORIG_GENRE
    table = ANIM_GENRES if s.get("style_cat") == "anim" else FILM_GENRES
    return table.get(g, ("", "—", "—", ""))


def build_audio_rules(s):
    mode = s.get("sound", "orig")
    music = MUSIC_GENRES.get(s.get("music_genre"), ("", "", "", ""))[3]
    if s.get("music_genre") == "m_dance":   # музика у стилі обраного танцю (з рецепта танцю)
        rec = DANCE_STYLES.get(s.get("style"), ("", "", "", ""))[3]
        music = (rec.split("SOUND:", 1)[-1].strip() if "SOUND:" in rec else "music typical for this dance") + \
            " Clear strong dance beat."
    tkey = s.get("timbre", "orig")
    voice = TIMBRES.get(tkey, TIMBRES["orig"])[3] or \
        f"same type as the source voice: {s.get('orig_voice', 'not specified')}"
    voice = f"{voice}; {NATURAL_VOICE}"

    if s.get("phrase_src") == "custom" and s.get("phrase"):
        lang_name = VOICE_LANGS.get(s.get("voice_lang", "uk"), VOICE_LANGS["uk"])[3]
        acc = (" Add acute stress accents only to multi-syllable words where you are sure; do not change the words."
               if lang_name == "Ukrainian" else "")
        line = f'Exact line (custom, in {lang_name}, do not change the words): "{s["phrase"]}".{acc}'
    else:
        line = ("Words: copy the original speech/lyrics for this time window word for word with their stress "
                f"accents, same language and same delivery. Original transcript: {s.get('orig_transcript', 'none')}")

    if mode == "none":
        return "AUDIO: no music and no voice. Only natural sound effects synchronized with the actions, plus ambience."
    if mode == "music":
        return f"AUDIO: music: {music} Beat accents land on the key actions. No voice. Natural sound effects."
    if mode == "voice":
        return f"AUDIO: no music. Voice: {voice}. {line} Natural sound effects."
    if mode == "music_voice":
        return f"AUDIO: music: {music} (quieter under the voice). Voice: {voice}. {line} Natural sound effects."
    return (f"AUDIO: recreate the source audio (same music type, tempo, beat accents, sound effects, ambience). "
            f"Arrange and treat the sound so it matches the visual style, keeping the same rhythm. "
            f"If there is a voice: same delivery, voice {voice}. "
            f"Words: copy the original speech/lyrics for this time window word for word with their stress accents. "
            f"Original transcript: {s.get('orig_transcript', 'none')}")


def hook_window(s):
    dur = float(s.get("duration") or CLIP_SECONDS)
    if dur <= SHORT_VIDEO_SEC:
        return 0.0, dur
    h = s.get("hook")
    if not h:
        return 0.0, float(CLIP_SECONDS)
    a = max(0.0, min(h["start"], dur - CLIP_SECONDS))
    return a, min(a + CLIP_SECONDS, dur)


def build_prompt_instruction(s):
    st = style_info(s)
    gn = genre_info(s)
    dur = float(s.get("duration") or CLIP_SECONDS)
    if s.get("gen_mode") == "v30":
        clip = s.get("v30_sec") or full_seconds(s)
        rules = PROMPT_RULES.format(clip=clip, words="250-450", beats=8, tl=tl_name(s["lang"]))
        task = (f"TASK: one continuous clip of {clip}s that faithfully recreates the source from 0s to {min(dur, clip):g}s "
                "with ALL its actions in order. Write exactly ONE segment.")
    else:
        rules = PROMPT_RULES.format(clip=CLIP_SECONDS, words="150-250", beats=4, tl=tl_name(s["lang"]))
        a, b = hook_window(s)
        if dur <= SHORT_VIDEO_SEC:
            task = (f"TASK: one clip that recreates the WHOLE source video ({dur:g}s) faithfully. "
                    "If it is slightly longer than 8s, keep every action and just tighten pauses. Write exactly ONE segment.")
        else:
            task = (f"TASK: one clip that faithfully recreates the source window {a:g}-{b:g}s (the key moment). "
                    "Write exactly ONE segment.")
    if s.get("style_cat") == "dance":
        task = ("TASK: one dance clip for the full clip length: the people from the source dance the chosen dance "
                "from the first to the last second. Write exactly ONE segment.")
        task += (" DANCE MODE: the breakdown below is used ONLY for the number of people, framing, setting and tempo. "
                 "Ignore its movements and actions — the timeline must be the dance moves (rule 12).")
    return (
        f"{rules}\n\n{task}\n\n"
        f"SETTINGS\n"
        f"STYLE ({st[2]}): {st[3]}\n"
        f"GENRE ({gn[2]}): {gn[3]}\n"
        f"{build_audio_rules(s)}\n\n"
        + (f"USER CORRECTIONS (highest priority — they override the breakdown wherever they disagree; "
           f"if they contain lyrics or speech, use those exact words and keep their capital letters): {s['user_note']}\n\n"
           if s.get("user_note") else "")
        + f"SOURCE VIDEO BREAKDOWN\n{s['base_analysis']}"
    )


# ═══════════════════════════════════════════════════════════════
# ОБРОБКА ВІДПОВІДІ ШІ
# ═══════════════════════════════════════════════════════════════
_VOWELS = "аеєиіїоуюяыэёАЕЄИІЇОУЮЯЫЭЁ"
_LATIN_ACUTE = {"á": "А", "é": "Е", "í": "І", "ó": "О", "ú": "У", "ý": "И"}
_CYR = "а-яА-ЯіїєґІЇЄҐёЁ'’"


def stress_to_caps(text: str) -> str:
    """Наголос (моло́ко) -> велика літера (молОко): знак наголосу губиться при копіюванні, а велика літера — ні."""
    text = re.sub(f"([{_VOWELS}])́", lambda m: m.group(1).upper(), text)
    text = re.sub(f"(?<=[{_CYR}])[áéíóúý]|[áéíóúý](?=[{_CYR}])", lambda m: _LATIN_ACUTE[m.group(0)], text)
    return text.replace("́", "")


def fill_passports(data):
    chars = [c for c in (data.get("characters") or []) if c.get("passport")]
    full = "; ".join(c["passport"] for c in chars[:3])
    if len(chars) > 3:   # натовп: головні — повністю, решта — однією фразою (інакше промпт — «простирадло»)
        full += f"; and {len(chars) - 3} more people in a similar look"
    for seg in data.get("segments") or []:
        p = seg.get("prompt_en") or ""
        if full and re.search(r"passport|as described|described (in|earlier|above)", p, re.I):
            p = re.sub(r"[^;\n]*?(passport|as described|described (in|earlier|above))[^;\n]*;?\s*", "", p, flags=re.I)
            first, _, rest = p.partition("\n")
            seg["prompt_en"] = f"{first}\nSubjects: {full}.\n{rest}".strip()
    return data


def fix_unicode_escapes(obj):
    if isinstance(obj, str):
        if "\\u" in obj:
            obj = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), obj)
        obj = obj.replace(" ", " ")
        obj = re.sub("[​‌‍⁠﻿]", "", obj)
        return stress_to_caps(obj)
    if isinstance(obj, list):
        return [fix_unicode_escapes(x) for x in obj]
    if isinstance(obj, dict):
        return {k: fix_unicode_escapes(v) for k, v in obj.items()}
    return obj


def parse_json_loose(text):
    if not text:
        return None
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    a, b = t.find("{"), t.rfind("}")
    if a == -1 or b == -1:
        return None
    chunk = t[a:b + 1]
    for attempt in (chunk, re.sub(r",\s*([}\]])", r"\1", chunk)):
        try:
            return fill_passports(fix_unicode_escapes(json.loads(attempt)))
        except Exception:
            continue
    return None


def cyr_ratio(text: str) -> float:
    letters = re.findall(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]", text or "")
    if not letters:
        return 0.0
    return sum(1 for c in letters if not c.isascii()) / len(letters)


STRESS_NOTE = " Capital letters inside the sung/spoken words mark stressed vowels."


def polish_segments(s, data):
    chars = data.get("characters") or []
    for seg in data["segments"]:
        if s["lang"] != "en" and seg.get("prompt_en") and not looks_translated(s["lang"], seg.get("prompt_ua"), seg["prompt_en"]):
            seg["prompt_ua"] = translate_ua(s, seg["prompt_en"]) or seg.get("prompt_ua", "")
        for field, key in (("prompt_en", "short_name"), ("prompt_ua", "short_name_ua")):
            txt = seg.get(field) or ""
            for c in chars:
                cid, name = c.get("id"), c.get(key) or c.get("short_name")
                if cid and name:
                    txt = re.sub(rf"\b{re.escape(cid)}\b", name, txt)
            txt = re.sub(r"(^|[.!?]\s+|\n\s*|:\s+)([a-zа-яіїєґ])", lambda m: m.group(1) + m.group(2).upper(), txt)
            seg[field] = txt
        en = seg.get("prompt_en") or ""
        if re.search(r"[а-яіїєґ][АЕЄИІЇОУЮЯ]", en) and "mark stressed vowels" not in en:
            seg["prompt_en"] = en.rstrip() + STRESS_NOTE


# ═══════════════════════════════════════════════════════════════
# ПОВІДОМЛЕННЯ І ПАНЕЛЬ
# ═══════════════════════════════════════════════════════════════
def send_safe_message(chat_id: int, text: str, parse_mode="Markdown", reply_markup=None):
    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)] or [""]
    last = None
    for i, chunk in enumerate(chunks):
        rm = reply_markup if i == len(chunks) - 1 else None
        try:
            last = bot.send_message(chat_id, chunk, parse_mode=parse_mode, reply_markup=rm)
        except Exception:
            try:
                last = bot.send_message(chat_id, chunk, parse_mode=None, reply_markup=rm)
            except Exception as e:
                log(f"Не вдалося надіслати повідомлення: {e}")
    return last


def clean_code(text):
    return (text or "").replace("`", "'").strip()


def btn(text, data):
    return tg_types.InlineKeyboardButton(text, callback_data=data)


FORMAT_NAMES = {"hook": ("🔥 Хук · тільки промпт", "🔥 Hook · prompt only"),
                "v8": ("🎬 Відео 8 с", "🎬 Video 8 s"),
                "v30": ("🎞 Відео до 30 с", "🎞 Video up to 30 s")}


def fmt_name(s):
    mode = s.get("gen_mode")
    return tr(s["lang"], f"fm_{mode}") if mode in ("hook", "v8", "v30") else ""


def sound_summary(s):
    mode = s.get("sound")
    if not mode:
        return None
    L = s["lang"]
    parts = [label(SOUND_MODES[mode], L)]
    if s.get("music_genre"):
        parts.append(label(DANCE_MUSIC if s["music_genre"] == "m_dance" else MUSIC_GENRES[s["music_genre"]], L))
    if mode in ("voice", "music_voice"):
        if s.get("phrase_src") == "custom" and s.get("phrase"):
            parts.append(f"«{s['phrase'][:40]}»")
        elif s.get("phrase_src") == "orig":
            parts.append(tr(L, "orig_words"))
        if s.get("timbre"):
            parts.append(label(TIMBRES[s["timbre"]], L))
    return " · ".join(parts)


def billboard(L):
    """Відео-білборд «Що робимо?» потрібною мовою (рамка + заголовок + 3 картки вшиті у відео)."""
    for lang in (L, "en"):
        p = os.path.join(HERE, f"billboard_{lang}.mp4")
        if os.path.exists(p):
            return p
    return None


def render_panel(s) -> str:
    L = s["lang"]
    if s.get("state") == "AGAIN":   # після результату — коротко: що далі
        return f"{tr(L, 'again_status')}\n\n{tr(L, 'q_AGAIN')}"
    if s.get("state") == "FORMAT" and s.get("photo") and billboard(L) and not s.get("ask_cancel"):
        # білборд уже все пояснює — під ним тексту немає; лише якщо щось пішло не так
        return f"⚠️ {s['analysis_error']}" if s.get("analysis_error") else ""
    lines = [tr(L, "panel_title")]
    if s.get("gen_mode"):
        lines.append(f"{tr(L, 'p_format')}: {fmt_name(s)}")
    if s.get("gen_mode") == "v8" and s.get("model"):
        m = VIDEO_MODELS[s["model"]]
        lines.append(f"{tr(L, 'p_model')}: {m['emoji']} {m['name']}")
    if s.get("style_cat") and (s.get("style") or s.get("style_cat") == "orig"):
        lines.append(f"{tr(L, 'p_style')}: {label(style_info(s), L)}")
    if s.get("genre") and s.get("style_cat") not in ("anim", "dance"):   # у анімації й танців жанру немає
        lines.append(f"{tr(L, 'p_genre')}: {label(genre_info(s), L)}")
    snd = sound_summary(s)
    if snd:
        lines.append(f"{tr(L, 'p_sound')}: {snd}".replace("`", "'"))
    if s.get("user_note"):
        lines.append(f"{tr(L, 'p_note')}: «{s['user_note'][:60]}»".replace("`", "'").replace("_", " ").replace("*", ""))
    if (s.get("state") in ("CONFIRM", "INVOICE") or s.get("paid")) and \
            (s.get("gen_mode") == "v30" or s.get("state") != "CONFIRM"):
        stars, _, sec, _ = order_info(s)
        lines.append(f"{tr(L, 'p_price')}: {stars} ⭐ · {sec} s")
    lines.append("──────────")
    if s.get("live_status") and (s.get("state") != "CONFIRM" or s.get("analysis_error")):
        lines.append(f"⏳ {s['live_status']}")   # у вікні моделі статус «Готово» не показуємо — бережемо місце
    q = tr(L, f"q_{s.get('state')}") if s.get("state") else ""
    if s.get("state") == "CONFIRM" and s.get("gen_mode") != "v30":
        q = tr(L, "q_CONFIRM_M")
    if s.get("ask_cancel"):
        q = tr(L, "cx_q_stop" if s.get("state") in ("GENERATING", "INVOICE") else "cx_q")
    elif s.get("state") == "CLARIFY" and s.get("photo"):
        q = ""   # підказка вже є на картинці — не дублюємо
    if q and not q.startswith("q_"):
        lines += ["", q]
    if s.get("state") == "CONFIRM" and not s.get("ask_cancel"):
        lines += ["", tr(L, "nsfw_short")]   # правило — до оплати
    bp = bipi_for(s)
    if bp and s.get("state") != "GENERATING" and s.get("_bp_show") == s.get("state"):
        lines += ["", bipi_line(bp[1])]   # Біпі «заговорив» через 3–4 с — вузький рядок над кнопками
    return "\n".join(lines)


def bipi_line(text):
    """Фраза Біпі одним рядком курсивом (без символів, що ламають Markdown)."""
    t = re.sub(r"[*_`\[\]]", "", text or "").strip()
    return f"_🤖 {t}_" if t else ""


def ui(s):
    """Оновити панель налаштувань (одне повідомлення, яке редагується)."""
    if not s or not s.get("msg_id"):
        return
    text = render_panel(s)
    kb = get_keyboard(s)
    sig = (text, s.get("state"), s.get("_kb_sig"), s.get("page"), s.get("ask_cancel"), bipi_for(s), s.get("_bp_show"))
    if s.get("_last") == sig:
        return
    def edit(mode):
        want = STATE_PIC.get(s.get("state"), s.get("pic")) if s.get("photo") else None
        if want == "pic_confirm" and s.get("gen_mode") != "v30":
            want = "pic_model"   # останній крок: вибір моделі з ціною
        if want == "pic_gen" and s.get("gen_mode", "hook") == "hook":
            want = "pic_prompt"   # безкоштовний хук: робимо промпт, а не відео
        if want == "pic_format" and want != s.get("pic") and billboard(s["lang"]):   # «Що робимо?» — білборд
            bb = billboard(s["lang"])
            fid = _bb_ids.get(bb)
            fh = None if fid else open(bb, "rb")
            try:
                media = tg_types.InputMediaAnimation(fid or fh, caption=text[:1020] or None, parse_mode=mode,
                                                     width=1080, height=880)
                r = bot.edit_message_media(media, chat_id=s["chat_id"], message_id=s["msg_id"], reply_markup=kb)
            finally:
                if fh:
                    fh.close()
            try:
                _bb_ids[bb] = r.animation.file_id
            except Exception:
                pass
            s["pic"], s["pic_key"] = want, (want, None)
            return
        bp = bipi_for(s) if s.get("state") == "GENERATING" else None   # картка — лише під час роботи
        pkey = (want, bp)
        if want and (want != s.get("pic") or pkey != s.get("pic_key")) and pic_path(want, s["lang"]):
            path = pic_path(want, s["lang"])   # новий крок (або новий Біпі) — нова картинка
            ckey, fh = None, None
            if bp and s.get("state") == "GENERATING":   # під час роботи — окрема картка (детектив / режисер)
                ckey, src = card_media(bp[0], bp[1], s["lang"])
            else:   # на кроці — чиста картинка; фраза Біпі з'явиться рядком у підписі
                src = _photo_ids.get(path)
                fh = None if src else open(path, "rb")
            try:
                media = tg_types.InputMediaPhoto(src or fh, caption=text[:1020] or None, parse_mode=mode if text else None)
                r = bot.edit_message_media(media, chat_id=s["chat_id"], message_id=s["msg_id"], reply_markup=kb)
            finally:
                if fh:
                    fh.close()
            if ckey:
                _remember_card(ckey, r)
            else:
                try:
                    _photo_ids[path] = r.photo[-1].file_id
                except Exception:
                    pass
            s["pic"], s["pic_key"] = want, pkey
            return
        if s.get("photo"):   # панель-картинка: текст живе в підписі (до 1024 символів)
            bot.edit_message_caption(caption=text[:1020], chat_id=s["chat_id"], message_id=s["msg_id"],
                                     parse_mode=mode if text else None, reply_markup=kb)
        else:
            bot.edit_message_text(text, s["chat_id"], s["msg_id"], parse_mode=mode, reply_markup=kb)
    try:
        edit("Markdown")
        s["_last"] = sig
    except Exception as e:
        if "message is not modified" not in str(e):
            try:
                edit(None)
                s["_last"] = sig
            except Exception:
                pass
    bipi_schedule(s)


BIPI_DELAY = 3.5   # через скільки секунд бездіяльності на кроці з'являється фраза Біпі


def bipi_schedule(s):
    """Новий крок → фраза Біпі прихована; якщо людина затрималась на кроці BIPI_DELAY секунд — рядок з'являється
    (міняється лише підпис, картинка не перезавантажується)."""
    st = s.get("state")
    if not BIPI_ON or st not in WINDOW_BIPI or not s.get("photo"):
        s["_bp_wait"] = s["_bp_show"] = None
        return
    here = (st, s.get("msg_id"))
    if s.get("_bp_wait") == here:
        return
    s["_bp_wait"], s["_bp_show"] = here, None
    s["_bp_tok"] = tok = s.get("_bp_tok", 0) + 1

    def reveal():
        if s.get("_bp_tok") != tok or s.get("state") != st or user_sessions.get(s.get("chat_id")) is not s:
            return
        s["_bp_show"] = st
        if not s.get("ask_cancel"):
            ui(s)
    t = threading.Timer(BIPI_DELAY, reveal)
    t.daemon = True
    t.start()


def react(call, s=None):
    """Відповідь на натискання: всплывашка зверху з реакцією Біпі на вибір («Ого, Фламенко!»), 2–3 с."""
    name = ""
    try:
        for row in call.message.reply_markup.keyboard:
            for b in row:
                if b.callback_data == call.data:
                    name = b.text
    except Exception:
        pass
    parts = name.split(" ", 1)
    if len(parts) == 2 and not re.match(r"\w", parts[0]):
        name = parts[1]   # без емодзі на початку
    name = name.split(" · ")[0].strip()
    text = ""
    if BIPI_ON and name:
        L = s["lang"] if s else user_lang(call.from_user)
        text = ph.pick(call.from_user.id, "react", L).replace("{x}", name)[:190]
    try:
        bot.answer_callback_query(call.id, text or None)
    except Exception:
        pass


def set_status(s, text):
    if s:
        s["live_status"] = text
        ui(s)


def grid(markup, items, prefix):
    row = []
    for key, title in items:
        name = title.split(" ", 1)[-1]
        limit = 13 if re.search(r"[а-яіїєґё]", name.lower()) else 15   # кирилиця ширша за латиницю
        if len(name) > limit:   # довга назва не влазить у пів-рядка — ставимо окремо
            if row:
                markup.row(*row)
                row = []
            markup.row(btn(title, f"{prefix}{key}"))
            continue
        row.append(btn(title, f"{prefix}{key}"))
        if len(row) == 2:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)


PAGE_MAX = 8    # кнопок на сторінці (4 ряди) — щоб над ними вміщалась велика картинка


def paged(markup, s, items, prefix):
    """Довгий список — рівними сторінками з гортанням ◀️ ▶️ (картинка лишається зверху)."""
    pages = max(1, math.ceil(len(items) / PAGE_MAX))
    per = math.ceil(len(items) / pages) if items else 1
    pg = min(s.get("page", 0), pages - 1)
    s["_pages"] = pages
    grid(markup, items[pg * per:(pg + 1) * per], prefix)
    if pages > 1:
        markup.row(btn("◀️" if pg else "·", "pg_prev"), btn(f"{pg + 1}/{pages}", "pg_none"),
                   btn("▶️" if pg < pages - 1 else "·", "pg_next"))


def confirm_models(s):
    """Моделі у вікні вибору. Omni переробляє сам ролик (рухи лишаються як в оригіналі),
    тому для танців — де рухи змінюються на обраний танець — його не показуємо."""
    return [(k, v) for k, v in VIDEO_MODELS.items() if not (k == "omni" and s.get("style_cat") == "dance")]


def get_keyboard(s):
    state = s.get("state")
    L = s["lang"]
    m = tg_types.InlineKeyboardMarkup()
    nav = [btn(tr(L, "back"), "nav_back"), btn(tr(L, "cancel"), "nav_cancel")]

    if s.get("ask_cancel"):   # перепитуємо: «Скасувати/Зупинити» скидає всі налаштування
        stop = state in ("GENERATING", "INVOICE")
        m.row(btn(tr(L, "cx_yes_stop" if stop else "cx_yes"), "cx_yes"))
        m.row(btn(tr(L, "cx_no_stop" if stop else "cx_no"), "cx_no"))
        return m
    if state == "FORMAT":
        free, extra = db.free_left(s["uid"], FREE_PER_DAY)
        if is_admin(s["uid"]) or free:
            hook = tr(L, "fm_hook", n=free if not is_admin(s["uid"]) else "∞")
        elif extra:
            hook = tr(L, "fm_hook_extra", n=extra)
        else:
            hook = tr(L, "fm_hook_none")
        m.row(btn(hook, "fm_hook"))
        any_ready = any(model_ready(k) for k in VIDEO_MODELS)
        p_min = min(price(k) for k in VIDEO_MODELS)
        m.row(btn(tr(L, "fm_v8") + ("" if any_ready else " 🔒"), "fm_v8"))
        m.row(btn(tr(L, "fm_v30") + ("" if model_ready("kling") else " 🔒"), "fm_v30"))
        m.row(btn(tr(L, "cancel"), "nav_cancel"))
    elif state == "MODEL":
        for k, v in VIDEO_MODELS.items():
            m.row(btn(f"{v['emoji']} {v['name']}" + ("" if model_ready(k) else " 🔒"), f"md_{k}"))
        m.row(*nav)
    elif state == "STYLE_CAT":
        m.row(btn(tr(L, "sc_orig"), "sc_orig"))
        m.row(btn(tr(L, "sc_dance"), "sc_dance"))
        m.row(btn(tr(L, "sc_film"), "sc_film"), btn(tr(L, "sc_anim"), "sc_anim"))
        m.row(*nav)
    elif state == "STYLE_FILM":
        m.row(btn(label(ORIG_STYLE, L), "st_orig"))   # немає потрібного стилю — як в оригіналі
        paged(m, s, [(k, label(v, L)) for k, v in FILM_STYLES.items()], "st_")
        m.row(*nav)
    elif state == "DANCE":
        paged(m, s, [(k, label(v, L)) for k, v in DANCE_STYLES.items()], "st_")
        m.row(*nav)
    elif state == "STYLE_ANIM":
        m.row(btn(label(ORIG_STYLE, L), "st_orig"))
        paged(m, s, [(k, label(v, L)) for k, v in ANIM_STYLES.items()], "st_")
        m.row(*nav)
    elif state == "GENRE":
        m.row(btn(label(ORIG_GENRE, L), "gn_orig"))
        table = ANIM_GENRES if s.get("style_cat") == "anim" else FILM_GENRES
        paged(m, s, [(k, label(v, L)) for k, v in table.items()], "gn_")
        m.row(*nav)
    elif state == "SOUND":
        m.row(btn(label(SOUND_MODES["orig"], L), "sd_orig"))
        m.row(btn(label(SOUND_MODES["music"], L), "sd_music"), btn(label(SOUND_MODES["voice"], L), "sd_voice"))
        m.row(btn(label(SOUND_MODES["music_voice"], L), "sd_music_voice"), btn(label(SOUND_MODES["none"], L), "sd_none"))
        m.row(*nav)
    elif state == "MUSIC":
        if s.get("style_cat") == "dance":
            m.row(btn(label(MUSIC_GENRES["m_orig"], L), "mu_m_orig"), btn(label(DANCE_MUSIC, L), "mu_m_dance"))
        else:
            m.row(btn(label(MUSIC_GENRES["m_orig"], L), "mu_m_orig"))
        grid(m, [(k, label(v, L)) for k, v in MUSIC_GENRES.items() if k != "m_orig"], "mu_")
        m.row(*nav)
    elif state == "PHRASE_SRC":
        m.row(btn(tr(L, "ps_orig"), "ps_orig"), btn(tr(L, "ps_custom"), "ps_custom"))
        m.row(*nav)
    elif state == "WAITING_TEXT":
        m.row(*nav)
    elif state == "LANG":
        grid(m, [(k, label(v, L)) for k, v in VOICE_LANGS.items()], "lg_")
        m.row(*nav)
    elif state == "TIMBRE":
        m.row(btn(label(TIMBRES["orig"], L), "tb_orig"))
        grid(m, [(k, label(v, L)) for k, v in TIMBRES.items() if k != "orig"], "tb_")
        m.row(*nav)
    elif state == "CLARIFY":
        m.row(btn(tr(L, "skip"), "cl_skip"))
        m.row(*nav)
    elif state == "CONFIRM":
        if s.get("gen_mode") == "v30":
            m.row(btn(tr(L, "pay_btn", p=order_info(s)[0]), "pay_go"))
        else:   # модель обирається тут: на кнопці — ціна
            for k, v in confirm_models(s):
                tag = f" · {tr(L, 'omni_tag')}" if k == "omni" else ""
                m.row(btn(f"{v['emoji']} {v['name']}{tag} · {price(k)} ⭐" + ("" if model_ready(k) else " 🔒"), f"pm_{k}"))
        if not s.get("reuse_prompt"):   # передумав платити — лише безкоштовний промпт з тими ж налаштуваннями
            m.row(btn(tr(L, "prompt_only_btn"), "po_go"))
        if is_admin(s["uid"]):   # адмін-запуск без оплати — один компактний рядок
            if s.get("gen_mode") == "v30":
                m.row(btn(tr(L, "admin_run"), "pay_admin"))
            else:
                m.row(*[btn(f"🛠 {v['name'].split()[0]}", f"pa_{k}") for k, v in confirm_models(s)])
        m.row(*nav)
    elif state == "AGAIN":
        if s.get("gen_mode") == "hook" and s.get("ready_seg") and any(model_ready(k) for k in VIDEO_MODELS):
            m.row(btn(tr(L, "again_video"), "ag_video"))
        m.row(btn(tr(L, "again_all"), "ag_all"))
        m.row(btn(tr(L, "again_style"), "ag_style"))
        m.row(btn(tr(L, "close"), "nav_cancel"))
    elif state in ("GENERATING", "INVOICE"):
        if not s.get("paid"):
            m.row(btn(tr(L, "stop"), "nav_cancel"))
        else:
            return None
    else:
        return None
    return m


TIP_STATES = ("MODEL", "STYLE_CAT", "STYLE_FILM", "STYLE_ANIM", "GENRE", "DANCE", "SOUND", "MUSIC",
              "PHRASE_SRC", "LANG", "TIMBRE")


def advance(s, new_state, **values):
    """Перехід на наступний крок із запам'ятовуванням (для кнопки «Назад»)."""
    s.setdefault("history", []).append((s.get("state"), list(values.keys())))
    s.update(values)
    s["state"] = new_state
    s.setdefault("_bp", {}).pop(new_state, None)   # на кожен крок — свіжа фраза Біпі
    s["page"] = 0
    s.pop("ask_cancel", None)
    ui(s)


def after_sound(s, **values):
    after_clarify(s, **values)   # вікно «Уточнення» прибрано


def after_clarify(s, **values):
    if s.get("gen_mode") == "hook":
        s.setdefault("history", []).append((s.get("state"), list(values.keys())))
        s.update(values)
        s["state"] = "GENERATING"
        ui(s)
        threading.Thread(target=run_free_prompt, args=(s,), daemon=True).start()
    else:
        advance(s, "CONFIRM", **values)


# ═══════════════════════════════════════════════════════════════
# ЗАВАНТАЖЕННЯ ВІДЕО ЗА ПОСИЛАННЯМ (3 способи по черзі)
# ═══════════════════════════════════════════════════════════════
UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def download_tiktok(url: str, output_path: str, s) -> bool:
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass
    set_status(s, tr(s["lang"], "st_download"))
    m = re.search(r"https?://\S+", url)
    if m:
        url = m.group(0)

    def save_from(video_url, source, duration=None):
        if video_url.startswith("/"):
            video_url = "https://www.tikwm.com" + video_url
        v = requests.get(video_url, headers=UA_HEADERS, timeout=60)
        if v.status_code != 200 or len(v.content) < 10000:
            log(f"[{source}] файл не завантажився: HTTP {v.status_code}, {len(v.content)} байт")
            return False
        with open(output_path, "wb") as f:
            f.write(v.content)
        if duration:
            s["duration"] = duration
            s["duration_from_source"] = True
        log(f"✅ [{source}] відео завантажено ({len(v.content) // 1024} KB)")
        return True

    for attempt in (1, 2):
        try:
            r = requests.post("https://www.tikwm.com/api/", data={"url": url, "hd": 1}, headers=UA_HEADERS, timeout=20)
            log(f"[tikwm] спроба {attempt}: HTTP {r.status_code}")
            if r.status_code == 403:
                break
            res = r.json()
            if res.get("code") == 0:
                d = res.get("data") or {}
                play = d.get("play") or d.get("wmplay") or ""
                if d.get("images") and not d.get("duration"):   # фото-карусель, а не відео
                    log(f"[tikwm] це фото-карусель ({len(d.get('images') or [])} фото), відео немає")
                    s["dl_reason"] = "photos"
                    return False
                if play and save_from(play, "tikwm", d.get("duration")):
                    return True
            else:
                log(f"[tikwm] відмовив: {res.get('msg')}")
        except Exception as e:
            log(f"[tikwm] збій: {e}")
        time.sleep(2)

    try:
        r = requests.get("https://api.tiklydown.eu.org/api/download", params={"url": url}, headers=UA_HEADERS, timeout=25)
        log(f"[tiklydown] HTTP {r.status_code}")
        if r.status_code == 200:
            vid = (r.json() or {}).get("video") or {}
            play = vid.get("noWatermark") or vid.get("watermark") or ""
            dur = vid.get("duration")
            if not isinstance(dur, (int, float)) or dur > 600:
                dur = None
            if play and save_from(play, "tiklydown", dur):
                return True
    except Exception as e:
        log(f"[tiklydown] збій: {e}")

    try:
        import yt_dlp
        opts = {"outtmpl": output_path, "format": "mp4/best", "quiet": True,
                "no_warnings": True, "overwrites": True, "http_headers": UA_HEADERS}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            if info and info.get("duration"):
                s["duration"] = info["duration"]
                s["duration_from_source"] = True
            log(f"✅ [yt-dlp] відео завантажено ({os.path.getsize(output_path) // 1024} KB)")
            return True
        log("[yt-dlp] файл не з'явився")
    except Exception as e:
        log(f"[yt-dlp] збій: {str(e)[:300]}")
    log(f"❌ Посилання не вдалося скачати жодним способом: {url[:80]}")
    return False


# ═══════════════════════════════════════════════════════════════
# БІПІ — мордочка бота. З'являється в картинці, яка вже на екрані (нічого не зсувається);
# якщо панелі немає — окремою карткою (великий Біпі + хмаринка «матове скло» з фразою)
# ═══════════════════════════════════════════════════════════════
BIPI_ON = str(cfg("BIPI", "1")).strip().lower() not in ("0", "false", "no", "off")
_card_ids = {}   # (картинка або «card», образ, фраза, мова) → file_id (удруге не малюємо й не вантажимо)


def _remember_card(key, r):
    try:
        _card_ids[key] = r.photo[-1].file_id
        if len(_card_ids) > 1500:
            _card_ids.pop(next(iter(_card_ids)))
    except Exception:
        pass


def pic_key_of(path):
    """pic_genre_uk.jpg → pic_genre (ключ розкладки Біпі на цій картинці)."""
    base = os.path.basename(path or "")
    return base.rsplit("_", 1)[0] if "_" in base else base


def card_media(role, text, L, base=None):
    """(ключ, file_id або файл у пам'яті): base — картинка кроку з маленьким Біпі в кутку (після анімації);
    без base — окрема картка (великий Біпі + хмаринка з фразою)."""
    key = ("peek", base, role) if base else ("card", role, text, L)
    if key in _card_ids:
        return key, _card_ids[key]
    from PIL import Image
    if base:
        with Image.open(base) as src:
            im = mascot.peek(src, role, pic_key_of(base))
    else:
        im = mascot.card(role, text, L)
    return key, mascot.jpeg(im)


def _with_text(text, caption, L):
    """Якщо хмаринку цією мовою не намалювати (арабська без потрібної бібліотеки) — фраза йде в підпис."""
    if mascot.can_write(L):
        return caption
    return f"{text}\n\n{caption}" if caption else text


def _drop_later(chat_id, mid, ttl):
    def go():
        try:
            bot.delete_message(chat_id, mid)
        except Exception:
            pass
    threading.Timer(ttl, go).start()


def send_card(chat_id, role, text, L, ttl=None, caption=None, reply_markup=None):
    """Окрема картка з Біпі. ttl — через скільки секунд прибрати (для дрібних підказок)."""
    if not text:
        return
    if not BIPI_ON:
        send_safe_message(chat_id, f"{text}\n\n{caption}" if caption else text, parse_mode=None, reply_markup=reply_markup)
        return
    try:
        key, src = card_media(role, text, L)
        r = bot.send_photo(chat_id, src, caption=_with_text(text, caption, L), reply_markup=reply_markup)
        _remember_card(key, r)
        if ttl:
            _drop_later(chat_id, r.message_id, ttl)
    except Exception as e:
        log(f"Картка Біпі не надіслалась: {str(e)[:150]}")
        send_safe_message(chat_id, f"{text}\n\n{caption}" if caption else text, parse_mode=None, reply_markup=reply_markup)


def panel_card(s, role, text, caption=None, reply_markup=None):
    """Панель (те саме повідомлення) перетворюється на картку з Біпі — нове повідомлення не з'являється."""
    L = s["lang"]
    if not BIPI_ON or not s.get("msg_id") or not s.get("photo"):
        send_card(s["chat_id"], role, text, L, caption=caption, reply_markup=reply_markup)
        return
    try:
        key, src = card_media(role, text, L)
        cap = _with_text(text, caption, L)
        r = bot.edit_message_media(tg_types.InputMediaPhoto(src, caption=(cap or None) and cap[:1020]),
                                   chat_id=s["chat_id"], message_id=s["msg_id"], reply_markup=reply_markup)
        _remember_card(key, r)
        s["pic"], s["pic_key"], s["_last"] = "card", None, None
    except Exception as e:
        log(f"Панель-картка не змінилась: {str(e)[:150]}")
        send_card(s["chat_id"], role, text, L, caption=caption, reply_markup=reply_markup)


def bipi_say(chat_id, uid, L, role, block, ttl=None, s=None, caption=None):
    """Випадкова фраза з блоку (без повторів) → Біпі: у панелі s (якщо є) або окремою карткою. Повертає фразу."""
    text = ph.pick(uid, block, L)
    if s is not None and s.get("msg_id") and s.get("photo"):
        panel_card(s, role, text, caption=caption)
    else:
        send_card(chat_id, role, text, L, ttl=ttl, caption=caption)
    return text


WINDOW_BIPI = {   # вікно → (образ Біпі, блок фраз саме про це вікно)
    "STYLE_CAT": ("happy", "w_cat"), "STYLE_FILM": ("director", "w_film"), "STYLE_ANIM": ("artist", "w_anim"),
    "DANCE": ("party", "w_dance"), "GENRE": ("detective", "w_genre"), "SOUND": ("happy", "w_sound"),
    "PHRASE_SRC": ("happy", "w_voice"), "LANG": ("happy", "w_voice"), "TIMBRE": ("happy", "w_voice"),
    "WAITING_TEXT": ("happy", "w_voice"),
    "MODEL": ("accountant", "w_model"), "CONFIRM": ("accountant", "w_model"), "INVOICE": ("accountant", "w_model"),
    "AGAIN": ("party", "w_again"),
}


def bipi_for(s):
    """Який Біпі зараз у панелі: (образ, фраза) або None. Фраза одна на крок (не блимає при оновленні статусу)."""
    if not BIPI_ON or not s.get("photo") or s.get("ask_cancel"):
        return None
    st = s.get("state")
    if st == "GENERATING":
        return s.get("bipi_gen")
    if st not in WINDOW_BIPI:
        return None
    role, block = WINDOW_BIPI[st]
    memo = s.setdefault("_bp", {})
    if st not in memo:
        memo[st] = (role, ph.pick(s.get("uid"), block, s["lang"]))
    return memo[st]


# ═══════════════════════════════════════════════════════════════
# ВИКЛИКИ ШІ: Groq (промпти) і Gemini (аналіз відео + запасний для промптів)
# ═══════════════════════════════════════════════════════════════
def cancelled(s):
    return bool(s and s.get("cancel"))


_MONEY_WORDS = ("402", "payment required", "payment_required", "billing", "insufficient", "balance",
                "credits", "exhausted balance", "user is locked", "prepay", "spend cap", "spending cap", "out of funds")


def money_problem(msg):
    """Схоже, що на сервісі закінчились гроші / кредити / ліміт витрат."""
    m = (msg or "").lower()
    return any(w in m for w in _MONEY_WORDS)


_alert_last = {}


def admin_alert(service, detail, text=None):
    """Повідомлення адміну про проблему з сервісом (не частіше ніж раз на 30 хв для одного сервісу)."""
    now = time.time()
    if now - _alert_last.get(service, 0) < 1800:
        return
    _alert_last[service] = now
    text = (text or (f"⚠️ {service}: схоже, закінчились гроші або ліміт.\n"
            f"Поповніть баланс — поки що замовлення не виконуються (зірки людям повертаються автоматично).")
            ) + f"\n\nДеталі: {str(detail)[:300]}"
    log(f"⚠️ {service}: проблема з балансом — {str(detail)[:200]}")
    for aid in ADMIN_IDS:
        try:
            bot.send_message(aid, text)
        except Exception:
            pass


def groq_call(s, prompt_text: str, label_text: str, json_mode=False):
    if not GROQ_API_KEY:
        return None, None
    for model_name in GROQ_MODELS:
        use_json = json_mode
        for attempt in (1, 2, 3):
            if cancelled(s):
                return None, None
            set_status(s, f"{label_text} (Groq · {model_name.split('/')[-1]})")
            body = {"model": model_name, "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.7, "max_completion_tokens": 12000}
            if use_json:
                body["response_format"] = {"type": "json_object"}
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                  headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                                  json=body, timeout=180)
                if r.status_code == 200:
                    text = (r.json().get("choices") or [{}])[0].get("message", {}).get("content")
                    if text and text.strip():
                        log(f"✅ {label_text}: Groq {model_name}")
                        return text, f"groq/{model_name.split('/')[-1]}"
                    break
                if r.status_code == 400 and use_json:
                    use_json = False
                    continue
                if r.status_code == 429:
                    log(f"🚫 Groq {model_name}: ліміт (429)")
                    break
                if r.status_code in (401, 402, 403) and money_problem(f"{r.status_code} {r.text}"):
                    admin_alert("Groq", f"HTTP {r.status_code} {r.text[:200]}")
                    return None, None   # далі промпт напише Gemini
                if r.status_code in (500, 502, 503):
                    time.sleep(5)
                    continue
                log(f"❌ Groq {model_name}: HTTP {r.status_code} {r.text[:200]}")
                break
            except Exception as e:
                log(f"❌ Groq {model_name}: {str(e)[:200]}")
                break
    return None, None


def gemini_call(s, run, label_text: str):
    """503 — чекаємо і пробуємо ще; 429 (ліміт) або 404 — одразу наступна модель.
    Для оплачених замовлень слабку lite-модель не беремо: краще чесно повернути зірки, ніж поганий результат."""
    models = [m for m in ANALYSIS_MODELS if not (s.get("paid") and "lite" in m)] or ANALYSIS_MODELS
    for model_name in models:
        skip_model = False
        for key_idx, key in enumerate(api_keys, 1):
            if skip_model:
                break
            client = genai.Client(api_key=key)
            for attempt in range(1, 4):
                if cancelled(s):
                    return None, None
                set_status(s, f"{label_text} ({model_name}{', #' + str(attempt) if attempt > 1 else ''})")
                try:
                    text = run(client, model_name)
                    if text:
                        log(f"✅ {label_text}: {model_name}")
                        return text, model_name
                    break
                except Exception as err:
                    msg = str(err)
                    if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                        if attempt == 3:
                            skip_model = True
                            break
                        for _ in range(10 * attempt):
                            if cancelled(s):
                                return None, None
                            time.sleep(1)
                        continue
                    if money_problem(msg) and "429" not in msg:
                        admin_alert("Google Gemini", msg)
                        break   # цей ключ без грошей — пробуємо наступний ключ
                    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                        log(f"🚫 {model_name}: денний ліміт вичерпано (429)")
                        skip_model = True
                        break
                    if "404" in msg or "NOT_FOUND" in msg:
                        log(f"🚫 {model_name}: модель недоступна (404)")
                        skip_model = True
                        break
                    log(f"❌ {model_name} помилка: {msg[:300]}")
                    break
    return None, None


def gemini_text(s, ask, label_text):
    def run(client, model_name):
        r = client.models.generate_content(model=model_name, contents=ask)
        return r.text if r else None
    return gemini_call(s, run, label_text)


# ═══════════════════════════════════════════════════════════════
# АНАЛІЗ ВІДЕО
# ═══════════════════════════════════════════════════════════════
def analysis_fps(duration):
    try:
        d = float(duration or 0)
    except (TypeError, ValueError):
        d = 0
    if d and d <= 30:
        return 5
    if d and d <= 60:
        return 3
    return 2


def link_key(url: str):
    """Ключ пам'яті для посилання: без «хвостів» ?is_from=... — те саме відео має той самий ключ."""
    m = re.search(r"https?://\S+", url or "")
    if not m:
        return ""
    clean = m.group(0).split("?")[0].rstrip("/").lower()
    return "u:" + hashlib.md5(clean.encode()).hexdigest()


def file_key(path: str):
    """Ключ пам'яті за самим відео: той самий ролик з іншого посилання теж упізнається."""
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return "c:" + h.hexdigest()
    except Exception:
        return ""


BAD_FLAGS = ("nudity", "sexual", "gore", "minor_risk", "blocked")
BLOCKED = "__blocked__"   # «помилка», якою wait_analysis повідомляє про непристойне відео


def safety_blocked(resp):
    """Gemini не дав відповіді через правила безпеки (непристойне / жорстоке відео)."""
    try:
        fb = getattr(resp, "prompt_feedback", None)
        if fb is not None and getattr(fb, "block_reason", None):
            return True
        for c in (getattr(resp, "candidates", None) or []):
            fr = str(getattr(c, "finish_reason", "") or "")
            if any(w in fr for w in ("SAFETY", "PROHIBITED", "BLOCKLIST", "SPII")):
                return True
    except Exception:
        pass
    return False


def apply_analysis(s, analysis_text, analysis_model):
    """Розкладає розбір ролика по полях сесії (однаково для свіжого й для збереженого)."""
    s["base_analysis"] = analysis_text
    f = re.search(r"\[SAFETY_START\]\s*([A-Za-z_]+)", analysis_text or "")
    flag = f.group(1).lower() if f else "ok"
    if flag in BAD_FLAGS:
        s["content_flag"] = flag
    else:
        s.pop("content_flag", None)
    s["analysis_model"] = analysis_model
    last_analysis[s["chat_id"]] = analysis_text
    t = re.search(r"\[TRANSCRIPT_START\]\s*(.*?)\s*\[TRANSCRIPT_END\]", analysis_text, re.DOTALL)
    v = re.search(r"\[VOICE_PROFILE_START\]\s*(.*?)\s*\[VOICE_PROFILE_END\]", analysis_text, re.DOTALL)
    s["orig_transcript"] = t.group(1).strip() if t else "no speech"
    s["orig_voice"] = v.group(1).strip() if v else "no voice"
    d = re.search(r"\[DURATION_START\]\s*([\d.]+)", analysis_text)
    if d and not s.get("duration_from_source"):
        try:
            s["duration"] = max(1, min(float(d.group(1)), 180))
        except ValueError:
            pass
    h = re.search(r"start_sec\s*=\s*([\d.]+).*?end_sec\s*=\s*([\d.]+)(?:.*?reason\s*=\s*([^\]\n]+))?",
                  analysis_text, re.DOTALL)
    if h:
        try:
            s["hook"] = {"start": float(h.group(1)), "end": float(h.group(2)), "reason": (h.group(3) or "").strip()}
        except ValueError:
            pass


def from_memory(s, key):
    """Якщо цей ролик уже розбирали — беремо розбір з бази (без Gemini й без очікування)."""
    if not key:
        return False
    saved = db.get_analysis(key)
    if not saved:
        return False
    apply_analysis(s, saved["body"], saved.get("model") or "?")
    log(f"♻️ Розбір узято з пам'яті ({key[:10]}…) — Gemini не потрібен")
    return True


def mp4_duration(path):
    """Тривалість mp4 з заголовка файлу (без ffmpeg). None — якщо не вдалося."""
    try:
        import struct
        with open(path, "rb") as f:
            data = f.read(4 * 1024 * 1024)
        i = data.find(b"mvhd")
        if i < 0:
            with open(path, "rb") as f:
                f.seek(max(0, os.path.getsize(path) - 4 * 1024 * 1024))
                data = f.read()
            i = data.find(b"mvhd")
        if i < 0:
            return None
        ver = data[i + 4]
        if ver == 1:
            scale, dur = struct.unpack(">IQ", data[i + 24:i + 36])
        else:
            scale, dur = struct.unpack(">II", data[i + 16:i + 24])
        return round(dur / scale, 2) if scale else None
    except Exception:
        return None


def fetch_video_task(s, url: str, local_file: str = None, src_key: str = ""):
    """Крок 1 — одразу й безкоштовно: завантажити ролик, дізнатись тривалість, перевірити пам'ять розборів.
    Gemini тут НЕ викликається: дивитись відео будемо лише після повного вибору (Хук) або оплати."""
    L = s["lang"]
    video_path = local_file or f"temp_{s['chat_id']}_{time.time_ns()}.mp4"
    keys = [k for k in (src_key, link_key(url)) if k]
    s["mem_keys"] = keys
    keep = False
    try:
        for k in keys:              # вже бачили це посилання чи цей файл — розбір готовий
            if from_memory(s, k):
                if s.get("content_flag"):   # цей ролик уже визнано непристойним — одразу зупиняємо
                    handle_violation(s)
                    return
                set_status(s, tr(L, "st_viewed"))
                return
        if not local_file and not download_tiktok(url, video_path, s):
            s["analysis_error"] = tr(L, "e_link")
            if s.get("state") == "FORMAT" and not s.get("paid"):
                # нічого вибирати — відео немає: панель із кнопками стає карткою, Біпі пояснює, що робити
                s["state"] = "DONE"
                bad = "tiktok" not in (url or "").lower()
                if s.get("dl_reason") == "photos":   # у TikTok це фото-карусель
                    bipi_say(s["chat_id"], s["uid"], L, "artist", "sit_photo", s=s)
                else:
                    bipi_say(s["chat_id"], s["uid"], L, "oops", "sit_badlink" if bad else "sit_link", s=s)
            else:
                set_status(s, tr(L, "e_link"))
            return
        if not s.get("duration_from_source"):
            d = mp4_duration(video_path)
            if d:
                s["duration"] = max(1, min(d, 180))
                s["duration_from_source"] = True
        ck = file_key(video_path)   # те саме відео, але з іншого посилання
        if ck:
            keys.append(ck)
            if from_memory(s, ck):
                if s.get("content_flag"):
                    handle_violation(s)
                    return
                set_status(s, tr(L, "st_viewed"))
                for k in keys[:-1]:
                    db.save_analysis(k, s["base_analysis"], s.get("analysis_model") or "")
                return
        s["video_path"] = video_path
        keep = True
        if s.get("state") != "GENERATING":
            set_status(s, tr(L, "st_got"))
    except Exception as e:
        log(f"Збій завантаження: {e}")
        s["analysis_error"] = tr(L, "e_internal")
    finally:
        if not keep and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass
        s["fetch_done"] = True


def ensure_analysis(s):
    """Запустити розбір Gemini, якщо його ще немає (викликається лише перед генерацією)."""
    if "base_analysis" in s or "analysis_error" in s or s.get("analysis_started"):
        return
    s["analysis_started"] = True
    threading.Thread(target=analyze_video_task, args=(s,), daemon=True).start()


def analyze_video_task(s):
    """Крок 2 — Gemini дивиться відео. Тільки після повного вибору (Хук) або після оплати."""
    L = s["lang"]
    waited = 0
    while not s.get("fetch_done") and waited < 300:   # ролик ще завантажується
        if cancelled(s):
            return
        time.sleep(1)
        waited += 1
    if "base_analysis" in s or "analysis_error" in s:
        return
    video_path = s.get("video_path") or ""
    keys = s.get("mem_keys") or []
    if not video_path or not os.path.exists(video_path):
        s["analysis_error"] = tr(L, "e_link")
        return
    try:
        set_status(s, tr(L, "st_watch"))
        mem_log("відео завантажено, починаю аналіз")

        def run_analysis(client, model_name):
            uploaded_file = client.files.upload(file=video_path)
            try:
                sec = 0
                while uploaded_file.state.name == "PROCESSING":
                    if cancelled(s):
                        return None
                    time.sleep(1)
                    sec += 1
                    if sec > 120:
                        raise RuntimeError("Google занадто довго обробляє відео")
                    uploaded_file = client.files.get(name=uploaded_file.name)
                fps = analysis_fps(s.get("duration"))
                video_part = uploaded_file
                try:
                    from google.genai import types as gtypes
                    video_part = gtypes.Part(
                        file_data=gtypes.FileData(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type),
                        video_metadata=gtypes.VideoMetadata(fps=fps))
                except Exception as e:
                    log(f"⚠️ Не вдалося задати {fps} кадрів/сек: {e}")
                try:
                    resp = client.models.generate_content(model=model_name, contents=[video_part, ANALYSIS_SYSTEM_PROMPT])
                    if video_part is not uploaded_file:
                        log(f"🎞 Gemini дивився відео з частотою {fps} кадрів/сек")
                except Exception as e:
                    msg = str(e)
                    if video_part is not uploaded_file and ("400" in msg or "INVALID_ARGUMENT" in msg
                                                            or "video_metadata" in msg or "extra" in msg.lower()):
                        log(f"⚠️ {model_name} не прийняв fps={fps}, дивлюсь стандартно")
                        resp = client.models.generate_content(model=model_name, contents=[uploaded_file, ANALYSIS_SYSTEM_PROMPT])
                    else:
                        raise
                text = None
                try:
                    text = resp.text if resp else None
                except Exception:
                    text = None
                if resp is not None and not (text or "").strip() and safety_blocked(resp):
                    log("🚫 Gemini відмовився дивитись відео через правила безпеки")
                    return "[SAFETY_START]blocked[SAFETY_END]"
                return text
            finally:
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass

        analysis_text, analysis_model = gemini_call(s, run_analysis, tr(L, "st_watch").rstrip("."))
        if cancelled(s):
            return
        if not analysis_text:
            s["analysis_error"] = tr(L, "e_analysis")
            set_status(s, tr(L, "e_analysis"))
            return

        apply_analysis(s, analysis_text, analysis_model)
        for k in keys:              # запам'ятовуємо розбір — наступного разу буде миттєво
            db.save_analysis(k, analysis_text, analysis_model or "")
        if s.get("state") != "GENERATING":
            set_status(s, tr(L, "st_viewed"))
    except Exception as e:
        log(f"Критичний збій аналізу: {e}")
        s["analysis_error"] = tr(L, "e_internal")
    finally:
        if os.path.exists(video_path) and not s.get("keep_video"):   # Omni ще потрібен сам ролик
            try:
                os.remove(video_path)
            except Exception:
                pass
        free_memory()
        mem_log("аналіз завершено")


# ═══════════════════════════════════════════════════════════════
# ПРОМПТ
# ═══════════════════════════════════════════════════════════════
def looks_translated(L, tr_text, en_text):
    """Чи схожий другий блок на справжній переклад потрібною мовою (а не на англійський текст)."""
    t = (tr_text or "").strip()
    if len(t) < 40:
        return False
    if L in ("uk", "ru"):
        return cyr_ratio(t) >= 0.6
    if L == "ar":
        letters = re.findall(r"[^\W\d_]", t)
        return bool(letters) and sum(1 for c in letters if "\u0600" <= c <= "\u06ff") / len(letters) >= 0.5
    en_words = set(re.findall(r"[a-z]{4,}", (en_text or "").lower()))
    words = re.findall(r"[a-zà-ÿğışçöüñ]{4,}", t.lower())
    if not words:
        return False
    same = sum(1 for w in words if w in en_words) / len(words)
    return same < 0.5


def translate_ua(s, text):
    L = s["lang"] if s["lang"] != "en" else "uk"
    ask = (f"Translate this video-generation prompt into natural {tl_name(L)}. Keep time codes. Keep everything inside "
           "quotes exactly as it is (do not translate or change lyrics). Output only the translation.\n\n" + text)
    tag = L.upper()
    out, _ = groq_call(s, ask, tag)
    if not out:
        out, _ = gemini_text(s, ask, tag)
    if out and looks_translated(L, out, text):
        return out.strip()
    return None


def apply_user_note(s):
    ask = (
        "Below is a breakdown of a video made by an AI, and corrections from a human who watched the video.\n"
        "The human is ALWAYS right. Rewrite the WHOLE breakdown applying the corrections everywhere they matter: "
        "gender words and pronouns (he/she, male/female, man/woman), ages, counts, objects, actions, speed, "
        "lyrics and speech (inside [TRANSCRIPT_START]...[TRANSCRIPT_END] use the human's words exactly, keep "
        "capital letters the human used). Keep the same structure, sections and tags, change nothing else. "
        "Output only the corrected breakdown.\n\n"
        f"HUMAN CORRECTIONS:\n{s['user_note']}\n\nBREAKDOWN:\n{s['base_analysis']}"
    )
    set_status(s, tr(s["lang"], "st_note"))
    out, _ = groq_call(s, ask, tr(s["lang"], "st_note").rstrip("."))
    if not out:
        out, _ = gemini_text(s, ask, tr(s["lang"], "st_note").rstrip("."))
    if out and len(out) > 0.5 * len(s["base_analysis"]):
        s["base_analysis"] = out.strip()
        s["note_applied"] = True
        last_analysis[s["chat_id"]] = s["base_analysis"]
        t = re.search(r"\[TRANSCRIPT_START\]\s*(.*?)\s*\[TRANSCRIPT_END\]", out, re.DOTALL)
        v = re.search(r"\[VOICE_PROFILE_START\]\s*(.*?)\s*\[VOICE_PROFILE_END\]", out, re.DOTALL)
        if t:
            s["orig_transcript"] = t.group(1).strip()
        if v:
            s["orig_voice"] = v.group(1).strip()
        log("✅ Розбір виправлено за уточненням користувача")


def wait_analysis(s):
    """Запускає (якщо треба) і чекає розбір. Повертає None або текст помилки ("cancel" — скасовано)."""
    L = s["lang"]
    fresh = "base_analysis" not in s and "analysis_error" not in s
    ensure_analysis(s)   # саме тепер (вибір зроблено / оплачено) Gemini дивиться відео
    if fresh:
        s["bipi_gen"] = ("detective", ph.pick(s["uid"], "wait_an", L))
        set_status(s, ph.pick(s["uid"], "wait_an", L))
    timer = 0
    while "base_analysis" not in s and "analysis_error" not in s:
        if cancelled(s):
            return "cancel"
        time.sleep(1)
        timer += 1
        if timer % 6 == 0:   # фраза очікування міняється, щоб не нудно було чекати
            set_status(s, f"{ph.pick(s['uid'], 'wait_an', L)} · {timer} s")
        if timer > 900:
            return tr(L, "e_analysis")
    if s.get("content_flag") and not s.get("analysis_error"):
        return BLOCKED
    return s.get("analysis_error")


def handle_violation(s, order=None):
    """Непристойне відео: зупиняємо ДО генерації. Платне замовлення — без повернення зірок (так у правилах).
    1-ше порушення — попередження, 2-ге — блок. Адміну — повідомлення (може зняти блок /unban)."""
    L, chat_id, uid = s["lang"], s["chat_id"], s["uid"]
    s["cancel"] = True
    s["state"] = "DONE"
    n = 0 if is_admin(uid) else db.add_strike(uid)
    warn = tr(L, "nsfw_warn1") if n == 1 else None
    if n >= 2:
        bipi_say(chat_id, uid, L, "guard", "sit_ban", s=s)
    elif order:
        bipi_say(chat_id, uid, L, "guard", "sit_nsfw_paid", s=s, caption=warn)
    else:
        bipi_say(chat_id, uid, L, "shy", "sit_nsfw", s=s, caption=warn)
    what = f"замовлення #{order['id']} ({order.get('stars') or 0} ⭐, без повернення)" if order else "безкоштовний Хук"
    note = (f"🚫 Непристойне відео ({s.get('content_flag')}) від користувача {uid}: {what}. "
            f"Порушення №{n}{' → заблоковано' if n >= 2 else ''}.\n"
            f"Помилка фільтра? Розблокувати: /unban {uid}" + (f" · повернути зірки: /refund {order['id']}" if order else ""))
    for aid in ADMIN_IDS:
        try:
            bot.send_message(aid, note)
        except Exception:
            pass
    log(f"🚫 Порушення від {uid}: {s.get('content_flag')} ({what}), №{n}")


def blocked_user(msg):
    """Заблокований за порушення — далі не пускаємо (адмін може зняти /unban)."""
    uid = msg.from_user.id
    if is_admin(uid) or not db.is_banned(uid):
        return False
    bipi_say(msg.chat.id, uid, user_lang(msg.from_user), "guard", "sit_ban", ttl=30)
    return True


def make_prompt(s):
    """Чекає аналіз, пише промпт. Повертає (segment, data, prompt_model) або (None, помилка, None)."""
    L = s["lang"]
    err = wait_analysis(s)
    if err:
        return None, err, None

    if s.get("user_note") and not s.get("note_applied"):
        apply_user_note(s)
    instruction = build_prompt_instruction(s)

    def run_prompt(client, model_name):
        resp = client.models.generate_content(model=model_name, contents=instruction,
                                              config={"response_mime_type": "application/json"})
        return resp.text if resp else None

    label_text = tr(L, "st_writing").rstrip(".")
    raw, prompt_model = groq_call(s, instruction, label_text, json_mode=True)
    data = parse_json_loose(raw)
    if not data and not cancelled(s):
        raw, prompt_model = gemini_call(s, run_prompt, label_text)
        data = parse_json_loose(raw)
    if cancelled(s):
        return None, "cancel", None
    if not data or not data.get("segments"):
        return None, tr(L, "e_prompt"), None
    polish_segments(s, data)
    return data["segments"][0], data, prompt_model


_copy_store = {}   # (chat_id, message_id) → {"en": ..., "ua": ...} для кнопок «Скопіювати»
_next_store = {}   # (chat_id, message_id) → сесія, з якої зроблено результат (для кнопки «Що далі?»)


def drop_panel(s):
    """Результат готовий — панель налаштувань (з картинкою «Генерую…») прибираємо, щоб не плутала."""
    if not s.get("msg_id"):
        return
    try:
        bot.delete_message(s["chat_id"], s["msg_id"])
        s["msg_id"] = None
    except Exception:
        pass


def next_keyboard(L, admin=False):
    kb = tg_types.InlineKeyboardMarkup()
    kb.row(btn(tr(L, "new_prompt_btn"), "rv_new"))
    kb.row(btn(tr(L, "next_btn"), "ag_next"))
    return kb


def remember_next(chat_id, msg, s):
    try:
        _next_store[(chat_id, msg.message_id)] = s
        if len(_next_store) > 500:
            _next_store.pop(next(iter(_next_store)))
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data == "rv_go")
def handle_make_video(call):
    """«Робимо відео?» під безкоштовним промптом → вибір моделі й оплата, промпт той самий."""
    s = _next_store.get((call.message.chat.id, call.message.message_id))
    L = user_lang(call.from_user)
    if not s or "base_analysis" not in s or not s.get("ready_seg"):
        bot.answer_callback_query(call.id, tr(L, "analysis_gone"), show_alert=True)
        return
    if not any(model_ready(k) for k in VIDEO_MODELS):
        bot.answer_callback_query(call.id, tr(L, "paid_off"), show_alert=True)
        return
    bot.answer_callback_query(call.id)
    new = offer_again(s, force=True, state="CONFIRM", key="pic_model")
    if new:
        new.update(gen_mode="v8", reuse_prompt=True)
        ui(new)


@bot.callback_query_handler(func=lambda c: c.data == "rv_new")
def handle_new_prompt(call):
    """«Робимо інший промпт» → знову вибір Танці / Кіно / Анімація. Ролик не аналізуємо вдруге."""
    s = _next_store.get((call.message.chat.id, call.message.message_id))
    L = user_lang(call.from_user)
    if not s or "base_analysis" not in s:
        bot.answer_callback_query(call.id, tr(L, "analysis_gone"), show_alert=True)
        return
    if s.get("gen_mode") == "hook" and not can_hook(s):
        bot.answer_callback_query(call.id, tr(L, "no_free"), show_alert=True)
        return
    bot.answer_callback_query(call.id)
    new = offer_again(s, force=True, state="STYLE_CAT", key="pic_cat")
    if new:
        new.pop("reuse_prompt", None)
        new["restyle"] = True
        ui(new)


@bot.callback_query_handler(func=lambda c: c.data == "ag_next")
def handle_next(call):
    """«Що далі?» — панель з варіантами з'являється лише на вимогу."""
    s = _next_store.get((call.message.chat.id, call.message.message_id))
    if not s or "base_analysis" not in s:
        bot.answer_callback_query(call.id, tr(user_lang(call.from_user), "analysis_gone"), show_alert=True)
        return
    bot.answer_callback_query(call.id)
    offer_again(s, force=True)


TG_PART = 3500   # Telegram приймає до 4096 знаків в одному повідомленні — лишаємо запас


def split_text(text, limit=TG_PART):
    """Ділить довгий текст на частини по межі речення (ніколи не рве слово)."""
    text = (text or "").strip()
    parts = []
    while len(text) > limit:
        cut = text[:limit]
        pos = max(cut.rfind("\n"), cut.rfind(". "), cut.rfind("; "))
        if pos < limit * 0.5:
            pos = cut.rfind(" ")
        if pos <= 0:
            pos = limit - 1
        parts.append(text[:pos + 1].strip())
        text = text[pos + 1:].strip()
    if text:
        parts.append(text)
    return parts or [""]


def send_prompt_box(chat_id, text, label, fold=False):
    """Промпт окремим повідомленням без заголовків.
    fold=False — блок коду: одне торкання копіює весь текст (і є значок «Копіювати» в шапці блоку).
    fold=True — згорнута цитата (для перекладу: його читають, а не копіюють).
    Довгий текст іде кількома такими ж блоками — ніколи не «простирадлом» звичайного тексту."""
    last = None
    for part in split_text(text):
        body = html.escape(part)
        variants = ([f"<blockquote expandable>{body}</blockquote>"] if fold else []) + \
                   [f'<pre><code class="language-{label}">{body}</code></pre>']
        sent = None
        for variant in variants:
            try:
                sent = bot.send_message(chat_id, variant, parse_mode="HTML")
                break
            except Exception as e:
                log(f"Промпт-блок не прийнято ({str(e)[:80]})")
        last = sent or send_safe_message(chat_id, part, parse_mode=None)
    return last


def send_prompt(s, seg, data, prompt_model):
    """Компактно: заголовок + промпт EN і переклад у згорнутих блоках (торкнись — розгорнеться) + кнопки копіювання."""
    L, chat_id = s["lang"], s["chat_id"]
    try:
        if s.get("gen_mode") == "v30":
            head = tr(L, "full_head", d=s.get("v30_sec") or full_seconds(s))
        else:
            wa, wb = hook_window(s)
            head = tr(L, "hook_head", a=f"{wa:g}", b=f"{wb:g}")
        head = html.escape(head.replace("*", ""))
        en, ua = (seg.get("prompt_en") or "").strip(), (seg.get("prompt_ua") or "").strip()
        # Кожен промпт — окреме повідомлення лише з текстом: торкнутися — розгорнути,
        # затиснути → «Копіювати» копіює рівно промпт, без заголовків.
        send_prompt_box(chat_id, en, "EN")   # торкнувся — скопіював увесь промпт
        show_ua = L != "en" and ua
        if show_ua:
            send_prompt_box(chat_id, ua, L.upper(), fold=True)
        parts = [f"<b>{head}</b>"]
        reason = data.get("hook_reason_ua") or ""
        if reason and L != "en" and s.get("gen_mode") != "v30":
            parts.append(f"💡 {html.escape(reason)}")
        parts.append(tr(L, "prompt_hint_ua" if show_ua else "prompt_hint"))
        parts.append(f"<i>{html.escape(ph.pick(s['uid'], 'prompt_done', L))}</i>")   # тепла фраза від бота
        if is_admin(s["uid"]):
            parts.append(f"🧠 {html.escape(s.get('analysis_model', '?'))} · {html.escape(prompt_model or '—')}")
        kb = tg_types.InlineKeyboardMarkup()
        if show_ua:   # англійський уже копіюється дотиком; переклад — окремим блоком на вимогу
            kb.row(btn(tr(L, "copy_ua"), "cp_ua"))
        if s.get("gen_mode") == "hook" and any(model_ready(k) for k in VIDEO_MODELS):
            kb.row(btn(tr(L, "make_video_btn"), "rv_go"))
        kb.row(btn(tr(L, "new_prompt_btn"), "rv_new"), btn(tr(L, "txt_btn"), "cp_txt"))
        msg = bot.send_message(chat_id, "\n\n".join(parts), parse_mode="HTML", reply_markup=kb)
        _copy_store[(chat_id, msg.message_id)] = {"en": en, "ua": ua}
        remember_next(chat_id, msg, s)
        if len(_copy_store) > 500:
            _copy_store.pop(next(iter(_copy_store)))
        return
    except Exception as e:
        log(f"Компактний промпт не вийшов ({str(e)[:80]}), шлю звичайним текстом")
    send_prompt_plain(s, seg, data, prompt_model)


@bot.callback_query_handler(func=lambda c: c.data in ("cp_en", "cp_ua", "cp_txt"))
def handle_copy(call):
    L = user_lang(call.from_user)
    item = _copy_store.get((call.message.chat.id, call.message.message_id))
    if call.data == "cp_txt" and item:
        bot.answer_callback_query(call.id)
        body = f"PROMPT (EN)\n\n{item['en']}\n"
        if item.get("ua"):
            body += f"\n{'─' * 30}\n\nПЕРЕКЛАД (UA)\n\n{item['ua']}\n"
        try:
            bot.send_document(call.message.chat.id, io.BytesIO(body.encode("utf-8")),
                              visible_file_name=f"prompt_{call.message.message_id}.txt")
        except Exception as e:
            log(f"txt не надіслано: {e}")
        return
    text = (item or {}).get(call.data[3:])
    if not text:
        bot.answer_callback_query(call.id, tr(L, "old_menu"), show_alert=True)
        return
    bot.answer_callback_query(call.id, tr(L, "copy_hint"))
    tag = "EN" if call.data == "cp_en" else L.upper()
    send_prompt_box(call.message.chat.id, text, tag)   # блок коду: дотик копіює; довгий — частинами


def send_prompt_plain(s, seg, data, prompt_model):
    L, chat_id = s["lang"], s["chat_id"]
    if s.get("gen_mode") == "v30":
        head = tr(L, "full_head", d=s.get("v30_sec") or full_seconds(s))
    else:
        wa, wb = hook_window(s)
        head = tr(L, "hook_head", a=f"{wa:g}", b=f"{wb:g}")
        reason = data.get("hook_reason_ua") or ""
        if reason and L != "en":
            head += f"\n💡 {reason}"
    models_line = f"🧠 `{s.get('analysis_model', '?')}` · `{prompt_model or '—'}`"
    send_safe_message(chat_id, f"{head}\n\n{tr(L, 'prompt_en')}\n`{clean_code(seg.get('prompt_en'))}`")
    tail = models_line if is_admin(s["uid"]) else ""
    if L != "en" and seg.get("prompt_ua"):
        send_safe_message(chat_id, f"{tr(L, 'translation')}\n{seg.get('prompt_ua', '')}\n\n{tail}",
                          reply_markup=analysis_button(L))
    else:
        send_safe_message(chat_id, tail or "✅", reply_markup=analysis_button(L))


def run_free_prompt(s):
    L = s["lang"]
    seg, data, prompt_model = make_prompt(s)
    if seg is None:
        if data == BLOCKED:
            handle_violation(s)
        elif data != "cancel":
            s["state"] = "DONE"
            bipi_say(s["chat_id"], s["uid"], L, "oops", "oops_free", s=s, caption=data)
        return
    if is_admin(s["uid"]):
        db.count_prompt(s["uid"])
    elif not db.consume_prompt(s["uid"], FREE_PER_DAY):
        s["state"] = "DONE"
        bipi_say(s["chat_id"], s["uid"], L, "sleepy", "sit_limit", s=s, caption=tr(L, "no_free"))
        return
    s["state"] = "DONE"
    set_status(s, tr(L, "st_done"))
    send_prompt(s, seg, data, prompt_model)
    drop_panel(s)
    s["ready_seg"] = (seg, data, prompt_model)   # для кнопки «Зробити з цього відео»


# ═══════════════════════════════════════════════════════════════
# ПОВТОР: той самий ролик ще раз — без повторного аналізу
# ═══════════════════════════════════════════════════════════════
_SKIP_ON_COPY = ("msg_id", "state", "history", "paid", "cancel", "live_status", "_last", "_kb_sig", "video_path",
                 "v30_sec", "analysis_error", "restyle", "prev_choices", "reuse_prompt", "_bp", "bipi_gen", "pic_key")


def offer_again(s, force=False, state="AGAIN", key="pic_done"):
    """Панель «Що далі?»: відео з цього промпту / інший стиль / почати заново (без нового аналізу)."""
    chat_id, L = s["chat_id"], s["lang"]
    if "base_analysis" not in s or (not force and user_sessions.get(chat_id) is not s):
        return
    cur = user_sessions.get(chat_id)
    if cur is not None and cur is not s and not cur.get("paid") and cur.get("state") not in ("AGAIN", "DONE"):
        cur["cancel"] = True   # незавершене налаштування іншого ролика замінюємо
    new = {k: v for k, v in s.items() if k not in _SKIP_ON_COPY}
    new["prev_choices"] = [k for _, keys in s.get("history", []) for k in keys]
    new.update(state=state, history=[], paid=False, cancel=False, live_status=tr(L, "again_status"))
    try:
        msg, new["photo"] = send_panel(chat_id, L, key=key)
        new["pic"] = key
    except Exception as e:
        log(f"Панель повтору не надіслана: {e}")
        return
    new["msg_id"] = msg.message_id
    user_sessions[chat_id] = new
    ui(new)
    return new


def can_hook(s):
    free, extra = db.free_left(s["uid"], FREE_PER_DAY)
    return bool(free or extra or is_admin(s["uid"]))


@bot.callback_query_handler(func=lambda c: c.data == "ag_video")
def handle_again_video(call):
    """Безкоштовний промпт сподобався → готове відео саме з нього (без нового аналізу й нового промпту)."""
    s = session_for(call)
    if not s or s.get("state") != "AGAIN" or not s.get("ready_seg"):
        return
    if not any(model_ready(k) for k in VIDEO_MODELS):
        bot.answer_callback_query(call.id, tr(s["lang"], "paid_off"), show_alert=True)
        return
    bot.answer_callback_query(call.id)
    s.update(gen_mode="v8", reuse_prompt=True, state="CONFIRM", history=[])
    ui(s)


@bot.callback_query_handler(func=lambda c: c.data in ("ag_all", "ag_style"))
def handle_again(call):
    s = session_for(call)
    if not s or s.get("state") != "AGAIN":
        return
    L = s["lang"]
    s.pop("reuse_prompt", None)
    if call.data == "ag_all":
        for k in s.get("prev_choices", []) + ["user_note", "gen_mode", "model"]:
            s.pop(k, None)
        bot.answer_callback_query(call.id)
        s.update(state="FORMAT", history=[], live_status=tr(L, "again_status"))
        ui(s)
        return
    if s.get("gen_mode") == "hook" and not can_hook(s):
        bot.answer_callback_query(call.id, tr(L, "no_free"), show_alert=True)
        return
    bot.answer_callback_query(call.id)
    s.update(state="STYLE_CAT", history=[], restyle=True)
    ui(s)


def genre_fits(s):
    g = s.get("genre")
    table = ANIM_GENRES if s.get("style_cat") == "anim" else FILM_GENRES
    return g == "orig" or g in table


# ═══════════════════════════════════════════════════════════════
# ГОТОВЕ ВІДЕО: fal.ai (LTX, Kling) і Google (Omni)
# ═══════════════════════════════════════════════════════════════
def fal_headers():
    return {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}


def fetch_to_file(url: str, path: str, timeout=180):
    """Качає файл шматками прямо на диск (не тримає відео в пам'яті). Повертає шлях або None."""
    try:
        with requests.get(url, headers=UA_HEADERS, timeout=timeout, stream=True) as r:
            if r.status_code != 200:
                log(f"Не вдалося завантажити файл: HTTP {r.status_code}")
                return None
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=256 * 1024):
                    if chunk:
                        f.write(chunk)
        if os.path.getsize(path) > 10000:
            return path
    except Exception as e:
        log(f"Не вдалося завантажити файл: {e}")
    try:
        os.remove(path)
    except Exception:
        pass
    return None


def _elapsed(t0):
    e = int(time.time() - t0)
    return f"{e // 60}:{e % 60:02d}"


def fal_video(s, endpoint, payload, max_wait=900):
    """Черга fal: відправити → чекати → повернути (url, помилка)."""
    L = s["lang"]
    try:
        r = requests.post(f"https://queue.fal.run/{endpoint}", headers=fal_headers(), json=payload, timeout=60)
        if r.status_code == 422 and isinstance(payload.get("duration"), int):
            payload = dict(payload, duration=str(payload["duration"]))  # деякі моделі хочуть тривалість рядком
            r = requests.post(f"https://queue.fal.run/{endpoint}", headers=fal_headers(), json=payload, timeout=60)
        if r.status_code != 200:
            return None, f"fal HTTP {r.status_code}: {r.text[:200]}"
        job = r.json()
        status_url, response_url = job.get("status_url"), job.get("response_url")
        if not status_url or not response_url:
            return None, "fal: no job address"
        t0, last = time.time(), 0
        while time.time() - t0 < max_wait:
            time.sleep(5)
            st = requests.get(status_url, headers=fal_headers(), timeout=30).json()
            status = st.get("status")
            if time.time() - last > 15:   # статус + весела фраза очікування (щоразу інша)
                set_status(s, tr(L, "v_queue" if status == "IN_QUEUE" else "v_gen", t=_elapsed(t0))
                           + "\n" + ph.pick(s["uid"], "sit_busy" if status == "IN_QUEUE" and time.time() - t0 > 90
                                             else "wait_gen", L))
                last = time.time()
            if status == "COMPLETED":
                if st.get("error"):
                    return None, f"fal: {st.get('error')}"
                res = requests.get(response_url, headers=fal_headers(), timeout=60).json()
                url = (res.get("video") or {}).get("url")
                return (url, None) if url else (None, f"fal: {str(res)[:200]}")
        return None, "timeout"
    except Exception as e:
        return None, f"fal: {str(e)[:200]}"


def omni_video(s, prompt, clip=None):
    """Gemini Omni 1.1 Flash через окремий платний ключ Google. З clip — переробляє сам ролик
    (відео → відео), без clip — робить відео з тексту. Повертає (bytes, помилка)."""
    client, up = None, None
    try:
        client = genai.Client(api_key=OMNI_API_KEY)
        if not hasattr(client, "interactions"):
            return None, "google-genai library is too old for Omni"
        inp = prompt
        if clip:
            up = client.files.upload(file=clip)
            waited = 0
            while str(getattr(getattr(up, "state", None), "name", "")) == "PROCESSING" and waited < 180:
                time.sleep(2)
                waited += 2
                up = client.files.get(name=up.name)
            if str(getattr(getattr(up, "state", None), "name", "")) == "FAILED":
                return None, "omni: Google could not process the input video"
            inp = [{"type": "video", "uri": up.uri}, {"type": "text", "text": prompt}]
        it = client.interactions.create(
            model=VIDEO_MODELS["omni"]["endpoint"], input=inp,
            response_format={"type": "video", "aspect_ratio": "9:16", "resolution": "720p"})
        ov = getattr(it, "output_video", None)
        data = getattr(ov, "data", None)
        if data:
            return (base64.b64decode(data) if isinstance(data, str) else data), None
        uri = getattr(ov, "uri", None)
        if uri:
            return client.files.download(file=uri), None
        return None, "omni: empty answer"
    except Exception as e:
        return None, f"omni: {str(e)[:250]}"
    finally:
        if client and up:
            try:
                client.files.delete(name=up.name)
            except Exception:
                pass


# ── Omni: «копія оригіналу» — сам ролик іде в Omni, промпт лише про людей, стиль і світ ──
OMNI_MAX_INPUT = 10   # Omni переробляє ролики до 10 с
_REGION_WORDS = ("region", "location", "country", "not available in your", "not supported in your",
                 "eea", "european", "unsupported_location", "user location")


def region_problem(msg):
    m = (msg or "").lower()
    return any(w in m for w in _REGION_WORDS)


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def omni_source(s):
    """Сам ролик: той, що вже на диску, або беремо ще раз (якщо розбір був із пам'яті і ролик не качали)."""
    vp = s.get("video_path")
    if vp and os.path.exists(vp):
        return vp
    path = f"temp_{s['chat_id']}_{time.time_ns()}.mp4"
    try:
        if s.get("src_file_id"):
            info = bot.get_file(s["src_file_id"])
            with open(path, "wb") as f:
                f.write(bot.download_file(info.file_path))
        elif not (s.get("src_url") and download_tiktok(s["src_url"], path, s)):
            return None
        s["video_path"] = path
        return path
    except Exception as e:
        log(f"Omni: не вдалося знову взяти ролик: {e}")
        return None


def omni_clip(s, src, out):
    """Шматок до 10 с для Omni: короткий ролик — цілком, довгий — ключовий момент (8 с)."""
    dur = float(s.get("duration") or CLIP_SECONDS)
    a, b = (0.0, dur) if dur <= OMNI_MAX_INPUT else hook_window(s)
    exe = ffmpeg_exe()
    if not exe:
        log("Omni: немає ffmpeg — шматок не вирізати")
        return src if dur <= OMNI_MAX_INPUT else None
    cmd = [exe, "-y", "-v", "error", "-ss", f"{a:.2f}", "-i", src, "-t", f"{min(b - a, OMNI_MAX_INPUT):.2f}",
           "-vf", "scale=-2:'min(1280,ih)'", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out]
    try:
        subprocess.run(cmd, timeout=180, check=True)
        return out if os.path.exists(out) and os.path.getsize(out) > 10000 else None
    except Exception as e:
        log(f"Omni: ffmpeg не вирізав шматок: {str(e)[:150]}")
        return None


def omni_people(s):
    """Хто в кадрі — лише коротко («a man in his 30s; a woman in her early 20s»), без одягу і дій."""
    ask = ("From this video breakdown, list who is clearly visible as short labels with gender and a clear adult "
           "age, e.g. 'a man in his 30s', 'a woman in her early 20s', 'a dog'. At most 3 labels; if there are more "
           "people, end with 'and N more people'. If someone looks under 18, write only 'a child' or 'a teenager'. "
           "No clothing, no actions, no names, no religion, ethnicity or nationality. Answer with ONE line, labels "
           "separated by '; '.\n\nBREAKDOWN:\n" + (s.get("base_analysis") or "")[:6000])
    label_text = tr(s["lang"], "st_writing").rstrip(".")
    txt, _ = groq_call(s, ask, label_text)
    if not txt:
        txt, _ = gemini_text(s, ask, label_text)
    line = (txt or "").strip().splitlines()[0].strip(" .\"'*`") if (txt or "").strip() else ""
    return line[:200] if 3 < len(line) else "the people in the video"


def omni_prompt(s, people):
    """Промпт для Omni (відео → відео): спершу хто в кадрі, далі лише стиль і світ. Дій не описуємо —
    рухи, темп і камеру Omni бере з самого ролика."""
    st, gn = style_info(s), genre_info(s)
    look = "" if (s.get("style_cat") == "orig" or s.get("style") == "orig") else re.split(r"\s*SOUND:", st[3])[0].strip()
    world = "" if s.get("genre") in (None, "orig") else re.split(r"\s*MUSIC FEEL:", gn[3])[0].strip()
    lines = [f"Restyle this video. People: {people}.",
             "Keep every person, every movement and gesture, the timing and the camera exactly as they are; "
             "change only how the video looks and the world around them."]
    if look:
        lines.append(f"Style: {look}")
    if world:
        lines.append(f"World: {world}")
    lines.append("No on-screen text, no subtitles, no watermark, no logos, no extra people.")
    return "\n".join(lines)


def omni_prepare(s, order_id):
    """Розбір (лише щоб знати, хто в кадрі, і де ключовий момент) → шматок ролику → короткий промпт.
    Повертає (segment, data, prompt_model, шлях до шматка) або (None, помилка, None, None)."""
    L = s["lang"]
    s["keep_video"] = True   # розбір не видаляє ролик — він потрібен Omni
    err = wait_analysis(s)
    if err:
        return None, err, None, None
    src = omni_source(s)
    if not src:
        return None, tr(L, "e_link"), None, None
    clip = omni_clip(s, src, f"omni_in_{order_id}.mp4")
    if not clip:
        return None, tr(L, "e_video"), None, None
    seg = {"prompt_en": omni_prompt(s, omni_people(s))}
    return seg, {"segments": [seg]}, "Omni", clip


VIDEO_PROMPT_MAX = 2500   # Kling радить до 2500 знаків; довше — модель губиться або відкидає


def fit_prompt(text, limit=VIDEO_PROMPT_MAX):
    """Дуже довгий промпт обрізаємо по межі речення (лише для відеомоделі; людина бачить повний)."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    pos = max(cut.rfind(". "), cut.rfind(".\n"), cut.rfind("\n"))
    return (cut[:pos + 1] if pos > limit * 0.6 else cut).strip()


def generate_video(s, key, seconds, prompt, path, clip=None):
    """Повертає (шлях до файлу або None, url або None, помилка або None)."""
    m = VIDEO_MODELS[key]
    set_status(s, tr(s["lang"], "st_video", model=m["name"]))
    if m["provider"] == "gemini":
        data, err = omni_video(s, prompt if clip else f"{prompt}\nLength: {seconds} seconds. Vertical 9:16.", clip)
        if err or not data:
            return None, None, err
        with open(path, "wb") as f:
            f.write(data)
        del data
        free_memory()
        return path, None, None
    payload = {"prompt": fit_prompt(prompt), "aspect_ratio": "9:16", "duration": seconds, **m["params"]}
    url, err = fal_video(s, m["endpoint"], payload)
    if err:
        return None, None, err
    return None, url, None   # спершу пробуємо віддати Telegram посилання — так бот взагалі не тримає відео


def paid_today_count():
    t0 = time.mktime(time.strptime(db.today(), "%Y-%m-%d"))
    row = db._q("SELECT COUNT(*) FROM orders WHERE created>=? AND status IN ('running','done') AND kind!='pack'",
                (t0,), one=True)
    return db._first(row) or 0


def refund(order, err, lang, chat_id):
    stars = order.get("stars") or 0
    if not order.get("charge_id") or stars <= 0:
        db.set_order(order["id"], "failed")
        bipi_say(chat_id, order.get("user_id"), lang, "oops", "oops_free", caption=f"❌ {err}")
        return
    try:
        bot.refund_star_payment(order["user_id"], order["charge_id"])
        db.set_order(order["id"], "refunded")
        log(f"↩️ Повернуто {stars} ⭐ за замовлення #{order['id']}")
        bipi_say(chat_id, order.get("user_id"), lang, "oops", "sit_tech" if err == tr(lang, "e_service") else "error",
                 caption=tr(lang, "refunded", err=err, stars=stars))
    except Exception as e:
        db.set_order(order["id"], "refund_failed")
        log(f"❌ Повернення не вдалося #{order['id']}: {e}")
        send_safe_message(chat_id, tr(lang, "refund_fail", err=err, stars=stars), parse_mode=None)


def run_paid_order(s, order_id):
    """Оплачене (або адмінське) замовлення: промпт → відео. При будь-якій невдачі — повернення зірок."""
    L, chat_id = s["lang"], s["chat_id"]
    order = db.get_order(order_id)
    stars, cost, seconds, key = order_info(s)
    if paid_today_count() >= PAID_DAILY_CAP:
        refund(order, tr(L, "cap_reached"), L, chat_id)
        return
    db.set_order(order_id, "running")
    s.update(paid=True, cancel=False, state="GENERATING")
    if s.get("gen_mode") == "v30":
        s["v30_sec"] = seconds
    ui(s)

    clip = None
    if key == "omni":   # Omni переробляє сам ролик: короткий промпт без опису дій
        seg, data, prompt_model, clip = omni_prepare(s, order_id)
    elif s.get("reuse_prompt") and s.get("ready_seg"):
        seg, data, prompt_model = s["ready_seg"]   # той самий промпт, який людина вже бачила
    else:
        seg, data, prompt_model = make_prompt(s)
    if seg is None:
        if key == "omni":
            s.pop("keep_video", None)
        if data == BLOCKED:   # непристойне відео: генерацію не запускаємо, зірки не повертаємо (правила)
            db.set_order(order_id, "blocked")
            handle_violation(s, db.get_order(order_id))
            return
        refund(db.get_order(order_id), data if data != "cancel" else tr(L, "e_prompt"), L, chat_id)
        s["state"] = "DONE"
        set_status(s, "❌")
        return
    db.count_prompt(s["uid"])   # промпт прийде файлом разом із готовим відео

    log(f"🎬 Замовлення #{order_id}: {VIDEO_MODELS[key]['name']}, {seconds} с, {stars} ⭐")
    mem_log(f"замовлення #{order_id}: старт генерації")
    cleanup_old_files()
    vpath = f"out_{order_id}.mp4"
    s["bipi_gen"] = ("director", ph.pick(s["uid"], "wait_gen", L))
    ui(s)
    video, url, err = generate_video(s, key, seconds, seg.get("prompt_en", ""), vpath, clip=clip)
    mem_log(f"замовлення #{order_id}: відео готове")
    if clip:   # шматок і сам ролик Omni більше не потрібні
        for f in {clip, s.get("video_path")}:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
        s.pop("video_path", None)
        s.pop("keep_video", None)
    if err or (not video and not url):
        log(f"❌ Відео #{order_id}: {err}")
        svc = "Google Omni" if VIDEO_MODELS[key]["provider"] == "gemini" else "fal.ai"
        if money_problem(err):
            admin_alert(svc, err)
            user_err = tr(L, "e_service")
        elif clip and region_problem(err):
            admin_alert(svc, err, "⚠️ Google Omni: переробка відео недоступна з регіону сервера "
                                  "(Google не дозволяє її з ЄС, а сервер Render — у Франкфурті). "
                                  "Зірки людям повертаються автоматично.")
            user_err = tr(L, "e_service")
        else:
            user_err = tr(L, "e_video")   # людині — без технічних подробиць
        refund(db.get_order(order_id), user_err, L, chat_id)
        s["state"] = "DONE"
        set_status(s, "❌")
        send_prompt_file(s, seg, data, prompt_model, order_id)
        return
    caption = tr(L, "video_caption", model=VIDEO_MODELS[key]["name"]) + "\n" + ph.pick(s["uid"], "video_done", L)
    db.set_order_note(order_id, url if url else f"file:{video}")   # для кнопки «Завантажити»
    dl_kb = tg_types.InlineKeyboardMarkup()
    dl_kb.row(btn(tr(L, "dl_btn"), f"dl_{order_id}"))
    sent = False
    if url:   # 1) Telegram сам забирає відео за посиланням — пам'ять бота не потрібна
        try:
            bot.send_video(chat_id, url, caption=caption, supports_streaming=True, reply_markup=dl_kb)
            sent = True
        except Exception as e:
            log(f"Telegram не взяв відео за посиланням ({str(e)[:120]}), качаю файл")
            video = fetch_to_file(url, vpath)
    if not sent and video:   # 2) відправка з файлу на диску
        try:
            if os.path.getsize(video) <= 49 * 1024 * 1024:
                with open(video, "rb") as f:
                    bot.send_video(chat_id, f, caption=caption, supports_streaming=True, reply_markup=dl_kb)
                sent = True
        except Exception as e:
            log(f"Не вдалося надіслати відео: {e}")
    if not sent and url:   # 3) запасний варіант — просто посилання
        send_safe_message(chat_id, tr(L, "video_link", url=url), parse_mode=None)
        sent = True
    if url:   # файл з fal можна викачати знову за посиланням; файл Omni лишаємо на диску для «Завантажити»
        try:
            if os.path.exists(vpath):
                os.remove(vpath)
        except Exception:
            pass
    free_memory()
    mem_log(f"замовлення #{order_id}: завершено")
    db.set_order(order_id, "done")
    db.add_spent(s["uid"], order.get("stars") or 0)
    if (order.get("stars") or 0) > 0:
        reward_referrer(s["uid"])
    s["state"] = "DONE"
    send_prompt_file(s, seg, data, prompt_model, order_id)
    drop_panel(s)


def cleanup_old_files(max_age=6 * 3600):
    """Прибирає старі відеофайли з диска (Omni та завантаження)."""
    for name in os.listdir("."):
        if name.startswith(("out_", "dl_", "temp_", "omni_in_")) and name.endswith(".mp4"):
            try:   # temp_ — ролики, які так і не дійшли до розбору (людина не завершила вибір)
                if time.time() - os.path.getmtime(name) > (2 * 3600 if name.startswith("temp_") else max_age):
                    os.remove(name)
            except Exception:
                pass
        elif name.startswith("bipi_") and name.endswith((".webm", ".webp", ".mp4")):   # тимчасовий файл Біпі
            try:
                if time.time() - os.path.getmtime(name) > 600:
                    os.remove(name)
            except Exception:
                pass


def send_prompt_file(s, seg, data, prompt_model, order_id):
    """Промпт до готового відео — файлом .txt (а не довгим текстом у чаті)."""
    L, chat_id = s["lang"], s["chat_id"]
    parts = [f"PROMPT (EN)\n\n{seg.get('prompt_en', '').strip()}"]
    if seg.get("negative"):
        parts.append(f"NEGATIVE PROMPT\n\n{seg['negative'].strip()}")
    if L != "en" and seg.get("prompt_ua"):
        parts.append(f"TRANSLATION ({L.upper()})\n\n{seg['prompt_ua'].strip()}")
    body = ("\n\n" + "─" * 30 + "\n\n").join(parts) + "\n"
    caption = tr(L, "prompt_file_caption")
    if is_admin(s["uid"]):
        caption += f"\n🧠 {s.get('analysis_model', '?')} · {prompt_model or '—'}"
    try:
        f = io.BytesIO(body.encode("utf-8"))
        m = bot.send_document(chat_id, f, caption=caption, visible_file_name=f"prompt_{order_id}.txt",
                              reply_markup=next_keyboard(L, is_admin(s["uid"])))
        remember_next(chat_id, m, s)
    except Exception as e:
        log(f"Файл промпту не надіслано: {e}")
        send_prompt(s, seg, data, prompt_model)


@bot.callback_query_handler(func=lambda c: c.data.startswith("dl_"))
def handle_download(call):
    L = user_lang(call.from_user)
    try:
        order = db.get_order(int(call.data[3:]))
    except ValueError:
        order = None
    if not order or order["user_id"] != call.from_user.id or not order.get("note"):
        bot.answer_callback_query(call.id, tr(L, "dl_gone"), show_alert=True)
        return
    bot.answer_callback_query(call.id, tr(L, "dl_wait"))
    threading.Thread(target=send_download, args=(call.message.chat.id, order, L), daemon=True).start()


def send_download(chat_id, order, L):
    """Надсилає відео документом — у вихідній якості, без стиснення Telegram."""
    note, path, tmp = order.get("note") or "", None, False
    if note.startswith("file:") and os.path.exists(note[5:]):
        path = note[5:]
    elif note.startswith("http"):
        path, tmp = fetch_to_file(note, f"dl_{order['id']}_{int(time.time())}.mp4"), True
    if not path:
        send_safe_message(chat_id, tr(L, "dl_gone"), parse_mode=None)
        return
    try:
        if os.path.getsize(path) > 49 * 1024 * 1024:
            send_safe_message(chat_id, tr(L, "video_link", url=note) if note.startswith("http") else tr(L, "dl_gone"),
                              parse_mode=None)
            return
        with open(path, "rb") as f:
            bot.send_document(chat_id, f, visible_file_name=f"ai_video_{order['id']}.mp4")
    except Exception as e:
        log(f"Не вдалося надіслати файл відео: {e}")
        send_safe_message(chat_id, tr(L, "dl_gone"), parse_mode=None)
    finally:
        if tmp:
            try:
                os.remove(path)
            except Exception:
                pass
        free_memory()


# ═══════════════════════════════════════════════════════════════
# ОПЛАТА ЗІРКАМИ (Telegram Stars, валюта XTR)
# ═══════════════════════════════════════════════════════════════
def send_stars_invoice(chat_id, title, desc, payload, stars):
    bot.send_invoice(chat_id, title=title, description=desc, invoice_payload=payload,
                     provider_token="", currency="XTR",
                     prices=[tg_types.LabeledPrice(label=title[:30], amount=int(stars))])


@bot.pre_checkout_query_handler(func=lambda q: True)
def handle_pre_checkout(q):
    ok, err = True, None
    try:
        if not is_allowed(q.from_user):
            ok, err = False, "Access closed"
        elif q.invoice_payload.startswith("ord:"):
            order = db.get_order(int(q.invoice_payload[4:]))
            if (not order or order["status"] != "invoice" or order["user_id"] != q.from_user.id
                    or order["stars"] != q.total_amount):
                ok, err = False, "Order expired. Send the video again."
        elif q.invoice_payload.startswith("pack:"):
            ok = q.total_amount == price("pack")
            err = None if ok else "Price changed. Try again."
        else:
            ok, err = False, "Unknown order"
    except Exception as e:
        ok, err = False, "Error"
        log(f"pre_checkout: {e}")
    try:
        bot.answer_pre_checkout_query(q.id, ok=ok, error_message=err)
    except Exception as e:
        log(f"answer_pre_checkout_query: {e}")


@bot.message_handler(content_types=["successful_payment"])
def handle_paid(msg):
    sp = msg.successful_payment
    uid, chat_id = msg.from_user.id, msg.chat.id
    L = user_lang(msg.from_user)
    payload, charge = sp.invoice_payload, sp.telegram_payment_charge_id
    log(f"⭐ Оплата {sp.total_amount} від {uid}: {payload}")
    if payload.startswith("pack:"):
        oid = db.create_order(uid, "pack", sp.total_amount, 0)
        db.set_order(oid, "done", charge)
        db.add_extra(uid, PACK_SIZE)
        db.add_spent(uid, sp.total_amount)
        send_safe_message(chat_id, tr(L, "pack_ok") + "\n\n" + ph.pick(uid, "buy", L))
        reward_referrer(uid)
        return
    if not payload.startswith("ord:"):
        return
    oid = int(payload[4:])
    db.set_order(oid, "paid", charge)
    s = pending_orders.pop(oid, None)
    if not s:
        refund(db.get_order(oid), tr(L, "order_lost"), L, chat_id)
        return
    send_safe_message(chat_id, tr(L, "paid_ok"))
    threading.Thread(target=run_paid_order_safe, args=(s, oid), daemon=True).start()


_busy_chats = set()   # чати, де зараз генерується оплачене відео


def run_paid_order_safe(s, oid):
    _busy_chats.add(s["chat_id"])
    try:
        run_paid_order(s, oid)
    finally:
        _busy_chats.discard(s["chat_id"])


# ═══════════════════════════════════════════════════════════════
# ДОСТУП (тестовий режим)
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(commands=["myid"])
def cmd_myid(message):
    bot.reply_to(message, f"Your Telegram ID: {message.from_user.id}")


@bot.message_handler(func=lambda m: not is_allowed(m.from_user), content_types=ALL_CONTENT_TYPES)
def deny_message(message):
    uid = message.from_user.id if message.from_user else "?"
    L = guess_lang(message.from_user)
    log(f"🔒 Відхилено повідомлення від ID {uid}")
    try:
        bot.reply_to(message, tr(L, "denied_id", uid=uid) if not ADMIN_IDS else tr(L, "denied"))
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: not is_allowed(c.from_user))
def deny_callback(call):
    try:
        bot.answer_callback_query(call.id, "🔒", show_alert=True)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# ЗАСТАВКА (/start) І ГОЛОВНЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════
HERE = os.path.dirname(os.path.abspath(__file__))
BANNER_PATH = os.path.join(HERE, "banner.jpg")


def picture(name, L):
    """Картинка потрібною мовою: welcome_uk.jpg / welcome_en.jpg (або None)."""
    return pic_path(name, L)


def send_picture(chat_id, path, caption, reply_markup=None):
    try:
        with open(path, "rb") as f:
            bot.send_photo(chat_id, f, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)
        return True
    except Exception as e:
        log(f"Картинка {os.path.basename(path)} не надіслалась: {e}")
        return False


def bot_username():
    if not _bot_username[0]:
        try:
            _bot_username[0] = bot.get_me().username
        except Exception:
            return "your_bot"
    return _bot_username[0]


def reward_referrer(uid):
    """Друг, який прийшов за посиланням, зробив першу покупку → +REF_BONUS промптів тому, хто запросив."""
    try:
        inviter = db.claim_ref_reward(uid)
        if not inviter:
            return
        db.add_referral(inviter, REF_BONUS)
        iu = db.get_user(inviter) or {}
        log(f"🎁 Бонус за друга: {inviter} +{REF_BONUS} (друг {uid} зробив першу покупку)")
        bot.send_message(inviter, tr(iu.get("lang") or "en", "ref_bonus", bonus=REF_BONUS))
    except Exception as e:
        log(f"Бонус за друга не нараховано: {e}")


def status_line(uid, L):
    """Рядок про безкоштовні промпти. Адміну не показуємо (у нього без ліміту)."""
    if is_admin(uid):
        return ""
    free, extra = db.free_left(uid, FREE_PER_DAY)
    line = tr(L, "status", free=free, total=FREE_PER_DAY)
    if extra:
        line += tr(L, "status_extra", extra=extra)
    return line


def welcome_text(uid, L):
    return tr(L, "welcome", free_day=FREE_PER_DAY, p_min=range8(), p30=range30(),
              status=status_line(uid, L)).rstrip()


def main_menu(L):
    m = tg_types.InlineKeyboardMarkup()
    m.row(btn(tr(L, "b_how"), "mm_how"), btn(tr(L, "b_prices"), "mm_prices"))
    m.row(btn(tr(L, "b_buy"), "mm_buy"))
    m.row(btn(tr(L, "b_invite"), "mm_invite"), btn(tr(L, "b_lang"), "mm_lang"))
    return m


def welcome_caption(uid, L):
    return tr(L, "welcome_short", status=status_line(uid, L)).rstrip()   # коротко: фрази тут займали б місце


def back_kb(L):
    m = tg_types.InlineKeyboardMarkup()
    m.row(btn(tr(L, "back"), "mm_home"))
    return m


_screen_tok = {}   # (чат, повідомлення) → лічильник, щоб стара анімація не перебила новий екран


def show_screen(call, path, caption, kb, parse_mode="Markdown", bipi=None):
    """Міняє картинку й текст у тому самому повідомленні-заставці (нічого не «втікає» вгору).
    bipi=(образ, блок фраз): на картинці з розкладкою Біпі вистрибне за 2 с; інакше — картка з Біпі."""
    if not path or getattr(call.message, "content_type", "photo") not in ("photo", "animation"):
        return False
    L = user_lang(call.from_user)
    chat_id, mid = call.message.chat.id, call.message.message_id
    bp = (bipi[0], ph.pick(call.from_user.id, bipi[1], L)) if (bipi and BIPI_ON) else None
    as_card = False
    _screen_tok[(chat_id, mid)] = tok = _screen_tok.get((chat_id, mid), 0) + 1
    for mode in (parse_mode, None):
        ckey, fh = None, None
        if as_card:
            ckey, src = card_media(bp[0], bp[1], L)
        else:
            src = _photo_ids.get(path)
            fh = None if src else open(path, "rb")
        try:
            r = bot.edit_message_media(tg_types.InputMediaPhoto(src or fh, caption=caption[:1020], parse_mode=mode),
                                       chat_id=chat_id, message_id=mid, reply_markup=kb)
            if ckey:
                _remember_card(ckey, r)
            else:
                try:
                    _photo_ids[path] = r.photo[-1].file_id
                except Exception:
                    pass
            if bp:
                def reveal(cap=caption, m=mode):
                    if _screen_tok.get((chat_id, mid)) != tok:
                        return
                    line = bipi_line(bp[1]) if m else bp[1]
                    try:
                        bot.edit_message_caption(caption=f"{cap}\n\n{line}"[:1020], chat_id=chat_id, message_id=mid,
                                                 parse_mode=m, reply_markup=kb)
                    except Exception:
                        pass
                t = threading.Timer(BIPI_DELAY, reveal)
                t.daemon = True
                t.start()
            return True
        except Exception as e:
            if "not modified" in str(e):
                return True
            log(f"Екран не змінився: {str(e)[:120]}")
        finally:
            if fh:
                fh.close()
    return False


# ── Заставка-слайди: 1) відео «було → стало», 2) як надіслати, 3) що можна отримати ──
INTRO_VIDEO = os.path.join(HERE, "intro_loop.mp4")
INTRO_STEPS = 3
_intro_anim = [None]   # file_id відео в Telegram — удруге не вантажимо файл


def intro_caption(L, step):
    dots = " ".join("●" if i == step else "○" for i in range(INTRO_STEPS))
    return f"{tr(L, f'intro_{step + 1}', free=FREE_PER_DAY)}\n\n{dots}"


def intro_kb(L, step):
    """Слайди гортаються вперед і назад; «Пропустити» / «Почати» — на головний екран."""
    m = tg_types.InlineKeyboardMarkup()
    last = step >= INTRO_STEPS - 1
    row = [btn(tr(L, "back"), f"in_{step - 1}")] if step > 0 else []
    row.append(btn(tr(L, "intro_go"), "in_home") if last else btn(tr(L, "intro_next"), f"in_{step + 1}"))
    m.row(*row)
    if not last:
        m.row(btn(tr(L, "intro_skip"), "in_home"))
    return m


def intro_pic(step, L):
    return picture("welcome" if step == 1 else "pic_format", L)


def intro_media(L, step, caption, mode):
    """(медіа для edit_message_media, відкритий файл або None)."""
    if step == 0 and os.path.exists(INTRO_VIDEO):
        fh = None if _intro_anim[0] else open(INTRO_VIDEO, "rb")
        return tg_types.InputMediaAnimation(_intro_anim[0] or fh, caption=caption, parse_mode=mode,
                                            width=1080, height=560), fh
    path = intro_pic(step, L)
    fh = None if _photo_ids.get(path) else open(path, "rb")
    return tg_types.InputMediaPhoto(_photo_ids.get(path) or fh, caption=caption, parse_mode=mode), fh


def remember_media(r, step, L):
    try:
        if step == 0 and getattr(r, "animation", None):
            _intro_anim[0] = r.animation.file_id
        elif getattr(r, "photo", None):
            _photo_ids[intro_pic(step, L)] = r.photo[-1].file_id
    except Exception:
        pass


def send_intro(chat_id, L):
    """Перший слайд заставки окремим повідомленням. False — не вийшло (тоді покажемо звичайний старт)."""
    if not os.path.exists(INTRO_VIDEO):
        return False
    for mode in ("Markdown", None):
        fh = None if _intro_anim[0] else open(INTRO_VIDEO, "rb")
        try:
            r = bot.send_animation(chat_id, _intro_anim[0] or fh, caption=intro_caption(L, 0), parse_mode=mode,
                                   reply_markup=intro_kb(L, 0), width=1080, height=560)
            remember_media(r, 0, L)
            return True
        except Exception as e:
            log(f"Заставка не надіслалась: {str(e)[:120]}")
        finally:
            if fh:
                fh.close()
    return False


def show_intro(call, L, step):
    """Гортаємо слайди в тому самому повідомленні."""
    if getattr(call.message, "content_type", "photo") not in ("photo", "animation"):
        return False
    for mode in ("Markdown", None):
        media, fh = intro_media(L, step, intro_caption(L, step), mode)
        try:
            r = bot.edit_message_media(media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                       reply_markup=intro_kb(L, step))
            remember_media(r, step, L)
            return True
        except Exception as e:
            if "not modified" in str(e):
                return True
            log(f"Слайд не змінився: {str(e)[:120]}")
        finally:
            if fh:
                fh.close()
    return False


def start_screen(chat_id, uid, L):
    """/start — щоразу заставка-слайди з початку (відео → як надіслати → головний екран)."""
    if not db.intro_seen(uid):
        db.mark_intro(uid)
    if send_intro(chat_id, L):
        return
    send_welcome(chat_id, uid, L)


@bot.callback_query_handler(func=lambda c: c.data.startswith("in_"))
def handle_intro(call):
    uid, chat_id = call.from_user.id, call.message.chat.id
    L = user_lang(call.from_user)
    bot.answer_callback_query(call.id)
    what = call.data[3:]
    if what == "home":
        if not show_screen(call, picture("welcome", L), welcome_caption(uid, L), main_menu(L)):
            send_welcome(chat_id, uid, L)
        return
    try:
        step = max(0, min(INTRO_STEPS - 1, int(what)))
    except ValueError:
        return
    if not show_intro(call, L, step):
        send_welcome(chat_id, uid, L)


def send_welcome(chat_id, uid, L):
    pic = picture("welcome", L)   # уся інформація — на картинці, під нею лише 2 рядки
    if pic:
        if send_picture(chat_id, pic, welcome_caption(uid, L), main_menu(L)):
            return
    text = welcome_text(uid, L)
    if os.path.exists(BANNER_PATH):
        try:
            with open(BANNER_PATH, "rb") as f:
                bot.send_photo(chat_id, f, caption=text, parse_mode="Markdown", reply_markup=main_menu(L))
            return
        except Exception as e:
            log(f"Банер не надіслався: {e}")
    send_safe_message(chat_id, text, reply_markup=main_menu(L))


@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    user = message.from_user
    parts = (message.text or "").split(maxsplit=1)
    ref = None
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            ref = int(parts[1][4:])
        except ValueError:
            ref = None
    u, is_new = db.ensure_user(user.id, guess_lang(user), ref_by=ref if ref and db.get_user(ref) else None)
    # бонус тому, хто запросив, — лише після ПЕРШОЇ покупки друга (див. reward_referrer)
    if is_new and lang_code(user) in ("ru", "be"):
        bot.send_message(message.chat.id, tr("en", "lang_pick"), reply_markup=lang_kb(first=True))
        return
    start_screen(message.chat.id, user.id, u.get("lang") or "en")


def lang_kb(back=False, first=False):
    """Вибір мови. first=True — перший запуск з російською мовою телефону: лише укр / рус / англ."""
    m = tg_types.InlineKeyboardMarkup()
    codes = ["uk", "ru", "en"] if first else LANG_ORDER
    grid(m, [(c, LANG_LABEL[c]) for c in codes], "ln_")
    if back:
        m.row(btn("◀️", "mm_home"))
    return m


@bot.callback_query_handler(func=lambda c: c.data.startswith("ln_"))
def handle_pick_lang(call):
    uid, chat_id = call.from_user.id, call.message.chat.id
    new = call.data[3:]
    if new not in LANG_ORDER:
        bot.answer_callback_query(call.id)
        return
    db.ensure_user(uid, guess_lang(call.from_user))
    db.set_lang(uid, new)
    bot.answer_callback_query(call.id, tr(new, "lang_set"))
    if not db.intro_seen(uid):   # перший запуск: після вибору мови — заставка
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass
        start_screen(chat_id, uid, new)
        return
    if getattr(call.message, "content_type", "") == "photo":
        if show_screen(call, picture("welcome", new), welcome_caption(uid, new), main_menu(new)):
            return
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except Exception:
        pass
    send_welcome(chat_id, uid, new)


@bot.message_handler(commands=["paysupport"])
def cmd_paysupport(message):
    send_safe_message(message.chat.id, tr(user_lang(message.from_user), "paysupport"))


@bot.message_handler(commands=["terms"])
def cmd_terms(message):
    L = user_lang(message.from_user)
    send_safe_message(message.chat.id, tr(L, "terms").rstrip() + "\n" + tr(L, "terms_nsfw"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mm_"))
def handle_main_menu(call):
    uid, chat_id = call.from_user.id, call.message.chat.id
    L = user_lang(call.from_user)
    what = call.data[3:]
    bot.answer_callback_query(call.id)
    if what == "how":   # «Як це працює» — ті самі слайди заставки
        if not show_intro(call, L, 0):
            send_safe_message(chat_id, tr(L, "how"))
    elif what == "prices":
        models = "\n".join(f"{v['emoji']} {v['name']} — {price(k)} ⭐" for k, v in VIDEO_MODELS.items())
        text = tr(L, "prices", free_day=FREE_PER_DAY, pack=price("pack"), models=models, p30=range30())
        text += "\n\n" + tr(L, "nsfw_short")
        if not show_screen(call, pic_path("pic_format", L), text, back_kb(L), bipi=("accountant", "prices")):
            send_safe_message(chat_id, text)
    elif what == "home":
        if not show_screen(call, picture("welcome", L), welcome_caption(uid, L), main_menu(L)):
            send_welcome(chat_id, uid, L)
    elif what == "buy":
        send_stars_invoice(chat_id, tr(L, "inv_pack_title"), tr(L, "inv_pack_desc"), f"pack:{uid}", price("pack"))
    elif what == "invite":
        text = tr(L, "invite", link=f"https://t.me/{bot_username()}?start=ref_{uid}", bonus=REF_BONUS)
        if not show_screen(call, picture("welcome", L), text, back_kb(L), parse_mode=None, bipi=("gift", "friend")):
            send_safe_message(chat_id, text, parse_mode=None)
    elif what == "lang":
        if not show_screen(call, picture("welcome", L), tr(L, "lang_pick"), lang_kb(back=True), parse_mode=None):
            bot.send_message(chat_id, tr(L, "lang_pick"), reply_markup=lang_kb())


# ═══════════════════════════════════════════════════════════════
# КОМАНДИ АДМІНА
# ═══════════════════════════════════════════════════════════════
ADMIN_HELP = ("👑 Команди адміна:\n"
              "/stats — статистика\n"
              "/prices — поточні ціни\n"
              "/setprice КЛЮЧ ЗІРКИ — змінити ціну (ключі: ltx, omni, kling, kling30, pack)\n"
              "/give ID N — додати користувачу N промптів\n"
              "/refund НОМЕР — повернути зірки за замовлення\n"
              "/unban ID — зняти блок за порушення (і обнулити попередження)\n"
              "/broadcast ТЕКСТ — розсилка всім користувачам\n"
              "/myid — свій Telegram ID")


@bot.message_handler(commands=["admin", "stats", "prices", "setprice", "give", "refund", "broadcast", "unban"],
                     func=lambda m: is_admin(m.from_user.id))
def cmd_admin(message):
    parts = (message.text or "").split(maxsplit=2)
    cmd = parts[0].lstrip("/").split("@")[0]
    chat_id = message.chat.id
    if cmd == "admin":
        bot.reply_to(message, ADMIN_HELP)
    elif cmd == "stats":
        st = db.stats()
        income = st["stars"] * STAR_USD
        per_paid = (st["prompts_total"] / st["paid_orders"]) if st["paid_orders"] else 0
        bot.reply_to(message, (
            "📊 Статистика\n"
            f"Користувачів: {st['users']} (сьогодні активних {st['users_today']}, нових {st['new_today']})\n"
            f"Промптів усього: {st['prompts_total']}\n"
            f"Оплачених замовлень: {st['paid_orders']}, повернень: {st['refunded']}\n"
            f"Зірок: {st['stars']} ⭐ ≈ ${income:.2f}\n"
            f"Витрати на сервіси ≈ ${st['cost']:.2f} · різниця ≈ ${income - st['cost']:.2f}\n"
            f"Промптів на одну покупку: {per_paid:.1f}\n"
            f"Запрошено друзів: {st['referrals']}\n"
            f"Відео сьогодні: {paid_today_count()} з {PAID_DAILY_CAP}\n"
            f"Доступ: {ACCESS_MODE} · тестові ціни: {'так' if PRICE_TEST_MODE else 'ні'}\n"
            f"Моделі: " + ", ".join(f"{v['name']} {'✅' if model_ready(k) else '🔒'}" for k, v in VIDEO_MODELS.items())))
    elif cmd == "prices":
        bot.reply_to(message, "💰 Ціни:\n" + "\n".join(f"{k}: {price(k)} ⭐" for k in DEFAULT_PRICES))
    elif cmd == "setprice":
        try:
            key, val = parts[1], int(parts[2])
            assert key in DEFAULT_PRICES and val > 0
            db.set_setting(f"price_{key}", val)
            bot.reply_to(message, f"✅ {key} = {val} ⭐")
        except Exception:
            bot.reply_to(message, "Формат: /setprice kling 115")
    elif cmd == "give":
        try:
            uid, n = int(parts[1]), int(parts[2])
            db.ensure_user(uid, "en")
            db.add_extra(uid, n)
            bot.reply_to(message, f"✅ Користувачу {uid} додано {n} промптів")
        except Exception:
            bot.reply_to(message, "Формат: /give 123456789 10")
    elif cmd == "refund":
        try:
            order = db.get_order(int(parts[1]))
            assert order and order.get("charge_id")
            bot.refund_star_payment(order["user_id"], order["charge_id"])
            db.set_order(order["id"], "refunded")
            bot.reply_to(message, f"✅ Повернуто {order['stars']} ⭐ за #{order['id']}")
        except Exception as e:
            bot.reply_to(message, f"Не вдалося: {str(e)[:200]}")
    elif cmd == "unban":
        try:
            uid = int(parts[1])
            db.unban(uid)
            bot.reply_to(message, f"✅ Користувача {uid} розблоковано, попередження обнулено")
        except Exception:
            bot.reply_to(message, "Формат: /unban 123456789")
    elif cmd == "broadcast":
        text = (message.text or "").split(maxsplit=1)
        if len(text) < 2:
            bot.reply_to(message, "Формат: /broadcast Текст повідомлення")
            return

        def go():
            ok = 0
            for uid in db.all_user_ids():
                try:
                    bot.send_message(uid, text[1])
                    ok += 1
                except Exception:
                    pass
                time.sleep(0.05)
            bot.send_message(chat_id, f"✅ Розіслано: {ok}")
        threading.Thread(target=go, daemon=True).start()


# ═══════════════════════════════════════════════════════════════
# КНОПКИ НАЛАШТУВАНЬ
# ═══════════════════════════════════════════════════════════════
def session_for(call):
    chat_id = call.message.chat.id
    s = user_sessions.get(chat_id)
    if not s or s.get("msg_id") != call.message.message_id:
        # сесії немає взагалі — бота перезапускали (оновлення); інша сесія — просто стара кнопка
        block = "sit_update" if not user_sessions.get(chat_id) else "sit_old"
        try:
            bot.answer_callback_query(call.id, ph.pick(call.from_user.id, block, user_lang(call.from_user)),
                                      show_alert=True)
        except Exception:
            pass
        return None
    return s


@bot.callback_query_handler(func=lambda c: c.data == "cx_no")
def handle_cancel_no(call):
    s = user_sessions.get(call.message.chat.id)
    bot.answer_callback_query(call.id)
    if s and s.get("ask_cancel"):
        s.pop("ask_cancel", None)
        ui(s)


@bot.callback_query_handler(func=lambda c: c.data in ("nav_cancel", "cx_yes"))
def handle_cancel(call):
    chat_id = call.message.chat.id
    s = user_sessions.get(chat_id)
    L = s["lang"] if s else user_lang(call.from_user)
    if s and s.get("paid"):
        bot.answer_callback_query(call.id)
        return
    if (call.data == "nav_cancel" and s and s.get("state") not in ("AGAIN", "DONE")
            and s.get("msg_id") == call.message.message_id):
        bot.answer_callback_query(call.id)   # спершу перепитуємо
        s["ask_cancel"] = True
        ui(s)
        return
    if s:
        s["cancel"] = True
    user_sessions.pop(chat_id, None)
    try:
        bot.answer_callback_query(call.id)
        if getattr(call.message, "content_type", "") == "photo":
            bot.edit_message_caption(caption=tr(L, "cancelled"), chat_id=chat_id, message_id=call.message.message_id)
        else:
            bot.edit_message_text(tr(L, "cancelled"), chat_id, call.message.message_id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data == "nav_back")
def handle_back(call):
    s0 = user_sessions.get(call.message.chat.id)
    if s0 and s0.get("history"):   # вікно, куди повертаємось, отримає нову фразу про себе
        s0.setdefault("_bp", {}).pop(s0["history"][-1][0], None)
    _handle_back(call)


def _handle_back(call):
    s = session_for(call)
    if not s:
        return
    hist = s.get("history") or []
    if hist:
        prev_state, keys = hist.pop()
        for k in keys:
            s.pop(k, None)
        s["state"] = prev_state
    elif "base_analysis" in s and s.get("state") not in ("AGAIN", "FORMAT", "GENERATING", "DONE"):
        # прийшли з «Робимо відео?» / «Інший промпт» — кроків позаду немає: повертаємось на «Що далі?»
        if s.pop("reuse_prompt", None) and s.get("ready_seg"):
            s["gen_mode"] = "hook"   # повертаємось до безкоштовного промпту, з якого прийшли
        s["state"] = "AGAIN"
    s["page"] = 0
    bot.answer_callback_query(call.id)
    ui(s)


@bot.callback_query_handler(func=lambda c: c.data.startswith("fm_"))
def handle_format(call):
    s = session_for(call)
    if not s:
        return
    L, mode = s["lang"], call.data[3:]
    if mode == "hook":
        free, extra = db.free_left(s["uid"], FREE_PER_DAY)
        if not (free or extra or is_admin(s["uid"])):
            bot.answer_callback_query(call.id, tr(L, "no_free"), show_alert=True)
            return
        react(call, s)
        advance(s, "STYLE_CAT", gen_mode="hook")
    elif mode == "v8":
        if not any(model_ready(k) for k in VIDEO_MODELS):
            bot.answer_callback_query(call.id, tr(L, "paid_off"), show_alert=True)
            return
        react(call, s)
        advance(s, "STYLE_CAT", gen_mode="v8")   # модель обирається в кінці, з ціною
    elif mode == "v30":
        if not model_ready("kling"):
            bot.answer_callback_query(call.id, tr(L, "paid_off"), show_alert=True)
            return
        react(call, s)
        advance(s, "STYLE_CAT", gen_mode="v30")


@bot.callback_query_handler(func=lambda c: c.data.startswith("md_"))
def handle_model(call):
    s = session_for(call)
    if not s:
        return
    key = call.data[3:]
    if key not in VIDEO_MODELS or not model_ready(key):
        bot.answer_callback_query(call.id, tr(s["lang"], "model_locked"), show_alert=True)
        return
    react(call, s)
    if s.get("reuse_prompt"):
        advance(s, "CONFIRM", model=key)   # промпт уже є — стиль не питаємо
    else:
        advance(s, "STYLE_CAT", model=key)


@bot.callback_query_handler(func=lambda c: c.data.startswith("sc_"))
def handle_style_cat(call):
    s = session_for(call)
    if not s:
        return
    cat = call.data[3:]
    react(call, s)
    if cat == "orig":
        if s.get("restyle"):
            s.pop("style", None)
            after_clarify(s, style_cat="orig", genre="orig", sound="orig")
        else:
            after_sound(s, style_cat="orig", genre="orig", sound="orig")  # «як в оригіналі» — без жанру і звуку
    elif cat == "dance":
        advance(s, "DANCE", style_cat="dance")
    elif cat == "film":
        advance(s, "STYLE_FILM", style_cat="film")
    else:
        advance(s, "STYLE_ANIM", style_cat="anim")


@bot.callback_query_handler(func=lambda c: c.data.startswith("st_"))
def handle_style(call):
    s = session_for(call)
    if not s:
        return
    react(call, s)
    key = call.data[3:]
    cat = s.get("style_cat")
    if cat == "dance":   # танець → одразу генерація (музика в стилі танцю)
        after_clarify(s, style=key, genre="orig", sound="music", music_genre="m_dance")
        return
    if cat == "anim":    # у анімації жанрів немає — одразу звук
        if s.get("restyle") and s.get("sound"):
            after_clarify(s, style=key, genre="orig")
        else:
            advance(s, "SOUND", style=key, genre="orig")
        return
    if s.get("restyle") and genre_fits(s):
        after_clarify(s, style=key)   # лише новий стиль — решта як була
    else:
        advance(s, "GENRE", style=key)


GENRE_PAGE = 8


@bot.callback_query_handler(func=lambda c: c.data.startswith("pg_"))
def handle_page(call):
    """Гортання сторінок у стилях, жанрах і танцях."""
    s = session_for(call)
    if not s:
        return
    bot.answer_callback_query(call.id)
    pg = s.get("page", 0) + {"pg_next": 1, "pg_prev": -1}.get(call.data, 0)
    pg = max(0, min(pg, s.get("_pages", 1) - 1))
    if pg != s.get("page", 0):
        s["page"] = pg
        ui(s)


@bot.callback_query_handler(func=lambda c: c.data == "po_go")
def handle_prompt_only(call):
    """На кроці оплати: замість відео — безкоштовний промпт (у рахунок денного ліміту)."""
    s = session_for(call)
    if not s or s.get("state") != "CONFIRM":
        bot.answer_callback_query(call.id)
        return
    L = s["lang"]
    free, extra = db.free_left(s["uid"], FREE_PER_DAY)
    if not (free or extra or is_admin(s["uid"])):
        bot.answer_callback_query(call.id, tr(L, "no_free"), show_alert=True)
        return
    bot.answer_callback_query(call.id)
    s.update(gen_mode="hook", state="GENERATING")
    s.pop("model", None)
    ui(s)
    threading.Thread(target=run_free_prompt, args=(s,), daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data.startswith("gn_"))
def handle_genre(call):
    s = session_for(call)
    if not s:
        return
    react(call, s)
    if s.get("restyle") and s.get("sound"):
        after_clarify(s, genre=call.data[3:])
    else:
        advance(s, "SOUND", genre=call.data[3:])


@bot.callback_query_handler(func=lambda c: c.data.startswith("sd_"))
def handle_sound(call):
    s = session_for(call)
    if not s:
        return
    mode = call.data[3:]
    react(call, s)
    if mode in ("music", "music_voice"):
        advance(s, "MUSIC", sound=mode)
    elif mode == "voice":
        advance(s, "PHRASE_SRC", sound=mode)
    else:
        after_sound(s, sound=mode)


@bot.callback_query_handler(func=lambda c: c.data.startswith("mu_"))
def handle_music(call):
    s = session_for(call)
    if not s:
        return
    react(call, s)
    if s.get("sound") == "music_voice":
        advance(s, "PHRASE_SRC", music_genre=call.data[3:])
    else:
        after_sound(s, music_genre=call.data[3:])


@bot.callback_query_handler(func=lambda c: c.data.startswith("ps_"))
def handle_phrase_src(call):
    s = session_for(call)
    if not s:
        return
    bot.answer_callback_query(call.id)
    if call.data[3:] == "custom":
        advance(s, "WAITING_TEXT", phrase_src="custom")
    else:
        advance(s, "TIMBRE", phrase_src="orig")


@bot.callback_query_handler(func=lambda c: c.data.startswith("lg_"))
def handle_lang(call):
    s = session_for(call)
    if not s:
        return
    react(call, s)
    advance(s, "TIMBRE", voice_lang=call.data[3:])


@bot.callback_query_handler(func=lambda c: c.data.startswith("tb_"))
def handle_timbre(call):
    s = session_for(call)
    if not s:
        return
    react(call, s)
    after_sound(s, timbre=call.data[3:])


@bot.callback_query_handler(func=lambda c: c.data == "cl_skip")
def handle_clarify_skip(call):
    s = session_for(call)
    if not s:
        return
    bot.answer_callback_query(call.id)
    after_clarify(s)


@bot.callback_query_handler(func=lambda c: c.data in ("pay_go", "pay_admin") or c.data[:3] in ("pm_", "pa_"))
def handle_pay(call):
    s = session_for(call)
    if not s:
        return
    L = s["lang"]
    if s.get("state") in ("GENERATING", "INVOICE", "DONE"):
        bot.answer_callback_query(call.id)
        return
    if call.data[:3] in ("pm_", "pa_"):   # кнопка моделі з ціною
        key = call.data[3:]
        if key not in dict(confirm_models(s)) or not model_ready(key):
            bot.answer_callback_query(call.id, tr(L, "model_locked"), show_alert=True)
            return
        s["model"] = key
        call.data = "pay_admin" if call.data.startswith("pa_") else "pay_go"
    stars, cost, seconds, key = order_info(s)
    if not model_ready(key):
        bot.answer_callback_query(call.id, tr(L, "model_locked"), show_alert=True)
        return
    if call.data == "pay_admin":
        if not is_admin(s["uid"]):
            bot.answer_callback_query(call.id)
            return
        bot.answer_callback_query(call.id)
        s["state"] = "GENERATING"   # друге натискання вже нічого не запустить
        oid = db.create_order(s["uid"], f"admin:{s['gen_mode']}:{key}", 0, cost)
        threading.Thread(target=run_paid_order, args=(s, oid), daemon=True).start()
        return
    bot.answer_callback_query(call.id)
    if s.get("gen_mode") == "v30":
        s["v30_sec"] = seconds
    oid = db.create_order(s["uid"], f"{s['gen_mode']}:{key}", stars, cost)
    pending_orders[oid] = s
    if s.get("gen_mode") == "v30":
        title = tr(L, "inv_v30_title", d=seconds)
    else:
        title = tr(L, "inv_v8_title", model=VIDEO_MODELS[key]["name"])
    s["state"] = "INVOICE"
    set_status(s, tr(L, "inv_sent"))
    try:
        send_stars_invoice(s["chat_id"], title, tr(L, "inv_video_desc"), f"ord:{oid}", stars)
    except Exception as e:
        log(f"❌ Рахунок не створено: {e}")
        pending_orders.pop(oid, None)
        db.set_order(oid, "failed")
        s["state"] = "CONFIRM"
        set_status(s, f"❌ {str(e)[:100]}")


def analysis_button(L):
    return None   # кнопку «Розбір відео» прибрано


@bot.callback_query_handler(func=lambda c: c.data == "an_show")
def handle_show_analysis(call):
    chat_id = call.message.chat.id
    L = user_lang(call.from_user)
    text = last_analysis.get(chat_id)
    if not text:
        bot.answer_callback_query(call.id, tr(L, "analysis_gone"), show_alert=True)
        return
    bot.answer_callback_query(call.id)
    f = io.BytesIO(text.encode("utf-8"))
    f.name = "video_breakdown.txt"
    try:
        bot.send_document(chat_id, f, caption=tr(L, "analysis_caption"))
    except Exception as e:
        log(f"Не вдалося надіслати розбір файлом: {e}")
        send_safe_message(chat_id, text, parse_mode=None)


# ═══════════════════════════════════════════════════════════════
# ПОВІДОМЛЕННЯ: посилання, файли, текст
# ═══════════════════════════════════════════════════════════════
_photo_ids = {}   # картинка → file_id у Telegram (вдруге не вантажимо файл, відправка миттєва)

# Кожен крок панелі — своя картинка-пояснення (pic_format_uk.jpg тощо).
# Стилі, жанри й музика — тонка смужка, щоб кнопки починалися одразу.
STATE_PIC = {
    "FORMAT": "pic_format", "MODEL": "pic_model", "STYLE_CAT": "pic_cat",
    "STYLE_FILM": "pic_style", "STYLE_ANIM": "pic_astyle", "GENRE": "pic_genre",
    "DANCE": "pic_dance",
    "SOUND": "pic_sound", "MUSIC": "pic_music",
    "PHRASE_SRC": "pic_voice", "WAITING_TEXT": "pic_voice", "LANG": "pic_voice", "TIMBRE": "pic_voice",
    "CLARIFY": "pic_clarify", "CONFIRM": "pic_confirm", "INVOICE": "pic_confirm",
    "GENERATING": "pic_gen", "AGAIN": "pic_done",
}


def pic_path(key, L):
    for lang in (L, "en", "uk"):
        p = os.path.join(HERE, f"{key}_{lang}.jpg")
        if os.path.exists(p):
            return p
    return None


_bb_ids = {}   # шлях білборда → file_id у Telegram (удруге файл не вантажимо)


def send_panel(chat_id, L="uk", reply_to=None, key="pic_format"):
    """Нова панель вибору: картинка кроку зверху + короткий підпис. Повертає (повідомлення, чи_фото).
    Перший крок нового ролика («Що робимо?») — відео-білборд «було → стало» з кнопками під ним."""
    bb = billboard(L) if key == "pic_format" else None
    if bb:
        fid = _bb_ids.get(bb)
        fh = None if fid else open(bb, "rb")
        try:
            msg = bot.send_animation(chat_id, fid or fh, reply_to_message_id=reply_to, width=1080, height=880)
            try:
                _bb_ids[bb] = msg.animation.file_id
            except Exception:
                pass
            return msg, True
        except Exception as e:
            log(f"Панель-відео не надіслалась: {e}")
        finally:
            if fh:
                fh.close()
    path = pic_path(key, L)
    if path:
        try:
            if path in _photo_ids:
                msg = bot.send_photo(chat_id, _photo_ids[path], caption="🎬 ...", reply_to_message_id=reply_to)
            else:
                with open(path, "rb") as f:
                    msg = bot.send_photo(chat_id, f, caption="🎬 ...", reply_to_message_id=reply_to)
                try:
                    _photo_ids[path] = msg.photo[-1].file_id
                except Exception:
                    pass
            return msg, True
        except Exception as e:
            log(f"Панель-картинка не надіслалась: {e}")
    return bot.send_message(chat_id, "🎬 ...", reply_to_message_id=reply_to), False


def new_session(msg, status_key, **extra):
    chat_id = msg.chat.id
    cleanup_old_files()
    old = user_sessions.get(chat_id)
    if old and not old.get("paid"):
        old["cancel"] = True
        vp = old.get("video_path")   # кинутий ролик, який так і не дійшов до розбору — прибираємо
        if vp and not old.get("analysis_started") and os.path.exists(vp):
            try:
                os.remove(vp)
            except Exception:
                pass
    L = user_lang(msg.from_user)
    status_msg, is_photo = send_panel(chat_id, L, reply_to=msg.message_id)
    s = {"chat_id": chat_id, "uid": msg.from_user.id, "lang": L, "msg_id": status_msg.message_id, "photo": is_photo,
         "pic": "pic_format", "pic_key": ("pic_format", None),
         "state": "FORMAT", "live_status": tr(L, status_key), "history": [], **extra}
    user_sessions[chat_id] = s
    ui(s)
    return s


@bot.message_handler(content_types=["text"])
def handle_text_messages(msg):
    chat_id = msg.chat.id
    txt = (msg.text or "").strip()
    s = user_sessions.get(chat_id)

    if s and s.get("state") == "CLARIFY" and not re.match(r"https?://", txt):
        try:
            bot.delete_message(chat_id, msg.message_id)
        except Exception:
            pass
        after_clarify(s, user_note=txt.replace("`", "'")[:1000], note_applied=False)
        return
    if s and s.get("state") == "WAITING_TEXT":
        try:
            bot.delete_message(chat_id, msg.message_id)
        except Exception:
            pass
        advance(s, "LANG", phrase=txt.replace("`", "'")[:300])
        return
    if blocked_user(msg):
        return
    L = user_lang(msg.from_user)
    if "http" not in txt:
        bipi_say(chat_id, msg.from_user.id, L, "happy", "sit_text", ttl=40)
        return
    if chat_id in _busy_chats:   # оплачене відео ще генерується — друге паралельно не беремо
        bipi_say(chat_id, msg.from_user.id, L, "director", "sit_dup", ttl=40)
        return
    s = new_session(msg, "st_download", src_url=txt)
    threading.Thread(target=fetch_video_task, args=(s, txt), daemon=True).start()


MAX_TG_DOWNLOAD = 20 * 1024 * 1024


@bot.message_handler(content_types=["video", "document", "animation"])
def handle_video_file(msg):
    L = user_lang(msg.from_user)
    if blocked_user(msg):
        return
    uid = msg.from_user.id
    media = msg.video or msg.animation or msg.document
    mime = getattr(media, "mime_type", "") or ""
    if msg.document and not mime.startswith("video"):
        role, block = ("artist", "sit_photo") if mime.startswith("image") else \
                      ("happy", "sit_audio") if mime.startswith("audio") else ("oops", "sit_file")
        bipi_say(msg.chat.id, uid, L, role, block, ttl=40)
        return
    if (getattr(media, "file_size", 0) or 0) > MAX_TG_DOWNLOAD:
        bipi_say(msg.chat.id, uid, L, "oops", "sit_big")
        return
    if msg.chat.id in _busy_chats:
        bipi_say(msg.chat.id, uid, L, "director", "sit_dup", ttl=40)
        return
    dur = getattr(media, "duration", None)
    s = new_session(msg, "st_file", duration=dur or CLIP_SECONDS, duration_from_source=bool(dur),
                    src_file_id=media.file_id)
    uid_key = "f:" + str(getattr(media, "file_unique_id", "") or "")   # той самий файл удруге — розбір із пам'яті
    if len(uid_key) > 2 and from_memory(s, uid_key):
        set_status(s, tr(L, "st_viewed"))
        return
    try:
        info = bot.get_file(media.file_id)
        data = bot.download_file(info.file_path)
        path = f"temp_{msg.chat.id}_{time.time_ns()}.mp4"
        with open(path, "wb") as f:
            f.write(data)
        log(f"✅ Файл від користувача отримано ({len(data) // 1024} KB)")
    except Exception as e:
        log(f"Не вдалося отримати файл: {e}")
        s["analysis_error"] = tr(L, "file_fail")
        s["state"] = "DONE"
        bipi_say(msg.chat.id, uid, L, "oops", "sit_bad", s=s)
        return
    threading.Thread(target=fetch_video_task, args=(s, "", path, uid_key if len(uid_key) > 2 else ""),
                     daemon=True).start()


@bot.message_handler(content_types=[t for t in ALL_CONTENT_TYPES if t not in ("text", "video", "document", "animation")])
def handle_other_messages(msg):
    """Фото, голосове, музика, стікер… — Біпі весело пояснює, що потрібне відео."""
    t = msg.content_type
    role, block = ("artist", "sit_photo") if t == "photo" else \
                  ("happy", "sit_audio") if t in ("audio", "voice") else \
                  ("oops", "sit_file") if t in ("video_note",) else ("happy", "sit_text")
    try:
        bipi_say(msg.chat.id, msg.from_user.id, user_lang(msg.from_user), role, block, ttl=40)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# ОПИС БОТА (те, що видно ДО натискання «Старт») І МЕНЮ КОМАНД
# ═══════════════════════════════════════════════════════════════
def setup_profile():
    descr = {
        "uk": ("🎬 Перетворюю TikTok-відео на професійні промпти й готові ролики в будь-якому стилі: кіно, аніме, "
               "3D-мульти, кіберпанк, спогади дитинства та ще 40+.\n\n🔥 Промпт на головні 8 секунд — безкоштовно щодня.\n"
               "🎬 Готове відео 8–30 с — за зірки. Не вийшло — зірки повертаються автоматично.\n\n"
               "Натисніть «Старт» і надішліть посилання 👇"),
        "en": ("🎬 I turn TikTok videos into pro prompts and finished clips in any style: cinema, anime, 3D cartoon, "
               "cyberpunk, childhood memories and 40+ more.\n\n🔥 A prompt for the best 8 seconds — free every day.\n"
               "🎬 Finished 8–30 s videos — for stars. If it fails, stars are refunded automatically.\n\n"
               "Tap Start and send a link 👇"),
    }
    descr.update({
        "ru": ("🎬 Превращаю TikTok-видео в профессиональные промпты и готовые ролики в любом стиле: кино, аниме, "
               "3D-мульты, киберпанк, воспоминания детства и ещё 40+.\n\n🔥 Промпт на главные 8 секунд — бесплатно каждый день.\n"
               "🎬 Готовое видео 8–30 с — за звёзды. Не получилось — звёзды возвращаются автоматически.\n\n"
               "Нажмите «Старт» и отправьте ссылку 👇"),
        "es": ("🎬 Convierto vídeos de TikTok en prompts profesionales y clips terminados en cualquier estilo: cine, anime, "
               "dibujos 3D, cyberpunk, recuerdos de infancia y más de 40.\n\n🔥 Un prompt para los mejores 8 segundos — gratis cada día.\n"
               "🎬 Vídeos terminados de 8–30 s — con estrellas. Si falla, las estrellas se devuelven automáticamente.\n\n"
               "Pulsa «Iniciar» y envía un enlace 👇"),
        "pt": ("🎬 Transformo vídeos do TikTok em prompts profissionais e clipes prontos em qualquer estilo: cinema, anime, "
               "desenhos 3D, cyberpunk, memórias de infância e mais de 40.\n\n🔥 Um prompt para os melhores 8 segundos — grátis todo dia.\n"
               "🎬 Vídeos prontos de 8–30 s — com estrelas. Se falhar, as estrelas voltam automaticamente.\n\n"
               "Toque em «Iniciar» e envie um link 👇"),
        "de": ("🎬 Ich verwandle TikTok-Videos in Profi-Prompts und fertige Clips in jedem Stil: Kino, Anime, 3D-Trickfilm, "
               "Cyberpunk, Kindheitserinnerungen und 40+ weitere.\n\n🔥 Ein Prompt für die besten 8 Sekunden — jeden Tag gratis.\n"
               "🎬 Fertige Videos 8–30 s — gegen Sterne. Klappt es nicht, gibt es die Sterne automatisch zurück.\n\n"
               "Tippe auf «Starten» und schick einen Link 👇"),
        "ar": ("🎬 أحوّل فيديوهات TikTok إلى برومبتات احترافية ومقاطع جاهزة بأي أسلوب: سينما، أنمي، كرتون ثلاثي الأبعاد، سايبربانك، "
               "ذكريات الطفولة وأكثر من 40 غيرها.\n\n🔥 برومبت لأفضل 8 ثوانٍ — مجانًا كل يوم.\n"
               "🎬 فيديوهات جاهزة 8–30 ث — مقابل النجوم. إذا فشل الإنشاء تُعاد النجوم تلقائيًا.\n\n"
               "اضغط «ابدأ» وأرسل رابطًا 👇"),
        "tr": ("🎬 TikTok videolarını her tarzda profesyonel promptlara ve hazır kliplere dönüştürürüm: sinema, anime, "
               "3D çizgi film, cyberpunk, çocukluk anıları ve 40'tan fazlası.\n\n🔥 En iyi 8 saniye için prompt — her gün ücretsiz.\n"
               "🎬 Hazır 8–30 sn videolar — yıldızla. Olmazsa yıldızlar otomatik iade edilir.\n\n"
               "«Başlat»a dokun ve bir bağlantı gönder 👇"),
    })
    short = {"uk": "TikTok → професійний промпт або готове відео в будь-якому стилі",
             "en": "TikTok → pro prompt or finished video in any style",
             "ru": "TikTok → профессиональный промпт или готовое видео в любом стиле",
             "es": "TikTok → prompt profesional o vídeo terminado en cualquier estilo",
             "pt": "TikTok → prompt profissional ou vídeo pronto em qualquer estilo",
             "de": "TikTok → Profi-Prompt oder fertiges Video in jedem Stil",
             "ar": "TikTok ← برومبت احترافي أو فيديو جاهز بأي أسلوب",
             "tr": "TikTok → profesyonel prompt veya her tarzda hazır video"}
    cmds = {"en": ("Menu", "Payment support", "Terms"), "uk": ("Меню", "Підтримка оплат", "Умови"),
            "ru": ("Меню", "Поддержка оплат", "Условия"), "es": ("Menú", "Soporte de pagos", "Condiciones"),
            "pt": ("Menu", "Suporte de pagamentos", "Termos"), "de": ("Menü", "Zahlungs-Support", "Bedingungen"),
            "ar": ("القائمة", "دعم المدفوعات", "الشروط"), "tr": ("Menü", "Ödeme desteği", "Koşullar")}
    try:
        bot.set_my_description(descr["en"])
        bot.set_my_short_description(short["en"])
        for lc in descr:
            kw = {} if lc == "en" else {"language_code": lc}
            bot.set_my_description(descr[lc], **kw)
            bot.set_my_short_description(short[lc], **kw)
            c = cmds[lc]
            bot.set_my_commands([tg_types.BotCommand("start", c[0]), tg_types.BotCommand("paysupport", c[1]),
                                 tg_types.BotCommand("terms", c[2])], **kw)
        log("✅ Опис і меню команд бота оновлено")
    except Exception as e:
        log(f"⚠️ Опис бота не оновлено: {str(e)[:150]}")


def recover_interrupted_orders():
    """Після аварійного перезапуску: незавершені замовлення не запускаємо знову, а закриваємо з поверненням зірок."""
    time.sleep(3)
    for order in db.unfinished_orders():
        log(f"⚠️ Замовлення #{order['id']} перервано перезапуском бота")
        u = db.get_user(order["user_id"]) or {}
        lang = u.get("lang") or "en"
        refund(order, tr(lang, "e_restart"), lang, order["user_id"])


# ═══════════════════════════════════════════════════════════════
# ЗАПУСК: на Render — webhook, на комп'ютері — polling
# ═══════════════════════════════════════════════════════════════
from http.server import BaseHTTPRequestHandler, HTTPServer


def run_webhook(public_url: str):
    secret = hashlib.sha256(TELEGRAM_TOKEN.encode()).hexdigest()[:32]
    SECRETS.append(secret)
    path = f"/tg/{secret}"
    port = int(os.environ.get("PORT", "10000"))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def do_POST(self):
            if self.path != path or self.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret:
                self.send_response(403)
                self.end_headers()
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                update = tg_types.Update.de_json(body)
                if db.seen_update(update.update_id):
                    log(f"↩️ Повтор оновлення {update.update_id} від Telegram — пропускаю")
                else:
                    bot.process_new_updates([update])
            except Exception as e:
                log(f"Помилка обробки оновлення: {e}")
            self.send_response(200)
            self.end_headers()

    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=public_url.rstrip("/") + path, secret_token=secret, drop_pending_updates=False)
        log("✅ Webhook встановлено, бот чекає повідомлень")
    except Exception as e:
        log(f"❌ Не вдалося встановити webhook: {e}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    log(f"Бот запущено. Доступ: {ACCESS_MODE} · адмінів: {len(ADMIN_IDS)} · тестерів: {len(TESTER_IDS)}")
    log(f"Аналіз: {', '.join(ANALYSIS_MODELS)} · Промпти: {'Groq ' + GROQ_MODELS[0] if GROQ_API_KEY else 'Gemini'}")
    log("Відео: " + ", ".join(f"{v['name']} {'✅' if model_ready(k) else '🔒'}" for k, v in VIDEO_MODELS.items())
        + (" · ТЕСТОВІ ЦІНИ 1 ⭐" if PRICE_TEST_MODE else ""))
    mem_log("старт")
    threading.Thread(target=setup_profile, daemon=True).start()
    threading.Thread(target=recover_interrupted_orders, daemon=True).start()
    public_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("WEBHOOK_URL")
    if public_url:
        run_webhook(public_url)
    else:
        try:
            bot.remove_webhook()
        except Exception:
            pass
        bot.infinity_polling(logger_level=logging.ERROR, allowed_updates=None)
