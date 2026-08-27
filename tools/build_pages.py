#!/usr/bin/env python3
"""Generate the inner pages and the shared data module.

The tariff numbers live here and nowhere else. The table on tarifler.html and
the calculator's data.js are both produced from this one list, so the price a
visitor is quoted cannot disagree with the price they are shown -- the kind of
contradiction that costs a courier a customer.

    python3 tools/build_pages.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

# --- The single source for pricing ------------------------------------------
DESTINATIONS = [
    {
        "id": "baku",
        "label": "Bakı (şəhərdaxili)",
        "base": 5.5,
        "perKg": 1.0,
        "duration": "Eyni gün",
        "note": "Saat 14:00-a qədər verilən sifarişlər",
        "cities": "Bakının bütün rayonları",
    },
    {
        "id": "sumqayit",
        "label": "Sumqayıt / Abşeron",
        "base": 7.0,
        "perKg": 1.2,
        "duration": "Eyni gün / ertəsi gün",
        "note": "Axşam 17:00-dək qəbul",
        "cities": "Sumqayıt, Xırdalan, Abşeron rayonu",
    },
    {
        "id": "region-yaxin",
        "label": "Yaxın regionlar",
        "base": 9.5,
        "perKg": 1.6,
        "duration": "24 saat",
        "note": "Gündəlik reys",
        "cities": "Gəncə, Şəki, Quba, Şirvan, Mingəçevir",
    },
    {
        "id": "region-uzaq",
        "label": "Uzaq regionlar",
        "base": 13.0,
        "perKg": 2.1,
        "duration": "48 saat",
        "note": "Həftədə 4 reys",
        "cities": "Lənkəran, Zaqatala, Naxçıvan, Astara",
    },
]

ORIGIN_SURCHARGE = {"baku": 1, "sumqayit": 1.1, "gence": 1.15}
URGENT_MULTIPLIER = 1.5
MAX_WEIGHT_KG = 500

SHIPMENTS = {
    "XE4827193": {
        "status": "yolda",
        "from": "Bakı, Nizami küçəsi 118",
        "to": "Gəncə, Atatürk prospekti 42",
        "weight": 4.5,
        "service": "Regionlara çatdırılma",
        "estimate": "29.08.2026",
        "events": [
            {"date": "27.08.2026 09:14", "place": "Bakı, mərkəzi anbar", "text": "Yük qəbul edildi"},
            {"date": "27.08.2026 11:40", "place": "Bakı, mərkəzi anbar", "text": "Çeşidləmə tamamlandı"},
            {"date": "27.08.2026 15:22", "place": "Bakı → Gəncə", "text": "Yola salındı"},
        ],
    },
    "XE1029384": {
        "status": "catdirilib",
        "from": "Bakı, 28 May küçəsi 7",
        "to": "Bakı, Xətai rayonu, Babək prospekti 12",
        "weight": 1.2,
        "service": "Şəhərdaxili kuryer",
        "estimate": "26.08.2026",
        "events": [
            {"date": "26.08.2026 10:02", "place": "Bakı, 28 May", "text": "Kuryer yükü götürdü"},
            {"date": "26.08.2026 12:35", "place": "Bakı, Xətai", "text": "Çatdırılma marşrutunda"},
            {"date": "26.08.2026 14:08", "place": "Bakı, Xətai", "text": "Alıcıya təhvil verildi"},
        ],
    },
    "XE5560271": {
        "status": "qebul",
        "from": "Sumqayıt, Sülh küçəsi 3",
        "to": "Lənkəran, Həzi Aslanov küçəsi 55",
        "weight": 12,
        "service": "Yük daşıma",
        "estimate": "30.08.2026",
        "events": [
            {"date": "27.08.2026 16:45", "place": "Sumqayıt, qəbul məntəqəsi", "text": "Yük qəbul edildi"},
        ],
    },
}

STATUS_LABELS = {
    "qebul": {"text": "Qəbul edildi", "tone": "wait"},
    "yolda": {"text": "Yoldadır", "tone": "move"},
    "catdirilib": {"text": "Çatdırıldı", "tone": "done"},
}

BRANCHES = [
    {"city": "Bakı", "name": "Mərkəzi ofis", "address": "Nizami küçəsi 118", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-19:00, Şənbə 10:00-16:00"},
    {"city": "Bakı", "name": "Xətai filialı", "address": "Babək prospekti 24", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-19:00, Şənbə 10:00-16:00"},
    {"city": "Bakı", "name": "Nərimanov filialı", "address": "Atatürk prospekti 9", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-19:00, Şənbə 10:00-16:00"},
    {"city": "Bakı", "name": "Binəqədi qəbul məntəqəsi", "address": "Ə. Naxçıvani küçəsi 41", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-18:00"},
    {"city": "Bakı", "name": "Yasamal qəbul məntəqəsi", "address": "Şərifzadə küçəsi 203", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-18:00"},
    {"city": "Sumqayıt", "name": "Sumqayıt filialı", "address": "Sülh küçəsi 3", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-18:00, Şənbə 10:00-15:00"},
    {"city": "Xırdalan", "name": "Xırdalan qəbul məntəqəsi", "address": "Həsən Əliyev küçəsi 12", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-18:00"},
    {"city": "Gəncə", "name": "Gəncə filialı", "address": "Atatürk prospekti 42", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-18:00, Şənbə 10:00-15:00"},
    {"city": "Şəki", "name": "Şəki qəbul məntəqəsi", "address": "M.Ə.Rəsulzadə küçəsi 8", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-17:00"},
    {"city": "Quba", "name": "Quba qəbul məntəqəsi", "address": "Heydər Əliyev prospekti 61", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-17:00"},
    {"city": "Lənkəran", "name": "Lənkəran filialı", "address": "Həzi Aslanov küçəsi 55", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-18:00"},
    {"city": "Mingəçevir", "name": "Mingəçevir qəbul məntəqəsi", "address": "Heydər Əliyev prospekti 17", "phone": "+994 00 000 00 00", "hours": "B.e-Cümə 09:00-17:00"},
]


def azn(value: float) -> str:
    """Azerbaijani writes the decimal with a comma."""
    return f"{value:.2f}".replace(".", ",") + " ₼"


def write_data_js() -> None:
    """data.js is generated so it can never drift from the table above."""
    body = f"""/**
 * Shared data for the demo.
 *
 * GENERATED by tools/build_pages.py -- edit the tables there, not this file.
 *
 * The tariff table and the calculator read the same numbers, so the price a
 * visitor is quoted can never disagree with the price on the tariff page.
 */
