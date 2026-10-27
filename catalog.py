# ═══════════════════════════════════════════════════════════════
# КАТАЛОГ: стилі, жанри, музика, голоси
#
# СТИЛЬ  = як виглядає кадр (колір, світло, оптика, плівка/рендер,
#          фактура, одяг і зачіски, емоція, звучання).
# ЖАНР   = у якому світі й з яким настроєм (локація, фон, погода,
#          події вдалині, музика).
# Ні стиль, ні жанр НЕ змінюють дії, тіла, темп і слова пісні.
#
# Кожен пункт: ключ → (емодзі, назва UA, назва EN, рецепт для ШІ англійською)
# Порядок усередині списків — від теплих до холодних.
# ═══════════════════════════════════════════════════════════════

FILM_STYLES = {
    "f_child": ("☀️", "Ностальгія", "Nostalgia",
        "COLOR & LIGHT: overexposed golden summer sun, faded warm colors of old family photos, soft blooming glow around "
        "every bright area, sun flares. LENS: slightly soft focus toward the edges, gentle vignette, dreamy shallow depth. "
        "MEDIUM: Super 8 or 1990s home-camcorder footage, visible grain, light leaks and orange film burns at the frame edges. "
        "WORLD DETAILS: dust floating in sunbeams, dandelion fluff drifting in the air, bicycles, a garden swing, laundry "
        "on a line, old patterned wallpaper or a sunny yard. WARDROBE: knitted cardigans, sandals, bright shorts, hair "
        "ribbons, faded t-shirts. EMOTION: tender warm nostalgia with a quiet sadness — a memory you can never return to. "
        "SOUND: the melody on a warm acoustic guitar and soft keys, cicadas, soft tape hiss."),
    "f_film": ("🎞", "Німе кіно", "Silent film",
        "COLOR & LIGHT: sepia or silver black-and-white, high-key studio light, bright halos on whites. LENS: vintage "
        "soft lens, heavy round vignette, iris-in feel at the corners. MEDIUM: 1920s silent-film footage — scratches, "
        "dust specks, gate weave, flicker, slightly uneven exposure. WORLD DETAILS: period streets, gas lamps, old cars or "
        "carriages, ornate interiors. WARDROBE: 1920s suits, flat caps, cloche hats, suspenders, pearls, slicked hair. "
        "EMOTION: charming, theatrical, a little melancholic. SOUND: the melody arranged for a lone ragtime piano with a "
        "projector rattle and crackle."),
    "f_retrofut": ("🛸", "Ретро-космос", "Retrofuturism",
        "COLOR & LIGHT: optimistic pastel atomic-age palette — mint, coral, cream, chrome highlights, bright even light. "
        "LENS: clean wide lens, Technicolor saturation. MEDIUM: glossy 1950s-60s film stock. WORLD DETAILS: rounded chrome "
        "architecture, glass domes, rocket-shaped cars, monorails, friendly robots with antennas in the background. "
        "WARDROBE: shiny jumpsuits, bubble helmets, space-age dresses, retro hairstyles. EMOTION: naive wonder about the "
        "future. SOUND: theremin and vintage space-age lounge arrangement."),
    "f_pastel": ("💖", "Рожевий світ", "Pink world",
        "COLOR & LIGHT: candy palette of hot pink, baby blue and lemon, perfect bright soft light with no harsh shadows. "
        "LENS: clean wide lens, tilt-shift miniature hint. MEDIUM: glossy, plastic-perfect surfaces. WORLD DETAILS: pink "
        "dollhouse buildings, plastic palm trees, glitter, perfectly clean streets. WARDROBE: doll-perfect styling, glossy "
        "hair, pastel outfits, heart sunglasses. EMOTION: playful, sweet, ironic perfection. SOUND: bubblegum pop arrangement "
        "with sparkly chimes."),
    "f_fashion": ("👠", "Модний подіум", "Fashion runway",
        "COLOR & LIGHT: glossy high-fashion light, strong white key light, bold color blocks, rim light, flashes of "
        "photographers' cameras. LENS: sharp portrait lens, creamy background blur, slow elegant tracking camera. MEDIUM: "
        "luxury fashion-film grade, flawless fabric texture. WORLD DETAILS: a surreal couture runway — a long glossy catwalk "
        "through an unexpected place (desert dunes, a flooded marble hall, a glass corridor over clouds), front-row "
        "silhouettes, wind machine moving hair and fabric. WARDROBE: avant-garde couture looks, sculptural silhouettes, "
        "perfect makeup and hair. EMOTION: confident, cool, aspirational. SOUND: sleek minimal electronic runway beat."),
    "f_real": ("🎬", "Сучасне кіно", "Modern film",
        "COLOR & LIGHT: true-to-life colors with a soft cinematic grade, natural motivated light, golden-hour rim light. "
        "LENS: modern large-sensor cinema camera, shallow depth of field, slow camera push-ins, smooth drone fly-over "
        "establishing moves. MEDIUM: photorealistic live action, natural skin texture, realistic materials, 4K clarity. "
        "WORLD DETAILS: a real location matching the scene, atmospheric haze, dust in the light. WARDROBE: realistic, "
        "well-styled clothes. EMOTION: grounded, cinematic, believable. SOUND: natural realistic sound with subtle score."),
    "f_doc": ("🎤", "Репортаж", "Documentary",
        "COLOR & LIGHT: available light only, slightly underexposed shadows. LENS: handheld camera, small shake, quick "
        "reframing and focus pulls. MEDIUM: raw unpolished documentary footage. WORLD DETAILS: real streets, real people "
        "passing in the background. WARDROBE: everyday clothes. EMOTION: immediate, authentic, 'caught on camera'. SOUND: "
        "on-camera microphone sound with ambience."),
    "f_pov": ("📹", "Очима героя", "POV action",
        "COLOR & LIGHT: punchy contrast, bright daylight. LENS: ultra-wide fisheye action camera, strong barrel distortion, "
        "level horizon. MEDIUM: action-camera footage, crisp motion. WORLD DETAILS: the same scene seen as an immersive "
        "first-person or chest-mounted view. WARDROBE: unchanged, sporty details. EMOTION: adrenaline, you are there. SOUND: "
        "wind noise on the microphone, close breathing, impacts."),
    "f_game": ("🎮", "Відеогра", "Video game",
        "COLOR & LIGHT: sun-drenched saturated colors, ray-traced reflections, golden-hour haze. LENS: game-trailer camera "
        "with smooth cinematic moves. MEDIUM: next-gen open-world game render, hyper-detailed 3D characters. WORLD DETAILS: "
        "sunny coastal city, palm trees, sports cars, neon signs at dusk. WARDROBE: stylized streetwear. EMOTION: cool, "
        "confident, cinematic swagger. SOUND: game-trailer bass hits and city ambience."),
    "f_block": ("🎬", "Блокбастер", "Blockbuster",
        "COLOR & LIGHT: rich contrast, deep shadows, teal-and-orange grade, dramatic backlight and volumetric rays. LENS: "
        "large-format camera, anamorphic flares, epic wide shots. MEDIUM: fine film grain, huge scale. WORLD DETAILS: the "
        "location made grander, atmospheric haze and particles. WARDROBE: movie-star styling. EMOTION: epic, heroic, "
        "goosebumps. SOUND: huge orchestral and percussive arrangement with deep booms."),
    "f_clip": ("🎵", "Музичний кліп", "Music video",
        "COLOR & LIGHT: colored rim lights, moving light beams, haze, strobes on the beat. LENS: stylish gimbal moves, lens "
        "flares. MEDIUM: glossy music-video look. WORLD DETAILS: stage-like location with light beams and smoke. WARDROBE: "
        "performer styling, statement outfits. EMOTION: energetic, rhythmic, magnetic. SOUND: polished modern production "
        "of the same song."),
    "f_vhs": ("📼", "Камера 90-х", "90s camcorder",
        "COLOR & LIGHT: harsh on-camera flash or tungsten indoor light, oversaturated reds. LENS: cheap camcorder with "
        "auto-focus hunting. MEDIUM: low-resolution VHS tape — scanlines, color bleeding, tracking noise lines, a blinking "
        "PLAY icon feel without readable text. WORLD DETAILS: 1990s interiors, CRT TV, posters. WARDROBE: 1990s tracksuits, "
        "denim, scrunchies. EMOTION: home-video nostalgia. SOUND: tape-warped, slightly muffled sound with hiss."),
    "f_surreal": ("👁", "Сюрреалізм", "Surrealism",
        "COLOR & LIGHT: dreamlike soft light from impossible directions, muted pastel sky. LENS: calm, slow, perfectly "
        "composed. MEDIUM: painted-dream realism. WORLD DETAILS: impossible geometry, floating objects, melting clocks, "
        "staircases to nowhere, giant objects at strange scale. WARDROBE: same clothes with subtle impossible details. "
        "EMOTION: uncanny calm, curiosity. SOUND: reversed echoes and soft drones. VISUAL DISTORTIONS ARE WELCOME for the "
        "world and textures, but bodies, proportions and motion stay exactly as in the source."),
    "f_psy": ("🌀", "Психоделіка", "Psychedelic",
        "COLOR & LIGHT: liquid rainbow colors, glowing neon edges, color trails. LENS: kaleidoscope mirroring at the frame "
        "edges. MEDIUM: fluid psychedelic animation over live action. WORLD DETAILS: breathing walls, melting and swirling "
        "surroundings, fractal patterns, flowers opening everywhere. WARDROBE: iridescent patterns flowing over clothes and "
        "skin. EMOTION: euphoric trip. SOUND: phased, swirling psychedelic arrangement. VISUAL DISTORTIONS ARE WELCOME for "
        "the world and textures, but bodies, proportions and motion stay exactly as in the source."),
    "f_synth": ("🌆", "Неон 80-х", "80s neon",
        "COLOR & LIGHT: neon magenta and cyan, sunset gradient, glowing grid on the horizon, chrome reflections. LENS: soft "
        "glow, light bloom. MEDIUM: 1980s retro-wave film look. WORLD DETAILS: neon night highway, palm silhouettes, arcade "
        "signs. WARDROBE: 80s jackets, aviator sunglasses, big hair, neon accents. EMOTION: cool retro night drive. SOUND: "
        "analog synth arrangement with gated drums."),
    "f_noir": ("🌃", "Нічне місто", "Night city",
        "COLOR & LIGHT: night, deep blacks, hard side light through blinds, single neon accents in red or teal, smoke. LENS: "
        "low angles, long shadows. MEDIUM: high-contrast film. WORLD DETAILS: rain-wet streets with reflections, alleys, "
        "flickering signs. WARDROBE: long coats, hats, dark suits. EMOTION: tense, lonely, mysterious. SOUND: muted trumpet "
        "and rain."),
    "f_bw": ("🖤", "Чорно-біле", "Black & white",
        "COLOR & LIGHT: black-and-white only, deep inky blacks, hard key light, venetian-blind shadows across faces and "
        "walls, cigarette-smoke haze. LENS: classic 1940s studio camera, Dutch angles, low angles. MEDIUM: grainy 35mm "
        "black-and-white film, slight gate weave. WORLD DETAILS: rain on the glass, a lone streetlamp, wet cobblestones, an "
        "old office with a ceiling fan. WARDROBE: fedoras, trench coats, 1940s suits and dresses, red-lip glamour in grey "
        "tones. EMOTION: fatalistic suspense. SOUND: smoky jazz saxophone and rain."),
    "f_wes": ("🎀", "Пастель-кіно", "Pastel cinema",
        "COLOR & LIGHT: soft pastel palette — powder pink, mint, mustard yellow — flat even light. LENS: perfectly centered "
        "symmetrical compositions, frontal static camera, whip pans between neat tableaux. MEDIUM: crisp 35mm film with "
        "storybook clarity. WORLD DETAILS: dollhouse-like interiors, vintage props, hand-painted signs, miniature-model "
        "exteriors. WARDROBE: matching uniforms, vintage suits, berets, neat retro haircuts. EMOTION: deadpan, whimsical, "
        "bittersweet. SOUND: quirky harpsichord, pizzicato strings and whistling."),
    "f_goth": ("🦇", "Готика", "Gothic",
        "COLOR & LIGHT: desaturated moonlit blues and greys with candle-orange accents, pale faces, deep shadows. LENS: "
        "slightly exaggerated wide angles, swirling camera. MEDIUM: dark fairy-tale film look. WORLD DETAILS: crooked "
        "spiral trees, gothic towers, striped lampposts, fog, bats against a full moon, crooked graveyard fences. WARDROBE: "
        "black-and-white striped clothes, Victorian coats, lace, dark eyeliner, wild hair. EMOTION: spooky but charming. "
        "SOUND: harpsichord, choir and gothic waltz."),
    "f_mini": ("🔎", "Світ-іграшка", "Toy world",
        "COLOR & LIGHT: bright sunny saturated colors, crisp toy-like highlights. LENS: strong tilt-shift effect — a thin "
        "band of sharp focus with heavy blur at the top and bottom, high camera looking down, slightly sped-up feel. "
        "MEDIUM: the whole world looks like a detailed scale model: model-railway trees, tiny painted buildings, tiny "
        "cars, matte plastic and painted textures. WORLD DETAILS: model-kit streets, scale-model scenery, fake grass mats. "
        "WARDROBE: people look like tiny painted scale figures with simple bright clothes. EMOTION: playful, curious. "
        "SOUND: light pizzicato and ticking clockwork arrangement."),
    "f_figure": ("🧩", "Фігурка", "Figurine",
        "COLOR & LIGHT: bright product-shot light, soft studio reflections, clean gradient or shelf background. LENS: "
        "macro lens close to the subjects, shallow depth of field, slow product-style orbit. MEDIUM: every adult person "
        "becomes a designer vinyl collectible figure — glossy plastic skin, simplified rounded proportions, big head, "
        "visible seam lines and painted details, but the same poses and movements. WORLD DETAILS: the scene recreated "
        "as a detailed collector's diorama on a desk or shelf, a collector's box nearby. WARDROBE: the same outfits as "
        "molded painted plastic. EMOTION: fun, surprising. SOUND: plastic clicks and a bouncy synth arrangement."),
    "f_lofi": ("☕", "Затишний дім", "Cozy lo-fi",
        "COLOR & LIGHT: soft warm lamp light, purple-orange dusk through the window, gentle glow. LENS: calm static or "
        "very slow camera, soft focus. MEDIUM: cozy hand-painted lo-fi animation look over live action, subtle grain. "
        "WORLD DETAILS: rain on the window, a steaming mug, houseplants, fairy lights, a city skyline at dusk, a sleeping "
        "cat on the windowsill. WARDROBE: oversized hoodies, headphones, knitted sweaters. EMOTION: calm, safe, "
        "relaxing. SOUND: lo-fi hip-hop arrangement with vinyl crackle and rain."),
    "f_pulse": ("🔊", "Під ритм", "Music pulse",
        "COLOR & LIGHT: dark background with glowing neon light that flashes on every beat, color shifts on drops. "
        "LENS: subtle zoom bumps and camera shakes on the beat. MEDIUM: audio-reactive visuals — the background, light "
        "and surfaces pulse, ripple and morph in time with the music; equalizer-like light bars and waves in the "
        "environment. WORLD DETAILS: walls and floor breathing with the bass, particles bursting on the kick. WARDROBE: "
        "unchanged with glowing edges. EMOTION: hypnotic, energetic. SOUND: punchy beat with strong bass. VISUAL "
        "DISTORTIONS ARE WELCOME for the world and textures, but bodies, proportions and motion stay exactly as in the "
        "source."),
    "f_absurd": ("🐟", "Дивні меми", "Absurd meme",
        "COLOR & LIGHT: oversaturated bright colors, harsh flat daylight. LENS: slightly fisheye, dramatic zooms. MEDIUM: "
        "glossy hyper-real 3D render. CHARACTERS: every person becomes an absurd hybrid creature — for example a shark "
        "wearing sneakers, a coffee cup with legs, a crocodile-airplane — keeping the same poses, movements, timing and "
        "number of characters. WORLD DETAILS: an ordinary location treated completely seriously. EMOTION: deadpan, "
        "funny, meme energy. SOUND: dramatic over-the-top narrator-style music and cartoon sound effects."),
    "f_dune": ("🏜", "Піщана планета", "Sand planet",
        "COLOR & LIGHT: blazing orange and ochre desert palette, hazy golden-white sky, two pale suns, heat shimmer, "
        "long hard shadows, dust in the air. LENS: huge epic wide shots, slow monumental camera moves, people tiny "
        "against vast landscapes. MEDIUM: large-format cinematic film, fine grain, muted desaturated tones. WORLD "
        "DETAILS: endless sculpted sand dunes, monumental brutalist stone fortresses, dragonfly-wing aircraft overhead, "
        "spice dust glittering in the light, a colossal sandworm rising from the sand far in the distance, sandstorm "
        "wall on the horizon. WARDROBE: grey-brown desert body suits with tubes and hoods, flowing dark cloaks, face "
        "masks, intense blue-glowing eyes. EMOTION: epic, mythic, solemn. SOUND: deep throat-singing choir, huge low "
        "drums and desert wind."),
    "f_matrix": ("🟩", "Цифровий код", "Digital code",
        "COLOR & LIGHT: everything tinted sickly green, cold fluorescent light, deep blacks, glossy reflections. LENS: "
        "sleek symmetrical framing, slow push-ins. MEDIUM: crisp late-1990s cyber-thriller film look. WORLD DETAILS: "
        "cascading green digital code raining on screens and glass, grey office corridors, rainy rooftops, old green "
        "computer monitors, ringing payphones. WARDROBE: long black leather coats, tiny black sunglasses, black "
        "boots, slick hair. EMOTION: cool, mysterious, 'nothing is real'. SOUND: dark industrial electronic beat and "
        "digital glitches."),
    "f_inter": ("🪐", "Далекий космос", "Deep space",
        "COLOR & LIGHT: dusty amber Earth light or cold blue space light, a giant black hole with a glowing golden "
        "accretion ring in the sky. LENS: IMAX-scale wide shots, slow drifting camera, real-feeling handheld moments. "
        "MEDIUM: 70mm film, natural grain, realistic practical look. WORLD DETAILS: dusty cornfields under a brown sky, "
        "a frozen ice planet with white cloud cliffs, a shallow ocean planet with mountain-high waves, a rotating "
        "spaceship ring, blocky robot silhouettes. WARDROBE: bulky white-and-grey spacesuits with patches, dusty "
        "farm clothes. EMOTION: awe, loneliness, hope. SOUND: huge church-organ score and deep space silence."),
}

