#!/usr/bin/env python3
"""Build the inner pages from the shell that index.html already defines.

The site ships as plain HTML with no build step -- this script is a development
aid, not a runtime dependency. It exists because the header and footer appear on
nine pages: editing a nav link by hand nine times is how a dead link gets into a
site, which is one of the things we bill clients to find.

index.html is the single source for the shell. Run from the project root:

    python3 tools/render.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
SITE_URL = "https://twenion.github.io/cargo-site-demo/"


def slice_between(text: str, start: str, end: str, what: str) -> str:
    i = text.find(start)
    j = text.find(end, i)
    if i == -1 or j == -1:
        sys.exit(f"render.py: could not find the {what} block in index.html")
    return text[i : j + len(end)]


def shell() -> tuple[str, str]:
    html = INDEX.read_text(encoding="utf-8")
    header = slice_between(html, '    <header class="site-header">', "    </header>", "header")
    footer = slice_between(html, '    <footer class="site-footer">', "    </footer>", "footer")
    return header, footer


def head(title: str, description: str, slug: str, og_title: str, og_desc: str, jsonld: str = "") -> str:
    url = SITE_URL + ("" if slug == "index.html" else slug)
    block = f"""<!doctype html>
<html lang="az" class="no-js">
  <head>
    <meta charset="utf-8" />
    <!-- Drops the no-js class before first paint, so the menu never flashes open. -->
    <script>document.documentElement.classList.remove("no-js");</script>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <meta name="description" content="{description}" />
    <link rel="canonical" href="{url}" />
    <link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml" />
    <link rel="stylesheet" href="assets/css/style.css" />

    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="Xəzər Ekspres" />
    <meta property="og:locale" content="az_AZ" />
    <meta property="og:title" content="{og_title}" />
    <meta property="og:description" content="{og_desc}" />
    <meta property="og:image" content="{SITE_URL}assets/img/og-cover.png" />
    <meta property="og:url" content="{url}" />
    <meta name="twitter:card" content="summary_large_image" />
"""
    if jsonld:
        block += f'\n    <script type="application/ld+json">\n{jsonld}\n    </script>\n'
    block += "  </head>\n"
    return block


def breadcrumbs(slug: str, label: str) -> str:
    """Every inner page says where it sits, so search results show a path."""
    return (
        "      {\n"
        '        "@context": "https://schema.org",\n'
        '        "@type": "BreadcrumbList",\n'
        '        "itemListElement": [\n'
        '          { "@type": "ListItem", "position": 1, "name": "Ana səhifə", "item": "'
        + SITE_URL
        + '" },\n'
        '          { "@type": "ListItem", "position": 2, "name": "'
        + label
        + '", "item": "'
        + SITE_URL
        + slug
        + '" }\n'
        "        ]\n"
        "      }"
    )


def write(slug: str, title: str, description: str, og_title: str, og_desc: str, body: str, jsonld: str = "") -> None:
    header, footer = shell()
    # The nav marks whichever page is being rendered.
    header = header.replace(' aria-current="page"', "")
    header = header.replace(f'href="{slug}"', f'href="{slug}" aria-current="page"', 1)

    page = head(title, description, slug, og_title, og_desc, jsonld)
    page += '\n  <body>\n    <a class="skip-link" href="#main">Əsas məzmuna keç</a>\n\n'
    page += header + "\n\n"
    page += body.rstrip() + "\n\n"
    page += footer + "\n\n"
    page += '    <script src="assets/js/data.js" defer></script>\n'
    page += '    <script src="assets/js/site.js" defer></script>\n'
    page += "  </body>\n</html>\n"

    (ROOT / slug).write_text(page, encoding="utf-8")
    print(f"  {slug:22s} {len(page):>6d} bytes")