window.XE = window.XE || {{}};

/* Base covers the first kilogram; every kilo after that is charged at perKg. */
window.XE.tariffs = {{
  destinations: {json.dumps(DESTINATIONS, ensure_ascii=False, indent=4)},
  /* Picking the parcel up outside Baku adds a leg to the route. */
  originSurcharge: {json.dumps(ORIGIN_SURCHARGE, ensure_ascii=False)},
  urgentMultiplier: {URGENT_MULTIPLIER},
  maxWeightKg: {MAX_WEIGHT_KG},
}};

/* Sample shipments so the tracking page has something to show. The footer says
   plainly that these are made up. */
window.XE.shipments = {json.dumps(SHIPMENTS, ensure_ascii=False, indent=2)};

window.XE.statusLabels = {json.dumps(STATUS_LABELS, ensure_ascii=False, indent=2)};
"""
    (render.ROOT / "assets/js/data.js").write_text(body, encoding="utf-8")
    print(f"  {'assets/js/data.js':22s} {len(body):>6d} bytes")


def page_header(eyebrow: str, title: str, lede: str) -> str:
    return f"""    <main id="main">
      <section class="page-head">
        <div class="wrap">
          <p class="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p class="page-head__lede">{lede}</p>
        </div>
      </section>
"""


def build_tariffs() -> None:
    rows = []
    for d in DESTINATIONS:
        rows.append(
            f"""              <tr>
                <th scope="row">
                  {d['label']}
                  <span class="table__sub">{d['cities']}</span>
                </th>
                <td data-label="İlk 1 kq">{azn(d['base'])}</td>
                <td data-label="Sonrakı hər kq">{azn(d['perKg'])}</td>
                <td data-label="Müddət">{d['duration']}<span class="table__sub">{d['note']}</span></td>
              </tr>"""
        )

    examples = []
    for d in DESTINATIONS:
        five_kg = d["base"] + 4 * d["perKg"]
        examples.append(f"<li><strong>{d['label']}</strong>, 5 kq — {azn(five_kg)}</li>")

    body = page_header(
        "Qiymətlər",
        "Tariflər və çatdırılma müddətləri",
        "Qiymət çəkiyə və istiqamətə görə hesablanır. Gizli əlavə haqq yoxdur — "
        "yükləmə və boşaltma məbləğə daxildir.",
    )
    body += f"""
      <section class="section--tight">
        <div class="wrap">
          <div class="table-wrap">
            <table class="table">
              <caption class="visually-hidden">İstiqamətlərə görə çatdırılma qiymətləri və müddətləri</caption>
              <thead>
                <tr>
                  <th scope="col">İstiqamət</th>
                  <th scope="col">İlk 1 kq</th>
                  <th scope="col">Sonrakı hər kq</th>
                  <th scope="col">Müddət</th>
                </tr>
              </thead>
              <tbody>
{chr(10).join(rows)}
              </tbody>
            </table>
          </div>

          <div class="note-grid">
            <div class="note">
              <h3>Təcili çatdırılma</h3>
              <p>Standart tarifin üzərinə <strong>+50%</strong>. Bakı daxilində 3 saat ərzində.</p>
            </div>
            <div class="note">
              <h3>Çəki həddi</h3>
              <p>Bir göndərişdə <strong>500 kq</strong>-a qədər. Daha ağır yüklər üçün bizimlə əlaqə saxlayın.</p>
            </div>
            <div class="note">
              <h3>Korporativ tarif</h3>
              <p>Ayda 50-dən çox göndəriş üçün fərdi qiymət və aylıq hesab-faktura.</p>
            </div>
          </div>
        </div>
      </section>

      <section class="section section--alt" id="hesablayici">
        <div class="wrap calc">
          <div class="calc__copy">
            <div class="section-head">
              <h2>Öz yükünüzü hesablayın</h2>
              <p>Cədvəldəki eyni qiymətlərlə işləyir — nəticə birbaşa yuxarıdakı tariflərdən çıxır.</p>
            </div>
            <ul class="tick-list">
{chr(10).join('              ' + e for e in examples)}
            </ul>
          </div>

          <form class="calc__panel" data-calc-form>
            <h3 class="calc__title">Çatdırılma hesablayıcısı</h3>

            <div class="field">
              <label for="calc-from">Haradan</label>
              <select class="select" id="calc-from" name="from" data-calc-from>
                <option value="baku">Bakı</option>
                <option value="sumqayit">Sumqayıt</option>
                <option value="gence">Gəncə</option>
              </select>
            </div>

            <div class="field">
              <label for="calc-to">Haraya</label>
              <select class="select" id="calc-to" name="to" data-calc-to>
{chr(10).join(f'                <option value="{d["id"]}">{d["label"]}</option>' for d in DESTINATIONS)}
              </select>
            </div>

            <div class="field">
              <label for="calc-weight">Çəki (kq)</label>
              <input class="input" id="calc-weight" name="weight" type="number" min="0.5" max="500" step="0.5" value="3" data-calc-weight />
            </div>

            <div class="field">
              <label for="calc-speed">Sürət</label>
              <select class="select" id="calc-speed" name="speed" data-calc-speed>
                <option value="standart">Standart</option>
                <option value="tecili">Təcili (+50%)</option>
              </select>
            </div>

            <output class="calc__result" data-calc-output>
              <span class="calc__result-label">Təxmini məbləğ</span>
              <span class="calc__result-value" data-calc-price>{azn(DESTINATIONS[0]['base'] + 2 * DESTINATIONS[0]['perKg'])}</span>
              <span class="calc__result-note" data-calc-note>{DESTINATIONS[0]['label']} · standart · 3 kq</span>
            </output>

            <noscript>
              <p class="dim">Hesablayıcı üçün JavaScript lazımdır — qiymətləri yuxarıdakı cədvəldən götürə bilərsiniz.</p>
            </noscript>

            <a class="btn btn--primary btn--block" href="sifaris.html">Bu şərtlərlə sifariş ver</a>
          </form>
        </div>
      </section>
    </main>