# ═══════════════════════════════════════════════════════════════
# ТАНЦІ — окреме вікно (кнопка «💃 Танці» у стилях кіно).
# На відміну від інших стилів, танець ЗМІНЮЄ рухи героїв: вони танцюють цей танець
# у ритм ролика (той самий таймінг і кількість людей). Рецепт починається з "DANCE:".
# ═══════════════════════════════════════════════════════════════
_D = ("DANCE: this is a dance video. Ignore the source movements completely — every person performs {d}. Big, clear, "
      "recognizable dance moves from the first second to the last, a new move every 1-2 seconds, exactly on the music "
      "beat. From the source keep only the number of people, the camera framing and the tempo. ")
DANCE_STYLES = {
    "d_hopak": ("🇺🇦", "Гопак", "Hopak", _D.format(d="an energetic folk hopak — high squat kicks, leaps with legs "
        "spread, spins") + "WARDROBE: white linen shirts with red-and-black cross-stitch embroidery, wide red trousers, "
        "red sash, red boots; flower wreaths with ribbons for women. WORLD: sunflower field or village square, warm "
        "sunlight. SOUND: fast folk band with violin, bandura-like strings and drum, rhythmic shouts."),
    "d_geo": ("🇬🇪", "Грузинський", "Georgian dance", _D.format(d="a proud mountain folk dance — men on "
        "their toes with fast stamps and leaps, women gliding smoothly with graceful arms") + "WARDROBE: long dark "
        "fitted coats with cartridge pockets, soft leather boots, long flowing dresses with veils. WORLD: mountain "
        "fortress, green valley, old balconied town. SOUND: fast drums and accordion-like panduri folk music."),
    "d_flamenco": ("🇪🇸", "Фламенко", "Flamenco", _D.format(d="passionate flamenco — sharp heel stamps, proud "
        "posture, curved arms, swirling skirts, hand claps") + "WARDROBE: red ruffled polka-dot dress, hair flower, "
        "black fitted vest and trousers. WORLD: white sunlit courtyard with tiles and orange trees, or candle-lit "
        "tavern. SOUND: flamenco guitar, palmas claps and heel rhythm."),
    "d_samba": ("🇧🇷", "Самба", "Samba", _D.format(d="fast carnival samba — quick hip and foot steps, bouncing "
        "rhythm, raised arms") + "WARDROBE: bright sequined carnival costumes, feathers, colorful shirts. WORLD: "
        "carnival street parade, confetti, colorful houses, tropical sun. SOUND: loud batucada drums and whistles."),
    "d_forro": ("🇧🇷", "Форро", "Forró", _D.format(d="close partner forró — swaying side steps, spins, relaxed "
        "joyful partner dancing") + "WARDROBE: checked shirts, straw hats, flowing summer dresses. WORLD: festive "
        "countryside dance yard with paper flags and string lights at night. SOUND: accordion, triangle and zabumba drum."),
    "d_tango": ("🌹", "Танго", "Tango", _D.format(d="dramatic tango — sharp head turns, long walking steps, leg "
        "hooks and dips, intense close embrace") + "WARDROBE: black suits and fedoras, slit red dresses. WORLD: "
        "smoky night dance hall or cobblestone street under lamps. SOUND: bandoneon, violin and piano tango."),
    "d_belly": ("🌙", "Східні танці", "Belly dance", _D.format(d="graceful belly dance — hip shimmies, figure-"
        "eight hips, flowing snake arms, veil swirls") + "WARDROBE: sparkling coin-belt costumes, flowing veils, gold "
        "jewelry; men in long embroidered robes. WORLD: lantern-lit palace hall or desert tent. SOUND: darbuka drum, "
        "oud and finger cymbals."),
    "d_halay": ("🇹🇷", "Халай", "Halay", _D.format(d="a joyful line folk dance — dancers hold little fingers in a "
        "line, rhythmic stamps, shoulder shakes, the leader waves a handkerchief") + "WARDROBE: festive embroidered "
        "vests and scarves. WORLD: open-air wedding party, lights, mountains. SOUND: big davul drum and zurna pipe."),
    "d_bavaria": ("🇩🇪", "Баварський", "Bavarian dance", _D.format(d="a lively alpine folk dance — slapping "
        "thighs and shoe soles, stomping, partner spins") + "WARDROBE: leather shorts with suspenders, checked shirts, "
        "dirndl dresses with aprons. WORLD: beer-festival tent with long tables or alpine meadow. SOUND: brass oompah "
        "band and accordion."),
    "d_round": ("🪆", "Хоровод", "Round dance", _D.format(d="a calm folk round dance — dancers hold hands and move in "
        "a slow circle, smooth gliding steps, gentle bows") + "WARDROBE: long embroidered sarafan dresses, ribbons, "
        "flower wreaths, embroidered belted shirts. WORLD: birch grove or riverside meadow at sunset. SOUND: soft folk "
        "choir with balalaika-like strings."),
    "d_hiphop": ("🕺", "Хіп-хоп", "Hip-hop", _D.format(d="street hip-hop choreography — grooves, hits on the beat, "
        "footwork, synchronized crew moves") + "WARDROBE: oversized streetwear, sneakers, caps. WORLD: city basketball "
        "court or graffiti underpass at night. SOUND: hard hip-hop beat."),
    "d_break": ("🤸", "Брейк-данс", "Breakdance", _D.format(d="breakdance — toprock, fast footwork, power moves "
        "and freezes on the beat") + "WARDROBE: tracksuits, beanies, sneakers. WORLD: cardboard on a street, crowd "
        "circle, boombox. SOUND: old-school breakbeat with scratches."),
    "d_kpop": ("💜", "K-pop", "K-pop", _D.format(d="a sharp synchronized K-pop idol choreography — precise "
        "formations, hand gestures, point moves on the beat") + "WARDROBE: matching stylish stage outfits, bright hair "
        "colors. WORLD: glossy music-video stage with LED walls. SOUND: polished upbeat K-pop production."),
    "d_salsa": ("💃", "Сальса", "Salsa", _D.format(d="hot salsa and bachata partner dancing — quick steps, "
        "spins, hip sway, close embrace") + "WARDROBE: satin shirts, fringed dresses. WORLD: tropical night club with "
        "warm lights. SOUND: salsa band with congas, piano and brass."),
    "d_disco": ("🪩", "Диско 70-х", "70s disco", _D.format(d="1970s disco — finger pointing up and down, hip "
        "swings, spins, line-dance moves") + "WARDROBE: flared trousers, glittery shirts with big collars, afro hair. "
        "WORLD: lit-up dance floor and mirror ball. SOUND: disco strings, funky bass, four-on-the-floor."),
    "d_waltz": ("🎻", "Вальс", "Waltz", _D.format(d="an elegant ballroom waltz — couples turning in smooth "
        "rise-and-fall circles") + "WARDROBE: ball gowns, tailcoats, white gloves. WORLD: palace ballroom with crystal "
        "chandeliers and candlelight. SOUND: romantic orchestral waltz in three-four time."),
}

