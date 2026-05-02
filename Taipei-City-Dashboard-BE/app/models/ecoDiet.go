package models

import (
	"math"

	"github.com/lib/pq"
)

// 市民綠色飲食行為流程儀表板 — model layer
// API contract: docs/eco_diet_openapi.yaml
// DE schema:    Taipei-City-Dashboard-BE/scripts/eco_diet_schema.sql

// ─── 領域 struct (對齊 mrtA11y 既有 pattern) ─────────────────────────

// EcoRestaurantPoint 對應 eco_restaurant 表的一列。env_actions 為 PostgreSQL TEXT[]，
// 使用 pq.StringArray 才能正確 scan；新北側資料一律為空陣列（DE plan §11 修正 #3）。
type EcoRestaurantPoint struct {
	SourceDataset string         `gorm:"column:source_dataset" json:"source_dataset"`
	SeqNo         string         `gorm:"column:seq_no"         json:"seq_no"`
	Name          string         `gorm:"column:name"           json:"name"`
	Address       string         `gorm:"column:address"        json:"address"`
	City          string         `gorm:"column:city"           json:"city"`
	District      *string        `gorm:"column:district"       json:"district"`
	Tel           *string        `gorm:"column:tel"            json:"tel"`
	EnvActions    pq.StringArray `gorm:"column:env_actions;type:text[]" json:"env_actions"`
	Lng           float64        `gorm:"column:lng"            json:"lng"`
	Lat           float64        `gorm:"column:lat"            json:"lat"`
}

// GreenStorePoint 對應 green_store 表的一列。
type GreenStorePoint struct {
	SourceDataset string  `gorm:"column:source_dataset" json:"source_dataset"`
	StoreCode     *string `gorm:"column:store_code"     json:"store_code"`
	Name          string  `gorm:"column:name"           json:"name"`
	Address       string  `gorm:"column:address"        json:"address"`
	City          string  `gorm:"column:city"           json:"city"`
	District      *string `gorm:"column:district"       json:"district"`
	Tel           *string `gorm:"column:tel"            json:"tel"`
	StoreType     *string `gorm:"column:store_type"     json:"store_type"`
	Lng           float64 `gorm:"column:lng"            json:"lng"`
	Lat           float64 `gorm:"column:lat"            json:"lat"`
}

// FoodBankPoint 對應 food_bank 表的一列。新北側 org_type 為 NULL（DE plan §11 修正 #6）；
// 臺北側 postal_code/tel 為 NULL（S5 來源無此欄位，DE plan §1.1）。
type FoodBankPoint struct {
	SourceDataset string  `gorm:"column:source_dataset" json:"source_dataset"`
	SeqNo         string  `gorm:"column:seq_no"         json:"seq_no"`
	Name          string  `gorm:"column:name"           json:"name"`
	OrgType       *string `gorm:"column:org_type"       json:"org_type"`
	City          string  `gorm:"column:city"           json:"city"`
	District      *string `gorm:"column:district"       json:"district"`
	DistrictCode  *string `gorm:"column:district_code"  json:"district_code"`
	PostalCode    *string `gorm:"column:postal_code"    json:"postal_code"`
	Address       string  `gorm:"column:address"        json:"address"`
	Tel           *string `gorm:"column:tel"            json:"tel"`
	Lng           float64 `gorm:"column:lng"            json:"lng"`
	Lat           float64 `gorm:"column:lat"            json:"lat"`
}

// FoodBankPointNearby 嵌入 FoodBankPoint 並補 distance_m，對齊 MrtA11yStationNearby（[mrtA11y.go:171]）。
type FoodBankPointNearby struct {
	FoodBankPoint
	DistanceM int `json:"distance_m"`
}

// ─── 私用 raw row（內部聚合用） ──────────────────────────────────────

// ecoDietWasteRow 是 gov_open_waste_yearly 經 UNION ALL 攤平後的一列；
// y_axis 已經是 `{county}-{metric_label}` 形式，餵給共用的 groupThreeDimRows() 即可。
type ecoDietWasteRow struct {
	Xaxis string `gorm:"column:x_axis"`
	Icon  string `gorm:"column:icon"`
	Yaxis string `gorm:"column:y_axis"`
	Data  int    `gorm:"column:data"`
}