"""

    render.write(
        "tarifler.html",
        "Tariflər — çatdırılma qiymətləri və müddətləri | Xəzər Ekspres",
        "Bakı və regionlara çatdırılma qiymətləri: ilk 1 kq və sonrakı kiloqramlar üzrə tarif, "
        "çatdırılma müddətləri, təcili göndəriş və korporativ şərtlər.",
        "Tariflər — çatdırılma qiymətləri",
        "İstiqamətə və çəkiyə görə qiymət cədvəli, üstəlik onlayn hesablayıcı.",
        body,
        render.breadcrumbs("tarifler.html", "Tariflər"),
    )


def build_tracking() -> None:
    samples = "".join(
        f'<li><button class="code-chip" type="button" data-sample-code="{code}">{code}</button> '
        f'<span class="dim">{s["service"]}</span></li>'
        for code, s in SHIPMENTS.items()
    )

    body = page_header(
        "İzləmə",
        "Bağlamanızı izləyin",
        "Sifariş qeydə alınanda sizə 9 simvolluq izləmə kodu göndərilir. Kodu daxil edin — "
        "yükün hansı mərhələdə olduğunu göstərək.",
    )
    body += f"""
      <section class="section--tight">
        <div class="wrap track-page">
          <form class="track-panel" data-track-form data-track-page>
            <div class="field">
              <label for="track-code">İzləmə kodu</label>
              <input
                class="input"
                id="track-code"
                name="kod"
                type="text"
                inputmode="latin"
                autocomplete="off"
                placeholder="XE4827193"
                pattern="[A-Za-z]{{2}}[0-9]{{7}}"
                maxlength="9"
                required
              />
              <p class="field-error" data-error>Kod 2 hərf və 7 rəqəmdən ibarət olmalıdır. Nümunə: XE4827193</p>
            </div>
            <button class="btn btn--primary" type="submit">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
                <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
              </svg>
              Yükü tap
            </button>
          </form>

          <div class="sample-codes">
            <h2>Sınamaq üçün nümunə kodlar</h2>
            <ul>{samples}</ul>
          </div>

          <noscript>
            <div class="demo-notice" style="margin-top: var(--s-6)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" /><path d="M12 8v5M12 16.5v.5" />
              </svg>
              <span>İzləmə nəticəsini göstərmək üçün JavaScript lazımdır. Kodunuzu
              <a href="tel:+994000000000">+994 00 000 00 00</a> nömrəsinə deyin — operator sizə məlumat versin.</span>
            </div>
          </noscript>

          <!-- Filled in by site.js; aria-live so a screen reader hears the result. -->
          <div class="track-result" data-track-result aria-live="polite"></div>
        </div>
      </section>
    </main>
