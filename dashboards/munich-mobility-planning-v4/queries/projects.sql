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
    -- rule 4: 2nd trunk = new-tunnel trains (above) plus a 15-minute basic interval; nothing removed from the existing trunk (slots reused).
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
pinfo AS (
    SELECT p."project_id" AS project_id, MIN(p."project_name") AS project_name, MIN(p."status") AS status, MAX(p."funded") AS funded,
           MIN(p."opening_year") AS opening_year, MIN(p."opening_year_risk") AS opening_year_risk,
           MIN(p."opening_year_model") AS opening_year_model, MAX(p."opening_year_assumed") AS opening_year_assumed,
           ROUND(AVG(p."verified"), 2) AS verified_share, COUNT(*) AS n_rows,
           SUM(CASE WHEN p."station_name" = 'unknown' THEN 1 ELSE 0 END) AS unknown_rows
    FROM MUNICH_DATASET.PT_PROJECT_STATIONS p GROUP BY p."project_id"
),
psum AS (
    SELECT c.project_id,
           GROUP_CONCAT(DISTINCT CASE WHEN c.comp_kind = 'added' THEN c.calc_method END SEPARATOR ', ') AS calc_method,
           SUM(CASE WHEN c.departures > 0 THEN c.departures * c.capacity ELSE 0 END) AS gross_places,
           SUM(CASE WHEN c.departures < 0 AND c.requires_project IS NULL THEN c.departures * c.capacity ELSE 0 END) AS removed_places,
           SUM(CASE WHEN c.requires_project IS NULL THEN c.departures * c.capacity ELSE 0 END) AS net_places,
           SUM(CASE WHEN c.requires_project IS NULL THEN c.departures ELSE 0 END) AS net_departures
    FROM comps c GROUP BY c.project_id
),
pdist AS (
    SELECT x.project_id, GROUP_CONCAT(x.district || ' ' || x.n ORDER BY x.district SEPARATOR ', ') AS stations_by_district
    FROM (SELECT c.project_id, d."district_name" AS district, COUNT(DISTINCT c.station_name) AS n
          FROM comps c JOIN MUNICH_DATASET.DISTRICTS d ON d."district_no" = c.district_no
          WHERE c.comp_kind = 'added' GROUP BY c.project_id, d."district_name") x
    GROUP BY x.project_id
),
outp AS (
    SELECT 'project' AS kind, i.project_id, i.project_name, i.status, i.funded, i.opening_year, i.opening_year_risk, i.opening_year_model,
           i.opening_year_assumed, i.verified_share, i.n_rows, i.unknown_rows, s.calc_method, ROUND(s.gross_places) AS gross_places,
           ROUND(s.removed_places) AS removed_places, ROUND(s.net_places) AS net_places, ROUND(s.net_departures) AS net_departures,
           pdist.stations_by_district,
           CAST(NULL AS VARCHAR(200)) AS station_name, CAST(NULL AS DOUBLE) AS lat, CAST(NULL AS DOUBLE) AS lon,
           CAST(NULL AS DECIMAL(3,0)) AS station_is_new, CAST(NULL AS DECIMAL(3,0)) AS district_no, CAST(NULL AS VARCHAR(50)) AS line
    FROM pinfo i LEFT JOIN psum s ON s.project_id = i.project_id LEFT JOIN pdist ON pdist.project_id = i.project_id
    UNION ALL
    SELECT 'station', c.project_id, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, c.calc_method, NULL, NULL, NULL, NULL, NULL,
           c.station_name, c.lat, c.lon, c.station_is_new, c.district_no, c.line
    FROM comps c WHERE c.comp_kind = 'added' AND c.lat IS NOT NULL
)
SELECT kind, project_id, project_name, status, funded, opening_year, opening_year_risk, opening_year_model, opening_year_assumed,
       verified_share, n_rows, unknown_rows, calc_method, gross_places, removed_places, net_places, net_departures, stations_by_district,
       station_name, lat, lon, station_is_new, district_no, line
FROM outp
ORDER BY kind, net_places DESC, project_id