# ═══════════════════════════════════════════════════════════════
# КРАЇНИ — окреме вікно (кнопка «🌍 Країни»): дух країни — одяг, місця, кольори.
# Рухи не змінюються. Людей не описуємо за національністю — лише одяг і місця.
# ═══════════════════════════════════════════════════════════════
WORLD_STYLES = {
    "c_ua": ("🇺🇦", "Україна", "Ukraine",
        "COLOR & LIGHT: warm golden summer light, deep blue sky over yellow fields. MEDIUM: rich cinematic film. WORLD "
        "DETAILS: endless sunflower and wheat fields, white clay cottages with thatched roofs, bright folk floral "
        "murals, cherry orchards, a wide river with green hills. WARDROBE: white linen shirts and dresses with red-and-"
        "black cross-stitch embroidery, flower wreaths with long ribbons. EMOTION: warm, proud, soulful. SOUND: "
        "bandura-like strings and folk choir."),
    "c_ge": ("🇬🇪", "Грузія", "Georgia",
        "COLOR & LIGHT: crisp mountain sunlight, green valleys, warm sunset over old roofs. MEDIUM: rich cinematic film. "
        "WORLD DETAILS: snowy Caucasus peaks, ancient stone towers and monasteries, an old town with carved wooden "
        "balconies and sulfur-bath domes, vineyards, a long feast table with clay wine jugs. WARDROBE: long dark fitted "
        "coats with cartridge pockets, flowing long dresses with veils. EMOTION: proud, hospitable. SOUND: polyphonic "
        "male choir and panduri strings."),
    "c_es": ("🇪🇸", "Іспанія", "Spain",
        "COLOR & LIGHT: blazing southern sun, white walls, deep blue shadows, orange sunsets. MEDIUM: warm cinematic "
        "film. WORLD DETAILS: whitewashed narrow streets with flower pots, Moorish tiled courtyards, orange trees, "
        "fountains, a seaside promenade. WARDROBE: red ruffled dresses, fans, linen shirts, wide-brim hats. EMOTION: "
        "passionate, sunny. SOUND: Spanish guitar and hand claps."),
    "c_br": ("🇧🇷", "Бразилія", "Brazil",
        "COLOR & LIGHT: tropical vivid colors, strong sun, turquoise sea. MEDIUM: bright cinematic film. WORLD DETAILS: "
        "carnival streets with confetti and feathers, colorful hillside houses, palm-lined beach with mountains in the "
        "sea, beach football. WARDROBE: bright carnival costumes, beachwear, colorful shirts. EMOTION: joyful, "
        "explosive energy. SOUND: samba drums and whistles."),
    "c_de": ("🇩🇪", "Німеччина", "Germany",
        "COLOR & LIGHT: fresh clear daylight, green and white tones, warm tent lights in the evening. MEDIUM: crisp "
        "cinematic film. WORLD DETAILS: half-timbered houses, fairy-tale castle on a hill, alpine meadows, a festive "
        "beer tent with long wooden tables and big mugs, pretzels. WARDROBE: leather shorts with suspenders, checked "
        "shirts, dirndl dresses. EMOTION: cheerful, cozy. SOUND: brass band and accordion."),
    "c_ar": ("🌙", "1001 ніч", "Arabian tale",
        "COLOR & LIGHT: warm gold and turquoise, lantern glow, desert sunset. MEDIUM: rich storybook cinematic look. "
        "WORLD DETAILS: palace arches with mosaics, glowing brass lanterns, bustling spice bazaar, flying carpet in the "
        "sky, desert dunes with camels, starry night. WARDROBE: flowing silk robes, embroidered vests, sashes, veils, "
        "gold jewelry. EMOTION: magical, adventurous. SOUND: oud, darbuka and strings."),
    "c_tr": ("🇹🇷", "Туреччина", "Turkey",
        "COLOR & LIGHT: soft golden light over water, turquoise and ruby accents. MEDIUM: rich cinematic film. WORLD "
        "DETAILS: a grand skyline of domes over a wide strait, ferries and seagulls, a grand bazaar with mosaic lamps, "
        "patterned carpets, tea in tulip glasses, hot-air balloons over rock valleys at dawn. WARDROBE: elegant coats, "
        "embroidered vests, silk scarves. EMOTION: romantic, timeless. SOUND: saz strings, ney flute and darbuka."),
    "c_slav": ("❄️", "Зимова казка", "Slavic winter",
        "COLOR & LIGHT: blue snowy daylight, warm orange window glow, golden sunset on snow. MEDIUM: rich fairy-tale "
        "cinematic film. WORLD DETAILS: deep snow forest, carved wooden houses with painted shutters, a three-horse "
        "sleigh with bells, frozen river, birch trees, steaming samovar. WARDROBE: fur hats, long embroidered coats, "
        "patterned scarves, felt boots. EMOTION: magical, crisp, cozy. SOUND: sleigh bells, balalaika-like strings "
        "and folk choir."),
}

