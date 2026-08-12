# Legacy 中文欄位表清單(待遷英文)- 2026-06-22

dashboard-stream 共 **43 張**表帶中文欄位名,均為 award 開發前既有 legacy。
其中 **13 張有被 component 引用**(遷移需連 query_charts 一起改),其餘無引用可能是廢表。

| # | 表 | 中文欄數 | 被組件引用 | 中文欄位範例 |
|--:|---|--:|---|---|
| 1 | `building_landuse` | 8 | building_landuse | 編號, landuse group_metadata_用地分類, 分區簡稱, 圖層 |
| 2 | `building_license` | 20 | building_license | 監造人, 執照年度, 戶數, 執照號碼 |
| 3 | `building_permit` | 4 | building_license | 110年建造執照2_發照日期, 110年建造執照2_執照號碼, cadastral map_key_地籍圖key值, 發照日 |
| 4 | `building_publand` | 4 | building_publand | publand_1_土地權屬情形, cadastral map_key_地籍圖key值, publand_1_管理機關, publand_1_類型 |
| 5 | `building_renewarea_10` | 1 | building_renew | 案件編號 |
| 6 | `building_renewarea_40` | 1 | building_renew | 案件編號 |
| 7 | `building_renewunit_12` | 1 | building_renew | 案件編號 |
| 8 | `building_renewunit_20` | 1 | building_renew | 案件編號 |
| 9 | `building_renewunit_30` | 1 | building_renew | 案件編號 |
| 10 | `building_unsued_land` | 3 | building_unsued | cadastral map_key_地籍圖key值, 10712土地_1_土地權屬情形, 10712土地_1_管理機關 |
| 11 | `city_age_distribution_newtaipei` | 3 | city_age_distribution | 統計類型, 區域別, 年份 |
| 12 | `city_age_distribution_taipei` | 3 | city_age_distribution | 統計類型, 區域別, 年份 |
| 13 | `patrol_criminal_case` | 11 | patrol_criminalcase | 犯罪人口率[人/十萬人], 嫌疑犯[人], 破獲件數/積案[件], 發生件數[件] |
| 14 | `building_info_from_license` | 10 | (無,可能廢表) | 建築地點, 戶數, 地段地號, 建築面積 |
| 15 | `building_landuse_backup` | 8 | (無,可能廢表) | 圖層, 分區簡稱, landuse group_metadata_用地分類, 編號 |
| 16 | `building_license_all` | 3 | (無,可能廢表) | 發照日, 地段地號, 執照號碼 |
| 17 | `building_license_history` | 19 | (無,可能廢表) | 建築地點, 構造種類, 棟數, 設計人 |
| 18 | `building_permit_all` | 3 | (無,可能廢表) | 發照日, 執照號碼, 地段地號 |
| 19 | `building_permit_history` | 19 | (無,可能廢表) | 棟數, 執照號碼, 其他基地面積, 戶數 |
| 20 | `building_publand_history` | 4 | (無,可能廢表) | publand_1_土地權屬情形, publand_1_類型, publand_1_管理機關, cadastral map_key_地籍圖key值 |
| 21 | `building_unsued_land_history` | 3 | (無,可能廢表) | cadastral map_key_地籍圖key值, 10712土地_1_土地權屬情形, 10712土地_1_管理機關 |
| 22 | `building_unsued_nonpublic` | 4 | (無,可能廢表) | 編號, 管理機關, 閒置面積_㎡, 門牌 |
| 23 | `building_unsued_nonpublic_history` | 4 | (無,可能廢表) | 門牌, 閒置面積_㎡, 編號, 管理機關 |
| 24 | `building_unsued_public` | 13 | (無,可能廢表) | 行政區, 目前執行情形, 門牌, 閒置樓層_閒置樓層/該建物總樓層 |
| 25 | `building_unsued_public_history` | 13 | (無,可能廢表) | 閒置樓層_閒置樓層/該建物總樓層, 門牌, 行政區, 目前執行情形 |
| 26 | `patrol_designate_place` | 20 | (無,可能廢表) | 服務里別, 縣市, 聯絡人電話, 是否設置無障礙設施 |
| 27 | `patrol_designate_place_history` | 20 | (無,可能廢表) | 道路門牌, 室外, 聯絡人姓名, 管理人姓名 |
| 28 | `powerbi_g2_nation` | 2 | (無,可能廢表) | 人數, 資料更新時間 |
| 29 | `tp_building_height` | 9 | (無,可能廢表) | 圖例碼, 出入口高程, 地形碼, 線形碼 |
| 30 | `ubike_visibility_summary` | 1 | (無,可能廢表) | 租賃站名稱 |
| 31 | `v_e2` | 32 | (無,可能廢表) | 新竹市, 19歲以下, 日期, 60歲以上 |
| 32 | `v_e2_v2` | 32 | (無,可能廢表) | 19歲以下, 新竹市, 40~49歲, 日期 |
| 33 | `v_e2_v3` | 32 | (無,可能廢表) | 19歲以下, 新竹市, 40~49歲, 60歲以上 |
| 34 | `v_e2_v4` | 32 | (無,可能廢表) | 桃園市, 宜蘭縣, 總人數, 基隆市 |
| 35 | `v_g2` | 32 | (無,可能廢表) | 雲林縣, 20到29歲人數, 臺北市, 屏東縣 |
| 36 | `v_g2_nation` | 1 | (無,可能廢表) | 人數 |
| 37 | `v_g2_v2` | 32 | (無,可能廢表) | 新北市, 總人數, 基隆市, 臺東縣 |
| 38 | `v_g2_v3` | 32 | (無,可能廢表) | 臺東縣, 澎湖縣, 40到49歲人數, 新竹市 |
| 39 | `v_g2_v5` | 32 | (無,可能廢表) | 南投縣, 新竹縣, 臺中市, 金門縣 |
| 40 | `v_top_10_nation` | 1 | (無,可能廢表) | 人數 |
| 41 | `work_pump_station_static_info` | 5 | (無,可能廢表) | 起抽水位, 警戒水位, 流域, 站碼 |
| 42 | `work_sewer_location` | 5 | (無,可能廢表) | 緯度, 站碼, 經度, 站名 |
| 43 | `work_sewer_location_history` | 5 | (無,可能廢表) | 緯度, 行政區, 經度, 站碼 |
