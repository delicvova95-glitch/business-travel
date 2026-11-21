// Общие скрипты: меню, шапка, анимации появления, мелкая логика форм поиска
(function () {
  "use strict";

  // --- Мобильное меню ---
  const burger = document.getElementById("burger");
  const nav = document.getElementById("nav");
  if (burger && nav) {
    const setMenu = (open) => {
      nav.classList.toggle("open", open);
      burger.classList.toggle("open", open);
      burger.setAttribute("aria-expanded", String(open));
      // Блокируем прокрутку страницы под открытым меню
      document.body.classList.toggle("menu-open", open);
    };
    burger.addEventListener("click", () => {
      setMenu(!nav.classList.contains("open"));
    });
    nav.addEventListener("click", (e) => {
      if (e.target.tagName === "A") setMenu(false);
    });
  }

  // --- Компактная шапка при прокрутке ---
  const header = document.getElementById("header");
  if (header) {
    const onScroll = () => header.classList.toggle("compact", window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // --- Анимации появления ---
  const revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          e.target.classList.add("visible");
          io.unobserve(e.target);
        }
      }
    }, { threshold: 0.12 });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("visible"));
  }

  // --- Поиск: возраст детей и суммарное число туристов ---
  const childrenSel = document.getElementById("s-children");
  const agesWrap = document.getElementById("children-ages-wrap");
  if (childrenSel && agesWrap) {
    childrenSel.addEventListener("change", () => {
      agesWrap.hidden = Number(childrenSel.value) === 0;
    });
  }
  const searchForm = document.querySelector(".search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", () => {
      const adults = Number(document.getElementById("s-adults").value || 0);
      const children = Number(document.getElementById("s-children").value || 0);
      document.getElementById("s-tourists").value = String(adults + children);
    });
  }
})();
