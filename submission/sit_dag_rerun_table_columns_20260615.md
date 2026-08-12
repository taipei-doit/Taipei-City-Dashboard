# SIT DAG Rerun Table Columns - 2026-06-15

Source: live SIT Airflow rerun and live SIT DB `information_schema.columns` verification.

All tables listed below were checked with `chinese_columns=NONE`.

| DAG | Table | Rows | DB columns |
|---|---:|---:|---|
| `proj_city_dashboard_food_hygiene_award_locations` | `food_hygiene_award_locations` | 1855 | `data_time`, `source_city`, `source_agency`, `award_year`, `grade`, `business_name`, `registration_no`, `address`, `district`, `area_code`, `lng`, `lat`, `source_record_id`, `award_image_url`, `wkb_geometry`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_city_dashboard_food_supply_market_locations` | `food_supply_market_locations` | 79 | `data_time`, `source_city`, `source_agency`, `source_record_id`, `district`, `area_code`, `market_name`, `market_type`, `address`, `phone`, `description`, `opened_date`, `total_stalls`, `vegetable_stalls`, `fruit_stalls`, `meat_stalls`, `seafood_stalls`, `poultry_stalls`, `grain_stalls`, `flower_stalls`, `grocery_stalls`, `department_store_stalls`, `food_stalls`, `other_stalls`, `lng`, `lat`, `wkb_geometry`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_city_dashboard_organic_farm_locations` | `organic_farm_locations` | 66 | `data_time`, `source_city`, `source_agency`, `source_record_id`, `farm_name`, `operator_name`, `address`, `district`, `phone`, `certification_no`, `certification_type`, `expire_date`, `farm_area_hectare`, `food_education`, `beekeeping`, `chicken_raising`, `note`, `lng`, `lat`, `wkb_geometry`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_city_dashboard_urban_planning_tpe` | `urban_planning_tpe` | 105 | `data_time`, `district`, `land_use_zone`, `zone_count`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_new_taipei_city_dashboard_urban_planning_new_tpe` | `urban_planning_new_tpe` | 333 | `data_time`, `district`, `land_use_zone`, `zone_count`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_city_dashboard_purchase_subsidy_application_status` | `purchase_subsidy_application_status` | 19 | `data_time`, `city`, `year`, `application_households`, `planned_households`, `approved_households`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_city_dashboard_rental_subsidy_application_status` | `rental_subsidy_application_status` | 19 | `data_time`, `city`, `year`, `application_households`, `planned_households`, `approved_households`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_city_dashboard_repair_subsidy_application_status` | `repair_subsidy_application_status` | 19 | `data_time`, `city`, `year`, `application_households`, `planned_households`, `approved_households`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_new_taipei_city_dashboard_purchase_subsidy_application_status` | `purchase_subsidy_application_status` | 19 | `data_time`, `city`, `year`, `application_households`, `planned_households`, `approved_households`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_new_taipei_city_dashboard_rental_subsidy_application_status` | `rental_subsidy_application_status` | 19 | `data_time`, `city`, `year`, `application_households`, `planned_households`, `approved_households`, `_ctime`, `_mtime`, `ogc_fid` |
| `proj_new_taipei_city_dashboard_repair_subsidy_application_status` | `repair_subsidy_application_status` | 19 | `data_time`, `city`, `year`, `application_households`, `planned_households`, `approved_households`, `_ctime`, `_mtime`, `ogc_fid` |

Note: the three housing tables are shared by Taipei and New Taipei DAGs and use replace behavior. The last successful rerun was the New Taipei DAG set, so the current table data values have `city = 新北市`. This is a data value, not a DB column name.
