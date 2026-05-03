-- green_land / 01_dashboard_data.sql → DB: dashboard
-- 由 clean_green_land.py 自 臺北市市容綠美化.csv 產生
-- 排除: 樹木修剪數[株]、公有田園城市示範園圃/建置數[處]
-- 道路綠地面積、路燈汰換數: 已做逐期累加；植栽五欄為各期原值；
-- 後巷為來源累計巷數；田園面積為各期快照（見 clean_green_land.py 註解）。

DROP TABLE IF EXISTS public.green_land_beautification;

CREATE TABLE public.green_land_beautification (
    id                      SERIAL PRIMARY KEY,
    stat_label              VARCHAR(20) NOT NULL,
    roc_year                INTEGER NOT NULL,
    road_green_m2           INTEGER NOT NULL DEFAULT 0,
    street_trees            INTEGER NOT NULL DEFAULT 0,
    park_trees              INTEGER NOT NULL DEFAULT 0,
    neighborhood_park_trees INTEGER NOT NULL DEFAULT 0,
    flower_pots             INTEGER NOT NULL DEFAULT 0,
    shrub_count             INTEGER NOT NULL DEFAULT 0,
    streetlight_units       INTEGER NOT NULL DEFAULT 0,
    alley_count             INTEGER NOT NULL DEFAULT 0,
    demo_farm_m2            INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_green_land_roc_year
    ON public.green_land_beautification (roc_year);

INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('70年', 70, 0, 81780, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('71年', 71, 0, 86011, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('72年', 72, 0, 86404, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('73年', 73, 0, 107257, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('74年', 74, 0, 108881, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('75年', 75, 0, 125468, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('76年', 76, 0, 98860, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('77年', 77, 0, 101017, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('78年', 78, 0, 102845, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('79年', 79, 0, 105004, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('80年', 80, 0, 109478, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('81年', 81, 0, 107712, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('82年', 82, 0, 109383, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('83年', 83, 0, 113782, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('84年', 84, 0, 114154, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('85年', 85, 0, 113517, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('86年', 86, 0, 114590, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('87年', 87, 0, 113939, 0, 0, 0, 0, 23284, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('88年', 88, 0, 113458, 0, 0, 0, 0, 53990, 0, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('89年', 89, 14727, 113702, 0, 0, 1234710, 123444, 90680, 25, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('90年', 90, 37893, 113849, 0, 0, 1195449, 79848, 133954, 50, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('91年', 91, 60181, 111716, 0, 0, 1303041, 63921, 173568, 117, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('92年', 92, 79870, 109765, 0, 0, 1284031, 42300, 200694, 129, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('93年', 93, 104568, 104875, 0, 0, 1231473, 55592, 233565, 143, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('94年', 94, 129548, 83758, 0, 0, 1091825, 30374, 255995, 170, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('95年', 95, 157683, 88423, 0, 0, 821116, 19160, 284429, 233, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('96年', 96, 212097, 87907, 0, 0, 787335, 19818, 322259, 261, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('97年', 97, 316443, 87948, 0, 0, 720186, 31204, 348902, 298, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('98年', 98, 384587, 87553, 0, 0, 760931, 25052, 397061, 337, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('99年', 99, 485411, 88282, 82910, 0, 733381, 271196, 421565, 461, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('100年', 100, 602721, 88478, 82243, 0, 733913, 228990, 447178, 689, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('101年', 101, 722721, 90116, 84418, 0, 773476, 375300, 473860, 868, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('102年', 102, 855112, 90371, 82707, 0, 734052, 412197, 500525, 1054, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('103年', 103, 998333, 90129, 83550, 0, 701467, 423059, 512597, 1242, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('104年', 104, 1201792, 88711, 82383, 0, 609631, 414631, 522658, 1354, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('105年', 105, 1398008, 88313, 106385, 0, 593860, 371201, 535986, 1468, 0);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('106年', 106, 1589676, 87946, 83747, 24485, 518801, 299760, 546238, 1644, 4515);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('107年', 107, 1807902, 88718, 83981, 24402, 482598, 220487, 547432, 1807, 5349);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('108年', 108, 2039822, 88116, 83320, 23996, 417235, 94531, 547432, 1926, 5349);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('109年', 109, 2280051, 87754, 84460, 23849, 366935, 45843, 547432, 2120, 4931);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('110年', 110, 2530923, 87790, 109315, 0, 363476, 53570, 547432, 2263, 5831);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('111年', 111, 2782495, 89158, 111093, 0, 582720, 176729, 547432, 2456, 4420);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('112年', 112, 3039665, 92447, 112491, 0, 602181, 343796, 547432, 2606, 4822);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('113年', 113, 3302391, 93435, 111705, 0, 541326, 259547, 547432, 2683, 4082);
INSERT INTO public.green_land_beautification (stat_label, roc_year, road_green_m2, street_trees, park_trees, neighborhood_park_trees, flower_pots, shrub_count, streetlight_units, alley_count, demo_farm_m2) VALUES ('114年', 114, 3563292, 92196, 88645, 0, 484801, 113908, 547432, 2812, 2503);
