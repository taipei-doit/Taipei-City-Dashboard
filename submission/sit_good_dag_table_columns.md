# SIT 成功 Award DAG 對應 Table 與欄位

來源: `git diff --name-only develop...sit` 中新增的 award DAG `job_config.json`。

排除原本未完成 3 支: `food_hygiene_award_locations`, `organic_farm_locations`, `food_supply_market_locations`。

成功 DAG 數量: 34

| # | DAG | Ready table | 欄位 |
|---:|---|---|---|
| 1 | `eco_friendly_restaurant` | `eco_friendly_restaurant` | `data_time, seq, restaurant_category, restaurant_name, phone, ext, mobile, address, extra_eco_actions` |
| 2 | `emergency_medical_institutions` | `emergency_medical_institutions` | `data_time, seq, institution_name, zipcode, address, phone` |
| 3 | `family_medicine_institutions` | `family_medicine_institutions` | `data_time, seq, institution_name, zipcode, address, phone` |
| 4 | `food_bank_contacts` | `food_bank_contacts` | `data_time, seq, institution_type, institution_name, district_code, address` |
| 5 | `food_factory_locations_taipei` | `food_factory_locations_taipei` | `data_time, factory_id, name, address, city, district, lng, lat, wkb_geometry` |
| 6 | `general_medicine_institutions` | `general_medicine_institutions` | `data_time, seq, institution_name, zipcode, address, phone` |
| 7 | `green_store` | `green_store` | `data_time, seq, store_name, address, store_code, contact_person, contact_phone, extension, mobile, store_type` |
| 8 | `internal_medicine_institutions` | `internal_medicine_institutions` | `data_time, seq, institution_name, zipcode, address, phone` |
| 9 | `noise_monitoring_stations_tpe` | `noise_monitoring_stations_tpe` | `data_time, station_name, station_no, address, control_area, monitor_type, lng, lat, wkb_geometry` |
| 10 | `pharmacies` | `pharmacies` | `data_time, seq, pharmacy_name, zipcode, address, phone` |
| 11 | `purchase_subsidy_application_status` | `purchase_subsidy_application_status` | `data_time, 縣市, 項目, 自購住宅貸款利息補貼申請戶數, 自購住宅貸款利息補貼計畫戶數, 自購住宅貸款利息補貼核定戶數` |
| 12 | `rat_disaster` | `rat_disaster` | `waste_cleaned_tons, rat_holes_filled_count, mouse_traps_placed_count, rodenticide_applied_grams, rats_captured_count, education_outreach_sessions, violation_reports_count, disinfection_area_square_meters` |
| 13 | `rental_subsidy_application_status` | `rental_subsidy_application_status` | `data_time, 縣市, 項目, 租金補貼申請戶數, 租金補貼計畫戶數, 租金補貼核定戶數` |
| 14 | `repair_subsidy_application_status` | `repair_subsidy_application_status` | `data_time, 縣市, 項目, 修繕住宅貸款利息補貼申請戶數, 修繕住宅貸款利息補貼計畫戶數, 修繕住宅貸款利息補貼核定戶數` |
| 15 | `river_channel` | `river_channel` | `data_time, river_id, river_name, river_class, manage_unit, county, source_year, wkb_geometry` |
| 16 | `river_water_quality_tpe` | `river_water_quality_tpe` | `data_time, site_id, site_name, county, township, basin, river, twd97_lon, twd97_lat, twd97_tm2x, twd97_tm2y, sample_date, item_name, item_eng_abbreviation, item_value, item_unit, note, wkb_geometry` |
| 17 | `school_food_supply_chain_links` | `school_food_supply_chain_links` | `data_time, city, district, source_name, target_name, value, layer` |
| 18 | `urban_planning_tpe` | `urban_planning_tpe` | `data_time, 行政區, 使用分區, 數量` |
| 19 | `eco_friendly_restaurant_ntpe` | `eco_friendly_restaurant_ntpe` | `data_time, seq, restaurant_category, city, countycode, restaurant_name, phone, address` |
| 20 | `emergency_medical_institutions_ntpe` | `emergency_medical_institutions_ntpe` | `data_time, seqno, hosp_name, hosp_id, area, hosp_addr, tel, division, remark` |
| 21 | `family_medicine_institutions_ntpe` | `family_medicine_institutions_ntpe` | `data_time, seqno, hosp_name, hosp_id, area, hosp_addr, tel, division, remark` |
| 22 | `food_bank_ntpe` | `food_bank_ntpe` | `data_time, seq, title, county_code, county, area_code, area, postal_code, address, phone` |
| 23 | `food_factory_locations_new_taipei` | `food_factory_locations_new_taipei` | `data_time, factory_id, name, address, city, district, lng, lat, wkb_geometry` |
| 24 | `general_medicine_institutions_ntpe` | `general_medicine_institutions_ntpe` | `data_time, seqno, hosp_name, hosp_id, area, hosp_addr, tel, division, remark` |
| 25 | `green_store_ntpe` | `green_store_ntpe` | `data_time, seq, store_name, address, store_code, contact_phone, store_type, city, county_code` |
| 26 | `internal_medicine_institutions_ntpe` | `internal_medicine_institutions_ntpe` | `data_time, seqno, hosp_name, hosp_id, area, hosp_addr, tel, division, remark` |
| 27 | `noise_monitoring_stations_ntpc` | `noise_monitoring_stations_ntpc` | `data_time, station_name, station_no, address, control_area, road_width, lng, lat, wkb_geometry` |
| 28 | `pharmacies_ntpe` | `pharmacies_ntpe` | `data_time, seqno, pharmacy_name, zipcode, address, phone` |
| 29 | `purchase_subsidy_application_status` | `purchase_subsidy_application_status` | `data_time, 縣市, 項目, 自購住宅貸款利息補貼申請戶數, 自購住宅貸款利息補貼計畫戶數, 自購住宅貸款利息補貼核定戶數` |
| 30 | `rental_subsidy_application_status` | `rental_subsidy_application_status` | `data_time, 縣市, 項目, 租金補貼申請戶數, 租金補貼計畫戶數, 租金補貼核定戶數` |
| 31 | `repair_subsidy_application_status` | `repair_subsidy_application_status` | `data_time, 縣市, 項目, 修繕住宅貸款利息補貼申請戶數, 修繕住宅貸款利息補貼計畫戶數, 修繕住宅貸款利息補貼核定戶數` |
| 32 | `river_channel_ntpe` | `river_channel_ntpe` | `data_time, river_id, river_name, river_class, manage_unit, county, source_year, wkb_geometry` |
| 33 | `river_water_quality_ntpe` | `river_water_quality_ntpe` | `data_time, site_id, site_name, county, township, basin, river, twd97_lon, twd97_lat, twd97_tm2x, twd97_tm2y, sample_date, item_name, item_eng_abbreviation, item_value, item_unit, note, wkb_geometry` |
| 34 | `urban_planning_new_tpe` | `urban_planning_new_tpe` | `data_time, 行政區, 使用分區, 數量` |
