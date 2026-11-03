"""
radar_ch2.py — Радар Дніпро, КАНАЛ 2 («Ями Днепр погода (тучі)», закрита група).

Читає групу окремим акаунтом-читачем (Telethon + сесія з секретів GitHub),
жорстко фільтрує балачки й питання, ставить мітки в ОКРЕМІ папки Firebase:
  ch2_points          — живі мітки (40 хв)
  ch2_stats_archive   — архів (для «Хроніки» і радіо)
  ch2_status          — «пульс» читача (для пометки на перемикачі)

Перший канал (radar.py) цей файл НЕ змінює і від нього не залежить у роботі:
звідти беруться лише спільні функції (розпізнавання вулиць, база знань, Gemini-ключі).

БЕЗПЕКА: репозиторій публічний, тому в журнал пишуться ТІЛЬКИ ЦИФРИ.
Жодних текстів повідомлень, імен авторів чи назв улиць у лог не потрапляє.
"""
import os
import re
import sys
import json
import time
import random
import asyncio

import requests

import radar as R1  # спільні функції першого каналу (main у ньому не запускається)

from telethon import TelegramClient, errors
from telethon.sessions import StringSession

# ----------------------------------------------------------------------
# Налаштування
# ----------------------------------------------------------------------
TG_API_ID = int(os.environ.get("TG_API_ID", "0").strip() or "0")
TG_API_HASH = os.environ.get("TG_API_HASH", "").strip()
TG_SESSION = os.environ.get("TG_SESSION", "").strip()
TG_CHAT = os.environ.get("TG_CHAT", "").strip()          # необов'язково: id або @username групи
GROUP_TITLE_RE = re.compile(r"ям[ыи]\s*дн[еі]пр", re.IGNORECASE)

BASE = R1.BASE_FB_URL
CH2_POINTS_URL = f"{BASE}/ch2_points.json" if BASE else ""
CH2_ARCHIVE_URL = f"{BASE}/ch2_stats_archive.json" if BASE else ""
CH2_STATUS_URL = f"{BASE}/ch2_status.json" if BASE else ""

LIFETIME_MS = 40 * 60 * 1000
POLL_SEC = 20
START_LOOKBACK_MS = 60 * 60 * 1000      # при старті беремо повідомлення за останню годину
MAX_RUNTIME_SEC = 5 * 3600 + 40 * 60
KEY_PREFIX = "tg2_"

# Вода (місце для «навчання», як у першому каналі)
WATER_LAT, WATER_LNG = 48.5020, 34.9280


def log(msg):
    print(msg, flush=True)


# ----------------------------------------------------------------------
# Словники для другого каналу
# ----------------------------------------------------------------------
# Питання (повідомлення відкидається, але запам'ятовується — на нього можуть відповісти)
Q_RE = re.compile(
    r"\?|❓|❔|🤔|🧐|🙏"
    r"|^\s*(?:а\s+)?(?:как|як|шо|що|что|кто|хто|где|де)\b"
    r"|\b(?:подскаж\w*|підкаж\w*|кто\s+знает|хто\s+знає|кто\s+в\s+курсе|хто\s+в\s+курсі|есть\s+инф\w*|є\s+інф\w*"
    r"|как\s+там|як\s+там|что\s+там|шо\s+там|що\s+там|кто\s+проезжал|хто\s+їхав|кто\s+ехал|как\s+обстановка"
    r"|скажите|скажіть|знает\s+кто|знає\s+хто|кто\s+был|хто\s+був)\b",
    re.IGNORECASE,
)

