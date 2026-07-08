"""
Sanitized excerpt: rule-based classifier mapping messy, free-text profession /
degree strings onto Colombia's official SNIES higher-education taxonomy
(8 knowledge areas -> nucleo basico -> canonical profession).

On a real corpus of 50,044 resumes this covered 99.4% of records with rules
alone (no LLM cost); the long tail is reserved for an LLM pass. The full rule
table (~90 entries) is trimmed here for illustration.
"""
from __future__ import annotations

import re
import unicodedata

# The 8 official SNIES knowledge areas (labels abbreviated here).
AREA_ENG = "Engineering, Architecture, Urbanism & Related"
AREA_ECON = "Economics, Administration, Accounting & Related"
AREA_SOCIAL = "Social & Human Sciences"
AREA_MATH = "Mathematics & Natural Sciences"


def normalize_text(text: str | None) -> str:
    """UPPERCASE, strip accents, Ñ->N, collapse to [A-Z0-9 ]."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.upper().replace("Ñ", "N")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", t)).strip()


# (required_keywords, canonical_profession, nucleo_basico, knowledge_area).
# Evaluated IN ORDER; first rule whose keywords are ALL present wins.
# Specific rules precede generic ones to avoid false positives, e.g.
# "Administration of Civil Works" must not match on "CIVIL" -> Civil Eng.
RULES: list[tuple[list[str], str, str, str]] = [
    (["OBRAS", "CIVILES"], "Civil Works Administration", "Civil Eng. & Related", AREA_ENG),
    (["CIVIL"],            "Civil Engineering",          "Civil Eng. & Related", AREA_ENG),
    (["SISTEMAS"],         "Systems Engineering",        "Systems/IT Eng. & Related", AREA_ENG),
    (["INDUSTRIAL"],       "Industrial Engineering",     "Industrial Eng. & Related", AREA_ENG),
    (["ECONOM"],           "Economics",                  "Economics", AREA_ECON),   # ECONOMIA / ECONOMISTA
    (["CONTAD"],           "Public Accounting",          "Accounting", AREA_ECON),
    (["ADMINISTRA"],       "Business Administration",    "Administration", AREA_ECON),
    (["DERECHO"],          "Law",                        "Law & Related", AREA_SOCIAL),
    (["ABOGAD"],           "Law",                        "Law & Related", AREA_SOCIAL),
    (["PSICOLOG"],         "Psychology",                 "Psychology", AREA_SOCIAL),
    (["ESTADISTIC"],       "Statistics",                 "Mathematics, Statistics & Related", AREA_MATH),
    # ... ~80 more rules across all 8 areas ...
]


def classify_title(raw: str | None) -> dict | None:
    """Map a free-text title to (canonical, nucleo_basico, area), or None.

    Using word ROOTS (e.g. 'ECONOM') rather than exact forms is what lets the
    same table classify both the corpus values ('ECONOMIA') and natural-language
    queries ('economista', 'economist').
    """
    n = normalize_text(raw)
    if not n:
        return None
    for keywords, canonical, nbc, area in RULES:
        if all(kw in n for kw in keywords):
            return {"profession_canonical": canonical,
                    "snies_nbc": nbc, "snies_area": area}
    return None


if __name__ == "__main__":
    for q in ["Ingeniería Civil", "economista", "ABOGADO",
              "Administración de Obras Civiles"]:
        print(f"{q:32} -> {classify_title(q)}")
