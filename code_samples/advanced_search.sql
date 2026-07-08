-- Sanitized excerpt: the SQL function behind natural-language & advanced talent
-- search. It runs the array/JSONB-heavy predicates IN THE DATABASE, which the
-- REST client cannot express cleanly, and keeps retrieval deterministic.
--
-- The interesting part is the last predicate: "at least N master's degrees in a
-- specific SNIES knowledge area" is answered by counting matching entries inside
-- the normalized education JSONB array — so a query like "civil engineer with 2
-- master's in engineering" is a single, indexed SQL call.

CREATE OR REPLACE FUNCTION search_talent_advanced(
    p_profession_canonical      text[]  DEFAULT NULL,
    p_snies_area                text[]  DEFAULT NULL,
    p_min_experience            numeric DEFAULT 0,
    p_education_level_canonical text    DEFAULT NULL,
    p_min_maestrias             int     DEFAULT 0,
    p_min_doctorados            int     DEFAULT 0,
    p_maestria_area             text    DEFAULT NULL,   -- master's in THIS area
    p_min_maestrias_area        int     DEFAULT 0,
    p_location                  text    DEFAULT NULL,
    p_exclude_duplicates        boolean DEFAULT true,
    p_limit                     int     DEFAULT 500
)
RETURNS SETOF talent_candidates
LANGUAGE sql STABLE
AS $$
    SELECT tc.*
    FROM talent_candidates tc
    WHERE (p_profession_canonical IS NULL OR tc.profession_canonical = ANY(p_profession_canonical))
      AND (p_snies_area IS NULL OR tc.snies_area = ANY(p_snies_area))
      AND (COALESCE(tc.experience_years, 0) >= COALESCE(p_min_experience, 0))
      AND (p_education_level_canonical IS NULL OR tc.education_level_canonical = p_education_level_canonical)
      AND (COALESCE(tc.maestria_count, 0)  >= COALESCE(p_min_maestrias, 0))
      AND (COALESCE(tc.doctorado_count, 0) >= COALESCE(p_min_doctorados, 0))
      AND (p_location IS NULL OR tc.location ILIKE '%' || p_location || '%')
      AND (NOT p_exclude_duplicates OR COALESCE(tc.is_duplicate, false) = false)
      -- "N master's degrees whose knowledge area is X": count inside the JSONB
      AND (
          p_maestria_area IS NULL
          OR (
              SELECT COUNT(*)
              FROM jsonb_array_elements(COALESCE(tc.education_normalized, '[]'::jsonb)) e
              WHERE e->>'nivel'      = 'Maestría'
                AND e->>'snies_area' = p_maestria_area
          ) >= COALESCE(p_min_maestrias_area, 0)
      )
    ORDER BY tc.experience_years DESC NULLS LAST
    LIMIT COALESCE(p_limit, 500);
$$;