# Небезпека (у цій групі «яма», «тучі», «оливки», «баклажани» = пост)
DANGER_RE = re.compile(
    r"(?<![а-яіїєґa-z])(?:"
    r"бп|б\s*/\s*п|б\.п|блок\s*-?\s*пост\w*|блокпост\w*|бус\w*|бусик\w*|ям[аиыуойе]?|ямк\w*"
    r"|туч\w*|хмар\w*|дожд\w*|дощ\w*|ливень|злива"
    r"|оливк\w*|баклажан\w*|нацгвард\w*|жезл\w*|вояк\w*|военн\w*|військов\w*|тцк|ттк|зелен[ыі]е?\s+человечк\w*"
    r"|мент\w*|полиц\w*|поліц\w*|копы|копи|мусор\w*|патрул\w*|экипаж\w*|екіпаж\w*|облав\w*"
    r"|моргал\w*|моргают|мигал\w*|мигают|помигал\w*|блимал\w*"
    r"|принима\w*|приймаю\w*|пакуют|пакують|пакував\w*|ловят|ловлять|хватают|хапають"
    r"|стоят|стоять|стоїть|стоит|стояли|ставят|ставлять|тормоз\w*|зупиня\w*|останавлива\w*"
    r"|провер\w*|перевір\w*|шмона\w*|аккуратн\w*|акуратн\w*|окуратн\w*|обережн\w*|осторожн\w*"
    r")(?![а-яіїєґa-z])",
    re.IGNORECASE,
)

# Фрази «без постів» — прибираємо перед пошуком небезпеки, щоб «без бп» не стало червоним
NO_DANGER_PHRASE_RE = re.compile(
    r"(?<![а-яіїєґa-z])(?:"
    r"(?:без|нет|нету|немає|нема|ні|ни)\s+(?:бп|б\s*/\s*п|ям\w*|блок\w*|никого|нікого|туч\w*|хмар\w*|постов|постів|поста)"
    r"|(?:бп|б\s*/\s*п|ям\w*|блок\w*|туч\w*|хмар\w*|постов|постів|поста)\s+(?:нет|нету|немає|нема)"
    r")(?![а-яіїєґa-z])",
    re.IGNORECASE,
)

CLEAN_RE = re.compile(
    r"(?<![а-яіїєґa-z])(?:"
    r"ч[иі]?[сc]т[оa]\w*|чсто|чичто|чистенько|пусто|вільно|свободно|спокійно|спокойно|тихо"
    r"|никого|нікого|ничего\s+нет|нічого\s+нема\w*|все\s+хорошо|всё\s+хорошо|все\s+ок|все\s+добре"
    r"|норм|нормально|нормик|сонц\w*|солнц\w*|сонечк\w*|ясно|сухо|зелено|без\s+бп|без\s+ям\w*"
    r")(?![а-яіїєґa-z])",
    re.IGNORECASE,
)
CLEAN_NEG_RE = re.compile(r"не\s*(?:чисто|норм\w*|пусто|спок\w*|тихо|вільно|свободно)", re.IGNORECASE)
GONE_RE = re.compile(
    r"(?<![а-яіїєґa-z])(?<!не\s)(?<!ні\s)(?:уехали|уїхали|поехали|поїхали|сняли\w*|зняли\w*|снялись|знялись|знялися|убрали\w*|прибрали\w*"
    r"|свернул\w*|згорнул\w*|разъехал\w*|роз'їхал\w*|пропали|уже\s+нет|вже\s+нема\w*|уже\s+нету|нет\s+уже)(?![а-яіїєґa-z])",
    re.IGNORECASE,
)
SUN_EMOJIS = ("☀", "🌞", "🌈", "🍏", "🟢", "💚", "👍", "👌")
CLOUD_EMOJIS = ("🌤", "⛅", "🌥", "🌦", "☁", "🌧", "⛈", "🌩", "🌨", "🌪", "🌫", "☔", "💧", "💦", "🚔", "👮", "🚨", "🔴")

# Слова, які викидаємо з тексту питання, щоб залишилося саме місце
Q_STRIP_RE = re.compile(
    r"\b(?:подскаж\w*|підкаж\w*|пожалуйста|будь\s*ласка|плиз|плз|срочно|терміново|как|як|шо|що|что|кто|хто|знает|знає"
    r"|в\s+курсе|в\s+курсі|есть|є|инф\w*|інф\w*|там|сейчас|зараз|обстановка|ситуация|ситуація|погода|дела|справи"
    r"|ребята|ребят|парни|хлопці|люди|народ|друзья|друзі|доброе|добрий|утро|ранок|ранку|привет|привіт|а|ну|и|і)\b",
    re.IGNORECASE,
)