"""

    render.write(
        "izleme.html",
        "Bağlama izləmə — yükünüz haradadır? | Xəzər Ekspres",
        "İzləmə kodunu daxil edib bağlamanızın hansı mərhələdə olduğunu, hara çatdığını və "
        "təxmini çatdırılma tarixini görün.",
        "Bağlama izləmə",
        "İzləmə kodu ilə yükünüzün hazırkı mərhələsini görün.",
        body,
        render.breadcrumbs("izleme.html", "İzləmə"),
    )


def build_order() -> None:
    dest_options = "\n".join(
        f'                  <option value="{d["id"]}">{d["label"]} — {d["duration"]}</option>' for d in DESTINATIONS
    )

    body = page_header(
        "Sifariş",
        "Onlayn sifariş verin",
        "Formu doldurun — kuryer Bakı daxilində 2 saat ərzində ünvanınıza gəlsin. "
        "İş saatlarında sifarişlər 15 dəqiqə içində təsdiqlənir.",
    )
    body += f"""
      <section class="section--tight">
        <div class="wrap order">
          <form class="order__form" data-order-form novalidate>
            <fieldset class="fieldset">
              <legend>Göndərən</legend>
              <div class="field-row">
                <div class="field">
                  <label for="sender-name">Ad, soyad <span class="req" aria-hidden="true">*</span></label>
                  <input class="input" id="sender-name" name="sender-name" type="text" autocomplete="name" required />
                  <p class="field-error" data-error>Adınızı yazın.</p>
                </div>
                <div class="field">
                  <label for="sender-phone">Telefon <span class="req" aria-hidden="true">*</span></label>
                  <input class="input" id="sender-phone" name="sender-phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+994 00 000 00 00" required />
                  <p class="field-error" data-error>Telefon nömrəsini tam yazın.</p>
                </div>
              </div>
              <div class="field">
                <label for="sender-address">Götürülmə ünvanı <span class="req" aria-hidden="true">*</span></label>
                <input class="input" id="sender-address" name="sender-address" type="text" autocomplete="street-address" required />
                <p class="field-error" data-error>Kuryerin gələcəyi ünvanı yazın.</p>
              </div>
            </fieldset>

            <fieldset class="fieldset">
              <legend>Alıcı</legend>
              <div class="field-row">
                <div class="field">
                  <label for="receiver-name">Ad, soyad <span class="req" aria-hidden="true">*</span></label>
                  <input class="input" id="receiver-name" name="receiver-name" type="text" required />
                  <p class="field-error" data-error>Alıcının adını yazın.</p>
                </div>
                <div class="field">
                  <label for="receiver-phone">Telefon <span class="req" aria-hidden="true">*</span></label>
                  <input class="input" id="receiver-phone" name="receiver-phone" type="tel" inputmode="tel" placeholder="+994 00 000 00 00" required />
                  <p class="field-error" data-error>Telefon nömrəsini tam yazın.</p>
                </div>
              </div>
              <div class="field">
                <label for="receiver-address">Çatdırılma ünvanı <span class="req" aria-hidden="true">*</span></label>
                <input class="input" id="receiver-address" name="receiver-address" type="text" required />
                <p class="field-error" data-error>Çatdırılma ünvanını yazın.</p>
              </div>
            </fieldset>

            <fieldset class="fieldset">
              <legend>Yük</legend>
              <div class="field-row">
                <div class="field">
                  <label for="order-dest">İstiqamət</label>
                  <select class="select" id="order-dest" name="dest" data-calc-to>
{dest_options}
                  </select>
                </div>
                <div class="field">
                  <label for="order-weight">Çəki (kq)</label>
                  <input class="input" id="order-weight" name="weight" type="number" min="0.5" max="500" step="0.5" value="3" data-calc-weight />
                </div>
              </div>
              <div class="field">
                <label for="order-note">Qeyd <span class="dim">(istəyə bağlı)</span></label>
                <textarea class="textarea" id="order-note" name="note" placeholder="Kövrək yükdür, ehtiyatlı olun."></textarea>
              </div>
            </fieldset>

            <div class="order__summary">
              <span class="calc__result-label">Təxmini məbləğ</span>
              <span class="calc__result-value" data-calc-price>{azn(DESTINATIONS[0]['base'] + 2 * DESTINATIONS[0]['perKg'])}</span>
              <span class="calc__result-note" data-calc-note>{DESTINATIONS[0]['label']} · standart · 3 kq</span>
            </div>

            <button class="btn btn--primary btn--block" type="submit">Sifarişi göndər</button>
            <p class="dim">Formu göndərməklə <a href="mexfilik.html">məxfilik siyasəti</a> ilə razılaşırsınız.</p>

            <div class="form-status" data-form-status role="status" aria-live="polite"></div>
          </form>

          <aside class="order__aside">
            <div class="card">
              <h2>Kuryer nə vaxt gəlir?</h2>
              <ul class="tick-list" style="margin-top: var(--s-4)">
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 13 4 4L19 7" /></svg>Bakı daxilində 2 saat ərzində</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 13 4 4L19 7" /></svg>Sumqayıt və Abşeronda eyni gün</li>
                <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 13 4 4L19 7" /></svg>Regionlarda ertəsi səhər</li>
              </ul>
            </div>

            <div class="card">
              <h2>Zəng etmək daha rahatdır?</h2>
              <p class="muted">İş saatlarında birbaşa operatorla danışın.</p>
              <p style="margin-top: var(--s-4)">
                <a class="btn btn--ghost btn--block" href="tel:+994000000000">+994 00 000 00 00</a>
              </p>
              <p style="margin-top: var(--s-3)">
                <a class="btn btn--ghost btn--block" href="https://wa.me/994000000000" rel="noopener nofollow" target="_blank">WhatsApp ilə yazın</a>
              </p>
            </div>
          </aside>
        </div>
      </section>
    </main>
