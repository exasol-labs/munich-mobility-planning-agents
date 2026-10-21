SELECT "district_no" AS district_no, "district_name" AS district, "centroid_lat" AS centroid_lat, "centroid_lon" AS centroid_lon,
       "polygon_wkt" AS polygon_wkt
FROM MUNICH_DATASET.DISTRICTS
ORDER BY "district_no"
