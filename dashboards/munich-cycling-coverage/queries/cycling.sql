-- per-district cycling supply: weighted network km per 1,000 activity (year Y, w) and per km2, both against the city average
-- connectors (Übergang, Anschlussabschnitt) and Dummy segments excluded; two-way paths count x2; weights are assumptions (0-1)
WITH seg AS (
    SELECT "district_no" AS district_no, "length_m" AS length_m,
           REPLACE("path_type", ' (Zweirichtungsradweg)', '') AS base_type,
           CASE WHEN INSTR("path_type", '(Zweirichtungsradweg)') > 0 THEN 2 ELSE 1 END AS dir_factor
    FROM MUNICH_DATASET.CYCLING_INFRASTRUCTURE
    WHERE "path_type" NOT IN ('Dummy', 'Übergang', 'Anschlussabschnitt') AND "district_no" IS NOT NULL
),
segw AS (
    SELECT district_no, length_m, dir_factor, base_type,
           CASE base_type WHEN 'Radweg' THEN {w_radweg!f}
                          WHEN 'Fahrradstraße' THEN {w_fahrradstrasse!f}
                          WHEN 'Getrennter Rad- und Gehweg' THEN {w_getrennt!f}
                          WHEN 'Radfahr-/Schutzstreifen' THEN {w_streifen!f}
                          WHEN 'Gemeinsamer Geh- und Radweg' THEN {w_gemeinsam!f}
                          WHEN 'Gehweg Radverkehr frei' THEN {w_gehweg!f}
                          ELSE 0 END AS weight,
           CASE WHEN base_type IN ('Radweg', 'Fahrradstraße', 'Getrennter Rad- und Gehweg') THEN 1 ELSE 0 END AS high_quality
    FROM seg
),
net AS (
    SELECT district_no,
           SUM(length_m * dir_factor * weight) / 1000.0 AS weighted_km,
           SUM(length_m) / 1000.0 AS raw_km,
           SUM(length_m * dir_factor) / 1000.0 AS dir_km,
           SUM(length_m * dir_factor * high_quality) / 1000.0 AS hq_km,
           COUNT(*) AS segments
    FROM segw GROUP BY district_no
),
dem AS (
    -- residents: linear interpolation 2024 -> 2045 forecast, jobs: 2022 estimate as the 2024 baseline -> 2040 forecast, held after 2040
    SELECT d."district_no" AS district_no, d."district_name" AS district, d."area_km2" AS area_km2,
           p."pop_2024" + (p."pop_2045_forecast" - p."pop_2024") * ({year!d} - 2024) / 21.0 AS pop_y,
           e."jobs_2022" + (e."jobs_2040_forecast" - e."jobs_2022") * (LEAST({year!d}, 2040) - 2024) / 16.0 AS jobs_y,
           p."pop_2024" AS pop_24,
           e."jobs_2022" AS jobs_24
    FROM MUNICH_DATASET.DISTRICTS d
    JOIN MUNICH_DATASET.DISTRICT_POPULATION p ON p."district_no" = d."district_no"
    JOIN MUNICH_DATASET.DISTRICT_EMPLOYMENT e ON e."district_no" = d."district_no"
),
m AS (
    SELECT dem.district_no, dem.district, dem.area_km2, dem.pop_y AS population, dem.jobs_y AS jobs,
           dem.pop_y + {w_jobs!f} * dem.jobs_y AS activity,
           dem.pop_24 + {w_jobs!f} * dem.jobs_24 AS activity_24,
           (dem.pop_y + {w_jobs!f} * dem.jobs_y) / dem.area_km2 AS activity_per_km2,
           COALESCE(net.weighted_km, 0) AS weighted_km, COALESCE(net.raw_km, 0) AS raw_km, COALESCE(net.dir_km, 0) AS dir_km,
           COALESCE(net.hq_km, 0) AS hq_km, COALESCE(net.segments, 0) AS segments
    FROM dem LEFT JOIN net ON net.district_no = dem.district_no
),
r AS (
    SELECT m.*,
           1000.0 * weighted_km / activity AS km_per_1k_act,
           1000.0 * weighted_km / activity_24 AS km_per_1k_act_24,
           weighted_km / area_km2 AS km_per_km2,
           1000.0 * SUM(weighted_km) OVER () / SUM(activity_24) OVER () AS city_km_per_1k_act_24,
           1000.0 * SUM(weighted_km) OVER () / SUM(activity) OVER () AS city_km_per_1k_act,
           SUM(weighted_km) OVER () / SUM(area_km2) OVER () AS city_km_per_km2,
           SUM(weighted_km) OVER () AS city_weighted_km, SUM(raw_km) OVER () AS city_raw_km,
           NTILE(3) OVER (ORDER BY activity_per_km2 DESC, population DESC) AS act_t
    FROM m
)
SELECT district_no, district, ROUND(population) AS population, ROUND(jobs) AS jobs, ROUND(activity) AS activity,
       ROUND(area_km2, 2) AS area_km2, ROUND(activity_per_km2) AS activity_per_km2,
       ROUND(weighted_km, 2) AS weighted_km, ROUND(raw_km, 2) AS raw_km, ROUND(dir_km, 2) AS dir_km, segments,
       ROUND(km_per_1k_act, 4) AS km_per_1k_act, ROUND(km_per_1k_act_24, 4) AS km_per_1k_act_2024,
       ROUND(1000 * km_per_km2) AS m_per_km2,
       ROUND(100 * hq_km / NULLIF(dir_km, 0), 1) AS hq_share_pct,
       ROUND(km_per_1k_act / city_km_per_1k_act_24, 3) AS ratio_person,
       ROUND(km_per_1k_act_24 / city_km_per_1k_act_24, 3) AS ratio_person_2024,
       ROUND(km_per_km2 / city_km_per_km2, 3) AS ratio_area,
       ROUND(100 * (km_per_1k_act / km_per_1k_act_24 - 1), 1) AS pct_change_person,
       ROUND(city_km_per_1k_act_24, 4) AS city_km_per_1k_act_2024, ROUND(city_km_per_1k_act, 4) AS city_km_per_1k_act,
       ROUND(1000 * city_km_per_km2) AS city_m_per_km2, ROUND(city_weighted_km, 1) AS city_weighted_km, ROUND(city_raw_km, 1) AS city_raw_km,
       CASE WHEN act_t = 1 THEN 1 ELSE 0 END AS is_dense,
       {year!d} AS year_n
FROM r
ORDER BY ratio_person
