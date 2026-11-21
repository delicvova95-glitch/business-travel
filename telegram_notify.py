"""Уведомления менеджеров о новых заявках через Telegram Bot API.

Настройка:
    TELEGRAM_BOT_TOKEN — токен бота из @BotFather
    TELEGRAM_CHAT_ID   — id чата/группы для уведомлений

Без этих переменных интеграция отключается gracefully:
заявки сохраняются, статус уведомления — 'disabled'.
"""
import json
import logging
import os
import time
import urllib.error
import urllib.request
from html import escape

log = logging.getLogger("telegram")

API_URL = "https://api.telegram.org/bot{token}/sendMessage"
TIMEOUT = 5          # секунд на один запрос
MAX_ATTEMPTS = 3     # всего попыток, включая первую
RETRY_DELAY = 2      # базовая задержка между попытками (растёт линейно)


def is_configured():
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def format_request_message(req, tour_title=None):
    """Формирует текст уведомления из сохранённой заявки (HTML-экранирование)."""
    lines = [
        "<b>Новая заявка Business Travel</b>",
        f"Номер: #{escape(req['public_number'])}",
        f"Имя: {escape(req['name'])}",
        f"Телефон: {escape(req['phone'])}",
    ]
    if "organization" in req.keys() and req["organization"]:
        lines.append(f"Организация: {escape(req['organization'])}")
    if "position" in req.keys() and req["position"]:
        lines.append(f"Должность: {escape(req['position'])}")
    if req["email"]:
        lines.append(f"Email: {escape(req['email'])}")
    if req["country"]:
        lines.append(f"Направление: {escape(req['country'])}")
    if req["dates"]:
        lines.append(f"Предполагаемые даты: {escape(req['dates'])}")
    if req["tourists"]:
        lines.append(f"Количество туристов: {escape(req['tourists'])}")
    lines.append(f"Бюджет: {escape(req['budget']) if req['budget'] else 'не указан'}")
    if tour_title:
        lines.append(f"Тур: {escape(tour_title)}")
    if req["comment"]:
        lines.append(f"Комментарий: {escape(req['comment'])}")
    if req["source_page"]:
        lines.append(f"Источник: {escape(req['source_page'])}")
    lines.append(f"Время поступления: {escape(req['created_at'])}")
    return "\n".join(lines)


def _send_once(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL.format(token=token),
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return bool(body.get("ok"))


def send_request_notification(req, tour_title=None):
    """Отправляет уведомление с повторами при временных сбоях.

    Возвращает 'sent' | 'failed' | 'disabled'.
    Никогда не выбрасывает исключение наружу — ошибки логируются
    без токена и лишних персональных данных.
    """
    if not is_configured():
        return "disabled"

    text = format_request_message(req, tour_title)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            if _send_once(text):
                return "sent"
            log.warning("Telegram API вернул ok=false (заявка %s, попытка %s)",
                        req["public_number"], attempt)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                json.JSONDecodeError, OSError) as exc:
            # В лог идёт только тип и код ошибки, без токена и тела запроса
            log.warning("Ошибка Telegram API (%s) для заявки %s, попытка %s",
                        type(exc).__name__, req["public_number"], attempt)
        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_DELAY * attempt)
    return "failed"