ANIM_STYLES = {
    "a_child": ("🎈", "Дитячий малюнок", "Kid's drawing",
        "COLOR & LIGHT: bright warm crayon colors, flat light. MEDIUM: a child's crayon and colored-pencil drawing come to "
        "life — wobbly outlines, scribbled fill with gaps, paper texture, boiling line animation. WORLD DETAILS: simple "
        "drawn houses, a sun with a smiling face, grass strokes, stick trees. CHARACTERS: naive drawn versions of the same "
        "people with the same poses and movements. EMOTION: pure innocent joy. SOUND: kazoo, xylophone and claps arrangement."),
    "a_3d": ("🧸", "3D-мульт", "3D cartoon",
        "COLOR & LIGHT: warm global illumination, soft bounce light, appealing saturated colors. LENS: animated feature "
        "camera, gentle depth of field. MEDIUM: high-end family 3D animation, soft rounded shapes, tactile fabrics, subsurface "
        "skin. WORLD DETAILS: detailed cozy stylized 3D set. CHARACTERS: 3D cartoon versions of the same people with big "
        "expressive eyes; body poses and movements unchanged. EMOTION: heartwarming. SOUND: whimsical orchestral arrangement."),
    "a_cozy": ("🍃", "Затишне аніме", "Cozy anime",
        "COLOR & LIGHT: soft natural sunlight, lush greens, big fluffy clouds, warm calm palette. MEDIUM: hand-painted anime "
        "backgrounds, gentle cel animation. WORLD DETAILS: wind moving grass and hair, countryside, flowers, small details "
        "of everyday life. CHARACTERS: soft anime faces, simple everyday clothes, same movements. EMOTION: peaceful, kind, "
        "nostalgic. SOUND: gentle piano and strings arrangement."),
    "a_2d": ("🏰", "Казковий 2D", "Fairy-tale 2D",
        "COLOR & LIGHT: storybook colors, warm magical light. MEDIUM: classic hand-drawn 2D animation, clean ink lines, "
        "painted watercolor backgrounds, fluid motion. WORLD DETAILS: fairy-tale painted backgrounds, sparkles. CHARACTERS: "
        "classic animated heroes with expressive eyes, same movements. EMOTION: magical, uplifting. SOUND: lush orchestral "
        "musical arrangement."),
    "a_sitcom": ("📺", "Ситком-мульт", "Sitcom toon",
        "COLOR & LIGHT: bright saturated flat colors, sunny sky-blue background with puffy white clouds, no gradients. "
        "MEDIUM: classic American primetime TV cartoon from the 1990s — flat 2D cel animation, clean even black outlines, "
        "simple limited animation, slightly wobbly hand-drawn lines. WORLD DETAILS: an ordinary suburban town — pastel "
        "houses, a living room with a couch facing the TV, a kitchen, a small-town street, background extras drawn in the "
        "same flat style. CHARACTERS: original cartoon versions of the same people with bright yellow skin, big round white "
        "eyes with small dot pupils, simple exaggerated shapes and hair, same movements; invent original characters, do not "
        "copy any existing show or character. EFFECTS: comedic timing — snappy reaction shots, a quick zoom on a surprised "
        "face. EMOTION: satirical everyday family comedy. SOUND: playful TV-comedy arrangement with light orchestral stings."),
    "a_retro70": ("🐻", "Мульт СРСР", "USSR cartoon",
        "COLOR & LIGHT: warm faded gouache colors. MEDIUM: 1970s hand-drawn cartoon on textured paper, soft film grain, "
        "slightly limited animation. WORLD DETAILS: simple painted backgrounds, birch trees, cozy yards. CHARACTERS: charming "
        "simple cartoon figures, same movements. EMOTION: gentle naive charm. SOUND: accordion or small orchestra arrangement."),
    "a_clay": ("🧶", "Пластилін", "Claymation",
        "COLOR & LIGHT: soft studio light, saturated plasticine colors. MEDIUM: stop-motion clay animation, fingerprints on "
        "the clay, slightly jittery frame-by-frame motion. WORLD DETAILS: handmade miniature set, felt and cardboard props. "
        "CHARACTERS: chunky clay figures with the same poses and movements. EMOTION: funny and handmade. SOUND: quirky "
        "pizzicato arrangement."),
    "a_brick": ("🧱", "Кубики", "Toy bricks",
        "COLOR & LIGHT: bright toy colors, glossy reflections. LENS: tilt-shift miniature. MEDIUM: toy-brick stop-motion. "
        "WORLD DETAILS: everything built from plastic bricks and studs. CHARACTERS: minifigures with printed faces doing the "
        "same movements. EMOTION: playful. SOUND: upbeat toy-like arrangement with plastic clicks."),
    "a_paper": ("📄", "Паперова", "Paper cut-out",
        "COLOR & LIGHT: soft directional light with real shadows between layers. MEDIUM: paper-cut animation, layered "
        "cardboard and origami, visible paper fibers and torn edges. WORLD DETAILS: pop-up book set. CHARACTERS: paper cut-out "
        "figures, same movements. EMOTION: delicate, crafty. SOUND: soft marimba and paper rustle."),
    "a_water": ("💧", "Акварель", "Watercolor",
        "COLOR & LIGHT: translucent pigment washes, white paper glowing through. MEDIUM: watercolor animation, soft bleeding "
        "edges, light pencil lines, paper grain. WORLD DETAILS: painted soft world where colors spread like wet paint. "
        "CHARACTERS: watercolor-painted figures, same movements. EMOTION: poetic and calm. SOUND: soft piano and harp."),
    "a_oil": ("🖼", "Жива картина", "Oil painting",
        "COLOR & LIGHT: rich classical colors, chiaroscuro light. MEDIUM: living oil painting, thick visible brushstrokes "
        "that move and swirl, canvas texture. WORLD DETAILS: classical painted landscape or interior. CHARACTERS: painted like "
        "museum portraits, same movements. EMOTION: majestic and timeless. SOUND: chamber strings arrangement."),
    "a_1930": ("🎷", "Мульт 1930-х", "1930s cartoon",
        "COLOR & LIGHT: black-and-white, high contrast. MEDIUM: 1930s rubber-hose cartoon, bouncy rubbery limbs, pie-cut "
        "eyes, film scratches and flicker. WORLD DETAILS: simple cartoon backgrounds that bounce to the beat. CHARACTERS: "
        "rubbery cartoon characters with white gloves doing the same movements. EMOTION: cheeky, bouncy fun. SOUND: big-band "
        "swing arrangement on an old record."),
    "a_comic": ("💥", "Комікс", "Comic book",
        "COLOR & LIGHT: limited bold palette of red, yellow, cyan and black, flat color fills without gradients. MEDIUM: "
        "printed comic-book page in motion — thick black ink outlines, Ben-Day halftone dots and cross-hatching in the "
        "shadows, printed paper texture with slight color misregistration. CAMERA & FRAMING: dramatic comic angles, white "
        "panel borders that frame the shot, one freeze-frame panel on the key moment. EFFECTS: radiating speed lines behind "
        "every movement, one short onomatopoeia word in bold comic letters on the key action (one word only, like WHOOSH). "
        "CHARACTERS: comic-book versions of the same people with strong ink shadows, same movements. EMOTION: punchy and "
        "heroic. SOUND: punchy arrangement with comic hit sounds."),
    "a_paint3d": ("🎨", "Arcane 3D", "Painterly 3D",
        "COLOR & LIGHT: moody painted light, strong color contrast. MEDIUM: painterly 3D animation — 3D forms covered with "
        "hand-painted brush textures, angular faces, graphic shadows, 2D effects drawn on top. WORLD DETAILS: painted "
        "steampunk-like city. CHARACTERS: stylized painted characters with sharp features, same movements. EMOTION: intense, "
        "cinematic. SOUND: dark modern arrangement."),
    "a_anime": ("🌸", "Аніме", "Anime",
        "COLOR & LIGHT: vivid detailed skies with light rays, sparkling highlights. MEDIUM: modern anime, crisp line art, "
        "cel shading, dynamic sakuga moments. WORLD DETAILS: detailed anime city or nature, petals in the wind. CHARACTERS: "
        "anime faces, big eyes, colorful hair, same movements. EMOTION: emotional and dramatic. SOUND: J-pop or anime "
        "opening arrangement."),
    "a_anime90": ("📼", "Аніме 90-х", "90s anime",
        "COLOR & LIGHT: muted retro palette, glowing highlights, bold shadows. MEDIUM: 1990s hand-painted cel anime, film "
        "grain, slight chromatic blur. WORLD DETAILS: retro anime city at dusk, power lines. CHARACTERS: 90s anime designs, "
        "same movements. EMOTION: nostalgic, cool. SOUND: city-pop arrangement."),
    "a_mix": ("🕷", "Комікс-мікс", "Comic mix",
        "COLOR & LIGHT: bold pop colors, neon accents. MEDIUM: mixed comic and 3D animation, stepped frame rate, halftone "
        "shading on 3D forms, offset color print effect, graphic motion lines. WORLD DETAILS: comic-like city. CHARACTERS: "
        "3D figures with comic shading, same movements. EMOTION: energetic and fresh. SOUND: hip-hop arrangement."),
    "a_pixel": ("👾", "Піксель-арт", "Pixel art",
        "COLOR & LIGHT: limited retro game palette. MEDIUM: pixel-art animation, crisp visible pixels, sprite-like motion. "
        "WORLD DETAILS: side-view or top-down pixel game level. CHARACTERS: pixel sprites doing the same movements. EMOTION: "
        "retro gaming fun. SOUND: 8-bit chiptune arrangement."),
    "a_lowpoly": ("📐", "Low Poly", "Low poly",
        "COLOR & LIGHT: simple bold colors, clean directional light. MEDIUM: low-poly 3D with flat-shaded geometric facets. "
        "WORLD DETAILS: low-poly landscape. CHARACTERS: faceted geometric figures, same movements. EMOTION: calm and stylish. "
        "SOUND: minimal electronic arrangement."),
    "a_manga": ("🖋", "Манга Ч/Б", "B&W manga",
        "COLOR & LIGHT: pure black-and-white, high contrast. MEDIUM: manga page in motion — pen lines, screentone shading, "
        "ink splashes, speed lines. WORLD DETAILS: inked backgrounds. CHARACTERS: manga designs, same movements. EMOTION: "
        "intense and dramatic. SOUND: tense rock arrangement."),
}