// ─── C1a: GET /eco_diet/restaurant/points ───────────────────────────

// GetEcoRestaurantPoints 回傳含座標的全部餐廳。geocode 失敗的 row（lng/lat NULL）
// 會被 filter 掉，避免 FE 地圖上出現 (0,0) 等假點。
func GetEcoRestaurantPoints() ([]EcoRestaurantPoint, error) {
	var rows []EcoRestaurantPoint
	err := DBDashboard.Raw(`
		SELECT source_dataset, seq_no, name, address, city, district, tel,
		       env_actions, lng, lat
		FROM eco_restaurant
		WHERE lng IS NOT NULL AND lat IS NOT NULL
		ORDER BY city, district, name
	`).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	normalizeEnvActions(rows)
	return rows, nil
}

// ─── C1b: GET /eco_diet/restaurant/density-by-district ──────────────

// GetEcoRestaurantDensityByDistrict 回傳行政區密度。city 為空字串時回雙北合併。
func GetEcoRestaurantDensityByDistrict(city string) ([]TwoDimensionalDataOutput, error) {
	var rows []TwoDimensionalData
	var err error
	if city == "" {
		err = DBDashboard.Raw(`
			SELECT district AS x_axis, COUNT(*)::float8 AS data
			FROM eco_restaurant
			WHERE district IS NOT NULL
			GROUP BY district
			ORDER BY data DESC, district
		`).Scan(&rows).Error
	} else {
		err = DBDashboard.Raw(`
			SELECT district AS x_axis, COUNT(*)::float8 AS data
			FROM eco_restaurant
			WHERE district IS NOT NULL AND city = ?
			GROUP BY district
			ORDER BY data DESC, district
		`, city).Scan(&rows).Error
	}
	if err != nil {
		return nil, err
	}
	return []TwoDimensionalDataOutput{{Data: rows}}, nil
}

// ─── C2: GET /eco_diet/restaurant/count-by-city ─────────────────────

func GetEcoRestaurantCountByCity() ([]TwoDimensionalDataOutput, error) {
	var rows []TwoDimensionalData
	err := DBDashboard.Raw(`
		SELECT city AS x_axis, COUNT(*)::float8 AS data
		FROM eco_restaurant
		GROUP BY city
		ORDER BY x_axis
	`).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	return []TwoDimensionalDataOutput{{Data: rows}}, nil
}

// ─── C3: GET /eco_diet/restaurant/list ──────────────────────────────

// GetEcoRestaurantList 三個 filter 皆 optional（空字串視為不過濾）。
// `action` 對應 env_actions text[] 的 = ANY 比對；新北側 env_actions 為空，
// 因此若 `action` 有值，回傳結果會自然排除新北資料。
func GetEcoRestaurantList(district, action, city string) ([]EcoRestaurantPoint, error) {
	var rows []EcoRestaurantPoint
	err := DBDashboard.Raw(`
		SELECT source_dataset, seq_no, name, address, city, district, tel,
		       env_actions, lng, lat
		FROM eco_restaurant
		WHERE lng IS NOT NULL AND lat IS NOT NULL
		  AND (NULLIF(?, '') IS NULL OR district = ?)
		  AND (NULLIF(?, '') IS NULL OR ? = ANY(env_actions))
		  AND (NULLIF(?, '') IS NULL OR city = ?)
		ORDER BY city, district, name
	`, district, district, action, action, city, city).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	normalizeEnvActions(rows)
	return rows, nil
}

// ─── C4: GET /eco_diet/green_store/points ───────────────────────────

// GetGreenStorePoints 兩個 filter 皆 optional；省略時回全量。
func GetGreenStorePoints(storeType, city string) ([]GreenStorePoint, error) {
	var rows []GreenStorePoint
	err := DBDashboard.Raw(`
		SELECT source_dataset, store_code, name, address, city, district, tel,
		       store_type, lng, lat
		FROM green_store
		WHERE lng IS NOT NULL AND lat IS NOT NULL
		  AND (NULLIF(?, '') IS NULL OR store_type = ?)
		  AND (NULLIF(?, '') IS NULL OR city = ?)
		ORDER BY city, district, name
	`, storeType, storeType, city, city).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	return rows, nil
}

