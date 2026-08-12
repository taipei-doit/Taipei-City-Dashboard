# SIT Award DAG 期望輸出 Table 與欄位

來源: 本機 `sit` 分支 DAG 程式 `COL_MAP` 靜態解析。

備註: 這是 DAG 下一次成功寫入後的期望欄位，不是 live DB 現況。

DAG 數量: 37

| # | DAG | Ready table | Expected columns |
|---:|---|---|---|
| 1 | `eco_friendly_restaurant` | `eco_friendly_restaurant` | `data_time, seq, restaurant_category, restaurant_name, phone, ext, mobile, address, extra_eco_actions` |
| 2 | `emergency_medical_institutions` | `emergency_medical_institutions` | `data_time, seq, institution_name, zipcode, address, phone` |
| 3 | `family_medicine_institutions` | `family_medicine_institutions` | `data_time, seq, institution_name, zipcode, address, phone` |
| 4 | `food_bank_contacts` | `food_bank_contacts` | `data_time, seq, institution_type, institution_name, district_code, address` |
| 5 | `food_factory_locations_taipei` | `food_factory_locations_taipei` | `data_time, factory_id, name, address, city, district, lng, lat, wkb_geometry` |
| 6 | `food_hygiene_award_locations` | `food_hygiene_award_locations` | `data_time, source_city, source_agency, award_year, grade, business_name, registration_no, address, district, area_code, lng, lat, source_record_id, award_image_url, wkb_geometry` |
| 7 | `food_supply_market_locations` | `food_supply_market_locations` | `data_time, source_city, source_agency, source_record_id, district, area_code, market_name, market_type, address, phone, description, opened_date, total_stalls, vegetable_stalls, fruit_stalls, meat_stalls, seafood_stalls, poultry_stalls, grain_stalls, flower_stalls, grocery_stalls, department_store_stalls, food_stalls, other_stalls, lng, lat, wkb_geometry` |
| 8 | `general_medicine_institutions` | `general_medicine_institutions` | `data_time, seq, institution_name, zipcode, address, phone` |
| 9 | `green_store` | `green_store` | `data_time, seq, store_name, address, store_code, contact_person, contact_phone, extension, mobile, store_type` |
| 10 | `internal_medicine_institutions` | `internal_medicine_institutions` | `data_time, seq, institution_name, zipcode, address, phone` |
| 11 | `noise_monitoring_stations_tpe` | `noise_monitoring_stations_tpe` | `data_time, station_name, station_no, address, control_area, monitor_type, lng, lat, wkb_geometry` |
| 12 | `organic_farm_locations` | `organic_farm_locations` | `data_time, source_city, source_agency, source_record_id, farm_name, operator_name, address, district, phone, certification_no, certification_type, expire_date, farm_area_hectare, food_education, beekeeping, chicken_raising, note, lng, lat, wkb_geometry` |
| 13 | `pharmacies` | `pharmacies` | `data_time, seq, pharmacy_name, zipcode, address, phone` |
| 14 | `purchase_subsidy_application_status` | `purchase_subsidy_application_status` | `data_time, city, year, application_households, planned_households, approved_households` |
| 15 | `rat_disaster` | `rat_disaster` | `(未從 DAG 靜態解析到欄位)` |
| 16 | `rental_subsidy_application_status` | `rental_subsidy_application_status` | `data_time, city, year, application_households, planned_households, approved_households` |
| 17 | `repair_subsidy_application_status` | `repair_subsidy_application_status` | `data_time, city, year, application_households, planned_households, approved_households` |
| 18 | `river_channel` | `river_channel` | `data_time, river_id, river_name, river_class, manage_unit, county, source_year, wkb_geometry` |
| 19 | `river_water_quality_tpe` | `river_water_quality_tpe` | `data_time, site_id, site_name, county, township, basin, river, twd97_lon, twd97_lat, twd97_tm2x, twd97_tm2y, sample_date, item_name, item_eng_abbreviation, item_value, item_unit, note, wkb_geometry` |
| 20 | `school_food_supply_chain_links` | `school_food_supply_chain_links` | `data_time, city, district, source_name, target_name, value, layer` |
| 21 | `urban_planning_tpe` | `urban_planning_tpe` | `data_time, district, land_use_zone, zone_count` |
| 22 | `eco_friendly_restaurant_ntpe` | `eco_friendly_restaurant_ntpe` | `data_time, seq, restaurant_category, city, countycode, restaurant_name, phone, address` |
| 23 | `emergency_medical_institutions_ntpe` | `emergency_medical_institutions_ntpe` | `data_time, seqno, hosp_name, hosp_id, area, hosp_addr, tel, division, remark` |
| 24 | `family_medicine_institutions_ntpe` | `family_medicine_institutions_ntpe` | `data_time, seqno, hosp_name, hosp_id, area, hosp_addr, tel, division, remark` |
| 25 | `food_bank_ntpe` | `food_bank_ntpe` | `data_time, seq, title, county_code, county, area_code, area, postal_code, address, phone` |
| 26 | `food_factory_locations_new_taipei` | `food_factory_locations_new_taipei` | `data_time, factory_id, name, address, city, district, lng, lat, wkb_geometry` |
| 27 | `general_medicine_institutions_ntpe` | `general_medicine_institutions_ntpe` | `data_time, seqno, hosp_name, hosp_id, area, hosp_addr, tel, division, remark` |
| 28 | `green_store_ntpe` | `green_store_ntpe` | `data_time, seq, store_name, address, store_code, contact_phone, store_type, city, county_code` |
| 29 | `internal_medicine_institutions_ntpe` | `internal_medicine_institutions_ntpe` | `data_time, seqno, hosp_name, hosp_id, area, hosp_addr, tel, division, remark` |
| 30 | `noise_monitoring_stations_ntpc` | `noise_monitoring_stations_ntpc` | `data_time, station_name, station_no, address, control_area, road_width, lng, lat, wkb_geometry` |
| 31 | `pharmacies_ntpe` | `pharmacies_ntpe` | `data_time, seqno, pharmacy_name, zipcode, address, phone` |
| 32 | `purchase_subsidy_application_status` | `purchase_subsidy_application_status` | `data_time, city, year, application_households, planned_households, approved_households` |
| 33 | `rental_subsidy_application_status` | `rental_subsidy_application_status` | `data_time, city, year, application_households, planned_households, approved_households` |
| 34 | `repair_subsidy_application_status` | `repair_subsidy_application_status` | `data_time, city, year, application_households, planned_households, approved_households` |
| 35 | `river_channel_ntpe` | `river_channel_ntpe` | `data_time, river_id, river_name, river_class, manage_unit, county, source_year, wkb_geometry` |
| 36 | `river_water_quality_ntpe` | `river_water_quality_ntpe` | `data_time, site_id, site_name, county, township, basin, river, twd97_lon, twd97_lat, twd97_tm2x, twd97_tm2y, sample_date, item_name, item_eng_abbreviation, item_value, item_unit, note, wkb_geometry` |
| 37 | `urban_planning_new_tpe` | `urban_planning_new_tpe` | `data_time, district, land_use_zone, zone_count` |