"""

    render.write(
        "sifaris.html",
        "Onlayn sifariş — kuryer çağırın | Xəzər Ekspres",
        "Göndərən və alıcı məlumatlarını doldurun, kuryer Bakı daxilində 2 saat ərzində "
        "ünvanınıza gəlsin. Məbləği elə formada görün.",
        "Onlayn sifariş",
        "İki dəqiqəlik formu doldurun, kuryeri ünvanınıza çağırın.",
        body,
        render.breadcrumbs("sifaris.html", "Sifariş"),
    )


SERVICES = [
    {
        "id": "sheherdaxili",
        "title": "Şəhərdaxili kuryer",
        "lede": "Bakı üzrə eyni gün çatdırılma.",
        "text": "Sənəd, bağlama və kiçik yüklər üçün. Saat 14:00-a qədər verilən sifarişlər həmin gün "
        "çatdırılır, təcili rejimdə 3 saat ərzində. Kuryer ünvanınıza 2 saat içində gəlir.",
        "points": ["Eyni gün çatdırılma", "Təcili rejim: 3 saat", "Sənədli təhvil-təslim", "Qaytarma sənədi xidməti"],
        "from": 5.5,
    },
    {
        "id": "regionlar",
        "title": "Regionlara çatdırılma",
        "lede": "40-dan çox şəhər və rayona müntəzəm reys.",
        "text": "Gəncə, Şəki, Quba, Şirvan və Mingəçevirə gündəlik; Lənkəran, Zaqatala, Astara və "
        "Naxçıvana həftədə dörd reys. Yükünüz filiala çatan kimi alıcıya bildiriş gedir.",
        "points": ["Yaxın regionlar: 24 saat", "Uzaq regionlar: 48 saat", "Filialdan götürmə imkanı", "Ünvana çatdırılma"],
        "from": 9.5,
    },
    {
        "id": "yuk",
        "title": "Yük daşıma",
        "lede": "500 kq-a qədər palet və həcmli yüklər.",
        "text": "Mebel, avadanlıq və topdan mal göndərişləri üçün. Yükləmə və boşaltma qiymətə "
        "daxildir. Xüsusi qablaşdırma tələb edən yüklər üçün əvvəlcədən dəqiqləşdirmə aparılır.",
        "points": ["Yükləmə-boşaltma daxildir", "Palet və həcmli yüklər", "Sığorta imkanı", "Əvvəlcədən qiymətləndirmə"],
        "from": 13.0,
    },
    {
        "id": "anbar",
        "title": "Anbar və paylama",
        "lede": "Onlayn mağazalar üçün tam dövriyyə.",
        "text": "Malınızı anbarımızda saxlayırıq, sifariş gələndə yığıb müştəriyə çatdırırıq. "
        "Aylıq hesabat, qaytarmaların idarə olunması və nağd ödənişin toplanması daxil.",
        "points": ["Saxlama və yığım", "Müştəriyə paylama", "Qaytarmaların idarəsi", "Aylıq hesab-faktura"],
        "from": None,
    },
]


def build_services() -> None:
    cards = []
    for s in SERVICES:
        price = (
            f'<p class="service__price">{azn(s["from"])}-dən başlayır</p>'
            if s["from"] is not None
            else '<p class="service__price">Fərdi qiymət</p>'
        )
        points = "".join(
            f'<li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 13 4 4L19 7" /></svg>{p}</li>'
            for p in s["points"]
        )
        cards.append(
            f"""          <article class="service" id="{s['id']}">
            <div class="service__body">
              <h2>{s['title']}</h2>
              <p class="service__lede">{s['lede']}</p>
              <p class="muted">{s['text']}</p>
              <ul class="tick-list service__points">{points}</ul>
            </div>
            <div class="service__side">
              {price}
              <a class="btn btn--primary btn--block" href="sifaris.html">Sifariş ver</a>
              <a class="btn btn--ghost btn--block" href="tarifler.html">Tariflərə bax</a>
            </div>
          </article>"""
        )

    body = page_header(
        "Xidmətlər",
        "Nə göndərməli olsanız, bir sistem altında",
        "Bir zərfdən tam anbar idarəçiliyinə qədər. Hansı xidməti seçsəniz, izləmə kodu, "
        "sənədli təhvil-təslim və eyni dəstək xətti sizi müşayiət edir.",
    )
    body += f"""
      <section class="section--tight">
        <div class="wrap service-list">
{chr(10).join(cards)}
        </div>
      </section>
    </main>