# Місцеві назви, яких немає в спільній базі (лише ті, де місце однозначне)
CH2_LOCAL_DB = [
    (re.compile(r"(?<![а-яіїa-z])(?:лак(?:окраск\w*|офарб\w*)?)(?![а-яіїa-z])", re.I), "вул. Каштанова (Лакофарба)", 48.5035, 35.0838),
    (re.compile(r"зв[еёі]здн\w*\s*бул\w*|бул\w*\s*зв[еёі]здн\w*|зорян\w*\s*бул\w*|бул\w*\s*зорян\w*|\bзв[еёі]здн(?:ый|ом|ого)\b|\bзорян(?:ий|ому|ого|ый)\b", re.I), "Зоряний бульвар", 48.42746, 35.01983),
    (re.compile(r"краснопол\w*|краснопіл\w*", re.I), "Краснопілля (Краснопільська)", 48.41002, 34.99602),
    (re.compile(r"\bос[еі]нн\w*", re.I), "вул. Осіння (Лівий берег)", 48.50311, 35.08842),
]


# ----------------------------------------------------------------------
# Класифікація тексту
# ----------------------------------------------------------------------
def is_question(text):
    return bool(Q_RE.search(text or ""))


def status_of(text):
    """True = чисто, False = пост, None = не зрозуміло (балачки), 'mixed' = є і те, і те."""
    t = (text or "").lower().replace("ё", "е")
    if not t.strip():
        return None
    t_for_danger = NO_DANGER_PHRASE_RE.sub(" ", t)
    has_clean = (bool(CLEAN_RE.search(t)) or any(e in text for e in SUN_EMOJIS)) and not CLEAN_NEG_RE.search(t)
    has_danger = bool(DANGER_RE.search(t_for_danger)) or any(e in text for e in CLOUD_EMOJIS) or bool(CLEAN_NEG_RE.search(t))
    gone = bool(GONE_RE.search(t))
    if re.search(r"(?<![а-яіїєґa-z])н[еі]\s+(?:уехал|уїхал|разъехал|роз'їхал|сняли|зняли|снял|убрали|прибрали|свернул|згорнул)", t):
        has_danger = True
    if gone and not has_clean:
        return True     # «уехали», «сняли», «уже нет» — пост був, а тепер його немає
    if has_clean and not has_danger:
        return True
    if has_danger and not has_clean:
        return False
    if has_clean and has_danger:
        return "mixed"
    if NO_DANGER_PHRASE_RE.search(t):
        return True
    return None


def question_place(text):
    """З питання «Подскажите как Космическая?» залишає «Космическая»."""
    t = re.sub(r"[?!❓❔🤔🧐🙏.,:;]+", " ", text or "")
    t = Q_STRIP_RE.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip(" -—")


def locate(text, kb_list):
    """Шукає місце без інтернету: свої назви каналу 2 → ручні правила і база першого каналу → список вулиць."""
    low = (text or "").lower().replace("ё", "е")
    for rx, name, la, ln in CH2_LOCAL_DB:
        if rx.search(low):
            return name, la, ln
    addr, lat, lng = R1.geocode_local(text)
    if addr and lat and lng:
        return addr, round(float(lat), 5), round(float(lng), 5)
    kb = R1.match_knowledge_base(text, kb_list)
    if kb and kb.get("lat") and kb.get("lng"):
        try:
            return (kb.get("name") or kb.get("address") or kb.get("phrase"),
                    round(float(kb["lat"]), 5), round(float(kb["lng"]), 5))
        except (TypeError, ValueError):
            pass
    try:
        a2, la2, ln2 = R1.geocode_streets_list(text)
        if a2:
            return a2, la2, ln2
    except Exception:
        pass
    return None, None, None