ORIG_STYLE = ("🎯", "Оригінал", "Original",
    "Use the same visual look as the source video, described concretely in plain visual words (camera type such as phone "
    "or cinema camera, light, colors, textures, realism level). Never write the words 'original' or 'source' in the prompt.")

FILM_GENRES = {
    "romance": ("🌹", "Романтика", "Romance",
        "WORLD: a romantic version of the location. LIGHT & WEATHER: warm golden-hour light, soft haze, glowing bokeh. "
        "BACKGROUND LIFE: flower petals drifting, fairy lights, candles. MOOD: tender and intimate. MUSIC FEEL: soft romantic strings."),
    "comedy": ("😂", "Комедія", "Comedy",
        "WORLD: bright cheerful version of the location. LIGHT & WEATHER: sunny high-key light, clear sky. BACKGROUND LIFE: "
        "playful colorful props, a confused pigeon or passer-by reacting far behind. MOOD: light and funny. MUSIC FEEL: quirky upbeat."),
    "adventure": ("🗺", "Пригоди", "Adventure",
        "WORLD: wild scenic location — jungle, cliffs or ancient ruins. LIGHT & WEATHER: bright sun through mist. BACKGROUND "
        "LIFE: birds flying, waterfalls, old maps and relics. WARDROBE HINTS: explorer outfits, backpacks. MOOD: discovery. "
        "MUSIC FEEL: uplifting orchestra."),
    "western": ("🤠", "Вестерн", "Western",
        "WORLD: dusty frontier town or red desert canyon. LIGHT & WEATHER: hard sun, heat haze, warm sepia tint. BACKGROUND "
        "LIFE: tumbleweed, saloon doors, horses. WARDROBE HINTS: cowboy hats, boots, leather vests. MOOD: lonely and tough. "
        "MUSIC FEEL: twangy guitar and whistle."),
    "hero": ("🦸", "Супергерої", "Superheroes",
        "WORLD: city skyline at sunset. LIGHT & WEATHER: heroic backlight, dramatic clouds. BACKGROUND LIFE: a glowing "
        "energy aura around the hero, flying debris far away. WARDROBE HINTS: superhero suits and capes. MOOD: powerful. "
        "MUSIC FEEL: epic heroic theme."),
    "fantasy": ("🐉", "Фентезі", "Fantasy",
        "WORLD: enchanted forest or castle. LIGHT & WEATHER: magical glowing particles, god rays. BACKGROUND LIFE: a dragon "
        "or mythical creature far in the sky, floating lanterns. WARDROBE HINTS: fantasy costumes. MOOD: wonder. MUSIC FEEL: "
        "mystical choir."),
    "desert": ("🏜", "Пустеля", "Desert planet",
        "WORLD: epic desert planet — giant dunes, rock cliffs, brutalist stone structures. LIGHT & WEATHER: bleached ochre "
        "light, two suns, wind-blown sand. BACKGROUND LIFE: distant ornithopter-like aircraft, sand worms' trails. WARDROBE "
        "HINTS: layered sand-colored robes, scarves, desert suits. MOOD: vast and solemn. MUSIC FEEL: deep throat-singing drones."),
    "timetravel": ("⏳", "Машина часу", "Time travel",
        "WORLD: mixed-era details in one place. LIGHT & WEATHER: swirling light streaks. BACKGROUND LIFE: a shimmering time "
        "portal and floating clock symbols. MOOD: mysterious excitement. MUSIC FEEL: ticking clocks and synth pulse."),
    "action": ("⚡", "Екшн", "Action",
        "WORLD: gritty urban location. LIGHT & WEATHER: high contrast, orange explosions glowing far behind. BACKGROUND LIFE: "
        "sparks, smoke, a helicopter far away. WARDROBE HINTS: tactical outfits. MOOD: intense. MUSIC FEEL: driving percussion."),
    "detective": ("🕵️", "Детектив", "Detective",
        "WORLD: rainy streets or an office with evidence boards. LIGHT & WEATHER: low-key moody light, rain. BACKGROUND LIFE: "
        "red strings on a corkboard, a desk lamp. WARDROBE HINTS: trench coats, hats. MOOD: suspense. MUSIC FEEL: jazzy suspense."),
    "crime": ("🔫", "Кримінал", "Crime",
        "WORLD: night city, parking lots, back streets. LIGHT & WEATHER: hard sodium street light. BACKGROUND LIFE: black "
        "cars, police lights far away. WARDROBE HINTS: dark suits, sunglasses. MOOD: cold and dangerous. MUSIC FEEL: dark bass."),
    "mystic": ("🌌", "Містика", "Mystic",
        "WORLD: misty place at night. LIGHT & WEATHER: moonlight, drifting fog. BACKGROUND LIFE: strange glowing symbols, "
        "floating lights. MOOD: eerie calm. MUSIC FEEL: ambient mysterious drones."),
    "darkfantasy": ("⚔️", "Темне фентезі", "Dark fantasy",
        "WORLD: stone castles, muddy villages or dark forests. LIGHT & WEATHER: torchlight, cold mist, desaturated earthy "
        "palette. BACKGROUND LIFE: crows, banners, distant fires. WARDROBE HINTS: leather and steel armor, cloaks. MOOD: grim "
        "and epic. MUSIC FEEL: dark choir and drums."),
    "thriller": ("🔪", "Трилер", "Thriller",
        "WORLD: empty unsettling surroundings. LIGHT & WEATHER: cold sickly light, deep shadows. BACKGROUND LIFE: a figure "
        "barely visible far behind, a flickering lamp. MOOD: tension. MUSIC FEEL: pulsing low tones."),
    "aliens": ("🛸", "Прибульці", "Aliens",
        "WORLD: the location at night. LIGHT & WEATHER: otherworldly green-violet glow. BACKGROUND LIFE: a UFO hovering in "
        "the sky, strange beams of light. MOOD: awe and unease. MUSIC FEEL: eerie synth."),
    "robots": ("🤖", "Роботи і ШІ", "Robots & AI",
        "WORLD: high-tech surroundings. LIGHT & WEATHER: cold tech light, holographic glow. BACKGROUND LIFE: drones, "
        "holographic screens. WARDROBE HINTS: android details — visible mechanical joints, glowing eyes, metal panels on "
        "skin (same body shapes and movements). MOOD: cool, slightly uncanny. MUSIC FEEL: precise electronic beat."),
    "hardscifi": ("🧬", "Фантастика", "Hard sci-fi",
        "WORLD: high-tech lab or space-station interior. LIGHT & WEATHER: clean white and blue light. BACKGROUND LIFE: "
        "scientific instruments, robotic arms. WARDROBE HINTS: futuristic uniforms. MOOD: precise and curious. MUSIC FEEL: "
        "minimal electronic."),
    "space": ("🚀", "Космос", "Space",
        "WORLD: starship interior, space station or alien planet surface. LIGHT & WEATHER: cold blue and amber panel lights, "
        "stars and nebulae. BACKGROUND LIFE: huge starships passing, planets in the sky. WARDROBE HINTS: sleek space suits, "
        "helmets. MOOD: cosmic awe. MUSIC FEEL: spacey synth score."),
    "matrix": ("🟩", "Віртуальний світ", "Virtual world",
        "WORLD: grey city rooftops, empty corridors. LIGHT & WEATHER: green-tinted image, cold fluorescent light. BACKGROUND "
        "LIFE: cascading green code glyphs, subtle digital glitches on the surroundings (never on the characters' motion). "
        "WARDROBE HINTS: long black leather coats, small dark sunglasses. MOOD: cold and cool. MUSIC FEEL: industrial electronic."),
    "cyber": ("🌆", "Кіберпанк", "Cyberpunk",
        "WORLD: crowded neon megacity street. LIGHT & WEATHER: rain, dense neon signs, purple-teal light, steam. BACKGROUND "
        "LIFE: holograms, flying cars, drones. WARDROBE HINTS: techwear, glowing implants, LED visors. MOOD: gritty future. "
        "MUSIC FEEL: dark synth."),
    "postapoc": ("☢️", "Апокаліпсис", "Apocalypse",
        "WORLD: ruins, rusted wrecks. LIGHT & WEATHER: harsh sun through dust haze, desaturated rust palette, sandstorm. "
        "BACKGROUND LIFE: smoke columns, broken billboards. WARDROBE HINTS: makeshift armor, gas masks, goggles, dirt. MOOD: "
        "survival. MUSIC FEEL: distorted low drones."),
    "zombie": ("🧟", "Зомбі", "Zombies",
        "WORLD: abandoned surroundings. LIGHT & WEATHER: grim desaturated light, ash in the air. BACKGROUND LIFE: shadowy "
        "infected figures far away, not interacting. MOOD: dread. MUSIC FEEL: tense strings."),
    "horror": ("💀", "Жахи", "Horror",
        "WORLD: dark abandoned place. LIGHT & WEATHER: flickering light, fog, cold desaturated colors. BACKGROUND LIFE: creepy "
        "shadows moving far behind. MOOD: dread. MUSIC FEEL: dread-filled ambient with sudden low hits."),
    "history": ("🏰", "Історичне", "Historical",
        "WORLD: a grand historical setting — stone castle courtyard, torch-lit great hall or a cobbled old-town square, "
        "banners and carved wood everywhere. LIGHT & WEATHER: warm torch and candle light, shafts of daylight through tall "
        "windows, dust in the air. BACKGROUND LIFE: townsfolk, horses, market stalls and guards far behind. WARDROBE HINTS: "
        "period cloaks, embroidered tunics, leather belts and boots. MOOD: epic and noble. MUSIC FEEL: sweeping orchestral "
        "score with choir and drums."),
}

