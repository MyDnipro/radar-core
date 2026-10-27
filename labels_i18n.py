# Назви кнопок каталогу (стилі, жанри, звук, музика, голоси) іншими мовами.
# Рядок: українська | ru | es | pt | de | ar | tr
_ROWS = """
Дитинство|Детство|Infancia|Infância|Kindheit|الطفولة|Çocukluk
Стара плівка|Старая плёнка|Cine antiguo|Filme antigo|Alter Film|فيلم قديم|Eski film
VHS 90-х|VHS 90-х|VHS de los 90|VHS anos 90|90er-VHS|VHS التسعينات|90'lar VHS
Нуар 1940-х|Нуар 1940-х|Noir de los 40|Noir anos 40|40er-Noir|نوار الأربعينات|40'lar noir
Нео-нуар|Нео-нуар|Neo-noir|Neo-noir|Neo-Noir|نيو نوار|Neo-noir
Блокбастер|Блокбастер|Superproducción|Blockbuster|Blockbuster|فيلم ضخم|Gişe filmi
Відеогра|Видеоигра|Videojuego|Videogame|Videospiel|لعبة فيديو|Video oyunu
Барбі|Барби|Barbie|Barbie|Barbie|باربي|Barbie
Пастель-кіно|Пастель-кино|Cine pastel|Cinema pastel|Pastell-Kino|سينما باستيل|Pastel sinema
Готика|Готика|Gótico|Gótico|Gothic|قوطي|Gotik
Сюрреалізм|Сюрреализм|Surrealismo|Surrealismo|Surrealismus|سريالية|Sürrealizm
Психоделіка|Психоделика|Psicodelia|Psicodelia|Psychedelic|سايكيديلك|Psikedelik
3D-мульт|3D-мульт|Dibujo 3D|Desenho 3D|3D-Trickfilm|كرتون ثلاثي الأبعاد|3D çizgi film
Казковий 2D|Сказочный 2D|2D de cuento|2D de conto|Märchen-2D|رسوم حكايات ثنائية الأبعاد|Masalsı 2D
Затишне аніме|Уютное аниме|Anime acogedor|Anime aconchegante|Gemütliches Anime|أنمي دافئ|Sıcak anime
Аніме|Аниме|Anime|Anime|Anime|أنمي|Anime
Аніме 90-х|Аниме 90-х|Anime de los 90|Anime anos 90|90er-Anime|أنمي ٩٠|90'lar anime
Ситком-мульт|Ситком-мульт|Sitcom animada|Sitcom animada|Sitcom-Cartoon|سيتكوم كرتون|Sitcom çizgi
Мульт СРСР|Мульт СССР|Animación URSS|Desenho URSS|Sowjet-Cartoon|كرتون سوفيتي|Sovyet çizgi
Пластилін|Пластилин|Plastilina|Massinha|Knete|صلصال|Hamur
Кубики|Кубики|Bloques de juguete|Blocos de brinquedo|Spielsteine|مكعبات لعب|Oyuncak bloklar
Комікс|Комикс|Cómic|Quadrinhos|Comic|كوميكس|Çizgi roman
Комікс-мікс|Комикс-микс|Mezcla cómic|Mistura de quadrinhos|Comic-Mix|مزيج كوميكس|Çizgi roman karışımı
Піксель-арт|Пиксель-арт|Pixel art|Pixel art|Pixel-Art|بكسل آرت|Piksel sanat
Романтика|Романтика|Romance|Romance|Romantik|رومانسي|Romantik
Комедія|Комедия|Comedia|Comédia|Komödie|كوميدي|Komedi
Пригоди|Приключения|Aventura|Aventura|Abenteuer|مغامرة|Macera
Вестерн|Вестерн|Western|Faroeste|Western|ويسترن|Western
Супергерої|Супергерои|Superhéroes|Super-heróis|Superhelden|أبطال خارقون|Süper kahraman
Фентезі|Фэнтези|Fantasía|Fantasia|Fantasy|فانتازيا|Fantastik
Пустеля|Пустыня|Desierto|Deserto|Wüste|صحراء|Çöl
Машина часу|Сквозь время|Viaje temporal|Viagem no tempo|Zeitreise|آلة الزمن|Zaman yolculuğu
Екшн|Экшн|Acción|Ação|Action|أكشن|Aksiyon
Детектив|Детектив|Detective|Detetive|Krimi|تحقيق|Dedektif
Кримінал|Криминал|Crimen|Crime|Gangster|جريمة|Suç
Містика|Мистика|Misterio|Mistério|Mystery|غموض|Gizem
Темне фентезі|Дарк-фэнтези|Fantasía oscura|Fantasia negra|Dark Fantasy|فانتازيا مظلمة|Kara fantastik
Трилер|Триллер|Thriller|Suspense|Thriller|إثارة|Gerilim
Прибульці|Пришельцы|Alienígenas|Alienígenas|Aliens|كائنات فضائية|Uzaylılar
Роботи і ШІ|Роботы и ИИ|Robots e IA|Robôs e IA|Roboter & KI|روبوتات وذكاء|Robotlar ve YZ
Фантастика|Фантастика|Ciencia ficción|Ficção sci-fi|Sci-Fi|خيال علمي|Bilim kurgu
Космос|Космос|Espacio|Espaço|Weltraum|الفضاء|Uzay
Віртуальний світ|Виртуальный мир|Mundo virtual|Mundo virtual|Virtuelle Welt|عالم افتراضي|Sanal dünya
Кіберпанк|Киберпанк|Cyberpunk|Cyberpunk|Cyberpunk|سايبربانك|Cyberpunk
Апокаліпсис|Апокалипсис|Apocalipsis|Apocalipse|Apokalypse|نهاية العالم|Kıyamet
Зомбі|Зомби|Zombis|Zumbis|Zombies|زومبي|Zombi
Жахи|Ужасы|Terror|Terror|Horror|رعب|Korku
Дружба|Дружба|Amistad|Amizade|Freundschaft|صداقة|Dostluk
Казка|Сказка|Cuento de hadas|Conto de fadas|Märchen|حكاية خيالية|Masal
Про тварин|Про животных|Animales|Animais|Tiere|حيوانات|Hayvanlar
Страшилка|Страшилка|De miedo|Assustador|Gruselig|مخيف|Ürkütücü
Оригінал|Оригинал|Original|Original|Original|الأصل|Orijinal
Музика|Музыка|Música|Música|Musik|موسيقى|Müzik
Голос|Голос|Voz|Voz|Stimme|صوت|Ses
Музика+голос|Музыка+голос|Música + voz|Música + voz|Musik + Stimme|موسيقى + صوت|Müzik + ses
Тільки шуми|Только шумы|Solo efectos|Só efeitos|Nur Effekte|مؤثرات فقط|Sadece efekt
Епік-оркестр|Эпик-оркестр|Orquesta épica|Orquestra épica|Epik-Orchester|أوركسترا ملحمية|Epik orkestra
Lo-Fi|Lo-Fi|Lo-Fi|Lo-Fi|Lo-Fi|Lo-Fi|Lo-Fi
Синтвейв|Синтвейв|Synthwave|Synthwave|Synthwave|سينثويف|Synthwave
Фонк|Фонк|Phonk|Phonk|Phonk|فونك|Phonk
Космо-синт|Космо-синт|Space synth|Space synth|Space-Synth|سينث فضائي|Uzay synth
Індастріал|Индастриал|Industrial|Industrial|Industrial|إندستريال|Endüstriyel
Фортепіано|Фортепиано|Piano|Piano|Klavier|بيانو|Piyano
Нуар-джаз|Нуар-джаз|Jazz noir|Jazz noir|Noir-Jazz|جاز نوار|Noir caz
Інді-рок|Инди-рок|Indie rock|Indie rock|Indie-Rock|إندي روك|Indie rock
Акустика|Акустика|Acústico|Acústico|Akustik|أكوستيك|Akustik
Дип-хаус|Дип-хаус|Deep house|Deep house|Deep House|ديب هاوس|Deep house
Треп|Трэп|Trap|Trap|Trap|تراب|Trap
Метал|Метал|Metal|Metal|Metal|ميتال|Metal
Ембієнт|Эмбиент|Ambient|Ambient|Ambient|أمبينت|Ambient
Фанк|Фанк|Funk|Funk|Funk|فانك|Funk
Регі|Регги|Reggae|Reggae|Reggae|ريغي|Reggae
Драма-струнні|Драма-скрипки|Cuerdas drama|Cordas drama|Drama-Streicher|وتريات درامية|Dram yaylılar
Дрім-поп|Дрим-поп|Dream pop|Dream pop|Dream-Pop|دريم بوب|Dream pop
EDM|EDM|EDM|EDM|EDM|EDM|EDM
Диско|Диско|Disco|Disco|Disco|ديسكو|Disko
Бас (Ч)|Бас (М)|Bajo (H)|Grave (H)|Bass (M)|جهير (ر)|Bas (E)
Баритон (Ч)|Баритон (М)|Barítono (H)|Barítono (H)|Bariton (M)|باريتون (ر)|Bariton (E)
З хрипом (Ч)|Хриплый (М)|Rasposa (H)|Rouca (H)|Rau (M)|أجش (ر)|Boğuk (E)
Шепіт (Ч)|Шёпот (М)|Susurro (H)|Sussurro (H)|Flüstern (M)|همس (ر)|Fısıltı (E)
Оксамит (Ж)|Бархат (Ж)|Suave (M)|Aveludada (M)|Samtig (F)|مخملي (أ)|Kadife (K)
Дзвінкий (Ж)|Звонкий (Ж)|Brillante (M)|Brilhante (M)|Hell (F)|رنّان (أ)|Parlak (K)
Низький (Ж)|Низкий (Ж)|Grave (M)|Grave (M)|Tief (F)|منخفض (أ)|Kalın (K)
Шепіт (Ж)|Шёпот (Ж)|Susurro (M)|Sussurro (M)|Flüstern (F)|همس (أ)|Fısıltı (K)
Українська|Украинский|Ucraniano|Ucraniano|Ukrainisch|الأوكرانية|Ukraynaca
Англійська|Английский|Inglés|Inglês|Englisch|الإنجليزية|İngilizce
Іспанська|Испанский|Español|Espanhol|Spanisch|الإسبانية|İspanyolca
Португальська|Португальский|Portugués|Português|Portugiesisch|البرتغالية|Portekizce
Німецька|Немецкий|Alemán|Alemão|Deutsch|الألمانية|Almanca
Арабська|Арабский|Árabe|Árabe|Arabisch|العربية|Arapça
Турецька|Турецкий|Turco|Turco|Türkisch|التركية|Türkçe
Синтвейв 80-х|Синтвейв 80-х|Synthwave 80s|Synthwave 80|80er-Synthwave|سينثويف ٨٠|Synthwave 80
Ретрофутуризм|Ретрофутуризм|Retrofuturismo|Retrofuturismo|Retrofuturismus|مستقبل رجعي|Retrofütürizm
Музичний кліп|Клип|Videoclip|Videoclipe|Musikvideo|فيديو كليب|Müzik klibi
Модний подіум|Модный подиум|Pasarela|Passarela|Laufsteg|عرض أزياء|Moda podyumu
Кінореалізм|Кинореализм|Cine realista|Cinema real|Kino-Realismus|واقعية سينمائية|Gerçekçi sinema
POV GoPro|POV GoPro|POV GoPro|POV GoPro|POV GoPro|POV GoPro|POV GoPro
Репортаж|Репортаж|Documental|Documentário|Reportage|ريبورتاج|Belgesel
Мініатюра|Миниатюра|Miniatura|Miniatura|Miniaturwelt|عالم مصغّر|Minyatür
Фігурка|Фигурка|Figura|Colecionável|Sammelfigur|مجسّم|Figür
Lo-fi затишок|Lo-fi уют|Lo-fi acogedor|Lo-fi aconchego|Lo-fi gemütlich|لو-فاي دافئ|Lo-fi huzur
Пульс музики|Пульс музыки|Pulso musical|Pulso da música|Musik-Puls|نبض الموسيقى|Müzik nabzı
Абсурд-мем|Абсурд-мем|Meme absurdo|Meme absurdo|Absurd-Meme|ميم عبثي|Absürt mim
Танці|Танцы|Bailes|Danças|Tänze|رقصات|Danslar
Країни|Страны|Países|Países|Länder|بلدان|Ülkeler
Гопак|Гопак|Hopak|Hopak|Hopak|هوباك|Hopak
Грузинський|Грузинский|Baile georgiano|Dança georgiana|Georgisch|رقصة جورجية|Gürcü dansı
Фламенко|Фламенко|Flamenco|Flamenco|Flamenco|فلامنكو|Flamenko
Самба|Самба|Samba|Samba|Samba|سامبا|Samba
Форро|Форро|Forró|Forró|Forró|فورو|Forró
Танго|Танго|Tango|Tango|Tango|تانغو|Tango
Східні танці|Танец живота|Danza oriental|Dança do ventre|Bauchtanz|رقص شرقي|Oryantal dans
Халай|Халай|Halay|Halay|Halay|هالاي|Halay
Баварський|Баварский|Baile bávaro|Dança bávara|Schuhplattler|رقصة بافارية|Bavyera dansı
Хоровод|Хоровод|Corro|Ciranda|Reigen|رقصة دائرية|Halka dansı
Хіп-хоп|Хип-хоп|Hip-hop|Hip-hop|Hip-Hop|هيب هوب|Hip-hop
Брейк-данс|Брейк-данс|Breakdance|Breakdance|Breakdance|بريك دانس|Breakdans
K-pop|K-pop|K-pop|K-pop|K-Pop|كي-بوب|K-pop
Сальса|Сальса|Salsa|Salsa|Salsa|سالسا|Salsa
Диско 70-х|Диско 70-х|Disco 70s|Disco anos 70|70er-Disco|ديسكو السبعينات|70'ler disko
Вальс|Вальс|Vals|Valsa|Walzer|فالس|Vals
Україна|Украина|Ucrania|Ucrânia|Ukraine|أوكرانيا|Ukrayna
Грузія|Грузия|Georgia|Geórgia|Georgien|جورجيا|Gürcistan
Іспанія|Испания|España|Espanha|Spanien|إسبانيا|İspanya
Бразилія|Бразилия|Brasil|Brasil|Brasilien|البرازيل|Brezilya
Німеччина|Германия|Alemania|Alemanha|Deutschland|ألمانيا|Almanya
1001 ніч|1001 ночь|Cuento árabe|Conto árabe|Orient-Märchen|حكاية عربية|Arap masalı
Туреччина|Турция|Turquía|Turquia|Türkei|تركيا|Türkiye
Зимова казка|Зимняя сказка|Invierno eslavo|Inverno eslavo|Slawen-Winter|شتاء سلافي|Slav kışı
Як в оригіналі|Как в оригинале|Como el original|Como o original|Wie im Original|كما في الأصل|Orijinal gibi
Близько до оригіналу|Близко к оригиналу|Cerca del original|Perto do original|Nah am Original|قريب من الأصل|Orijinale yakın
Сучасне кіно|Кино сегодня|Cine moderno|Cinema moderno|Moderner Film|سينما حديثة|Modern sinema
Чорно-біле|Чёрно-белое|Blanco y negro|Preto e branco|Schwarz-Weiß|أبيض وأسود|Siyah-beyaz
Німе кіно|Немое кино|Cine mudo|Cinema mudo|Stummfilm|سينما صامتة|Sessiz film
Камера 90-х|Камера 90-х|Cámara 90s|Câmera anos 90|90er-Kamera|كاميرا ٩٠|90'lar kamera
Ностальгія|Ностальгия|Nostalgia|Nostalgia|Nostalgie|حنين|Nostalji
Нічне місто|Ночной город|Ciudad nocturna|Cidade à noite|Nachtstadt|مدينة ليلية|Gece şehri
Неон 80-х|Неон 80-х|Neón 80s|Neon anos 80|80er-Neon|نيون الثمانينات|80'ler neon
Рожевий світ|Розовый мир|Mundo rosa|Mundo rosa|Pinke Welt|العالم الوردي|Pembe dünya
Світ-іграшка|Мир-игрушка|Mundo juguete|Mundo-brinquedo|Spielzeugwelt|عالم الألعاب|Oyuncak dünya
Музика танцю|Музыка танца|Música del baile|Música da dança|Tanzmusik|موسيقى الرقصة|Dans müziği
Манга Ч/Б|Манга Ч/Б|Manga B/N|Mangá P&B|Manga S/W|مانغا|Manga S/B
Мульт 1930-х|Мульт 1930-х|Dibujos años 30|Desenho anos 30|30er-Cartoon|كرتون ٣٠|30'lar çizgi
Паперова|Бумажная|Papel|Papel|Papier|ورقية|Kâğıt
Arcane 3D|Arcane 3D|Arcane 3D|Arcane 3D|Arcane 3D|Arcane 3D|Arcane 3D
Low Poly|Low Poly|Low Poly|Low Poly|Low Poly|Low Poly|Low Poly
Акварель|Акварель|Acuarela|Aquarela|Aquarell|ألوان مائية|Suluboya
Жива картина|Живая картина|Cuadro vivo|Pintura viva|Ölgemälde|لوحة حية|Canlı tablo
Дитячий малюнок|Детский рисунок|Dibujo infantil|Desenho infantil|Kinderzeichnung|رسم طفل|Çocuk çizimi
Піщана планета|Песчаная планета|Planeta de arena|Planeta de areia|Sandplanet|كوكب الرمال|Kum gezegeni
Цифровий код|Цифровой код|Código digital|Código digital|Digitaler Code|الشيفرة الرقمية|Dijital kod
Далекий космос|Далёкий космос|Espacio profundo|Espaço profundo|Tiefer Weltraum|الفضاء البعيد|Derin uzay
Ретро-космос|Ретро-космос|Retrofuturo|Retrofuturo|Retro-Zukunft|فضاء ريترو|Retro uzay
Очима героя|Глазами героя|Primera persona|Primeira pessoa|Ich-Perspektive|بعيون البطل|Kahraman gözü
Затишний дім|Уютный дом|Hogar cálido|Casa cálida|Zuhause|بيت دافئ|Sıcak ev
Під ритм|Под ритм|Al ritmo|No ritmo|Im Takt|على الإيقاع|Ritme göre
Дивні меми|Странные мемы|Memes raros|Memes estranhos|Seltsame Memes|ميمز غريبة|Garip memler
Історичне|Историческое|Histórico|Histórico|Historisch|تاريخي|Tarihi
"""
_LANGS = ["ru", "es", "pt", "de", "ar", "tr"]
LBL = {l: {} for l in _LANGS}
for _line in _ROWS.strip().splitlines():
    _p = _line.split("|")
    for _i, _l in enumerate(_LANGS):
        LBL[_l][_p[0]] = _p[_i + 1]