def leftover_words(text):
    """Скільки букв залишається, якщо прибрати слова стану (для рішення «на воду»)."""
    t = CLEAN_RE.sub(" ", (text or "").lower())
    t = DANGER_RE.sub(" ", t)
    t = re.sub(r"[^а-яіїєґa-z]+", "", t)
    return len(t)


# ----------------------------------------------------------------------
# Gemini для складних повідомлень
# ----------------------------------------------------------------------
def gemini_batch(items):
    """items: [{"id": n, "text": "..."}]. Повертає {id: {...}}. Без ключів — порожньо."""
    if not items or not R1.GEMINI_KEYS:
        return {}
    prompt = f"""
Ти аналізуєш повідомлення з чату водіїв міста Дніпро (Україна) про пости поліції/ТЦК.
Сленг чату: «яма», «ями», «тучі», «хмари», «оливки», «баклажани», «бус», «БП», «стоять» = ПОСТ (небезпечно).
«чисто», «☀️», «пусто», «нікого», «норм» = чисто.
Для кожного повідомлення визнач:
- report: true, якщо воно ПОВІДОМЛЯЄ про пост або про його відсутність у конкретному місці Дніпра;
  false — питання, прохання, балачки, жарти, новини, реклама, повідомлення без місця.
- якщо report=true: status "чисто" або "опасно"; address (вулиця/орієнтир у Дніпрі);
  lat/lng строго в межах Дніпра (lat 48.25–48.70, lng 34.70–35.40). Якщо місце не визначити — found=false.
Повідомлення:
{json.dumps(items, ensure_ascii=False)}
Відповідай ВИКЛЮЧНО JSON-масивом:
[{{"id":0,"report":true,"found":true,"status":"опасно","address":"вул. ...","lat":48.45,"lng":35.01}},
 {{"id":1,"report":false}}]
"""
    for _ in range(max(1, len(R1.GEMINI_KEYS))):
        key = R1.get_active_gemini_key()
        for model in R1.SUPPORTED_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                r = requests.post(url, headers={"Connection": "close"}, timeout=15, json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
                })
                if r.status_code == 200:
                    raw = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    raw = raw.replace("```json", "").replace("```", "").strip()
                    data = json.loads(raw)
                    if isinstance(data, list):
                        return {d["id"]: d for d in data if isinstance(d, dict) and "id" in d}
                elif r.status_code in (429, 403):
                    R1.rotate_to_next_key()
                    break
            except Exception:
                R1.rotate_to_next_key()
                break
    return {}


# ----------------------------------------------------------------------
# Firebase
# ----------------------------------------------------------------------
PROCESSED = set()


def fb(method, url, **kw):
    try:
        return R1.fb_request(method, url, **kw)
    except Exception:
        return None


def preload_processed():
    for url in (CH2_POINTS_URL, CH2_ARCHIVE_URL):
        if not url:
            continue
        r = fb("GET", f"{url}?shallow=true", timeout=10)
        if r is not None and r.status_code == 200 and isinstance(r.json(), dict):
            for k in r.json().keys():
                mk = re.match(r"(tg2_\d+)", k)
                if mk:
                    PROCESSED.add(mk.group(1))
    log(f"✅ [КАНАЛ 2]: у базі вже є {len(PROCESSED)} оброблених записів")


def write_status(ok, reason=""):
    if not CH2_STATUS_URL:
        return
    fb("PUT", CH2_STATUS_URL, json={"last_active": int(time.time() * 1000), "ok": bool(ok), "reason": reason}, timeout=6)


def cleanup_points():
    if not CH2_POINTS_URL:
        return
    r = fb("GET", CH2_POINTS_URL, timeout=10)
    if r is None or r.status_code != 200 or not isinstance(r.json(), dict):
        return
    now = int(time.time() * 1000)
    old = {k: None for k, v in r.json().items()
           if not isinstance(v, dict) or (now - int(v.get("time") or 0)) > LIFETIME_MS}
    if old:
        fb("PATCH", CH2_POINTS_URL, json=old, timeout=10)
        log(f"🧹 [КАНАЛ 2]: прибрано застарілих міток: {len(old)}")