ANIM_GENRES = {
    "friends": ("💞", "Дружба", "Friendship",
        "WORLD: cozy friendly place. LIGHT: soft warm light. BACKGROUND LIFE: hearts and sparkles in the air. MOOD: happy. "
        "MUSIC FEEL: gentle happy tune."),
    "fairy": ("🧚", "Казка", "Fairy tale",
        "WORLD: grand castle courtyard or enchanted forest. LIGHT: glowing magical light, sparkles. BACKGROUND LIFE: fireflies, "
        "birds flying over the towers. WARDROBE HINTS: elegant royal fairy-tale costumes. MOOD: magical. MUSIC FEEL: sweeping "
        "orchestral strings and harp."),
    "comedy": ("😂", "Комедія", "Comedy",
        "WORLD: bright cartoon place. LIGHT: saturated colors. BACKGROUND LIFE: funny props, a cartoon animal reacting. "
        "MOOD: silly fun. MUSIC FEEL: bouncy playful."),
    "animals": ("🐾", "Про тварин", "Animals",
        "CHARACTERS are drawn as cute expressive animals with the same body poses and movements. WORLD: nature. MOOD: "
        "sweet. MUSIC FEEL: light woodwinds."),
    "adventure": ("🗺", "Пригоди", "Adventure",
        "WORLD: colorful exotic places. BACKGROUND LIFE: treasure maps, parrots, waterfalls. WARDROBE HINTS: explorer outfits. "
        "MOOD: curious. MUSIC FEEL: adventurous orchestra."),
    "hero": ("🦸", "Супергерої", "Superheroes",
        "WARDROBE HINTS: capes and hero suits with a glowing aura. WORLD: city skyline. MOOD: brave. MUSIC FEEL: heroic theme."),
    "fantasy": ("🐉", "Фентезі", "Fantasy",
        "WORLD: magical land. BACKGROUND LIFE: magic particles, friendly dragons far away. WARDROBE HINTS: fantasy costumes. "
        "MOOD: wonder. MUSIC FEEL: mystical."),
    "timetravel": ("⏳", "Машина часу", "Time travel",
        "BACKGROUND LIFE: glowing portal and clock symbols, dinosaurs or a future city far behind. MOOD: exciting. MUSIC "
        "FEEL: ticking synth."),
    "detective": ("🕵️", "Детектив", "Detective",
        "BACKGROUND LIFE: magnifying glasses, clue boards, footprints. LIGHT: soft moody light. MOOD: kid-friendly mystery. "
        "MUSIC FEEL: sneaky pizzicato."),
    "aliens": ("🛸", "Прибульці", "Aliens",
        "BACKGROUND LIFE: a cute UFO in the sky. WORLD: colorful alien planet. MOOD: curious. MUSIC FEEL: bubbly synth."),
    "robots": ("🤖", "Роботи", "Robots",
        "CHARACTERS look like friendly robots with the same movements. BACKGROUND LIFE: gadgets and screens. MOOD: playful "
        "tech. MUSIC FEEL: bleepy electronic."),
    "space": ("🚀", "Космос", "Space",
        "WORLD: outer space and planets. BACKGROUND LIFE: stars, rockets, comets. WARDROBE HINTS: astronaut suits. MOOD: "
        "wonder. MUSIC FEEL: dreamy space synth."),
    "cyber": ("🌆", "Кіберпанк", "Cyberpunk",
        "WORLD: neon city. BACKGROUND LIFE: holograms, drones. WARDROBE HINTS: glowing techwear. MOOD: cool future. MUSIC "
        "FEEL: synth beat."),
    "spooky": ("👻", "Страшилка", "Spooky",
        "WORLD: moonlit night. BACKGROUND LIFE: cute ghosts floating, pumpkins, bats. LIGHT: purple night colors. MOOD: "
        "kid-friendly spooky. MUSIC FEEL: playful spooky organ."),
}