"""

    render.write(
        "xidmetler.html",
        "Xidmətlər — kuryer, region çatdırılması, yük daşıma | Xəzər Ekspres",
        "Şəhərdaxili kuryer, regionlara çatdırılma, 500 kq-a qədər yük daşıma və onlayn "
        "mağazalar üçün anbar-paylama xidməti.",
        "Xidmətlər",
        "Kuryerdən anbar idarəçiliyinə qədər dörd xidmət, bir izləmə sistemi.",
        body,
        render.breadcrumbs("xidmetler.html", "Xidmətlər"),
    )


def build_branches() -> None:
    cities: dict[str, list[dict]] = {}
    for b in BRANCHES:
        cities.setdefault(b["city"], []).append(b)

    groups = []
    for city, items in cities.items():
        cards = "".join(
            f"""            <article class="branch">
              <h3>{b['name']}</h3>
              <p class="branch__address">{b['address']}</p>
              <p class="branch__hours">{b['hours']}</p>
              <p><a href="tel:{b['phone'].replace(' ', '')}">{b['phone']}</a></p>
            </article>"""
            for b in items
        )
        groups.append(
            f"""          <div class="branch-group">
            <h2>{city} <span class="dim">({len(items)})</span></h2>
            <div class="grid grid--3">
{cards}
            </div>
          </div>"""
        )

    body = page_header(
        "Filiallar",
        f"{len(BRANCHES)} filial və qəbul məntəqəsi",
        "Yükünüzü ən yaxın məntəqəyə gətirin və ya kuryer çağırın — hər iki halda eyni "
        "izləmə kodu ilə işləyirik.",
    )
    body += f"""
      <section class="section--tight">
        <div class="wrap branch-list">
{chr(10).join(groups)}
        </div>
      </section>
    </main>
"""

    render.write(
        "filiallar.html",
        "Filiallar və qəbul məntəqələri — ünvanlar, iş saatları | Xəzər Ekspres",
        "Bakı, Sumqayıt, Gəncə, Şəki, Quba, Lənkəran və Mingəçevirdə 12 filial və qəbul "
        "məntəqəsi: ünvan, telefon və iş saatları.",
        "Filiallar",
        "12 filial və qəbul məntəqəsinin ünvanı, telefonu və iş saatı.",
        body,
        render.breadcrumbs("filiallar.html", "Filiallar"),
    )


def build_about() -> None:
    body = page_header(
        "Haqqımızda",
        "2015-ci ildən yolda",
        "Bir furqon və iki kuryerlə başladıq. Bu gün 12 məntəqədə işləyirik və ayda "
        "1 400-dən çox korporativ göndəriş daşıyırıq.",
    )
    body += """
      <section class="section--tight">
        <div class="wrap about">
          <div class="about__main stack-lg">
            <div class="stack">
              <h2>Nə edirik</h2>
              <p class="muted">
                Xəzər Ekspres Bakı və Azərbaycanın regionları üzrə kuryer və yük çatdırılması
                ilə məşğuldur. Müştərilərimizin böyük hissəsi onlayn mağazalar, hüquq və
                mühasibat şirkətləri, bir də sənəd dövriyyəsi yüksək olan təşkilatlardır.
              </p>
              <p class="muted">
                İşimizin ölçüsü sadədir: yük vaxtında çatdımı, çatmadımı. Keçən il
                göndərişlərin 99,2%-i söz verilən müddətdə çatdırıldı — gecikən 0,8% üçün
                səbəbi müştəriyə yazılı bildiririk.
              </p>
            </div>

            <div class="stack">
              <h2>Necə işləyirik</h2>
              <p class="muted">
                Hər göndəriş qəbul anında qeydə alınır və izləmə kodu alır. Kod yükün keçdiyi
                hər mərhələdə yenilənir: qəbul, çeşidləmə, yola salınma, çatdırılma. Alıcı
                imzaladıqdan sonra göndərənə təsdiq bildirişi gedir.
              </p>
              <p class="muted">
                Qiymətlər saytda açıq göstərilib. Zəng edib «sizin üçün nə qədər olar» sualını
                vermək lazım deyil — hesablayıcı elə cədvəldəki rəqəmlərlə işləyir.
              </p>
            </div>

            <div class="stack">
              <h2>Komanda</h2>
              <p class="muted">
                34 nəfərlik komanda: 21 kuryer və sürücü, 6 anbar işçisi, 5 operator və
                2 nəfər inzibati heyət. Kuryerlərimizin yarıdan çoxu üç ildən artıqdır
                bizimlədir.
              </p>
            </div>
          </div>

          <aside class="about__aside">
            <div class="card">
              <h3>Rəqəmlərlə</h3>
              <ul class="fact-list">
                <li><strong>2015</strong><span>fəaliyyətin başlanğıcı</span></li>
                <li><strong>12</strong><span>filial və qəbul məntəqəsi</span></li>
                <li><strong>34</strong><span>işçi</span></li>
                <li><strong>99,2%</strong><span>vaxtında çatdırılma</span></li>
                <li><strong>1 400+</strong><span>aylıq korporativ göndəriş</span></li>
              </ul>
            </div>

            <div class="card">
              <h3>Korporativ müştəri olmaq</h3>
              <p class="muted">
                Ayda 50-dən çox göndəriş üçün fərdi tarif, aylıq hesab-faktura və ayrıca
                əlaqə şəxsi.
              </p>
              <p style="margin-top: var(--s-4)">
                <a class="btn btn--primary btn--block" href="elaqe.html">Bizimlə əlaqə</a>
              </p>
            </div>
          </aside>
        </div>
      </section>
    </main>
