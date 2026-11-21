// Формы заявок: клиентская валидация, защита от повторной отправки, вывод ошибок.
(function () {
  "use strict";

  const PHONE_RE = /^\+?[\d\s\-()]{10,18}$/;
  const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

  function setError(form, field, message) {
    const box = form.querySelector(`.field-error[data-field="${field}"]`);
    if (box) box.textContent = message || "";
  }

  function validate(form) {
    let ok = true;
    const name = form.elements.name.value.trim();
    const phone = form.elements.phone.value.trim();
    const email = form.elements.email.value.trim();

    if (!name) { setError(form, "name", "Укажите имя."); ok = false; }
    else setError(form, "name", "");

    const digits = phone.replace(/\D/g, "");
    if (!PHONE_RE.test(phone) || digits.length < 10 || digits.length > 15) {
      setError(form, "phone", "Укажите корректный телефон, например +7 999 123-45-67.");
      ok = false;
    } else setError(form, "phone", "");

    if (email && !EMAIL_RE.test(email)) {
      setError(form, "email", "Проверьте адрес электронной почты.");
      ok = false;
    } else setError(form, "email", "");

    if (!form.elements.consent_pd.checked) {
      setError(form, "consent_pd", "Необходимо согласие на обработку персональных данных.");
      ok = false;
    } else setError(form, "consent_pd", "");

    return ok;
  }

  document.querySelectorAll(".js-request-form").forEach((form) => {
    // Ключ идемпотентности: один на загрузку формы — повторные клики не создают дублей
    form.elements.idempotency_key.value =
      (crypto.randomUUID && crypto.randomUUID()) ||
      String(Date.now()) + "-" + Math.random().toString(36).slice(2);

    const submitBtn = form.querySelector('button[type="submit"]');
    const globalError = form.querySelector(".form-error-global");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      globalError.hidden = true;

      if (!validate(form)) return;

      submitBtn.disabled = true;
      const originalText = submitBtn.textContent;
      submitBtn.textContent = "Отправляем…";

      try {
        const resp = await fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: { "X-CSRF-Token": form.elements.csrf_token.value },
        });
        const data = await resp.json().catch(() => ({}));

        if (resp.ok && data.ok) {
          window.location.href = data.redirect;
          return;
        }
        if (data.errors) {
          for (const [field, message] of Object.entries(data.errors)) {
            setError(form, field, message);
          }
          globalError.textContent = "Проверьте выделенные поля и отправьте форму ещё раз.";
        } else {
          globalError.textContent = data.error || "Не удалось отправить заявку. Попробуйте ещё раз.";
        }
        globalError.hidden = false;
        // Данные формы не очищаем — пользователь может исправить и повторить
      } catch (err) {
        globalError.textContent = "Нет соединения с сервером. Проверьте интернет и повторите отправку — введённые данные сохранены.";
        globalError.hidden = false;
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  });
})();
