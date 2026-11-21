// Каталог: серверная фильтрация через fetch, URL, чипы, пагинация, состояния.
(function () {
  "use strict";

  const form = document.getElementById("filters-form");
  const grid = document.getElementById("catalog-grid");
  if (!form || !grid) return;

  const counter = document.getElementById("catalog-counter");
  const loading = document.getElementById("catalog-loading");
  const errorBox = document.getElementById("catalog-error");
  const emptyBox = document.getElementById("catalog-empty");
  const pagination = document.getElementById("catalog-pagination");
  const chipsBox = document.getElementById("active-filters");
  const sortSelect = document.getElementById("f-sort");
  const sortHidden = document.getElementById("f-sort-hidden");
  const pageInput = document.getElementById("f-page");

  const FILTER_LABELS = {
    country: "Страна", resort: "Курорт", departure_city: "Город вылета",
    date_from: "Вылет от", date_to: "Вылет до", nights_min: "Ночей от",
    nights_max: "Ночей до", price_min: "Бюджет от", price_max: "Бюджет до",
    stars: "Отель от", meal_type: "Питание", vacation_type: "Тип отдыха",
    tourists: "Туристов", special: "Спецпредложения",
  };

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function currentParams() {
    const fd = new FormData(form);
    fd.set("sort", sortSelect.value);
    fd.set("page", pageInput.value || "1");
    const params = new URLSearchParams();
    for (const [k, v] of fd.entries()) {
      if (v !== "" && v !== null) params.set(k, v);
    }
    return params;
  }

  function cardHtml(t) {
    const stars = t.hotel_stars ? "★".repeat(t.hotel_stars) : "";
    const badge = t.is_special ? '<span class="badge badge-gold">Специальное предложение</span>' : "";
    const note = t.price_needs_confirmation
      ? '<div class="price-note">Стоимость требует подтверждения менеджером</div>' : "";
    const df = (s) => s ? `${s.slice(8, 10)}.${s.slice(5, 7)}.${s.slice(0, 4)}` : "";
    return `
      <article class="tour-card">
        <a class="tour-card-img" href="${t.url}">
          <img src="${t.image}" alt="${escapeHtml(t.title)}" loading="lazy">${badge}
        </a>
        <div class="tour-card-body">
          <div class="tour-card-meta">${escapeHtml(t.country)}${t.resort ? ", " + escapeHtml(t.resort) : ""}</div>
          <h3 class="tour-card-title"><a href="${t.url}">${escapeHtml(t.title)}</a></h3>
          <div class="tour-card-hotel">${escapeHtml(t.hotel_name || "")} <span class="stars">${stars}</span></div>
          <ul class="tour-card-facts">
            <li>${df(t.date_from)} – ${df(t.date_to)}, ${t.nights} ночей</li>
            <li>${escapeHtml(t.meal_type || "")}</li>
            <li>Вылет из ${escapeHtml(t.departure_city)}</li>
          </ul>
          <div class="tour-card-footer">
            <div>
              <div class="tour-card-price">${escapeHtml(t.price_display)}</div>
              <div class="tour-card-per">за ${t.persons} чел.</div>${note}
            </div>
            <div class="tour-card-actions">
              <a class="btn btn-outline btn-sm" href="${t.url}">Подробнее</a>
              <a class="btn btn-primary btn-sm" href="${t.url}#request">Оставить заявку</a>
            </div>
          </div>
        </div>
      </article>`;
  }

  function renderChips(params) {
    chipsBox.innerHTML = "";
    for (const [key, label] of Object.entries(FILTER_LABELS)) {
      const value = params.get(key);
      if (!value) continue;
      let text = value;
      const field = form.elements[key];
      if (field && field.tagName === "SELECT" && key !== "sort") {
        const opt = field.querySelector(`option[value="${CSS.escape(value)}"]`);
        if (opt) text = opt.textContent;
      }
      if (key === "special") text = "";
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = text ? `${label}: ${text}` : label;
      chip.title = "Убрать фильтр";
      chip.addEventListener("click", () => {
        const el = form.elements[key];
        if (!el) return;
        if (el.type === "checkbox") el.checked = false; else el.value = "";
        pageInput.value = "1";
        load();
      });
      chipsBox.appendChild(chip);
    }
  }

  function renderPagination(page, pages) {
    pagination.innerHTML = "";
    if (pages <= 1) return;
    for (let p = 1; p <= pages; p++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "page-btn" + (p === page ? " active" : "");
      btn.textContent = String(p);
      btn.dataset.page = String(p);
      btn.addEventListener("click", () => {
        pageInput.value = String(p);
        load();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      pagination.appendChild(btn);
    }
  }

  let inflight = null;

  async function load() {
    const params = currentParams();
    history.replaceState(null, "", "?" + params.toString());

    if (inflight) inflight.abort();
    inflight = new AbortController();

    loading.hidden = false;
    errorBox.hidden = true;

    try {
      const resp = await fetch("/api/tours?" + params.toString(), { signal: inflight.signal });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();

      counter.textContent = "Найдено предложений: " + data.total;
      grid.innerHTML = data.items.map(cardHtml).join("");
      emptyBox.hidden = data.items.length > 0;
      renderChips(params);
      renderPagination(data.page, data.pages);
    } catch (err) {
      if (err.name === "AbortError") return;
      errorBox.hidden = false;
    } finally {
      loading.hidden = true;
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    pageInput.value = "1";
    load();
  });
  sortSelect.addEventListener("change", () => {
    sortHidden.value = sortSelect.value;
    pageInput.value = "1";
    load();
  });
  document.getElementById("catalog-retry").addEventListener("click", load);

  // Первичная отрисовка чипов из URL
  renderChips(currentParams());
})();