ORIG_GENRE = ("🎯", "Оригінал", "Original", "Keep the same mood and atmosphere as the source video.")

SOUND_MODES = {
    "orig": ("🎯", "Оригінал", "Original"),
    "music": ("🎵", "Музика", "Music"),
    "voice": ("🗣", "Голос", "Voice"),
    "music_voice": ("🎤", "Музика+голос", "Music + voice"),
    "none": ("🔉", "Тільки шуми", "Effects only"),
}

MUSIC_GENRES = {
    "m_orig": ("🎯", "Близько до оригіналу", "Close to the original", "The same music as in the source video: the same melody, tempo, rhythm and beat accents, described concretely (genre, instruments, tempo, mood), arranged to fit the visual style."),
    "m_epic": ("🎬", "Епік-оркестр", "Epic score", "Epic orchestral film score: deep brass, soaring strings, big drums, building tension."),
    "m_lofi": ("☕", "Lo-Fi", "Lo-Fi", "Warm lo-fi hip-hop: mellow keys, vinyl crackle, soft bass, relaxed 75 BPM."),
    "m_synth": ("🛼", "Синтвейв", "Synthwave", "1980s synthwave: analog synth arpeggios, gated snare, driving bass, night-drive vibe."),
    "m_phonk": ("🕶", "Фонк", "Phonk", "Aggressive drift phonk: distorted cowbell melody, heavy 808 bass, punchy drums."),
    "m_space": ("🪐", "Космо-синт", "Space synth", "Spacey sci-fi synth score: shimmering arpeggios, deep pads, slow pulse, cosmic wonder."),
    "m_cyber": ("⚡", "Індастріал", "Industrial", "Industrial cyberpunk beat: distorted bass, metallic percussion, glitchy textures."),
    "m_piano": ("🎹", "Фортепіано", "Piano", "Emotional solo piano, gentle melancholic melody."),
    "m_jazz": ("🎷", "Нуар-джаз", "Noir jazz", "Late-night noir jazz: muted trumpet, brushed drums, upright bass."),
    "m_rock": ("🎸", "Інді-рок", "Indie rock", "Energetic indie rock: jangly guitars, live drums, warm bass."),
    "m_folk": ("🪕", "Акустика", "Acoustic", "Warm acoustic folk: fingerpicked guitar, soft percussion."),
    "m_house": ("🎧", "Дип-хаус", "Deep house", "Hypnotic deep house: warm bass groove, crisp 4/4 kick, lush chords, 122 BPM."),
    "m_trap": ("🎤", "Треп", "Trap", "Dark trap: sliding 808 bass, fast hi-hats, bell melody."),
    "m_metal": ("💥", "Метал", "Metal", "Heavy metal: downtuned distorted riffs, double-kick drums."),
    "m_ambient": ("🌌", "Ембієнт", "Ambient", "Calm ambient drone: evolving pads, warm low tones."),
    "m_funk": ("🕺", "Фанк", "Funk", "Groovy funk: slap bass, wah guitar, tight drums, upbeat."),
    "m_reggae": ("🏝", "Регі", "Reggae", "Laid-back reggae: offbeat guitar, deep bass, echo."),
    "m_strings": ("🎻", "Драма-струнні", "Drama strings", "Dramatic string quartet: emotional swells, expressive cello."),
    "m_dream": ("🌸", "Дрім-поп", "Dream pop", "Dreamy pop: shimmering guitars, washed-out reverb, airy mix."),
    "m_edm": ("🔥", "EDM", "EDM", "Festival EDM: big supersaw lead, pumping bass, build-up and drop, 128 BPM."),
    "m_disco": ("🪩", "Диско", "Disco", "Retro disco: funky bassline, lush strings, open hi-hats, dancefloor energy."),
}

