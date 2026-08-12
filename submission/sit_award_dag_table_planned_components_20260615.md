# SIT Award DAG to Planned Component Mapping - 2026-06-15

Generated at: 2026-06-15 16:03:55 Asia/Taipei

Source: DAG `job_config.json` field `data_infos.component_name`, Git add commits, and current branch merge commits. DB rows come from the existing SIT DAG/table report.

Summary: 37 DAG/table rows from the SIT report; 36 are newly added DAGs on the current branch relative to `origin/develop`; 26 unique planned component names; 1 row(s) missing planned component name.

Merged-from branch summary:

| Merged from branch | Rows |
|---|---:|
| `feat/rat_disaster (SIT-only, not merged into current branch)` | 1 |
| `feature/team-merit01-random-write` | 8 |
| `feature/team-merit03-ai-plus-one` | 6 |
| `feature/team-no1-bombs-king` | 6 |
| `feature/team-no2-cashifa` | 13 |
| `feature/team-no3-guzhong-team` | 3 |

Missing planned component source:
- `proj_city_dashboard_rat_disaster` -> `rat_disaster`: job_config not present on current branch

Fixed 3 DAG mapping:

| DAG ID | Ready table | Planned component index/name | Merged from branch | Merge commit | Add commit |
|---|---|---|---|---|---|
| `proj_city_dashboard_food_hygiene_award_locations` | `food_hygiene_award_locations` | `food_hygiene_award_map` | `feature/team-no2-cashifa` | `0ed8b3b5` | `25fa7af8` |
| `proj_city_dashboard_food_supply_market_locations` | `food_supply_market_locations` | `food_supply_market_map` | `feature/team-no2-cashifa` | `0ed8b3b5` | `c9b7bece` |
| `proj_city_dashboard_organic_farm_locations` | `organic_farm_locations` | `organic_farm_map` | `feature/team-no2-cashifa` | `0ed8b3b5` | `1fd824d9` |

Full mapping:

