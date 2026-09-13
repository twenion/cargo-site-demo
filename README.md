# Xəzər Ekspres — demo cargo site

A static site for an Azerbaijani courier company, built as a portfolio piece and
a sales demo. **The company is fictional** — no real business's name, branding or
content is used, and the site says so in its own footer.

**Live:** https://twenion.github.io/cargo-site-demo/

## The demo set

Four sales demos for Azerbaijani small businesses, deliberately different in
sector, palette **and shape** — a service site, a catalogue, a booking site and a
quote bench — so they read as four pieces of work rather than one template four
times. Each is a fictional business, holds itself to the same audit checklist,
and ships as static files with no framework and no CDN.

| | | |
| --- | --- | --- |
| `cargo-site-demo` **← you are here** | Xəzər Ekspres — Courier | Tracking, tariffs and an order form — a dark, service-shaped site |
| [`ecommerce-site-demo`](https://github.com/twenion/ecommerce-site-demo) | Zərrə — Skincare retail | 24 products, cart and checkout — a light, catalogue-shaped site · [live](https://twenion.github.io/ecommerce-site-demo/) |
| [`hotel-site-demo`](https://github.com/twenion/hotel-site-demo) | Qırx Pəncərə — Şəki guesthouse | 365 published nightly prices and a booking form — a calendar-shaped site · [live](https://twenion.github.io/hotel-site-demo/) |
| [`manufacturing-site-demo`](https://github.com/twenion/manufacturing-site-demo) | Kəsim — Metal fabrication | A live quote calculator over a sheet-nesting model — a calculator-shaped site · [live](https://twenion.github.io/manufacturing-site-demo/) |

## Why it exists

I audit small-business websites in Azerbaijan. The same faults keep turning up:
an email link written `mail:` instead of `mailto:` so nothing opens, 72 of 84
images with an empty `alt`, no `<h1>`, a sitemap listing pages that 404, WordPress
placeholder posts still live years later. A courier site with none of the three
things a courier customer actually needs — tracking, prices, an order form.

Telling a client that is easier when you can show what the alternative looks like.

## The bar it is held to

The site has to pass the same checklist I run against client sites, so
`tools/audit.py` runs those checks against this repository:

| Check | |
| --- | --- |
| `<html lang="az">` | on every page |
| `<h1>` | exactly one, naming the page's subject rather than the brand |
| `alt` | present on every image; missing and empty counted as different faults |
| `<title>` / meta description | present, sensible length, unique across pages |
| Open Graph | all five tags, and `og:image` must be a file that exists |
| Canonical | on every page |
| JSON-LD | LocalBusiness, WebSite, FAQPage, BreadcrumbList — and it must parse |
| Protocol links | `mailto:` and `tel:` well-formed; `mail:`-style typos rejected |
| Internal links | every `.html` target exists |
| Assets | every referenced file exists |
| Placeholder text | no lorem ipsum, no "Salam dünya", no TODO left live |
| `robots.txt` / `sitemap.xml` | present, and the sitemap names only real pages |

```bash
python3 tools/audit.py   # exit 1 if anything fails
```

I verified the audit by injecting six faults and checking all six were caught. It
found a real one on its first run: every page pointed `og:image` at a file that
did not exist yet.

## Build

There is no build step at runtime — the site is HTML, CSS and vanilla JS, and it
runs from a folder with no server and no network. Two scripts help while working:

```bash
python3 tools/build_pages.py   # regenerate the inner pages, data.js, robots.txt, sitemap.xml
python3 tools/audit.py         # run the checklist
```

`tools/render.py` lifts the header and footer straight out of `index.html`, so a
nav link exists in one place rather than nine. Tariff numbers live in
`tools/build_pages.py` and produce both the table on `tarifler.html` and the
`data.js` the calculator reads — the quoted price cannot disagree with the
published one.

## Decisions worth naming

- **No CDN, no framework.** A client should be able to take the folder and host it
  anywhere. Nothing renders on a third-party request.
- **Inter, subset and self-hosted.** Latin plus Azerbaijani (Ə ə Ğ ğ İ ı Ş ş Ç ç
  Ö ö Ü ü) and the manat sign: 63 KB instead of 352 KB.
- **JS enhances, never builds.** Header and footer are in the markup. With script
  off, the nav is a plain list, the tracking box is a GET form that still reaches
  the tracking page, and the calculator points at the tariff table.
- **The forms admit they are a demo.** They validate properly in Azerbaijani and
  then say nothing was sent, rather than faking a submission a visitor only
  discovers when no courier arrives.
- **One photograph.** Most logistics stock photos carry the giveaways of somewhere
  else — Korean number plates, IKEA signage — which on an Azerbaijani courier's
  site reads as borrowed. The one used is night-time and motion-blurred, with no
  legible text or plate.

## Credits

Photograph from [Unsplash](https://unsplash.com/photos/a-van-driving-down-a-street-at-night-33e966c4c274)
(Unsplash License). Typeface: [Inter](https://rsms.me/inter/) by Rasmus Andersson
(SIL Open Font License 1.1).
