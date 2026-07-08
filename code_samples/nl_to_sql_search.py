"""
Sanitized excerpt: natural-language talent search.

A user types "civil engineer with 2 master's in engineering, 5+ years, Bogotá".
An LLM (pinned to a JSON-reliable model) parses it into a STRUCTURED filter
object; a deterministic SQL function does the retrieval. The LLM only produces a
validated filter — it never touches the data. This keeps the powerful-but-fuzzy
part (understanding) separate from the part that must be exact (retrieval).
"""
from __future__ import annotations

# The 8 SNIES knowledge areas the model is allowed to choose from.
SNIES_AREAS = [
    "Engineering, Architecture, Urbanism & Related",
    "Economics, Administration, Accounting & Related",
    "Social & Human Sciences",
    "Mathematics & Natural Sciences",
    # ... 4 more ...
]

PARSE_PROMPT = f"""Translate the user's talent query into JSON. Do NOT invent
filters the user did not ask for. For a postgraduate topic, pick EXACTLY one of
these knowledge areas: {SNIES_AREAS}. Return ONLY:
{{
  "profession": "<main profession or null>",
  "min_experience": <int>,
  "min_maestrias": <int>,
  "min_doctorados": <int>,
  "postgrado_area": "<one SNIES area or null>",
  "min_postgrados_area": <int>,
  "location": "<city or null>"
}}"""


async def parse_query(call_llm_json, query: str) -> dict:
    # Pin a JSON-reliable model: weaker models produced malformed JSON on
    # multi-filter queries, silently dropping constraints.
    return await call_llm_json(PARSE_PROMPT, query, provider="openai",
                               model="gpt-4o-mini", temperature=0.0)


def to_sql_params(parsed: dict, classify_title, limit: int = 200) -> dict:
    """Map the semantic parse onto the SQL function's parameters.

    `classify_title` reuses the SNIES taxonomy so 'civil engineer' becomes the
    canonical 'Civil Engineering' the database actually stores.
    """
    prof = classify_title(parsed.get("profession") or "")
    area = parsed.get("postgrado_area")
    n_area = int(parsed.get("min_postgrados_area") or 0)
    return {
        "p_profession_canonical": [prof["profession_canonical"]] if prof else None,
        "p_min_experience": int(parsed.get("min_experience") or 0),
        "p_min_maestrias": int(parsed.get("min_maestrias") or 0),
        "p_min_doctorados": int(parsed.get("min_doctorados") or 0),
        # "2 master's specifically in engineering" -> count within an area
        "p_maestria_area": area if n_area else None,
        "p_min_maestrias_area": n_area,
        "p_location": parsed.get("location"),
        "p_exclude_duplicates": True,   # never surface duplicate profiles
        "p_limit": limit,
    }


async def search(call_llm_json, run_sql_function, classify_title, query: str):
    parsed = await parse_query(call_llm_json, query)
    params = to_sql_params(parsed, classify_title)
    rows = await run_sql_function("search_talent_advanced", params)
    return parsed, rows   # return the parse too, to show the user "how I read it"