TIMBRES = {
    "orig": ("🎯", "Оригінал", "Original", None),
    "m_bass": ("🎙", "Бас (Ч)", "Bass (M)", "deep low male voice, calm and resonant"),
    "m_young": ("⚡", "Баритон (Ч)", "Baritone (M)", "lively young male voice, natural and energetic"),
    "m_gruff": ("🚬", "З хрипом (Ч)", "Raspy (M)", "rough raspy male voice, gritty and tired"),
    "m_whisper": ("🤫", "Шепіт (Ч)", "Whisper (M)", "soft male whisper, close and intimate"),
    "w_velvet": ("✨", "Оксамит (Ж)", "Velvet (F)", "warm soft female voice, smooth and calm"),
    "w_bright": ("⚡", "Дзвінкий (Ж)", "Bright (F)", "bright lively female voice, expressive"),
    "w_deep": ("🥀", "Низький (Ж)", "Low (F)", "low husky female voice, slow and confident"),
    "w_whisper": ("🤫", "Шепіт (Ж)", "Whisper (F)", "soft breathy female whisper"),
}

# Мова озвучки для власної фрази (без російської)
VOICE_LANGS = {"uk": ("🇺🇦", "Українська", "Ukrainian", "Ukrainian"),
               "en": ("🇬🇧", "Англійська", "English", "English"),
               "es": ("🇪🇸", "Іспанська", "Spanish", "Spanish"),
               "pt": ("🇧🇷", "Португальська", "Portuguese", "Brazilian Portuguese"),
               "de": ("🇩🇪", "Німецька", "German", "German"),
               "ar": ("🇸🇦", "Арабська", "Arabic", "Arabic"),
               "tr": ("🇹🇷", "Турецька", "Turkish", "Turkish")}


def label(item, lang):
    """Напис на кнопці: емодзі + назва потрібною мовою."""
    if lang == "uk":
        name = item[1]
    elif lang == "en":
        name = item[2]
    else:
        from labels_i18n import LBL
        name = LBL.get(lang, {}).get(item[1], item[2])
    return f"{item[0]} {name}"


# ═══════════════════════════════════════════════════════════════
# ЩО ПОКАЗУЄМО В МЕНЮ (порядок кнопок). Решта рецептів лишається вище —
# щоб повернути стиль, достатньо дописати його ключ у список.
# ═══════════════════════════════════════════════════════════════
# Стилі кіно — 24 штуки, рівно 3 сторінки по 8 (назви зрозумілі, довгі — в кінці сторінки).
FILM_STYLE_ORDER = [
    # сторінка 1 — найпопулярніші
    "f_dune", "f_matrix", "f_inter", "f_block", "f_game", "f_pastel", "f_synth", "f_noir",
    # сторінка 2 — плівка, ретро, зйомка
    "f_bw", "f_film", "f_vhs", "f_child", "f_retrofut", "f_goth", "f_pov", "f_fashion",
    # сторінка 3 — настрій і експерименти
    "f_doc", "f_wes", "f_lofi", "f_pulse", "f_surreal", "f_psy", "f_figure", "f_absurd"]
DANCE_MUSIC = ("💃", "Музика танцю", "Dance music")
ANIM_STYLE_ORDER = ["a_3d", "a_2d", "a_cozy", "a_anime", "a_anime90", "a_manga", "a_sitcom", "a_retro70",
                    "a_1930", "a_clay", "a_brick", "a_paper", "a_comic", "a_mix", "a_water"]
FILM_GENRE_HIDE = []
# Жанри кіно — 24 штуки, рівно 3 сторінки по 8.
FILM_GENRE_ORDER = [
    # сторінка 1 — найзрозуміліші
    "romance", "comedy", "action", "adventure", "fantasy", "hero", "detective", "thriller",
    # сторінка 2 — світи
    "space", "aliens", "hardscifi", "robots", "cyber", "matrix", "timetravel", "mystic",
    # сторінка 3 — темне й особливе
    "horror", "zombie", "crime", "western", "desert", "postapoc", "darkfantasy", "history"]
ANIM_GENRE_HIDE = ["robots", "cyber"]
FILM_STYLES = {k: FILM_STYLES[k] for k in FILM_STYLE_ORDER}
FILM_STYLES_ALL = dict(FILM_STYLES)
FILM_GENRES = {k: FILM_GENRES[k] for k in FILM_GENRE_ORDER if k in FILM_GENRES}
ANIM_STYLES = {k: ANIM_STYLES[k] for k in ANIM_STYLE_ORDER}
ANIM_GENRES = {k: v for k, v in ANIM_GENRES.items() if k not in ANIM_GENRE_HIDE}

# Порядок у вікнах: довгі назви (на весь рядок) — в кінці сторінки, щоб сітка не ламалась.
DANCE_STYLES = {k: DANCE_STYLES[k] for k in ["d_hopak", "d_geo", "d_flamenco", "d_samba", "d_forro", "d_tango",
                                             "d_halay", "d_belly", "d_bavaria", "d_round", "d_hiphop", "d_break",
                                             "d_kpop", "d_salsa", "d_disco", "d_waltz"]}