def save_point(key, text, addr, lat, lng, is_clean, t_ms, needs_training=False):
    now = int(time.time() * 1000)
    shown = text
    if is_clean and not re.search(r"(?:чисто|норм|без\s*ям|без\s*бп|☀|🌞)", text, re.I):
        shown = f"{text} (чисто)"
    if CH2_POINTS_URL and (now - t_ms) <= LIFETIME_MS:
        fb("PUT", CH2_POINTS_URL.replace(".json", f"/{key}.json"), timeout=8, json={
            "text": shown, "raw_text": text, "address": addr, "lat": lat, "lng": lng,
            "color": "green" if is_clean else "red", "status": "чисто" if is_clean else "опасно",
            "is_clean": bool(is_clean), "geo_refined": not needs_training, "needs_training": bool(needs_training),
            "channel": 2, "time": t_ms, "timestamp": t_ms,
        })
    if CH2_ARCHIVE_URL:
        fb("PUT", CH2_ARCHIVE_URL.replace(".json", f"/{key}.json"), timeout=8, json={
            "text": shown, "address": addr, "lat": lat, "lng": lng, "is_clean": bool(is_clean),
            "needs_training": bool(needs_training), "channel": 2, "time": t_ms,
        })


# ----------------------------------------------------------------------
# Обробка пачки повідомлень
# ----------------------------------------------------------------------
TEXT_CACHE = {}      # id повідомлення -> текст (для відповідей на питання)


def remember(msg_id, text):
    TEXT_CACHE[msg_id] = text or ""
    if len(TEXT_CACHE) > 3000:
        for k in sorted(TEXT_CACHE)[:1000]:
            TEXT_CACHE.pop(k, None)


async def parent_text(client, chat, msg):
    rid = getattr(getattr(msg, "reply_to", None), "reply_to_msg_id", None)
    if not rid:
        return None
    if rid in TEXT_CACHE:
        return TEXT_CACHE[rid]
    try:
        p = await client.get_messages(chat, ids=rid)
        txt = (getattr(p, "message", "") or "") if p else ""
        remember(rid, txt)
        return txt
    except Exception:
        return None


