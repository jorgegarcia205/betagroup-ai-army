"""
Sanitized excerpt: legal-standing verification via RUES (rues.org.co).

A browser SOLDIER checks whether a company (by NIT / tax id) holds a valid RUP
(bidder registration) and — critically — its renewal date. The public site is
a JS app with fragile markup, so extraction is done with *resilient DOM walkers*
that look for meaning by structure rather than by brittle CSS selectors.

Two robustness ideas worth showing:
  1. Wait on a POSITIVE signal (the "registro de proponentes" panel actually
     appearing), not on the ABSENCE of something — absence is ambiguous and was
     the source of false negatives.
  2. Extract fields by walking label/value pairs and blacklisting boilerplate
     (logos, headers) instead of trusting a single selector.
"""
from __future__ import annotations

import re

# Boilerplate that must never be mistaken for a company name.
_BLACKLIST = {"RUES", "REGISTRO", "CONSULTA", "INICIO", "PROPONENTES"}


async def has_rup(page, timeout_s: int = 12) -> bool:
    """Positive-signal wait: True only if the proponentes panel actually renders.

    We poll for the panel instead of concluding 'no RUP' from a missing element,
    which previously produced false negatives on slow loads.
    """
    for _ in range(timeout_s * 2):
        appeared = await page.evaluate(
            "() => !!document.querySelector('[id*=\"proponente\"],"
            " [class*=\"registro-proponente\"]')"
        )
        if appeared:
            return True
        await page.wait_for_timeout(500)
    return False


async def extract_company_name(page) -> str | None:
    """Walk visible text nodes; take the first plausible company name that is
    not boilerplate (RUES logo/header)."""
    return await page.evaluate(
        """(blacklist) => {
            const els = [...document.querySelectorAll('h1,h2,h3,strong,.title')];
            for (const el of els) {
                const t = (el.textContent || '').trim();
                const up = t.toUpperCase();
                if (t.length >= 5 && !blacklist.some(b => up.includes(b))) return t;
            }
            return null;
        }""",
        list(_BLACKLIST),
    )


async def extract_renewal_date(page) -> str | None:
    """Find the renewal date by pairing its label with the adjacent value.

    Works whether the site uses <dt>/<dd>, table cells, or sibling divs — we
    search for the label text and read the nearest date-looking string.
    """
    raw = await page.evaluate(
        """() => {
            const wanted = ['renovaci', 'renovacion', 'fecha de renovaci'];
            const nodes = [...document.querySelectorAll('*')];
            for (const n of nodes) {
                const label = (n.textContent || '').toLowerCase();
                if (wanted.some(w => label.includes(w))) {
                    // read this node's + next sibling's text and let Python parse
                    return (n.textContent || '') + ' | ' +
                           (n.nextElementSibling?.textContent || '');
                }
            }
            return '';
        }"""
    )
    m = re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}", raw)
    return m.group(0) if m else None


def clean_nit(raw: str) -> str:
    """Normalize a NIT: digits only, drop the check digit if present."""
    digits = re.sub(r"\D", "", raw)
    return digits[:-1] if len(digits) == 10 else digits
