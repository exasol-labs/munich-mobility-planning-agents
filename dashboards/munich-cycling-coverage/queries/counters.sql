-- the six permanent counters: average daily total, rain penalty (rain_mm > 1 vs dry days rain_mm <= 1), data period
SELECT s."station" AS station, s."station_name" AS station_name, s."lat" AS lat, s."lon" AS lon, s."district_no" AS district_no,
       d."district_name" AS district,
       COUNT(b."count_date") AS n_days,
       ROUND(AVG(b."total")) AS avg_per_day,
       SUM(CASE WHEN b."rain_mm" > 1 THEN 1 ELSE 0 END) AS rain_days,
       ROUND(AVG(CASE WHEN b."rain_mm" > 1 THEN b."total" END)) AS avg_rain,
       ROUND(AVG(CASE WHEN b."rain_mm" <= 1 THEN b."total" END)) AS avg_dry,
       ROUND(100 * (1 - AVG(CASE WHEN b."rain_mm" > 1 THEN b."total" END)
                        / NULLIF(AVG(CASE WHEN b."rain_mm" <= 1 THEN b."total" END), 0)), 1) AS rain_penalty_pct,
       MIN(b."count_date") AS first_day, MAX(b."count_date") AS last_day
FROM MUNICH_DATASET.BIKE_COUNT_STATIONS s
LEFT JOIN MUNICH_DATASET.BIKE_COUNTS_DAILY b ON b."station" = s."station" AND b."total" IS NOT NULL
LEFT JOIN MUNICH_DATASET.DISTRICTS d ON d."district_no" = s."district_no"
GROUP BY s."station", s."station_name", s."lat", s."lon", s."district_no", d."district_name"
ORDER BY avg_per_day DESC NULLS LAST
