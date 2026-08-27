#!/usr/bin/env python3
"""Run our own audit checklist against this site.

We sell clients a report saying their site has no H1, empty alt text and a
`mail:` link that cannot open. The demo has to survive the same checks, so they
run here as a script rather than as good intentions.

    python3 tools/audit.py

Exit code is 1 if anything failed, so CI can gate on it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.glob("*.html"))

FAIL: list[str] = []
WARN: list[str] = []


def fail(page: str, msg: str) -> None:
    FAIL.append(f"{page}: {msg}")


def warn(page: str, msg: str) -> None:
    WARN.append(f"{page}: {msg}")


def find_all(pattern: str, text: str) -> list[str]:
    return re.findall(pattern, text, re.I | re.S)


def check_page(path: Path, titles: dict, descriptions: dict) -> None:
    name = path.name
    html = path.read_text(encoding="utf-8")

    # 1. lang
    if not re.search(r'<html[^>]*\blang="az"', html, re.I):
        fail(name, 'html lang="az" yoxdur')

    # 2. title, unique
    title = find_all(r"<title>(.*?)</title>", html)
    if not title:
        fail(name, "title yoxdur")
    else:
        t = title[0].strip()
        if len(t) < 15:
            warn(name, f"title çox qısa ({len(t)} simvol)")
        if len(t) > 70:
            warn(name, f"title çox uzun ({len(t)} simvol)")
        titles.setdefault(t, []).append(name)

    # 3. meta description, unique
    desc = find_all(r'<meta\s+name="description"\s+content="(.*?)"', html)
    if not desc:
        fail(name, "meta description yoxdur")
    else:
        d = desc[0].strip()
        if len(d) < 70:
            warn(name, f"meta description qısa ({len(d)} simvol)")
        if len(d) > 200:
            warn(name, f"meta description uzun ({len(d)} simvol)")
        descriptions.setdefault(d, []).append(name)

    # 4. exactly one h1, and it is not just the brand
    h1s = find_all(r"<h1[^>]*>(.*?)</h1>", html)
    if len(h1s) != 1:
        fail(name, f"h1 sayı {len(h1s)} (1 olmalıdır)")
    elif re.sub(r"<[^>]+>", "", h1s[0]).strip().lower() == "xəzər ekspres":
        fail(name, "h1 yalnız brend adıdır, səhifənin mövzusu deyil")

    # 5. images: missing alt vs empty alt are different problems
    for tag in find_all(r"<img\b[^>]*>", html):
        if not re.search(r"\balt=", tag, re.I):
            fail(name, f"img-də alt atributu yoxdur: {tag[:70]}")
        elif re.search(r'\balt=""', tag, re.I) and "aria-hidden" not in tag.lower():
            warn(name, f"boş alt, aria-hidden yoxdur: {tag[:70]}")

    # 6. Open Graph — cargo links get shared in WhatsApp
    for prop in ("og:title", "og:description", "og:image", "og:url", "og:type"):
        if f'property="{prop}"' not in html:
            fail(name, f"{prop} yoxdur")

    # 6b. og:image has to be a file that exists, not just a URL that looks right
    for img_url in find_all(r'<meta\s+property="og:image"\s+content="(.*?)"', html):
        tail = img_url.split("cargo-site-demo/")[-1]
        if tail.startswith("assets/") and not (ROOT / tail).exists():
            fail(name, f"og:image faylı yoxdur: {tail}")

    # 7. canonical
    if 'rel="canonical"' not in html:
        fail(name, "canonical yoxdur")

    # 8. JSON-LD must parse
    for block in find_all(r'<script type="application/ld\+json">(.*?)</script>', html):
        try:
            json.loads(block)
        except json.JSONDecodeError as e:
            fail(name, f"JSON-LD parse olunmur: {e}")

    # 9. broken protocol links — courierbaku shipped `mail:` instead of `mailto:`
    for bad in find_all(r'href="(mail:[^"]*|telephone:[^"]*|tel :[^"]*)"', html):
        fail(name, f"yanlış protokol: {bad}")
    for href in find_all(r'href="(mailto:[^"]*)"', html):
        if "@" not in href:
            fail(name, f"mailto ünvansızdır: {href}")
    for href in find_all(r'href="(tel:[^"]*)"', html):
        if not re.match(r"^tel:\+?[0-9]{6,}$", href):
            fail(name, f"tel linki rəqəmsizdir və ya boşluqludur: {href}")

    # 10. internal links must point at files that exist
    for href in find_all(r'href="([^"#?:]+\.html)[^"]*"', html):
        if not (ROOT / href).exists():
            fail(name, f"ölü daxili link: {href}")

    # 11. assets referenced must exist
    for src in find_all(r'(?:src|href)="(assets/[^"]+)"', html):
        if not (ROOT / src).exists():
            fail(name, f"tapılmayan fayl: {src}")

    # 12. placeholder content left live — suruculukmektebi still ships "Salam dünya!"
    for needle in ("lorem ipsum", "salam dünya", "hello world", "TODO", "FIXME", "xxxxx"):
        if needle.lower() in html.lower():
            fail(name, f"placeholder məzmun qalıb: {needle}")

    # 13. skip link, for keyboard users
    if 'class="skip-link"' not in html:
        warn(name, "skip-link yoxdur")


def check_site() -> None:
    # robots.txt and sitemap must exist and agree with reality
    robots = ROOT / "robots.txt"
    sitemap = ROOT / "sitemap.xml"
    if not robots.exists():
        fail("robots.txt", "yoxdur")
    elif "Sitemap:" not in robots.read_text(encoding="utf-8"):
        fail("robots.txt", "Sitemap sətri yoxdur")

    if not sitemap.exists():
        fail("sitemap.xml", "yoxdur")
    else:
        xml = sitemap.read_text(encoding="utf-8")
        for loc in re.findall(r"<loc>(.*?)</loc>", xml):
            slug = loc.rstrip("/").split("/")[-1]
            if slug.endswith(".html") and not (ROOT / slug).exists():
                fail("sitemap.xml", f"mövcud olmayan səhifəyə işarə edir: {slug}")
        for page in PAGES:
            if page.name in ("404.html",):
                continue
            token = "/" if page.name == "index.html" else page.name
            if token not in xml:
                warn("sitemap.xml", f"{page.name} sitemap-da yoxdur")


def main() -> int:
    titles: dict[str, list[str]] = {}
    descriptions: dict[str, list[str]] = {}

    for page in PAGES:
        check_page(page, titles, descriptions)
    check_site()

    for t, pages in titles.items():
        if len(pages) > 1:
            fail(", ".join(pages), f"eyni title paylaşır: {t[:50]}")
    for d, pages in descriptions.items():
        if len(pages) > 1:
            fail(", ".join(pages), f"eyni meta description paylaşır: {d[:50]}")

    print(f"Checked {len(PAGES)} pages.\n")
    if WARN:
        print(f"WARN ({len(WARN)}):")
        for w in WARN:
            print(f"  ! {w}")
        print()
    if FAIL:
        print(f"FAIL ({len(FAIL)}):")
        for f in FAIL:
            print(f"  x {f}")
        return 1

    print("PASS — every check on our own list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