| # | Scope | Merged from branch | Merge commit | Add commit | DAG ID | Ready table | City | Planned component index/name | DB rows | Note |
|---:|---|---|---|---|---|---|---|---|---:|---|
| 1 | current branch added DAG | `feature/team-merit03-ai-plus-one` | `a888f848` | `eaad00c9` | `proj_city_dashboard_eco_friendly_restaurant` | `eco_friendly_restaurant` | `taipei` | `eco_friendly_restaurant_list` | 479 | nested: 3fcc93fc Merge: 環保餐廳數量 component 整併交付物 (DDL / config CSV / sample / DAG) |
| 2 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_city_dashboard_emergency_medical_institutions` | `emergency_medical_institutions` | `taipei` | `emergency_medical_institutions_table` | 22 |  |
| 3 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_city_dashboard_family_medicine_institutions` | `family_medicine_institutions` | `taipei` | `family_medicine_institutions_table` | 198 |  |
| 4 | current branch added DAG | `feature/team-merit03-ai-plus-one` | `a888f848` | `3de5a8b4` | `proj_city_dashboard_food_bank_contacts` | `food_bank_contacts` | `taipei` | `food_bank_points` | 23 | nested: 05957d75 Merge: 實物銀行數量 component 整併交付物 (DDL / sample CSV / Excel / seed SQL / DAG) |
| 5 | current branch added DAG | `feature/team-no3-guzhong-team` | `c2fbff79` | `fb39d295` | `proj_city_dashboard_food_factory_locations_taipei` | `food_factory_locations_taipei` | `taipei` | `food_factory_district` | 64 |  |
| 6 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `25fa7af8` | `proj_city_dashboard_food_hygiene_award_locations` | `food_hygiene_award_locations` | `taipei` | `food_hygiene_award_map` | 1855 |  |
| 7 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `c9b7bece` | `proj_city_dashboard_food_supply_market_locations` | `food_supply_market_locations` | `taipei` | `food_supply_market_map` | 79 |  |
| 8 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_city_dashboard_general_medicine_institutions` | `general_medicine_institutions` | `taipei` | `general_medicine_institutions_table` | 656 |  |
| 9 | current branch added DAG | `feature/team-merit03-ai-plus-one` | `a888f848` | `20dca603` | `proj_city_dashboard_green_store` | `green_store` | `taipei` | `green_store_table` | 1640 | nested: bf574273 Merge: 綠色商店數量 component 整併交付物 (DDL / config Excel / sample / DAG) |
| 10 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_city_dashboard_internal_medicine_institutions` | `internal_medicine_institutions` | `taipei` | `internal_medicine_institutions_table` | 225 |  |
| 11 | current branch added DAG | `feature/team-merit01-random-write` | `952c7cee` | `1856d7ab` | `proj_city_dashboard_noise_monitoring_stations_tpe` | `noise_monitoring_stations_tpe` | `taipei` | `noise_monitoring_stations_tpe_map` | 24 |  |
| 12 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `1fd824d9` | `proj_city_dashboard_organic_farm_locations` | `organic_farm_locations` | `taipei` | `organic_farm_map` | 66 |  |
| 13 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_city_dashboard_pharmacies` | `pharmacies` | `taipei` | `pharmacies_table` | 907 |  |
| 14 | current branch added DAG | `feature/team-no1-bombs-king` | `85b730f3` | `26b62152` | `proj_city_dashboard_purchase_subsidy_application_status` | `purchase_subsidy_application_status` | `taipei` | `purchase_subsidy_application_status_chart` | 19 |  |
| 15 | SIT report only / not added on current branch | `feat/rat_disaster (SIT-only, not merged into current branch)` | `N/A` | `4cdd0e43` | `proj_city_dashboard_rat_disaster` | `rat_disaster` | `taipei` | `MISSING` | 12 | job_config not present on current branch |
| 16 | current branch added DAG | `feature/team-no1-bombs-king` | `85b730f3` | `26b62152` | `proj_city_dashboard_rental_subsidy_application_status` | `rental_subsidy_application_status` | `taipei` | `rental_subsidy_application_status_chart` | 19 |  |
| 17 | current branch added DAG | `feature/team-no1-bombs-king` | `85b730f3` | `26b62152` | `proj_city_dashboard_repair_subsidy_application_status` | `repair_subsidy_application_status` | `taipei` | `repair_subsidy_application_status_chart` | 19 |  |
| 18 | current branch added DAG | `feature/team-merit01-random-write` | `952c7cee` | `cab99913` | `proj_city_dashboard_river_channel` | `river_channel` | `taipei` | `river_channel_map` | 13262 |  |
| 19 | current branch added DAG | `feature/team-merit01-random-write` | `952c7cee` | `395308b9` | `proj_city_dashboard_river_water_quality_tpe` | `river_water_quality_tpe` | `taipei` | `river_water_quality_map` | 35904 |  |
| 20 | current branch added DAG | `feature/team-no3-guzhong-team` | `c2fbff79` | `86722dde` | `proj_city_dashboard_school_food_supply_chain_links` | `school_food_supply_chain_links` | `taipei` | `school_food_supply_chain` | 0 |  |
| 21 | current branch added DAG | `feature/team-merit01-random-write` | `952c7cee` | `98d62ae1` | `proj_city_dashboard_urban_planning_tpe` | `urban_planning_tpe` | `taipei` | `urban_planning` | 105 |  |
| 22 | current branch added DAG | `feature/team-merit03-ai-plus-one` | `a888f848` | `c6421618` | `proj_new_taipei_city_dashboard_eco_friendly_restaurant_ntpe` | `eco_friendly_restaurant_ntpe` | `newtaipei` | `eco_friendly_restaurant_list` | 749 | nested: 3fcc93fc Merge: 環保餐廳數量 component 整併交付物 (DDL / config CSV / sample / DAG) |
| 23 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_new_taipei_city_dashboard_emergency_medical_institutions_ntpe` | `emergency_medical_institutions_ntpe` | `newtaipei` | `emergency_medical_institutions_ntpe_table` | 17 |  |
| 24 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_new_taipei_city_dashboard_family_medicine_institutions_ntpe` | `family_medicine_institutions_ntpe` | `newtaipei` | `family_medicine_institutions_ntpe_table` | 253 |  |
| 25 | current branch added DAG | `feature/team-merit03-ai-plus-one` | `a888f848` | `79cc7c17` | `proj_new_taipei_city_dashboard_food_bank_ntpe` | `food_bank_ntpe` | `newtaipei` | `food_bank_points` | 57 | nested: 05957d75 Merge: 實物銀行數量 component 整併交付物 (DDL / sample CSV / Excel / seed SQL / DAG) |
| 26 | current branch added DAG | `feature/team-no3-guzhong-team` | `c2fbff79` | `aa6a5091` | `proj_new_taipei_city_dashboard_food_factory_locations_new_taipei` | `food_factory_locations_new_taipei` | `newtaipei` | `food_factory_district` | 1230 |  |
| 27 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_new_taipei_city_dashboard_general_medicine_institutions_ntpe` | `general_medicine_institutions_ntpe` | `newtaipei` | `general_medicine_institutions_ntpe_table` | 472 |  |
| 28 | current branch added DAG | `feature/team-merit03-ai-plus-one` | `a888f848` | `997caace` | `proj_new_taipei_city_dashboard_green_store_ntpe` | `green_store_ntpe` | `newtaipei` | `green_store_table` | 2051 | nested: bf574273 Merge: 綠色商店數量 component 整併交付物 (DDL / config Excel / sample / DAG) |
| 29 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_new_taipei_city_dashboard_internal_medicine_institutions_ntpe` | `internal_medicine_institutions_ntpe` | `newtaipei` | `internal_medicine_institutions_ntpe_table` | 282 |  |
| 30 | current branch added DAG | `feature/team-merit01-random-write` | `952c7cee` | `1856d7ab` | `proj_new_taipei_city_dashboard_noise_monitoring_stations_ntpc` | `noise_monitoring_stations_ntpc` | `newtaipei` | `noise_monitoring_stations_ntpc_map` | 27 |  |
| 31 | current branch added DAG | `feature/team-no2-cashifa` | `0ed8b3b5` | `a22cad9a` | `proj_new_taipei_city_dashboard_pharmacies_ntpe` | `pharmacies_ntpe` | `newtaipei` | `pharmacies_ntpe_table` | 1146 |  |
| 32 | current branch added DAG | `feature/team-no1-bombs-king` | `85b730f3` | `26b62152` | `proj_new_taipei_city_dashboard_purchase_subsidy_application_status` | `purchase_subsidy_application_status` | `newtaipei` | `purchase_subsidy_application_status_chart` | 19 |  |
| 33 | current branch added DAG | `feature/team-no1-bombs-king` | `85b730f3` | `26b62152` | `proj_new_taipei_city_dashboard_rental_subsidy_application_status` | `rental_subsidy_application_status` | `newtaipei` | `rental_subsidy_application_status_chart` | 19 |  |
| 34 | current branch added DAG | `feature/team-no1-bombs-king` | `85b730f3` | `26b62152` | `proj_new_taipei_city_dashboard_repair_subsidy_application_status` | `repair_subsidy_application_status` | `newtaipei` | `repair_subsidy_application_status_chart` | 19 |  |
| 35 | current branch added DAG | `feature/team-merit01-random-write` | `952c7cee` | `cab99913` | `proj_new_taipei_city_dashboard_river_channel_ntpe` | `river_channel_ntpe` | `newtaipei` | `river_channel_map` | 13262 |  |
| 36 | current branch added DAG | `feature/team-merit01-random-write` | `952c7cee` | `395308b9` | `proj_new_taipei_city_dashboard_river_water_quality_ntpe` | `river_water_quality_ntpe` | `newtaipei` | `river_water_quality_map` | 104544 |  |
| 37 | current branch added DAG | `feature/team-merit01-random-write` | `952c7cee` | `98d62ae1` | `proj_new_taipei_city_dashboard_urban_planning_new_tpe` | `urban_planning_new_tpe` | `newtaipei` | `urban_planning` | 333 |  |