// ─── C5: GET /eco_diet/waste/yearly ─────────────────────────────────

// GetWasteYearly 回傳雙北 × 4 metric = 8 條 series。
// Series 命名 `{county}-{metric_label}`，FE 用 split('-') 拆解兩個維度。
func GetWasteYearly() ([]ThreeDimensionalDataOutput, []string, error) {
	var rows []ecoDietWasteRow
	err := DBDashboard.Raw(`
		WITH yearly AS (
			SELECT data_year, county,
			       food_wastes_recycled, garbage_clearance,
			       garbage_recycled, garbage_generated
			FROM gov_open_waste_yearly
			WHERE county IN ('臺北市', '新北市')
		)
		SELECT data_year::text AS x_axis, '' AS icon,
		       county || '-廚餘量' AS y_axis,
		       ROUND(food_wastes_recycled)::int AS data
		FROM yearly
		UNION ALL
		SELECT data_year::text, '', county || '-一般垃圾',
		       ROUND(garbage_clearance)::int FROM yearly
		UNION ALL
		SELECT data_year::text, '', county || '-資源垃圾',
		       ROUND(garbage_recycled)::int  FROM yearly
		UNION ALL
		SELECT data_year::text, '', county || '-總產生量',
		       ROUND(garbage_generated)::int FROM yearly
		ORDER BY 1, 3
	`).Scan(&rows).Error
	if err != nil {
		return nil, nil, err
	}
	return groupEcoDietWasteRows(rows)
}

// ─── C5b: GET /eco_diet/waste/carbon_footprint_yearly ───────────────

// 平均碳足跡係數（kg CO2e / 公噸 廢棄物），來源：repo 根目錄 `coal_emission.csv`：
//
//   - 廚餘:   有機廢棄物免發酵轉化肥料處理服務（n=1）→ 48.3
//   - 一般垃圾: 4 座都市垃圾焚化廠平均（永康/城西/苗栗/岡山，n=4，{327,333,340,360}）→ 340
//   - 資源垃圾: 再生料-廢*容器- 系列（kg→公噸 換算後 n=10）→ 369
//
// SQL 內以 公噸 CO2e/年（kg/1000）輸出，量級對齊 gov_open_waste_yearly 既有公噸欄位。
const (
	wasteCarbonCoefFood     = 0.0483 // 公噸 CO2e/公噸 廚餘
	wasteCarbonCoefGarbage  = 0.340  // 公噸 CO2e/公噸 一般垃圾
	wasteCarbonCoefRecycled = 0.369  // 公噸 CO2e/公噸 資源垃圾
)

// GetWasteCarbonFootprintYearly 回傳雙北逐年「廢棄物總碳足跡」(公噸 CO2e/年)。
// 公式：food_wastes_recycled × 0.0483 + garbage_clearance × 0.34 + garbage_recycled × 0.369。
// Series 命名 `{county}-碳足跡`，與 GetWasteYearly 同樣可被 FE 用 split('-') 拆解。
func GetWasteCarbonFootprintYearly() ([]ThreeDimensionalDataOutput, []string, error) {
	var rows []ecoDietWasteRow
	err := DBDashboard.Raw(`
		SELECT data_year::text AS x_axis, '' AS icon,
		       county || '-碳足跡' AS y_axis,
		       ROUND(
		           food_wastes_recycled * ? +
		           garbage_clearance    * ? +
		           garbage_recycled     * ?
		       )::int AS data
		FROM gov_open_waste_yearly
		WHERE county IN ('臺北市', '新北市')
		ORDER BY 1, 3
	`, wasteCarbonCoefFood, wasteCarbonCoefGarbage, wasteCarbonCoefRecycled).
		Scan(&rows).Error
	if err != nil {
		return nil, nil, err
	}
	return groupEcoDietWasteRows(rows)
}

// ─── C7a: GET /eco_diet/food_bank/points ────────────────────────────

