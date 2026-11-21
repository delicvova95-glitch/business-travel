"""Слой данных Business Travel: схема SQLite, подключение, сиды."""
import os
import sqlite3
import secrets
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "app.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    image TEXT DEFAULT '',
    is_popular INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER NOT NULL REFERENCES destinations(id),
    title TEXT NOT NULL,
    resort TEXT DEFAULT '',
    hotel_name TEXT DEFAULT '',
    hotel_stars INTEGER DEFAULT 0,
    date_from TEXT DEFAULT '',
    date_to TEXT DEFAULT '',
    nights INTEGER DEFAULT 7,
    meal_type TEXT DEFAULT '',
    departure_city TEXT DEFAULT 'Томск',
    vacation_type TEXT DEFAULT 'Пляжный',
    price INTEGER NOT NULL DEFAULT 0,
    currency TEXT DEFAULT 'RUB',
    persons INTEGER DEFAULT 2,
    includes TEXT DEFAULT '',
    extra_costs TEXT DEFAULT '',
    description TEXT DEFAULT '',
    payment_terms TEXT DEFAULT '',
    cancel_terms TEXT DEFAULT '',
    visa_info TEXT DEFAULT '',
    visa_info_date TEXT DEFAULT '',
    price_needs_confirmation INTEGER DEFAULT 1,
    image TEXT DEFAULT '',
    is_featured INTEGER DEFAULT 0,
    is_special INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT DEFAULT '',
    contact_pref TEXT DEFAULT 'phone',
    country TEXT DEFAULT '',
    dates TEXT DEFAULT '',
    tourists TEXT DEFAULT '',
    budget TEXT DEFAULT '',
    comment TEXT DEFAULT '',
    tour_id INTEGER REFERENCES tours(id),
    source_page TEXT DEFAULT '',
    consent_pd INTEGER NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'new',
    telegram_status TEXT DEFAULT 'pending',
    telegram_attempts INTEGER DEFAULT 0,
    idempotency_key TEXT UNIQUE,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_tours_destination ON tours(destination_id);
