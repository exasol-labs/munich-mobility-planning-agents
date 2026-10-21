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
pl AS (
    SELECT r."route_id", r."line_mode" AS line_mode, r."route_short_name" AS line,
           COALESCE(lc."capacity_per_trip", v."capacity_per_trip") AS capacity
    FROM MUNICH_DATASET.MVV_ROUTES r
    JOIN MUNICH_DATASET.VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode"
    LEFT JOIN MUNICH_DATASET.LINE_CAPACITY lc ON lc."line" = r."route_short_name" AND lc."line_mode" = r."line_mode"
    WHERE INSTR(',' || {lines!s} || ',', ',' || r."route_short_name" || ',') > 0
),
ev AS (
    SELECT pl.line_mode, pl.line, pl.capacity, s."district_no" AS district_no, COALESCE(s."parent_station", s."stop_id") AS station_id
    FROM MUNICH_DATASET.MVV_TRIPS t
    JOIN svc ON svc."service_id" = t."service_id"
    JOIN pl ON pl."route_id" = t."route_id"
    JOIN MUNICH_DATASET.MVV_STOP_TIMES st ON st."trip_id" = t."trip_id"
    JOIN MUNICH_DATASET.MVV_STOPS s ON s."stop_id" = st."stop_id"
    WHERE s."in_munich" = 1
)
SELECT line_mode, line, station_id, MIN(district_no) AS district_no, MIN(capacity) AS capacity, COUNT(*) AS dep_today
FROM ev GROUP BY line_mode, line, station_id
ORDER BY line, station_id