func GetFoodBankPoints() ([]FoodBankPoint, error) {
	var rows []FoodBankPoint
	err := DBDashboard.Raw(`
		SELECT source_dataset, seq_no, name, org_type,
		       city, district, district_code, postal_code,
		       address, tel, lng, lat
		FROM food_bank
		WHERE lng IS NOT NULL AND lat IS NOT NULL
		ORDER BY city, district, name
	`).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	return rows, nil
}

// ─── C7b: GET /eco_diet/food_bank/nearby ────────────────────────────

// GetFoodBankNearby 載入全量 → 計算 Haversine → 升冪排序 → 切前 limit 筆。
// limit <= 0 時回全部。對齊 MrtA11yStationNearby 既有實作（mrtA11y.go:179）。
func GetFoodBankNearby(lat, lng float64, limit int) ([]FoodBankPointNearby, error) {
	all, err := GetFoodBankPoints()
	if err != nil {
		return nil, err
	}
	out := make([]FoodBankPointNearby, len(all))
	for i, p := range all {
		out[i] = FoodBankPointNearby{
			FoodBankPoint: p,
			DistanceM:     int(math.Round(haversineMetersFoodBank(lat, lng, p.Lat, p.Lng))),
		}
	}
	// Insertion sort by DistanceM (small slice)
	for i := 1; i < len(out); i++ {
		for j := i; j > 0 && out[j-1].DistanceM > out[j].DistanceM; j-- {
			out[j-1], out[j] = out[j], out[j-1]
		}
	}
	if limit > 0 && limit < len(out) {
		out = out[:limit]
	}
	return out, nil
}

// haversineMetersFoodBank 是大圓距離（公尺）。命名加 FoodBank 避免與
// mrtA11y.go:haversineMeters 衝突（同 package 不能有同名 unexported function）。
func haversineMetersFoodBank(lat1, lng1, lat2, lng2 float64) float64 {
	const earthRadiusM = 6371000.0
	rad := func(d float64) float64 { return d * math.Pi / 180 }
	dLat := rad(lat2 - lat1)
	dLng := rad(lng2 - lng1)
	a := math.Sin(dLat/2)*math.Sin(dLat/2) +
		math.Cos(rad(lat1))*math.Cos(rad(lat2))*math.Sin(dLng/2)*math.Sin(dLng/2)
	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))
	return earthRadiusM * c
}

// ─── helpers ────────────────────────────────────────────────────────

// normalizeEnvActions 把 nil pq.StringArray 改成空陣列，確保 JSON 輸出 `[]` 而不是 `null`。
// DE plan §5.2 schema 允許 env_actions 為 NULL（無 NOT NULL 約束）；雖然 DE plan §5.3 ETL
// 實務上一律 populate（新北側填 []），但 BE 自己吸收這個邊緣情況，不要求 DE 改 schema。
func normalizeEnvActions(rows []EcoRestaurantPoint) {
	for i := range rows {
		if rows[i].EnvActions == nil {
			rows[i].EnvActions = pq.StringArray{}
		}
	}
}

// groupEcoDietWasteRows 將攤平的 (year, series_name, value) 列 reshape 成
// ThreeDimensional 結構：每個 unique y_axis 一條 series、x_axis 收集成 categories。
// 與 mrtA11y.go:groupLineRows 邏輯相同，但因為它是 unexported 不能跨檔重用。
func groupEcoDietWasteRows(rows []ecoDietWasteRow) ([]ThreeDimensionalDataOutput, []string, error) {
	var data []ThreeDimensionalDataOutput
	var categories []string
	for _, r := range rows {
		// collect unique x_axis (year)
		var foundX bool
		for _, c := range categories {
			if c == r.Xaxis {
				foundX = true
				break
			}
		}
		if !foundX {
			categories = append(categories, r.Xaxis)
		}
		// group by y_axis (series name)
		var foundY bool
		for i := range data {
			if data[i].Name == r.Yaxis {
				data[i].Data = append(data[i].Data, r.Data)
				foundY = true
				break
			}
		}
		if !foundY {
			data = append(data, ThreeDimensionalDataOutput{
				Name: r.Yaxis,
				Icon: r.Icon,
				Data: []int{r.Data},
			})
		}
	}
	if categories == nil {
		categories = []string{}
	}
	return data, categories, nil
}
