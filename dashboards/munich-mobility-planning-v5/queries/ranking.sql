WITH feed AS (
    SELECT MIN("start_date") AS f_start, MAX("end_date") AS f_end FROM MUNICH_DATASET.MVV_CALENDAR
),
base AS (SELECT LEAST(GREATEST(DATE '2026-10-21', f_start), ADD_DAYS(f_end, -6)) AS b FROM feed),  -- reference weekday pinned: Wed 21 Oct 2026
rd AS (SELECT ADD_DAYS(b, MOD(7 - MOD(DAYS_BETWEEN(b, DATE '1970-01-07'), 7), 7)) AS ref_date FROM base),
svc AS (
    SELECT c."service_id" FROM MUNICH_DATASET.MVV_CALENDAR c CROSS JOIN rd
    WHERE c."wednesday" = 1 AND rd.ref_date BETWEEN c."start_date" AND c."end_date"
      AND c."service_id" NOT IN (SELECT x."service_id" FROM MUNICH_DATASET.MVV_CALENDAR_DATES x CROSS JOIN rd r2
                                 WHERE x."date" = r2.ref_date AND x."exception_type" = 2)
    UNION
    SELECT x."service_id" FROM MUNICH_DATASET.MVV_CALENDAR_DATES x CROSS JOIN rd
    WHERE x."date" = rd.ref_date AND x."exception_type" = 1
),
lines AS (
    SELECT r."route_id", r."route_short_name" AS line, COALESCE(lc."capacity_per_trip", v."capacity_per_trip") AS capacity
    FROM MUNICH_DATASET.MVV_ROUTES r
    JOIN MUNICH_DATASET.VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode"
    LEFT JOIN MUNICH_DATASET.LINE_CAPACITY lc ON lc."line" = r."route_short_name" AND lc."line_mode" = r."line_mode"
),
wt AS (
    SELECT t."trip_id", l.line, l.capacity
    FROM MUNICH_DATASET.MVV_TRIPS t JOIN svc ON svc."service_id" = t."service_id"
    JOIN lines l ON l."route_id" = t."route_id"
),
need AS (
    -- lines whose current service is used: analog lines, plus every S-Bahn line (2nd trunk 15-minute basic interval, Laim restore)
    SELECT DISTINCT "mode" AS line_mode, "analog_line" AS line FROM MUNICH_DATASET.PT_PROJECT_STATIONS
    WHERE "analog_line" IS NOT NULL AND INSTR("analog_line", ',') = 0
    UNION SELECT DISTINCT "line_mode", "route_short_name" FROM MUNICH_DATASET.MVV_ROUTES WHERE "line_mode" = 'S-Bahn'
),
pl AS (
    SELECT r."route_id", r."line_mode" AS line_mode, r."route_short_name" AS line,
           COALESCE(lc."capacity_per_trip", v."capacity_per_trip") AS capacity
    FROM MUNICH_DATASET.MVV_ROUTES r
    JOIN need ON need.line_mode = r."line_mode" AND need.line = r."route_short_name"
    JOIN MUNICH_DATASET.VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode"
    LEFT JOIN MUNICH_DATASET.LINE_CAPACITY lc ON lc."line" = r."route_short_name" AND lc."line_mode" = r."line_mode"
),
ev_sel AS (
    SELECT pl.line_mode, pl.line, pl.capacity, t."direction_id" AS dir, s."district_no" AS district_no, s."in_munich" AS in_munich,
           COALESCE(s."parent_station", s."stop_id") AS station_id
    FROM MUNICH_DATASET.MVV_TRIPS t
    JOIN svc ON svc."service_id" = t."service_id"
    JOIN pl ON pl."route_id" = t."route_id"
    JOIN MUNICH_DATASET.MVV_STOP_TIMES st ON st."trip_id" = t."trip_id"
    JOIN MUNICH_DATASET.MVV_STOPS s ON s."stop_id" = st."stop_id"
),
ana AS (
    -- rule 1b: the analog line's mean weekday departures per station inside Munich on the reference Wednesday
    SELECT line_mode, line, 1.0 * COUNT(*) / COUNT(DISTINCT station_id) AS dep_per_station
    FROM ev_sel WHERE in_munich = 1 GROUP BY line_mode, line
),
laim AS (
    -- rule 3: restored inbound departures at Laim = current outbound minus current inbound, per line
    SELECT line, SUM(CASE WHEN dir = 1 THEN 1 ELSE 0 END) - SUM(CASE WHEN dir = 0 THEN 1 ELSE 0 END) AS restored_dep
    FROM ev_sel WHERE station_id = 'de:09162:9' AND line_mode = 'S-Bahn' GROUP BY line
),
sb AS (
    -- 2nd trunk, 15-minute basic interval: today's departures per S-Bahn line and station inside Munich,
    -- all lines except S2, S7 and S20 (Landtag 17/17196, 2017) and S5 (later reinforcement line, not in that concept)
    SELECT line, station_id, MIN(district_no) AS district_no, MIN(capacity) AS capacity, COUNT(*) AS dep_today
    FROM ev_sel WHERE line_mode = 'S-Bahn' AND in_munich = 1 AND line NOT IN ('S2', 'S5', 'S7', 'S20')
    GROUP BY line, station_id
),
ps AS (
    -- rule 2: capacity per trip of the project line (LINE_CAPACITY override, else VEHICLE_CAPACITY by mode)
    SELECT p.*, COALESCE(lc."capacity_per_trip", v."capacity_per_trip") AS capacity
    FROM MUNICH_DATASET.PT_PROJECT_STATIONS p
    JOIN MUNICH_DATASET.VEHICLE_CAPACITY v ON v."line_mode" = p."mode"
    LEFT JOIN MUNICH_DATASET.LINE_CAPACITY lc ON lc."line" = p."line" AND lc."line_mode" = p."mode"
    WHERE p."district_no" IS NOT NULL AND p."station_name" <> 'unknown'
),
pmeta AS (
    SELECT "project_id" AS project_id, MIN("opening_year_model") AS oy_model, MIN("opening_year_risk") AS oy_risk
    FROM MUNICH_DATASET.PT_PROJECT_STATIONS GROUP BY "project_id"
),
comps AS (
    -- rule 1a: published frequency: (tph_peak x 6 + tph_offpeak x 13) x 2 directions, peak falls back to off-peak
    SELECT ps."project_id" AS project_id, 'added' AS comp_kind, ps."district_no" AS district_no, ps."station_name" AS station_name,
           ps."lat" AS lat, ps."lon" AS lon, ps."station_is_new" AS station_is_new, ps."mode" AS line_mode, ps."line" AS line,
           CASE WHEN ps."project_id" = 'laim_inbound_restore' THEN 'proxy: outbound departures at Laim'
                WHEN COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") IS NOT NULL THEN 'frequency'
                WHEN ana.dep_per_station IS NOT NULL THEN 'analog ' || ps."analog_line"
                ELSE 'none (no frequency or analog)' END AS calc_method,
           COALESCE(CASE WHEN ps."project_id" = 'laim_inbound_restore' THEN laim.restored_dep
                         WHEN COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") IS NOT NULL
                           THEN (COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") * 6
                                 + COALESCE(ps."trains_per_hour_offpeak", ps."trains_per_hour_peak") * 13) * 2
                         ELSE ana.dep_per_station END, 0) AS departures,
           ps.capacity AS capacity, CAST(NULL AS VARCHAR(100)) AS requires_project
    FROM ps
    LEFT JOIN laim ON ps."project_id" = 'laim_inbound_restore' AND laim.line = ps."line"
    LEFT JOIN ana ON ana.line_mode = ps."mode" AND ana.line = ps."analog_line"
    UNION ALL
    -- rule 4: 2nd trunk = new-tunnel trains (above) plus a 15-minute basic interval; nothing removed from the old trunk (slots reused).
    -- every station a non-excluded S-Bahn line serves today: departures_new = GREATEST(departures_today, 152) = 4/h x 19 h x 2 directions
    SELECT 'stammstrecke2', 'upgraded: 15-minute basic interval', sb.district_no, sb.station_id, NULL, NULL, NULL, 'S-Bahn', sb.line,
           '15-min basic interval: GREATEST(today, 152)', GREATEST(sb.dep_today, 152) - sb.dep_today, sb.capacity, NULL
    FROM sb WHERE sb.dep_today < 152
    UNION ALL
    -- with the Laim restore active, the 15-minute rule applies to the restored numbers (no double count at Laim)
    SELECT 'stammstrecke2', 'adjusted: 15-minute rule on restored Laim', sb.district_no, sb.station_id, NULL, NULL, NULL, 'S-Bahn', sb.line,
           '15-min basic interval after Laim restore',
           (GREATEST(sb.dep_today + laim.restored_dep, 152) - sb.dep_today - laim.restored_dep) - (GREATEST(sb.dep_today, 152) - sb.dep_today),
           sb.capacity, 'laim_inbound_restore'
    FROM sb JOIN laim ON laim.line = sb.line
    WHERE sb.station_id = 'de:09162:9'
      AND sb.line IN (SELECT "line" FROM MUNICH_DATASET.PT_PROJECT_STATIONS WHERE "project_id" = 'laim_inbound_restore')
),
sel AS (
    -- rule 5: a project counts only if switched on and the year has reached its opening year (risk year when pessimistic)
    SELECT c.district_no, SUM(c.departures) AS add_dep, SUM(c.departures * c.capacity) AS add_places,
           GROUP_CONCAT(DISTINCT c.project_id ORDER BY c.project_id SEPARATOR ',') AS active_projects
    FROM comps c
    JOIN pmeta m ON m.project_id = c.project_id
    LEFT JOIN pmeta rq ON rq.project_id = c.requires_project
    WHERE INSTR(',' || {projects!s} || ',', ',' || c.project_id || ',') > 0
      AND {year!d} >= CASE WHEN {pessimistic!d} = 1 THEN COALESCE(m.oy_risk, m.oy_model) ELSE m.oy_model END
      AND (c.requires_project IS NULL
           OR (INSTR(',' || {projects!s} || ',', ',' || c.requires_project || ',') > 0
               AND {year!d} >= CASE WHEN {pessimistic!d} = 1 THEN COALESCE(rq.oy_risk, rq.oy_model) ELSE rq.oy_model END))
    GROUP BY c.district_no
),
ex_raw AS (
    -- v5 what-if: extra places per weekday per district, passed as one string 'district_no:places;district_no:places'
    -- ('' = NULL = nothing added). Built by assistant.py from what_if(); counted in every year >= 2024.
    SELECT REGEXP_SUBSTR({extra!s}, '[^;]+', 1, LEVEL) AS item FROM DUAL CONNECT BY LEVEL <= 100
),
ex AS (
    SELECT CAST(SUBSTR(item, 1, INSTR(item, ':') - 1) AS DECIMAL(4, 0)) AS district_no,
           SUM(CAST(SUBSTR(item, INSTR(item, ':') + 1) AS DOUBLE)) AS add_places
    FROM ex_raw WHERE item IS NOT NULL AND {year!d} >= 2024
    GROUP BY CAST(SUBSTR(item, 1, INSTR(item, ':') - 1) AS DECIMAL(4, 0))
),
dep AS (
    SELECT s."district_no" AS dno, COUNT(*) AS departures, SUM(wt.capacity) AS places, COUNT(DISTINCT wt.line) AS n_lines
    FROM MUNICH_DATASET.MVV_STOP_TIMES st
    JOIN wt ON wt."trip_id" = st."trip_id"
    JOIN MUNICH_DATASET.MVV_STOPS s ON s."stop_id" = st."stop_id"
    WHERE s."in_munich" = 1
    GROUP BY s."district_no"
),
stp AS (
    SELECT "district_no" AS dno, COUNT(*) AS stops,
           COUNT(DISTINCT COALESCE("parent_station", "stop_id")) AS stations,
           SUM(CASE WHEN "stop_mode" = 'Bus' THEN 1 ELSE 0 END) AS bus_stops,
           SUM(CASE WHEN "stop_mode" = 'Tram' THEN 1 ELSE 0 END) AS tram_stops,
           SUM(CASE WHEN "stop_mode" = 'U-Bahn' THEN 1 ELSE 0 END) AS ubahn_stops,
           SUM(CASE WHEN "stop_mode" = 'S-Bahn' THEN 1 ELSE 0 END) AS sbahn_stops,
           SUM(CASE WHEN "stop_mode" = 'Regional rail' THEN 1 ELSE 0 END) AS rail_stops
    FROM MUNICH_DATASET.MVV_STOPS WHERE "in_munich" = 1 GROUP BY "district_no"
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
           dem.pop_y / dem.area_km2 AS residents_per_km2,
           dem.pop_y + {w_jobs!f} * dem.jobs_y AS activity,
           dem.pop_24 + {w_jobs!f} * dem.jobs_24 AS activity_24,
           (dem.pop_y + {w_jobs!f} * dem.jobs_y) / dem.area_km2 AS activity_per_km2,
           (dem.pop_24 + {w_jobs!f} * dem.jobs_24) / dem.area_km2 AS activity_per_km2_24,
           COALESCE(stp.stations, 0) AS stations, COALESCE(stp.bus_stops, 0) AS bus_stops, COALESCE(stp.tram_stops, 0) AS tram_stops,
           COALESCE(stp.ubahn_stops, 0) AS ubahn_stops, COALESCE(stp.sbahn_stops, 0) AS sbahn_stops, COALESCE(stp.rail_stops, 0) AS rail_stops,
           COALESCE(dep.n_lines, 0) AS n_lines, COALESCE(dep.departures, 0) + COALESCE(sel.add_dep, 0) AS departures,
           COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0) AS places, COALESCE(dep.places, 0) AS places_today,
           COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0) AS add_places, COALESCE(sel.add_dep, 0) AS add_dep, sel.active_projects AS active_projects,
           1000.0 * (COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0)) / (dem.pop_y + {w_jobs!f} * dem.jobs_y) AS places_per_1k_act,
           1000.0 * COALESCE(dep.places, 0) / (dem.pop_24 + {w_jobs!f} * dem.jobs_24) AS places_per_1k_act_24,
           1000.0 * (COALESCE(dep.departures, 0) + COALESCE(sel.add_dep, 0)) / (dem.pop_y + {w_jobs!f} * dem.jobs_y) AS dep_per_1k_act,
           1000.0 * (COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0)) / dem.pop_y AS places_per_1k_res,
           dem.pop_y / NULLIF(stp.stations, 0) AS residents_per_station
    FROM dem
    LEFT JOIN stp ON stp.dno = dem.district_no
    LEFT JOIN dep ON dep.dno = dem.district_no
    LEFT JOIN sel ON sel.district_no = dem.district_no
    LEFT JOIN ex ON ex.district_no = dem.district_no
),
r AS (
    SELECT district_no, district, population, jobs, area_km2, residents_per_km2, activity, activity_per_km2,
           stations, bus_stops, tram_stops, ubahn_stops, sbahn_stops, rail_stops, n_lines, departures, places,
           add_places, add_dep, active_projects, activity_24,
           places_per_1k_act, places_per_1k_act_24, dep_per_1k_act, places_per_1k_res, residents_per_station,
           1000.0 * SUM(places) OVER () / SUM(activity) OVER () AS city_places_per_1k_act,
           1000.0 * SUM(places_today) OVER () / SUM(activity_24) OVER () AS city_places_per_1k_act_24,
           1000.0 * SUM(departures) OVER () / SUM(activity) OVER () AS city_dep_per_1k_act,
           SUM(add_places) OVER () AS city_added_places,
           RANK() OVER (ORDER BY activity_per_km2 DESC) AS act_density_rank,
           RANK() OVER (ORDER BY places_per_1k_act DESC) AS places_rank,
           RANK() OVER (ORDER BY dep_per_1k_act DESC) AS dep_rank,
           NTILE(3) OVER (ORDER BY activity_per_km2 DESC, population DESC) AS act_t,
           NTILE(3) OVER (ORDER BY places_per_1k_act DESC) AS places_t,
           NTILE(3) OVER (ORDER BY residents_per_km2 DESC, population DESC) AS res_t0,
           NTILE(3) OVER (ORDER BY places_per_1k_res DESC) AS places_t0,
           NTILE(3) OVER (ORDER BY activity_per_km2_24 DESC, population DESC) AS act_t24,
           NTILE(3) OVER (ORDER BY places_per_1k_act_24 DESC) AS places_t24
    FROM m
)
SELECT district_no, district, ROUND(population) AS population, ROUND(jobs) AS jobs, ROUND(area_km2, 1) AS area_km2,
       ROUND(residents_per_km2) AS density_per_km2, ROUND(activity) AS activity, ROUND(activity_per_km2) AS activity_per_km2,
       stations, bus_stops, tram_stops, ubahn_stops, sbahn_stops, rail_stops, n_lines, departures, places,
       ROUND(add_places) AS add_places, ROUND(add_dep) AS add_dep, active_projects,
       ROUND(city_dep_per_1k_act, 1) AS city_dep_per_1k_act, ROUND(city_added_places) AS city_added_places,
       ROUND(places_per_1k_act) AS places_per_1k_act, ROUND(places_per_1k_act_24) AS places_per_1k_act_2024,
       ROUND(dep_per_1k_act, 1) AS dep_per_1k_act,
       ROUND(places_per_1k_res) AS places_per_1k_res, ROUND(residents_per_station) AS residents_per_station,
       act_density_rank, places_rank, dep_rank, places_rank - act_density_rank AS gap,
       CASE WHEN act_t = 1 AND places_t = 3 THEN 1 ELSE 0 END AS flagged,
       CASE WHEN res_t0 = 1 AND places_t0 = 3 THEN 1 ELSE 0 END AS flagged_w0,
       CASE WHEN act_t24 = 1 AND places_t24 = 3 THEN 1 ELSE 0 END AS flagged_2024,
       CASE WHEN (act_t = 1 AND places_t = 3) AND NOT (res_t0 = 1 AND places_t0 = 3) THEN 'newly flagged'
            WHEN NOT (act_t = 1 AND places_t = 3) AND (res_t0 = 1 AND places_t0 = 3) THEN 'no longer flagged'
            ELSE '' END AS flag_change,
       CASE WHEN (act_t = 1 AND places_t = 3) AND NOT (act_t24 = 1 AND places_t24 = 3) THEN 'newly flagged'
            WHEN NOT (act_t = 1 AND places_t = 3) AND (act_t24 = 1 AND places_t24 = 3) THEN 'no longer flagged'
            ELSE '' END AS flag_change_2024,
       CASE WHEN places_rank - dep_rank > 5 THEN 'mostly bus'
            WHEN dep_rank - places_rank > 5 THEN 'mostly rail' ELSE '' END AS mode_note,
       ROUND(places_per_1k_act / city_places_per_1k_act_24, 3) AS service_ratio,
       ROUND(places_per_1k_act / city_places_per_1k_act, 3) AS ratio_own_year,
       ROUND(places_per_1k_act_24 / city_places_per_1k_act_24, 3) AS ratio_2024,
       ROUND(100 * (places_per_1k_act - places_per_1k_act_24) / city_places_per_1k_act_24, 1) AS ratio_change_pp,
       ROUND(100 * (places_per_1k_act / places_per_1k_act_24 - 1), 1) AS pct_change_places,
       ROUND(city_places_per_1k_act) AS city_places_per_1k_act,
       ROUND(city_places_per_1k_act_24) AS city_places_per_1k_act_2024,
       CASE WHEN act_t = 1 THEN 1 ELSE 0 END AS is_dense,
       {year!d} AS year_n,
       (SELECT ref_date FROM rd) AS ref_weekday
FROM r
ORDER BY gap DESC, act_density_rank