CREATE INDEX IF NOT EXISTS idx_tours_status ON tours(status);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
"""

DEFAULT_SETTINGS = {
    "phone": "+7 (___) ___-__-__",
    "email": "info@example.ru",
    "address": "г. Томск",
    "work_hours": "Пн–Пт, 10:00–19:00",
    "telegram": "",
    # Юридические реквизиты заполняет владелец в админке после подтверждения
    # оператора сайта. Пока пустые — на сайте показывается нейтральная формулировка.
    "legal_name": "",
    "legal_inn": "",
    "legal_ogrn": "",
    "legal_address": "",
}

DESTINATIONS = [
    ("turkey", "Турция", "Проверенные курорты Анталийского побережья, отели с системой «всё включено» и короткий перелёт.", 1),
    ("egypt", "Египет", "Красное море, коралловые рифы и отели Шарм-эль-Шейха и Хургады для спокойного отдыха.", 1),
    ("uae", "ОАЭ", "Дубай и Абу-Даби: городская инфраструктура, пляжи и высокий уровень сервиса.", 1),
    ("thailand", "Таиланд", "Пхукет и Самуи — тропические пляжи, экскурсии и мягкий климат круглый год.", 1),
    ("maldives", "Мальдивы", "Атоллы, водные виллы и уединённый отдых на белоснежных пляжах.", 1),
    ("vietnam", "Вьетнам", "Нячанг и Фукуок: доступные цены, интересная кухня и длинные пляжи.", 1),
    ("italy", "Италия", "Рим, Флоренция и побережье — насыщенные экскурсионные программы и гастрономия.", 1),
    ("russia", "Россия", "Сочи, Крым, Алтай и Байкал — отдых внутри страны без виз и дальних перелётов.", 1),
]

# (slug, title, resort, hotel, stars, nights, meal, depart, type, price, persons,
#  featured, special, priority, needs_confirm, desc)
TOURS = [
    ("turkey", "Анталья — отель у моря", "Анталья", "Mediterra Art Hotel", 4, 7, "Всё включено", "Томск", "Пляжный", 89500, 2, 1, 0, 10, 0,
     "Неделя на побережье Средиземного моря в отеле с собственным пляжем. Подойдёт для спокойного семейного отдыха."),
    ("turkey", "Кемер — семейный отдых", "Кемер", "Grand Ring Hotel", 5, 10, "Всё включено", "Новосибирск", "Пляжный", 124000, 2, 1, 1, 20, 0,
     "Десять ночей в Кемере: горы, сосны и море. Отель с аквапарком и детской анимацией."),
    ("turkey", "Белек — гольф и релакс", "Белек", "Pine Beach Resort", 5, 7, "Всё включено", "Москва", "Пляжный", 142000, 2, 0, 0, 5, 1,
     "Спокойный курорт с широкими пляжами и полями для гольфа рядом."),
    ("egypt", "Шарм-эль-Шейх — рифы Наама", "Шарм-эль-Шейх", "Naama Bay Promenade", 4, 9, "Полный пансион", "Томск", "Пляжный", 98000, 2, 1, 1, 15, 0,
     "Отель на первой линии бухты Наама-Бей. Коралловый риф доступен с понтона."),
    ("egypt", "Хургада — дайвинг и солнце", "Хургада", "Sunny Days Resort", 4, 7, "Всё включено", "Новосибирск", "Активный", 86000, 2, 0, 0, 5, 0,
     "Неделя на Красном море: пляж, сноркелинг, при желании — обучение дайвингу."),
    ("uae", "Дубай — город и пляж", "Дубай", "Rove Downtown", 3, 5, "Завтраки", "Москва", "Экскурсионный", 112000, 2, 1, 0, 12, 0,
     "Пять ночей в центре Дубая: небоскрёбы, набережные и пляж Джумейры."),
    ("uae", "Абу-Даби — спокойная роскошь", "Абу-Даби", "Corniche Hotel", 5, 7, "Завтраки и ужины", "Москва", "Пляжный", 156000, 2, 0, 1, 8, 1,
     "Неделя в столице Эмиратов: набережная Корниш, мечеть шейха Зайда, музей Лувр Абу-Даби."),
    ("thailand", "Пхукет — тропический отдых", "Пхукет", "Kata Palm Resort", 4, 11, "Завтраки", "Новосибирск", "Пляжный", 128000, 2, 1, 1, 18, 0,
     "Одиннадцать ночей на пляже Ката: тёплое море, фрукты и экскурсии по островам."),
    ("thailand", "Самуи — уединённые бухты", "Самуи", "Chaweng Garden Beach", 3, 10, "Завтраки", "Москва", "Пляжный", 119000, 2, 0, 0, 4, 1,
     "Камерный отель в саду у пляжа Чавенг. Подойдёт для отдыха вдвоём."),
    ("maldives", "Мальдивы — атолл и вилла", "Северный Мале", "Coconut Beach Villas", 4, 7, "Полупансион", "Москва", "Пляжный", 245000, 2, 1, 1, 25, 0,
     "Неделя на атолле: вилла у воды, сноркелинг на домашнем рифе, закаты над океаном."),
    ("vietnam", "Нячанг — город и море", "Нячанг", "Liberty Central", 4, 9, "Завтраки", "Новосибирск", "Пляжный", 95000, 2, 0, 0, 6, 0,
     "Девять ночей в Нячанге: длинный городской пляж, грязевые источники, острова."),
    ("vietnam", "Фукуок — тихий остров", "Фукуок", "Sai Gon Phu Quoc Resort", 4, 12, "Завтраки", "Москва", "Пляжный", 134000, 2, 0, 0, 3, 1,
     "Двенадцать ночей на острове Фукуок: белые пляжи и неспешный ритм."),
    ("italy", "Рим и Флоренция — классика", "Рим", "Hotel Artemide", 4, 6, "Завтраки", "Москва", "Экскурсионный", 168000, 2, 1, 0, 14, 0,
     "Шесть ночей: Рим, переезд во Флоренцию, прогулки по историческим центрам."),
    ("italy", "Сицилия — побережье и вулкан", "Катания", "Nettuno Palace", 4, 8, "Завтраки и ужины", "Москва", "Комбинированный", 178000, 2, 0, 0, 7, 1,
     "Восемь ночей на Сицилии: пляжи Ионического побережья и экскурсия на Этну."),
    ("russia", "Сочи — море и горы", "Сочи", "Zhemchuzhina Grand Hotel", 4, 7, "Завтраки", "Томск", "Пляжный", 78000, 2, 1, 1, 22, 0,
     "Неделя в Сочи: набережная, дендрарий, поездка в Красную Поляну."),
    ("russia", "Байкал — летнее приключение", "Листвянка", "Krestovaya Pad", 3, 5, "Завтраки", "Томск", "Активный", 62000, 2, 0, 0, 9, 0,
     "Пять ночей на Байкале: Листвянка, кругобайкальская железная дорога, Ольхон."),
    ("russia", "Алтай — горный воздух", "Ая", "Altika Resort", 3, 6, "Завтраки", "Томск", "Активный", 54000, 2, 0, 0, 2, 0,
     "Шесть ночей на Алтае: Катунь, Чемал, конные и пешие прогулки."),
    ("turkey", "Сиде — античность и пляж", "Сиде", "Side Crown Palace", 5, 8, "Всё включено", "Томск", "Комбинированный", 108000, 2, 0, 1, 11, 0,
     "Восемь ночей в Сиде: песчаный пляж и античный город в пешей доступности."),
]

INCLUDES_DEFAULT = "Перелёт, проживание, питание по выбранному типу, трансфер, медицинская страховка"
EXTRA_DEFAULT = "Личные расходы, экскурсии, топливный сбор (если применимо)"
PAYMENT_DEFAULT = "Предоплата 30% при бронировании, полная оплата — не позднее чем за 14 дней до вылета."
CANCEL_DEFAULT = "Условия отмены зависят от тарифа и сроков; точные условия сообщит менеджер до оплаты."
VISA_DEFAULT = "Информацию о визовых требованиях уточняйте у менеджера перед бронированием."


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def next_public_number(conn):
    row = conn.execute("SELECT COUNT(*) AS c FROM requests").fetchone()
    return f"BT-{(row['c'] + 1):06d}"


def seed():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) AS c FROM destinations").fetchone()["c"] > 0:
        conn.close()
        return

    for key, value in DEFAULT_SETTINGS.items():
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))

    dest_ids = {}
    for i, (slug, name, desc, popular) in enumerate(DESTINATIONS):
        cur = conn.execute(
            "INSERT INTO destinations (slug, name, description, image, is_popular, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (slug, name, desc, f"img/dest_{slug}.jpg", popular, i),
        )
        dest_ids[slug] = cur.lastrowid

    base = date.today() + timedelta(days=21)
    for i, t in enumerate(TOURS):
        (slug, title, resort, hotel, stars, nights, meal, depart, vtype, price,
         persons, featured, special, priority, needs_conf, desc) = t
        d_from = base + timedelta(days=(i * 4) % 30)
        d_to = d_from + timedelta(days=nights)
        conn.execute(
            """INSERT INTO tours (
                destination_id, title, resort, hotel_name, hotel_stars,
                date_from, date_to, nights, meal_type, departure_city, vacation_type,
                price, currency, persons, includes, extra_costs, description,
                payment_terms, cancel_terms, visa_info, visa_info_date,
                price_needs_confirmation, image, is_featured, is_special, priority, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'active')""",
            (dest_ids[slug], title, resort, hotel, stars,
             d_from.isoformat(), d_to.isoformat(), nights, meal, depart, vtype,
             price, "RUB", persons, INCLUDES_DEFAULT, EXTRA_DEFAULT, desc,
             PAYMENT_DEFAULT, CANCEL_DEFAULT, VISA_DEFAULT, date.today().isoformat(),
             needs_conf, f"img/dest_{slug}.jpg", featured, special, priority),
        )

    from werkzeug.security import generate_password_hash
    password = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(9)
    conn.execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        ("admin", generate_password_hash(password)),
    )
    conn.commit()
    conn.close()
    if "ADMIN_PASSWORD" not in os.environ:
        print("=" * 60)
        print("Создан администратор: логин 'admin'")
        print(f"Пароль (сгенерирован, показывается один раз): {password}")
        print("Задайте ADMIN_PASSWORD в переменных окружения для постоянного пароля.")
        print("=" * 60)


def migrate():
    """Идемпотентные миграции для уже существующей БД."""
    conn = get_db()
    # Новые поля заявки: организация и должность контактного лица
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(requests)").fetchall()}
    if "organization" not in cols:
        conn.execute("ALTER TABLE requests ADD COLUMN organization TEXT DEFAULT ''")
    if "position" not in cols:
        conn.execute("ALTER TABLE requests ADD COLUMN position TEXT DEFAULT ''")
    # Настройки, появившиеся после первоначального сида
    existing = {r["key"] for r in conn.execute("SELECT key FROM settings").fetchall()}
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing:
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def setup():
    init_db()
    seed()
    migrate()
