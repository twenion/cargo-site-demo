/**
 * Site behaviour.
 *
 * Everything here is an enhancement: with JS switched off the navigation is a
 * plain list, the tracking box is a GET form that lands on the tracking page,
 * and the calculator points at the tariff table. Nothing that matters is built
 * by script.
 */
(function () {
  "use strict";

  var XE = window.XE || {};

  /* --- Mobile navigation ------------------------------------------------- */
  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("main-nav");
    if (!toggle || !nav) return;

    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      nav.setAttribute("data-open", String(!open));
      toggle.querySelector(".visually-hidden").textContent = open ? "Menyunu aç" : "Menyunu bağla";
    });

    /* Escape closes it, because a menu that traps you is worse than no menu. */
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      if (toggle.getAttribute("aria-expanded") !== "true") return;
      toggle.setAttribute("aria-expanded", "false");
      nav.setAttribute("data-open", "false");
      toggle.focus();
    });
  }

  /* --- Money ------------------------------------------------------------- */
  /* Azerbaijani writes the decimal with a comma: 7,50 ₼ */
  function formatAzn(value) {
    return value.toFixed(2).replace(".", ",") + " ₼";
  }
  XE.formatAzn = formatAzn;

  function priceFor(destinationId, weightKg, originId, urgent) {
    var t = XE.tariffs;
    if (!t) return null;
    var dest = null;
    for (var i = 0; i < t.destinations.length; i++) {
      if (t.destinations[i].id === destinationId) dest = t.destinations[i];
    }
    if (!dest) return null;

    var weight = Math.min(Math.max(weightKg || 0, 0.5), t.maxWeightKg);
    var price = dest.base + Math.max(0, weight - 1) * dest.perKg;
    price *= t.originSurcharge[originId] || 1;
    if (urgent) price *= t.urgentMultiplier;
    return { price: price, dest: dest, weight: weight };
  }
  XE.priceFor = priceFor;

  /* --- Calculator -------------------------------------------------------- */
  function initCalculator() {
    var form = document.querySelector("[data-calc-form]");
    if (!form) return;

    var fromEl = form.querySelector("[data-calc-from]");
    var toEl = form.querySelector("[data-calc-to]");
    var weightEl = form.querySelector("[data-calc-weight]");
    var speedEl = form.querySelector("[data-calc-speed]");
    var priceEl = form.querySelector("[data-calc-price]");
    var noteEl = form.querySelector("[data-calc-note]");

    function update() {
      var urgent = speedEl.value === "tecili";
      var result = priceFor(toEl.value, parseFloat(weightEl.value), fromEl.value, urgent);
      if (!result) return;

      /* A short fade so the number reads as having changed, not as having been
         there all along. Reduced-motion users get the same value instantly. */
      priceEl.setAttribute("data-updating", "true");
      window.setTimeout(function () {
        priceEl.textContent = formatAzn(result.price);
        priceEl.removeAttribute("data-updating");
      }, 110);

      var weightText = String(result.weight).replace(".", ",");
      noteEl.textContent =
        result.dest.label + " · " + (urgent ? "təcili" : "standart") + " · " + weightText + " kq · " + result.dest.duration;
    }

    form.addEventListener("input", update);
    form.addEventListener("change", update);
    form.addEventListener("submit", function (e) { e.preventDefault(); });
    update();
  }

  /* --- Tracking form validation ------------------------------------------ */
  /* The browser's own message is in the browser's language, which on a phone in
     Baku is often not Azerbaijani. This one always is. */
  function initTrackForm() {
    var form = document.querySelector("[data-track-form]");
    if (!form) return;
    var input = form.querySelector("input[name='kod']");
    var field = input.closest(".field");

    form.addEventListener("submit", function (e) {
      var value = input.value.trim().toUpperCase();
      var valid = /^[A-Z]{2}[0-9]{7}$/.test(value);
      field.setAttribute("data-invalid", String(!valid));
      if (!valid) {
        e.preventDefault();
        input.focus();
        return;
      }
      input.value = value;
    });

    input.addEventListener("input", function () {
      if (field.getAttribute("data-invalid") === "true") field.setAttribute("data-invalid", "false");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initCalculator();
    initTrackForm();
  });
})();