async def process(client, chat, messages, kb_list):
    stats = {"нових": 0, "питань": 0, "балачок": 0, "медіа/службових": 0, "зелених": 0, "червоних": 0,
             "на воду": 0, "без місця": 0, "через ШІ": 0}
    to_ai = []   # (key, text, status_or_None, t_ms)

    for m in sorted(messages, key=lambda x: x.id):
        text = (getattr(m, "message", "") or "").strip()
        remember(m.id, text)
        key = f"{KEY_PREFIX}{m.id}"
        if key in PROCESSED:
            continue
        PROCESSED.add(key)
        stats["нових"] += 1

        if getattr(m, "action", None) or not text:
            stats["медіа/службових"] += 1
            continue
        if getattr(m, "via_bot_id", None) or R1.is_ad_or_spam(text):
            stats["балачок"] += 1
            continue
        if is_question(text):
            stats["питань"] += 1
            continue

        t_ms = int(m.date.timestamp() * 1000)

        # Кілька рядків з різними місцями («Береговая ☀️ / Отечественная ☀️») — кожен рядок окремо
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if len(lines) > 1 and len(text) <= 400:
            parts = [ln for ln in lines if status_of(ln) is not None and not is_question(ln) and locate(ln, kb_list)[0]]
            if len(parts) >= 2:
                for idx, ln in enumerate(parts):
                    st_l = status_of(ln)
                    a_l, la_l, ln_l = locate(ln, kb_list)
                    if st_l in (True, False):
                        save_point(f"{key}_{idx}", ln, a_l, la_l, ln_l, st_l, t_ms)
                        stats["зелених" if st_l else "червоних"] += 1
                    else:
                        to_ai.append((f"{key}_{idx}", ln, st_l, t_ms))
                continue

        report_text = text
        st = status_of(text)

        # Відповідь на питання: «Как Космическая?» → «Чисто» = Космическая чисто
        ptxt = await parent_text(client, chat, m)
        addr, lat, lng = locate(text, kb_list)
        if not addr and ptxt and is_question(ptxt) and st is not None and len(text) <= 60:
            place = question_place(ptxt)
            if len(place) >= 3:
                a2, la2, ln2 = locate(place, kb_list)
                report_text = f"{place[:1].upper()}{place[1:]}: {text}"
                if a2:
                    addr, lat, lng = a2, la2, ln2

        if st is None:
            stats["балачок"] += 1
            continue
        if len(text) > 220:          # довгі тексти — це майже завжди обговорення, не звіт
            stats["балачок"] += 1
            continue

        if addr and st in (True, False):
            save_point(key, report_text, addr, lat, lng, st, t_ms)
            stats["зелених" if st else "червоних"] += 1
        else:
            to_ai.append((key, report_text, st, t_ms))

    if to_ai:
        batch = gemini_batch([{"id": i, "text": it[1]} for i, it in enumerate(to_ai)])
        for i, (key, rtext, st, t_ms) in enumerate(to_ai):
            ai = batch.get(i)
            if ai is not None and not ai.get("report"):
                stats["балачок"] += 1
                continue
            final_status = st
            if ai is not None and ai.get("status") in ("чисто", "опасно") and st in ("mixed", None):
                final_status = ai["status"] == "чисто"
            if final_status not in (True, False):
                stats["балачок"] += 1
                continue
            if ai and ai.get("found") and ai.get("lat") and ai.get("lng"):
                try:
                    la, ln = float(ai["lat"]), float(ai["lng"])
                except (TypeError, ValueError):
                    la = ln = 0
                if 48.25 <= la <= 48.70 and 34.70 <= ln <= 35.40:
                    save_point(key, rtext, ai.get("address") or "Дніпро", round(la, 5), round(ln, 5), final_status, t_ms)
                    stats["через ШІ"] += 1
                    stats["зелених" if final_status else "червоних"] += 1
                    continue
            # Місце не знайдено. На воду (для ручного навчання) — тільки якщо в тексті справді є назва
            if (ai is not None and ai.get("report")) or (ai is None and leftover_words(rtext) >= 4):
                wl = round(WATER_LAT + random.uniform(-0.004, 0.004), 5)
                wn = round(WATER_LNG + random.uniform(-0.006, 0.006), 5)
                save_point(key, rtext, "Потребує навчання (натисніть та перетягніть з річки)", wl, wn,
                           final_status, t_ms, needs_training=True)
                stats["на воду"] += 1
            else:
                stats["без місця"] += 1

    if stats["нових"]:
        log("📢 [КАНАЛ 2]: " + " | ".join(f"{k}: {v}" for k, v in stats.items()))


# ----------------------------------------------------------------------
# Telegram
# ----------------------------------------------------------------------
async def find_group(client):
    if TG_CHAT:
        try:
            return await client.get_entity(int(TG_CHAT) if TG_CHAT.lstrip("-").isdigit() else TG_CHAT)
        except Exception:
            log("⚠️ [КАНАЛ 2]: TG_CHAT задано, але групу за ним не знайдено — шукаю за назвою")
    best = None
    async for d in client.iter_dialogs():
        if d.is_group and GROUP_TITLE_RE.search(d.name or ""):
            size = getattr(d.entity, "participants_count", 0) or 0
            if best is None or size > best[0]:
                best = (size, d.entity)
    return best[1] if best else None


def trigger_self_restart():
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "MyDnipro/radar-core")
    if not token:
        log("⚠️ [КАНАЛ 2]: немає GITHUB_TOKEN — самоперезапуск скасовано")
        return
    try:
        r = requests.post(f"https://api.github.com/repos/{repo}/actions/workflows/radar2.yml/dispatches",
                          headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {token}"},
                          json={"ref": "main"}, timeout=10)
        log("✅ [КАНАЛ 2]: естафету передано" if r.status_code == 204 else f"❌ [КАНАЛ 2]: самоперезапуск HTTP {r.status_code}")
    except Exception:
        log("⚠️ [КАНАЛ 2]: помилка мережі при самоперезапуску")