"""

    render.write(
        "haqqimizda.html",
        "Haqqımızda — Xəzər Ekspres kimdir? | Xəzər Ekspres",
        "2015-ci ildən Bakı və regionlarda kuryer və yük çatdırılması. 12 məntəqə, 34 işçi, "
        "ayda 1 400-dən çox korporativ göndəriş.",
        "Haqqımızda",
        "2015-dən bəri Bakı və regionlarda çatdırılma. Rəqəmlərlə komanda və iş üsulu.",
        body,
        render.breadcrumbs("haqqimizda.html", "Haqqımızda"),
    )


def build_contact() -> None:
    body = page_header(
        "Əlaqə",
        "Bizimlə əlaqə saxlayın",
        "Sifariş, korporativ təklif və ya şikayət — hansı olursa olsun, iş saatlarında "
        "eyni gün cavab veririk.",
    )
    body += """
      <section class="section--tight">
        <div class="wrap contact">
          <div class="contact__channels stack-lg">
            <div class="card">
              <span class="card-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z" />
                </svg>
              </span>
              <h2>Telefon</h2>
              <p class="muted">B.e-Cümə 09:00-19:00, Şənbə 10:00-16:00</p>
              <p style="margin-top: var(--s-3)"><a class="contact__big" href="tel:+994000000000">+994 00 000 00 00</a></p>
            </div>

            <div class="card">
              <span class="card-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" />
                </svg>
              </span>
              <h2>E-poçt</h2>
              <p class="muted">Yazılı müraciətlər və korporativ təkliflər üçün</p>
              <p style="margin-top: var(--s-3)"><a class="contact__big" href="mailto:info@xezerekspres.az">info@xezerekspres.az</a></p>
            </div>

            <div class="card">
              <span class="card-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="10" r="3" /><path d="M12 2a8 8 0 0 0-8 8c0 5.4 8 12 8 12s8-6.6 8-12a8 8 0 0 0-8-8z" />
                </svg>
              </span>
              <h2>Mərkəzi ofis</h2>
              <p class="muted">Nizami küçəsi 118, Bakı AZ1010</p>
              <p style="margin-top: var(--s-3)"><a href="filiallar.html">Bütün filiallara bax</a></p>
            </div>
          </div>

          <form class="contact__form" data-contact-form novalidate>
            <h2>Mesaj göndərin</h2>
            <p class="muted">Formu doldurun — iş saatlarında eyni gün cavab veririk.</p>

            <div class="field">
              <label for="c-name">Ad, soyad <span class="req" aria-hidden="true">*</span></label>
              <input class="input" id="c-name" name="name" type="text" autocomplete="name" required />
              <p class="field-error" data-error>Adınızı yazın.</p>
            </div>

            <div class="field">
              <label for="c-contact">Telefon və ya e-poçt <span class="req" aria-hidden="true">*</span></label>
              <input class="input" id="c-contact" name="contact" type="text" required />
              <p class="field-error" data-error>Sizə necə cavab verək? Telefon və ya e-poçt yazın.</p>
            </div>

            <div class="field">
              <label for="c-subject">Mövzu</label>
              <select class="select" id="c-subject" name="subject">
                <option value="sifaris">Sifariş haqqında</option>
                <option value="korporativ">Korporativ təklif</option>
                <option value="sikayet">Şikayət</option>
                <option value="diger">Digər</option>
              </select>
            </div>

            <div class="field">
              <label for="c-message">Mesaj <span class="req" aria-hidden="true">*</span></label>
              <textarea class="textarea" id="c-message" name="message" required></textarea>
              <p class="field-error" data-error>Mesajınızı yazın.</p>
            </div>

            <button class="btn btn--primary btn--block" type="submit">Göndər</button>
            <div class="form-status" data-form-status role="status" aria-live="polite"></div>
          </form>
        </div>
      </section>
    </main>
"""

    render.write(
        "elaqe.html",
        "Əlaqə — telefon, e-poçt və ünvan | Xəzər Ekspres",
        "Telefon +994 00 000 00 00, e-poçt info@xezerekspres.az, mərkəzi ofis Nizami küçəsi 118, "
        "Bakı. Mesaj formu ilə də yaza bilərsiniz.",
        "Əlaqə",
        "Telefon, e-poçt, ünvan və mesaj formu.",
        body,
        render.breadcrumbs("elaqe.html", "Əlaqə"),
    )


def build_privacy() -> None:
    body = page_header(
        "Sənədlər",
        "Məxfilik siyasəti",
        "Bu səhifə hansı məlumatları topladığımızı, nə üçün istifadə etdiyimizi və nə qədər "
        "saxladığımızı izah edir.",
    )
    body += """
      <section class="section--tight">
        <div class="wrap prose">
          <h2>Hansı məlumatları toplayırıq</h2>
          <p>
            Sifariş verərkən göndərənin və alıcının adı, telefon nömrəsi və ünvanı toplanır.
            Bunlar olmadan yükü götürmək və çatdırmaq mümkün deyil. Əlaqə formunda isə yalnız
            ad və sizinlə əlaqə üçün verdiyiniz telefon və ya e-poçt saxlanılır.
          </p>

          <h2>Nə üçün istifadə edirik</h2>
          <p>
            Məlumatlar yalnız çatdırılmanın təşkili, sizinlə əlaqə saxlanması və qanunla tələb
            olunan uçotun aparılması üçün istifadə olunur. Reklam məqsədilə üçüncü tərəflərə
            verilmir və satılmır.
          </p>

          <h2>Nə qədər saxlayırıq</h2>
          <p>
            Göndəriş məlumatları mühasibat uçotu tələblərinə uyğun olaraq 5 il saxlanılır.
            Əlaqə formu vasitəsilə göndərilən mesajlar cavablandırıldıqdan sonra 12 ay
            müddətində saxlanılır.
          </p>

          <h2>Kimlərlə paylaşırıq</h2>
          <p>
            Yalnız çatdırılmanı həyata keçirən kuryer və filial əməkdaşları ilə — və yalnız
            konkret göndərişə aid hissə ilə. Dövlət orqanlarına məlumat yalnız qanunvericiliyin
            tələb etdiyi hallarda və rəsmi sorğu əsasında verilir.
          </p>

          <h2>Kukilər (cookies)</h2>
          <p>
            Sayt yalnız işləmək üçün zəruri olan texniki kukilərdən istifadə edir. İzləmə və
            reklam kukisi yerləşdirilmir.
          </p>

          <h2>Hüquqlarınız</h2>
          <p>
            Sizə aid məlumatların surətini tələb edə, düzəliş etdirə və ya qanunla saxlanması
            tələb olunmayan hissəsinin silinməsini istəyə bilərsiniz. Müraciət üçün:
            <a href="mailto:info@xezerekspres.az">info@xezerekspres.az</a>.
          </p>

          <div class="demo-notice" style="margin-top: var(--s-7)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
              <circle cx="12" cy="12" r="9" /><path d="M12 8v5M12 16.5v.5" />
            </svg>
            <span>
              Bu mətn nümunə layihənin bir hissəsidir və hüquqi məsləhət deyil. Real saytda
              məxfilik siyasəti şirkətin faktiki iş qaydalarına uyğun hazırlanmalıdır.
            </span>
          </div>
        </div>
      </section>
    </main>
