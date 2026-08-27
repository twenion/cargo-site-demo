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
    /* The tracking page has its own handler that renders in place; this one is
       for the box on the home page, which navigates. */
    var form = document.querySelector("[data-track-form]:not([data-track-page])");
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


  /* --- Tracking results -------------------------------------------------- */
  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderShipment(code, shipment) {
    var label = XE.statusLabels[shipment.status] || { text: shipment.status, tone: "wait" };
    var events = shipment.events
      .slice()
      .reverse()
      .map(function (ev) {
        return (
          '<li class="timeline__item">' +
          '<p class="timeline__date">' + escapeHtml(ev.date) + "</p>" +
          '<p class="timeline__text">' + escapeHtml(ev.text) + "</p>" +
          '<p class="timeline__place">' + escapeHtml(ev.place) + "</p>" +
          "</li>"
        );
      })
      .join("");

    var weight = String(shipment.weight).replace(".", ",");

    return (
      '<article class="result-card">' +
      '<div class="result-card__head">' +
      '<p class="result-card__code">' + escapeHtml(code) + "</p>" +
      '<span class="badge" data-tone="' + label.tone + '">' + escapeHtml(label.text) + "</span>" +
      "</div>" +
      '<div class="result-card__body">' +
      '<dl class="result-meta">' +
      "<div><dt>Göndərən</dt><dd class=\"result-meta__value\">" + escapeHtml(shipment.from) + "</dd></div>" +
      "<div><dt>Alıcı</dt><dd class=\"result-meta__value\">" + escapeHtml(shipment.to) + "</dd></div>" +
      "<div><dt>Xidmət</dt><dd class=\"result-meta__value\">" + escapeHtml(shipment.service) + "</dd></div>" +
      "<div><dt>Çəki</dt><dd class=\"result-meta__value\">" + weight + " kq</dd></div>" +
      "<div><dt>Təxmini çatdırılma</dt><dd class=\"result-meta__value\">" + escapeHtml(shipment.estimate) + "</dd></div>" +
      "</dl>" +
      '<div><h2 class="visually-hidden">Yükün hərəkəti</h2><ol class="timeline">' + events + "</ol></div>" +
      "</div>" +
      "</article>"
    );
  }

  function renderMissing(code) {
    return (
      '<div class="result-empty">' +
      "<h2>Bu kod tapılmadı</h2>" +
      "<p><strong>" + escapeHtml(code) + "</strong> kodu ilə göndəriş qeydə alınmayıb. " +
      "Kodu bir daha yoxlayın — sifariş yeni verilibsə, sistemə düşməsi 15 dəqiqə çəkə bilər.</p>" +
      '<p style="margin-top: var(--s-4)">Kömək lazımdırsa: ' +
      '<a href="tel:+994000000000">+994 00 000 00 00</a></p>' +
      "</div>"
    );
  }

  function initTracking() {
    var output = document.querySelector("[data-track-result]");
    if (!output) return;

    var form = document.querySelector("[data-track-page]");
    var input = form ? form.querySelector("input[name='kod']") : null;

    function lookup(code) {
      var shipment = (XE.shipments || {})[code];
      output.innerHTML = shipment ? renderShipment(code, shipment) : renderMissing(code);
    }

    /* The sample codes are buttons rather than links so they fill the field in
       place -- a visitor trying the demo should see the field being used. */
    var chips = document.querySelectorAll("[data-sample-code]");
    for (var i = 0; i < chips.length; i++) {
      chips[i].addEventListener("click", function () {
        var code = this.getAttribute("data-sample-code");
        if (input) input.value = code;
        lookup(code);
        output.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    }

    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var code = input.value.trim().toUpperCase();
        var field = input.closest(".field");
        var valid = /^[A-Z]{2}[0-9]{7}$/.test(code);
        field.setAttribute("data-invalid", String(!valid));
        if (!valid) { input.focus(); return; }
        input.value = code;
        /* Keep the code in the URL so the result can be shared or reloaded. */
        if (window.history && window.history.replaceState) {
          window.history.replaceState({}, "", "izleme.html?kod=" + encodeURIComponent(code));
        }
        lookup(code);
      });
    }

    var fromUrl = new URLSearchParams(window.location.search).get("kod");
    if (fromUrl) {
      var code = fromUrl.trim().toUpperCase();
      if (input) input.value = code;
      lookup(code);
    }
  }

  /* --- Order and contact forms ------------------------------------------- */
  /* No backend exists for a demo, so the form validates properly and then says
     plainly that nothing was sent. Pretending to submit would be a lie the
     visitor discovers only when no courier arrives. */
  function initDemoForms() {
    var forms = document.querySelectorAll("[data-order-form], [data-contact-form]");

    for (var i = 0; i < forms.length; i++) {
      forms[i].addEventListener("submit", function (e) {
        e.preventDefault();
        var form = this;
        var status = form.querySelector("[data-form-status]");
        var required = form.querySelectorAll("[required]");
        var firstBad = null;

        for (var j = 0; j < required.length; j++) {
          var el = required[j];
          var field = el.closest(".field");
          var bad = !el.value.trim();
          if (field) field.setAttribute("data-invalid", String(bad));
          if (bad && !firstBad) firstBad = el;
        }

        if (firstBad) {
          status.setAttribute("data-tone", "error");
          status.textContent = "Formu göndərmək üçün ulduzlu xanaları doldurun.";
          firstBad.focus();
          return;
        }

        status.removeAttribute("data-tone");
        status.textContent =
          "Bu nümunə saytdır — form göndərilmədi. Real saytda sifariş bu anda qeydə alınır və " +
          "sizə izləmə kodu göndərilir.";
      });

      forms[i].addEventListener("input", function (e) {
        var field = e.target.closest(".field");
        if (field && field.getAttribute("data-invalid") === "true") {
          field.setAttribute("data-invalid", "false");
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initCalculator();
    initTrackForm();
    initTracking();
    initDemoForms();
  });
})();
