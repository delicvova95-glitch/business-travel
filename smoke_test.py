"""Smoke-тесты: все страницы, фильтры каталога, заявки, админка."""
import os
import re
import sys

os.environ.setdefault("ADMIN_PASSWORD", "test-admin-pass")

from app import app  # noqa: E402  (создаёт БД при импорте)

client = app.test_client()
failures = []


def check(name, cond, detail=""):
    status = "OK  " if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def csrf_from(html):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else None


# --- Публичные страницы ---
for path in ["/", "/tours", "/destinations/turkey", "/tours/1", "/specials",
             "/about", "/corporate", "/contacts", "/faq",
             "/privacy", "/consent", "/terms"]:
    r = client.get(path)
    check(f"GET {path} -> {r.status_code}", r.status_code == 200)

r = client.get("/no-such-page")
check("GET /no-such-page -> 404", r.status_code == 404)
check("404 содержит текст", "не существует" in r.get_data(as_text=True))

# --- Каталог: API и фильтры ---
r = client.get("/api/tours")
data = r.get_json()
check("GET /api/tours -> 200, JSON", r.status_code == 200 and "items" in data)
total_all = data["total"]
check("Каталог не пуст", total_all > 0, f"total={total_all}")

r = client.get("/api/tours?country=turkey")
data_tr = r.get_json()
check("Фильтр country=turkey работает",
      0 < data_tr["total"] < total_all,
      f"total={data_tr['total']} из {total_all}")
check("Все результаты — Турция",
      all(i["country"] == "Турция" for i in data_tr["items"]))

r = client.get("/api/tours?price_max=80000")
data_pr = r.get_json()
check("Фильтр price_max=80000",
      0 < data_pr["total"] and all(i["price_display"] for i in data_pr["items"]))

r = client.get("/api/tours?sort=price_asc")
items = r.get_json()["items"]
check("Сортировка price_asc", len(items) > 1)

r = client.get("/api/tours?special=1")
check("Фильтр special=1", all(i["is_special"] for i in r.get_json()["items"]))

r = client.get("/api/tours?country=turkey&price_max=1")
check("Пустой результат корректен",
      r.get_json()["total"] == 0 and r.get_json()["items"] == [])

r = client.get("/api/tours?page=2")
check("Пагинация page=2", r.status_code == 200)

# --- Заявки ---
r = client.get("/contacts")
token = csrf_from(r.get_data(as_text=True))
check("CSRF-токен выдаётся", bool(token))

# Без CSRF — отказ
r = client.post("/api/requests", data={"name": "Тест", "phone": "+79991234567", "consent_pd": "1"})
check("POST без CSRF -> 400", r.status_code == 400)

# Валидная заявка
payload = {
    "csrf_token": token,
    "name": "Тест Тестов",
    "phone": "+7 999 123-45-67",
    "email": "test@example.ru",
    "contact_pref": "phone",
    "country": "Турция",
    "dates": "10–17 июня",
    "tourists": "2",
    "budget": "до 150 000 ₽",
    "comment": "Smoke-тест",
    "tour_id": "1",
    "source_page": "/tours/1",
    "consent_pd": "1",
    "idempotency_key": "smoke-key-1",
}
r = client.post("/api/requests", data=payload)
check("POST заявки -> 200", r.status_code == 200, r.get_data(as_text=True)[:200])
resp = r.get_json()
check("Номер заявки BT-......", bool(re.match(r"BT-\d{6}", resp.get("number", ""))))
check("redirect на success", "/request/success/" in resp.get("redirect", ""))

# Идемпотентность: тот же ключ — тот же номер, без дубля
r2 = client.post("/api/requests", data=payload)
check("Повтор с тем же ключом — без дубля",
      r2.get_json().get("number") == resp["number"] and r2.get_json().get("duplicate") is True)

# Невалидная заявка
bad = dict(payload, phone="abc", idempotency_key="smoke-key-2")
r = client.post("/api/requests", data=bad)
check("Невалидный телефон -> 400 с ошибкой phone",
      r.status_code == 400 and "phone" in r.get_json().get("errors", {}))

# Без согласия
bad2 = dict(payload, idempotency_key="smoke-key-3")
bad2.pop("consent_pd")
r = client.post("/api/requests", data=bad2)
check("Без согласия -> 400", r.status_code == 400 and "consent_pd" in r.get_json().get("errors", {}))

# Страница успеха
r = client.get(resp["redirect"])
check("Страница успеха -> 200 с номером",
      r.status_code == 200 and resp["number"] in r.get_data(as_text=True))

# --- Админка ---
r = client.get("/admin/")
check("GET /admin/ без входа -> редирект", r.status_code == 302)

r = client.get("/admin/login")
token_admin = csrf_from(r.get_data(as_text=True))
r = client.post("/admin/login", data={
    "csrf_token": token_admin, "username": "admin", "password": "test-admin-pass",
})
check("Вход в админку -> редирект", r.status_code == 302)

r = client.get("/admin/")
check("Дашборд -> 200", r.status_code == 200)
r = client.get("/admin/requests")
check("Список заявок -> 200, заявка видна",
      r.status_code == 200 and "Тест Тестов" in r.get_data(as_text=True))
r = client.get("/admin/tours")
check("Список туров -> 200", r.status_code == 200)
r = client.get("/admin/destinations")
check("Направления -> 200", r.status_code == 200)
r = client.get("/admin/settings")
check("Настройки -> 200", r.status_code == 200)
r = client.get("/admin/tours/1/edit")
check("Форма тура -> 200", r.status_code == 200)

# Неверный пароль
client2 = app.test_client()
r = client2.get("/admin/login")
t2 = csrf_from(r.get_data(as_text=True))
r = client2.post("/admin/login", data={"csrf_token": t2, "username": "admin", "password": "wrong"})
check("Неверный пароль -> ошибка", "Неверный логин или пароль" in r.get_data(as_text=True))

print()
if failures:
    print(f"ПРОВАЛЕНО: {len(failures)}: {failures}")
    sys.exit(1)
print("Все проверки пройдены.")