"""

    render.write(
        "mexfilik.html",
        "Məxfilik siyasəti | Xəzər Ekspres",
        "Hansı şəxsi məlumatları topladığımız, nə üçün istifadə etdiyimiz, nə qədər saxladığımız "
        "və hüquqlarınız barədə.",
        "Məxfilik siyasəti",
        "Toplanan məlumatlar, saxlanma müddəti və hüquqlarınız.",
        body,
        render.breadcrumbs("mexfilik.html", "Məxfilik siyasəti"),
    )


def build_404() -> None:
    body = """    <main id="main">
      <section class="section notfound">
        <div class="wrap center stack-lg">
          <p class="eyebrow">Səhifə tapılmadı</p>
          <h1>Axtardığınız səhifə burada deyil</h1>
          <p class="muted" style="max-width: 54ch; margin-inline: auto">
            Ünvan səhv yazılmış ola bilər, ya da səhifə köçürülüb. Aşağıdakılardan biri
            işinizə yaraya bilər.
          </p>
          <div class="hero__actions" style="justify-content: center">
            <a class="btn btn--primary" href="index.html">Ana səhifəyə qayıt</a>
            <a class="btn btn--ghost" href="izleme.html">Bağlamanı izlə</a>
            <a class="btn btn--ghost" href="elaqe.html">Bizimlə əlaqə</a>
          </div>
        </div>
      </section>
    </main>
"""

    render.write(
        "404.html",
        "Səhifə tapılmadı | Xəzər Ekspres",
        "Axtardığınız səhifə mövcud deyil. Ana səhifəyə qayıda, bağlamanızı izləyə və ya "
        "bizimlə əlaqə saxlaya bilərsiniz.",
        "Səhifə tapılmadı",
        "Axtardığınız səhifə mövcud deyil.",
        body,
    )


PAGES_FOR_SITEMAP = [
    ("", "1.0", "weekly"),
    ("xidmetler.html", "0.9", "monthly"),
    ("tarifler.html", "0.9", "monthly"),
    ("izleme.html", "0.8", "monthly"),
    ("sifaris.html", "0.8", "monthly"),
    ("filiallar.html", "0.7", "monthly"),
    ("haqqimizda.html", "0.6", "yearly"),
    ("elaqe.html", "0.7", "yearly"),
    ("mexfilik.html", "0.3", "yearly"),
]


def write_seo_files() -> None:
    """A robots.txt and sitemap that list what actually exists.

    Several audited sites shipped a sitemap naming pages that 404, or a robots.txt
    pointing at a sitemap that was never uploaded. Generating both from the page
    list is what keeps that from happening here.
    """
    robots = f"""User-agent: *
Allow: /

Sitemap: {render.SITE_URL}sitemap.xml
"""
    (render.ROOT / "robots.txt").write_text(robots, encoding="utf-8")

    urls = "\n".join(
        f"""  <url>
    <loc>{render.SITE_URL}{slug}</loc>
    <lastmod>2026-08-27</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>"""
        for slug, prio, freq in PAGES_FOR_SITEMAP
    )
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""
    (render.ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"  {'robots.txt':22s} {len(robots):>6d} bytes")
    print(f"  {'sitemap.xml':22s} {len(sitemap):>6d} bytes")


def main() -> None:
    print("Building pages:")
    write_data_js()
    build_tariffs()
    build_tracking()
    build_order()
    build_services()
    build_branches()
    build_about()
    build_contact()
    build_privacy()
    build_404()
    write_seo_files()
    print("Done.")


if __name__ == "__main__":
    main()
