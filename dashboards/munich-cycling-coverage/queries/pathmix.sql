-- path-quality mix per district: km by path class, two-way paths counted x2, connectors and Dummy excluded
WITH seg AS (
    SELECT "district_no" AS district_no, "length_m" AS length_m,
           REPLACE("path_type", ' (Zweirichtungsradweg)', '') AS base_type,
           CASE WHEN INSTR("path_type", '(Zweirichtungsradweg)') > 0 THEN 2 ELSE 1 END AS dir_factor
    FROM MUNICH_DATASET.CYCLING_INFRASTRUCTURE
    WHERE "path_type" NOT IN ('Dummy', 'Übergang', 'Anschlussabschnitt') AND "district_no" IS NOT NULL
),
cls AS (
    SELECT district_no, length_m * dir_factor AS dir_m,
           CASE WHEN base_type IN ('Radweg', 'Fahrradstraße') THEN 'Cycle track and cycle street'
                WHEN base_type = 'Getrennter Rad- und Gehweg' THEN 'Separated cycle and footpath'
                WHEN base_type = 'Radfahr-/Schutzstreifen' THEN 'Painted lane'
                ELSE 'Shared footpath' END AS path_class
    FROM seg
)
SELECT d."district_no" AS district_no, d."district_name" AS district, c.path_class AS path_class,
       ROUND(SUM(c.dir_m) / 1000.0, 2) AS km
FROM cls c JOIN MUNICH_DATASET.DISTRICTS d ON d."district_no" = c.district_no
GROUP BY d."district_no", d."district_name", c.path_class
ORDER BY d."district_no", c.path_class
