SELECT "stop_name" AS name, "district_no" AS district_no, AVG("stop_lat") AS lat, AVG("stop_lon") AS lon, COUNT(*) AS n_stops
FROM MUNICH_DATASET.MVV_STOPS
WHERE "in_munich" = 1 AND "district_no" IS NOT NULL
GROUP BY "stop_name", "district_no"