async def main():
    log("🚀 [КАНАЛ 2]: запуск читача групи «Ями»")
    if not (TG_API_ID and TG_API_HASH and TG_SESSION):
        log("❌ [КАНАЛ 2]: не задано секрети TG_API_ID / TG_API_HASH / TG_SESSION")
        sys.exit(1)
    if not BASE:
        log("❌ [КАНАЛ 2]: не задано FIREBASE_URL")
        sys.exit(1)

    # Пауза, щоб попередній запуск точно встиг відключитися (одна сесія — одне підключення)
    await asyncio.sleep(15)

    client = TelegramClient(StringSession(TG_SESSION), TG_API_ID, TG_API_HASH,
                            device_model="Radar Reader", system_version="Linux", app_version="1.0",
                            receive_updates=False)
    restart = False
    try:
        await client.connect()
        if not await client.is_user_authorized():
            log("❌ [КАНАЛ 2]: сесія недійсна (Telegram вийшов з акаунта). Потрібно заново зробити крок з Colab.")
            write_status(False, "auth")
            sys.exit(1)

        chat = await find_group(client)
        if chat is None:
            log("❌ [КАНАЛ 2]: акаунт-читач не бачить групу «Ями» (не вступив або його видалили)")
            write_status(False, "no_group")
            sys.exit(1)
        log(f"✅ [КАНАЛ 2]: групу знайдено (id {getattr(chat, 'id', '?')})")

        preload_processed()
        R1.sync_cloud_knowledge_and_spam()
        write_status(True)

        # Старт: повідомлення за останню годину
        now_ms = int(time.time() * 1000)
        first = await client.get_messages(chat, limit=200)
        last_id = max((m.id for m in first), default=0)
        recent = [m for m in first if (now_ms - int(m.date.timestamp() * 1000)) <= START_LOOKBACK_MS]
        for m in first:
            remember(m.id, getattr(m, "message", "") or "")
        await process(client, chat, recent, R1.get_knowledge_base())

        start = time.time()
        while time.time() - start < MAX_RUNTIME_SEC:
            try:
                cleanup_points()
                R1.sync_cloud_knowledge_and_spam()
                write_status(True)
                new = await client.get_messages(chat, limit=100, min_id=last_id)
                if new:
                    last_id = max(last_id, max(m.id for m in new))
                    await process(client, chat, new, R1.get_knowledge_base())
            except errors.FloodWaitError as e:
                log(f"⏳ [КАНАЛ 2]: Telegram просить почекати {e.seconds} с")
                await asyncio.sleep(min(int(e.seconds) + 5, 900))
            except (errors.AuthKeyUnregisteredError, errors.AuthKeyDuplicatedError,
                    errors.SessionRevokedError, errors.UserDeactivatedError, errors.UserDeactivatedBanError):
                log("❌ [КАНАЛ 2]: Telegram відкликав сесію читача. Потрібно заново зробити крок з Colab.")
                write_status(False, "auth")
                sys.exit(1)
            except errors.ChannelPrivateError:
                log("❌ [КАНАЛ 2]: читача видалили з групи або доступ закрито")
                write_status(False, "no_group")
                sys.exit(1)
            except Exception as e:
                log(f"⚠️ [КАНАЛ 2]: помилка циклу ({type(e).__name__})")
                if not client.is_connected():
                    try:
                        await client.connect()
                    except Exception:
                        pass
            await asyncio.sleep(POLL_SEC)
        restart = True
        log("⏱️ [КАНАЛ 2]: час роботи вичерпано, передаю естафету")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
    if restart:
        await asyncio.sleep(3)
        trigger_self_restart()


if __name__ == "__main__":
    asyncio.run(main())
