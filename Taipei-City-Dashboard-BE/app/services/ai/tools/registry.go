package tools

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/ai/actions"
	"context"
	"encoding/json"
	"fmt"
	"math"
	"time"
)

// ToolFunc defines the signature for a tool function
type ToolFunc func(ctx context.Context, args string) (string, error)

var registry = make(map[string]ToolFunc)

func init() {
	// Register demo tools
	Register("get_current_time", GetCurrentTime)
	Register("get_population_summary", GetPopulationSummary)
	Register("get_nearby_stations", GetNearbyStations)
	Register("get_nearby_eco_facilities", GetNearbyEcoFacilities)
	Register("plan_route_to_nearest_eco_facility", PlanRouteToNearestEcoFacility)
	Register("list_eco_facilities_by_area", ListEcoFacilitiesByArea)
}

// Register adds a tool to the registry
func Register(name string, fn ToolFunc) {
	registry[name] = fn
}

// Execute calls a registered tool with the given arguments
func Execute(ctx context.Context, name string, args string) (string, error) {
	fn, ok := registry[name]
	if !ok {
		return "", fmt.Errorf("tool %s not found", name)
	}
	return fn(ctx, args)
}

// PopulationArgs defines the arguments for the get_population_summary tool
type PopulationArgs struct {
	City string `json:"city"`
	Year int    `json:"year"`
}

// GetPopulationSummary queries the population age distribution from the dashboard database
func GetPopulationSummary(ctx context.Context, args string) (string, error) {
	var params PopulationArgs
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("invalid arguments: %v", err)
	}

	// Default to Taipei if not specified or unrecognized
	tableName := "population_age_distribution_tpe"
	cityName := "台北市"
	if params.City == "new_taipei" {
		tableName = "population_age_distribution_new_tpe"
		cityName = "新北市"
	}

	// Define result structure based on database schema
	var result struct {
		Year      int `gorm:"column:year"`
		Young     int `gorm:"column:young_population"`
		Working   int `gorm:"column:working_age_population"`
		Elderly   int `gorm:"column:elderly_population"`
		DataTime  time.Time `gorm:"column:data_time"`
	}

	// Query the dashboard database
	err := models.DBDashboard.Table(tableName).
		Where("year = ?", params.Year).
		Order("data_time DESC"). // Get the latest record for that year
		First(&result).Error

	if err != nil {
		return "", fmt.Errorf("找不到 %s %d 年的人口統計資料: %v", cityName, params.Year, err)
	}

	// Format the response for the LLM
	return fmt.Sprintf(
		"【%d年 %s 人口結構概況】\n- 幼年人口 (0-14歲)：%d 人\n- 青壯年人口 (15-64歲)：%d 人\n- 老年人口 (65歲以上)：%d 人\n- 總人口： %d 人\n- 數據更新時間：%s",
		result.Year, cityName, result.Young, result.Working, result.Elderly,
		result.Young+result.Working+result.Elderly,
		result.DataTime.Format("2006-01-02"),
	), nil
}

// NearbyStationsArgs defines the arguments for the get_nearby_stations tool
type NearbyStationsArgs struct {
	Lat    float64 `json:"lat"`
	Lng    float64 `json:"lng"`
	Radius int     `json:"radius"`
}

// GetNearbyStations returns MRT accessibility facilities (elevator/ramp exits)
// within the given radius (meters) of the user's coordinate, joined with the
// latest active alert per station. Returned as a JSON string for the LLM.
func GetNearbyStations(ctx context.Context, args string) (string, error) {
	var params NearbyStationsArgs
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("invalid arguments: %v", err)
	}
	if params.Lat == 0 && params.Lng == 0 {
		return "", fmt.Errorf("lat/lng are required")
	}

	radius := params.Radius
	if radius <= 0 {
		radius = 500
	}

	stations, err := models.GetMrtStationsNearby(params.Lat, params.Lng, radius)
	if err != nil {
		return "", fmt.Errorf("查詢附近站點失敗: %v", err)
	}

	if len(stations) == 0 {
		return fmt.Sprintf(
			`{"radius_m":%d,"count":0,"stations":[],"note":"半徑內無資料，可建議使用者擴大查詢半徑"}`,
			radius,
		), nil
	}

	alertCount := 0
	for _, s := range stations {
		if s.AlertStatus == "active" {
			alertCount++
		}
	}

	payload := map[string]interface{}{
		"radius_m":           radius,
		"count":              len(stations),
		"active_alert_count": alertCount,
		"stations":           stations,
	}
	b, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("序列化結果失敗: %v", err)
	}
	return string(b), nil
}

// NearbyEcoFacilitiesArgs defines the arguments for the get_nearby_eco_facilities tool.
// FacilityTypes 為空陣列代表查全部（環保餐廳 + 綠色商店 + 實物銀行）。
type NearbyEcoFacilitiesArgs struct {
	Lat           float64  `json:"lat"`
	Lng           float64  `json:"lng"`
	Radius        int      `json:"radius"`
	FacilityTypes []string `json:"facility_types"`
}

// GetNearbyEcoFacilities returns eco-diet facilities (eco-restaurants, green stores,
// food banks) within radius meters of (lat, lng), grouped by facility type.
// 對齊 GetNearbyStations（registry.go:96）模式，回傳 JSON 字串給 LLM。
func GetNearbyEcoFacilities(ctx context.Context, args string) (string, error) {
	var params NearbyEcoFacilitiesArgs
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("invalid arguments: %v", err)
	}
	if params.Lat == 0 && params.Lng == 0 {
		return "", fmt.Errorf("lat/lng are required")
	}

	radius := params.Radius
	if radius <= 0 {
		radius = 800
	}

	// 空陣列＝全部三類
	wanted := map[string]bool{}
	if len(params.FacilityTypes) == 0 {
		wanted["restaurant"] = true
		wanted["green_store"] = true
		wanted["food_bank"] = true
	} else {
		for _, t := range params.FacilityTypes {
			wanted[t] = true
		}
	}

	const perTypeCap = 20

	payload := map[string]interface{}{
		"radius_m":      radius,
		"queried_types": []string{},
	}
	count := map[string]int{}
	queried := []string{}

	if wanted["restaurant"] {
		queried = append(queried, "restaurant")
		rows, err := models.GetEcoRestaurantNearby(params.Lat, params.Lng, radius)
		if err != nil {
			return "", fmt.Errorf("查詢附近環保餐廳失敗: %v", err)
		}
		if len(rows) > perTypeCap {
			rows = rows[:perTypeCap]
		}
		payload["restaurant"] = rows
		count["restaurant"] = len(rows)
	}
	if wanted["green_store"] {
		queried = append(queried, "green_store")
		rows, err := models.GetGreenStoreNearby(params.Lat, params.Lng, radius)
		if err != nil {
			return "", fmt.Errorf("查詢附近綠色商店失敗: %v", err)
		}
		if len(rows) > perTypeCap {
			rows = rows[:perTypeCap]
		}
		payload["green_store"] = rows
		count["green_store"] = len(rows)
	}
	if wanted["food_bank"] {
		queried = append(queried, "food_bank")
		rows, err := models.GetFoodBankNearbyByRadius(params.Lat, params.Lng, radius)
		if err != nil {
			return "", fmt.Errorf("查詢附近實物銀行失敗: %v", err)
		}
		if len(rows) > perTypeCap {
			rows = rows[:perTypeCap]
		}
		payload["food_bank"] = rows
		count["food_bank"] = len(rows)
	}

	totalCount := 0
	for _, n := range count {
		totalCount += n
	}

	payload["queried_types"] = queried
	payload["count"] = count
	payload["total_count"] = totalCount
	if totalCount == 0 {
		payload["note"] = "半徑內無資料，可建議使用者擴大查詢半徑或調整設施類型"
	}

	b, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("序列化結果失敗: %v", err)
	}
	return string(b), nil
}

// PlanRouteArgs defines the arguments for the plan_route_to_nearest_eco_facility tool.
type PlanRouteArgs struct {
	FacilityType string  `json:"facility_type"`
	Lat          float64 `json:"lat"`
	Lng          float64 `json:"lng"`
	Radius       int     `json:"radius"`
}

// 步行速度約 1.2 m/s，用於由直線距離粗估步行秒數。FE 會以 Mapbox Directions
// 回傳值覆寫真實曲折距離 / 時間，這裡只給 LLM 寫進回答用。
const planRouteWalkSpeedMps = 1.2

// 設施類型代碼 → 中文 label，給 LLM 與 user-facing 回答使用。
var planRouteFacilityLabel = map[string]string{
	"restaurant":  "環保餐廳",
	"green_store": "綠色商店",
	"food_bank":   "實物銀行",
}

// PlanRouteToNearestEcoFacility 找出指定設施類型距使用者最近的一家，並透過 ctx 寫入
// 兩條 actions（show_layer + draw_route）給 controller 收集回 FE。半徑 fallback：
// 先用 args.radius（預設 800），找不到自動擴大到 3000m 再查一次；仍然 0 筆時不寫
// actions、回字串告知 LLM。
func PlanRouteToNearestEcoFacility(ctx context.Context, args string) (string, error) {
	var p PlanRouteArgs
	if err := parseArgs(args, &p); err != nil {
		return "", fmt.Errorf("invalid arguments: %v", err)
	}
	if p.Lat == 0 && p.Lng == 0 {
		return "", fmt.Errorf("lat/lng are required")
	}
	if _, ok := planRouteFacilityLabel[p.FacilityType]; !ok {
		return "", fmt.Errorf("facility_type must be one of: restaurant | green_store | food_bank")
	}

	radius := p.Radius
	if radius <= 0 {
		radius = 800
	}

	findOnce := func(r int) (name string, lat, lng float64, dist int, err error) {
		switch p.FacilityType {
		case "restaurant":
			rows, e := models.GetEcoRestaurantNearby(p.Lat, p.Lng, r)
			if e != nil {
				err = e
				return
			}
			if len(rows) == 0 {
				return
			}
			return rows[0].Name, rows[0].Lat, rows[0].Lng, rows[0].DistanceM, nil
		case "green_store":
			rows, e := models.GetGreenStoreNearby(p.Lat, p.Lng, r)
			if e != nil {
				err = e
				return
			}
			if len(rows) == 0 {
				return
			}
			return rows[0].Name, rows[0].Lat, rows[0].Lng, rows[0].DistanceM, nil
		default: // food_bank
			rows, e := models.GetFoodBankNearbyByRadius(p.Lat, p.Lng, r)
			if e != nil {
				err = e
				return
			}
			if len(rows) == 0 {
				return
			}
			return rows[0].Name, rows[0].Lat, rows[0].Lng, rows[0].DistanceM, nil
		}
	}

	name, lat, lng, dist, err := findOnce(radius)
	if err != nil {
		return "", fmt.Errorf("查詢失敗: %v", err)
	}
	expanded := false
	if name == "" {
		const wide = 3000
		name, lat, lng, dist, err = findOnce(wide)
		if err != nil {
			return "", fmt.Errorf("查詢失敗: %v", err)
		}
		if name != "" {
			expanded = true
			radius = wide
		}
	}

	facLabel := planRouteFacilityLabel[p.FacilityType]

	if name == "" {
		// 半徑 3000m 內仍無；不 emit actions
		empty := map[string]interface{}{
			"status":           "empty",
			"facility_type":    p.FacilityType,
			"facility_label":   facLabel,
			"queried_radius_m": radius,
			"note":             "半徑 3000 公尺內查無此類設施，請婉轉告知使用者並建議改用其他設施類型或前往其他區域。",
		}
		b, _ := json.Marshal(empty)
		return string(b), nil
	}

	durationS := int(math.Round(float64(dist) / planRouteWalkSpeedMps))

	actions.Append(ctx, actions.ChatAction{
		Type:         "show_layer",
		FacilityType: p.FacilityType,
	})
	actions.Append(ctx, actions.ChatAction{
		Type:         "draw_route",
		FacilityType: p.FacilityType,
		To:           &actions.Point{Lat: lat, Lng: lng, Name: name},
		DistanceM:    dist,
		DurationS:    durationS,
	})

	durationMin := durationS / 60
	if durationMin < 1 {
		durationMin = 1
	}

	noteParts := []string{
		fmt.Sprintf("已為使用者規劃步行路線並自動開啟%s地圖圖層；請以繁體中文 1～2 句簡短告知最近一家%s「%s」、直線距離約 %d 公尺、約步行 %d 分鐘",
			facLabel, facLabel, name, dist, durationMin),
	}
	if expanded {
		noteParts = append(noteParts, "（半徑 800 公尺內無此類設施，已自動擴大到 3000 公尺）")
	}
	noteParts = append(noteParts, "。回答中不要重述座標數字。")

	result := map[string]interface{}{
		"status":           "ok",
		"facility_type":    p.FacilityType,
		"facility_label":   facLabel,
		"queried_radius_m": radius,
		"radius_expanded":  expanded,
		"nearest": map[string]interface{}{
			"name":              name,
			"distance_m":        dist,
			"approx_duration_s": durationS,
			"lat":               lat,
			"lng":               lng,
		},
		"note": joinNonEmpty(noteParts),
	}
	b, err := json.Marshal(result)
	if err != nil {
		return "", fmt.Errorf("序列化結果失敗: %v", err)
	}
	return string(b), nil
}

// EcoFacilitiesByAreaArgs — 「指定地區模式」tool 的 args；不依賴 GPS。
// district 與 city 至少要給一個，facility_types 為空陣列代表全部三類。
type EcoFacilitiesByAreaArgs struct {
	District      string   `json:"district"`
	City          string   `json:"city"`
	FacilityTypes []string `json:"facility_types"`
}

// ListEcoFacilitiesByArea 依 district / city 過濾綠色飲食設施清單。
// 對應 controllers.PostEcoDietNearbyChat 的「指定地區模式」prompt 區段：
// 使用者點名行政區或縣市時，AI 應呼叫此 tool 而不是 get_nearby_eco_facilities。
func ListEcoFacilitiesByArea(ctx context.Context, args string) (string, error) {
	var p EcoFacilitiesByAreaArgs
	if err := parseArgs(args, &p); err != nil {
		return "", fmt.Errorf("invalid arguments: %v", err)
	}
	if p.District == "" && p.City == "" {
		return "", fmt.Errorf("district 與 city 至少要提供一個")
	}

	wanted := map[string]bool{}
	if len(p.FacilityTypes) == 0 {
		wanted["restaurant"] = true
		wanted["green_store"] = true
		wanted["food_bank"] = true
	} else {
		for _, t := range p.FacilityTypes {
			wanted[t] = true
		}
	}

	const perTypeCap = 20

	payload := map[string]interface{}{
		"district":      p.District,
		"city":          p.City,
		"queried_types": []string{},
	}
	count := map[string]int{}
	queried := []string{}

	if wanted["restaurant"] {
		queried = append(queried, "restaurant")
		rows, err := models.GetEcoRestaurantList(p.District, "", p.City)
		if err != nil {
			return "", fmt.Errorf("查詢環保餐廳失敗: %v", err)
		}
		if len(rows) > perTypeCap {
			rows = rows[:perTypeCap]
		}
		payload["restaurant"] = rows
		count["restaurant"] = len(rows)
	}
	if wanted["green_store"] {
		queried = append(queried, "green_store")
		all, err := models.GetGreenStorePoints("", p.City)
		if err != nil {
			return "", fmt.Errorf("查詢綠色商店失敗: %v", err)
		}
		rows := filterGreenStoreByDistrict(all, p.District)
		if len(rows) > perTypeCap {
			rows = rows[:perTypeCap]
		}
		payload["green_store"] = rows
		count["green_store"] = len(rows)
	}
	if wanted["food_bank"] {
		queried = append(queried, "food_bank")
		all, err := models.GetFoodBankPoints()
		if err != nil {
			return "", fmt.Errorf("查詢實物銀行失敗: %v", err)
		}
		rows := filterFoodBankByArea(all, p.District, p.City)
		if len(rows) > perTypeCap {
			rows = rows[:perTypeCap]
		}
		payload["food_bank"] = rows
		count["food_bank"] = len(rows)
	}

	totalCount := 0
	for _, n := range count {
		totalCount += n
	}
	payload["queried_types"] = queried
	payload["count"] = count
	payload["total_count"] = totalCount
	if totalCount == 0 {
		payload["note"] = "此地區查無符合條件的設施，請告知使用者並建議改其他行政區、縣市或設施類型"
	}

	b, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("序列化結果失敗: %v", err)
	}
	return string(b), nil
}

func filterGreenStoreByDistrict(rows []models.GreenStorePoint, district string) []models.GreenStorePoint {
	if district == "" {
		return rows
	}
	out := make([]models.GreenStorePoint, 0, len(rows))
	for _, r := range rows {
		if r.District != nil && *r.District == district {
			out = append(out, r)
		}
	}
	return out
}

func filterFoodBankByArea(rows []models.FoodBankPoint, district, city string) []models.FoodBankPoint {
	if district == "" && city == "" {
		return rows
	}
	out := make([]models.FoodBankPoint, 0, len(rows))
	for _, r := range rows {
		if district != "" {
			if r.District == nil || *r.District != district {
				continue
			}
		}
		if city != "" && r.City != city {
			continue
		}
		out = append(out, r)
	}
	return out
}

func joinNonEmpty(parts []string) string {
	out := ""
	for _, s := range parts {
		out += s
	}
	return out
}

// GetCurrentTime is a demo tool that returns the current Taipei time
func GetCurrentTime(ctx context.Context, args string) (string, error) {
	loc, err := time.LoadLocation("Asia/Taipei")
	if err != nil {
		// Fallback to UTC if timezone data is missing
		return time.Now().Format(time.RFC3339), nil
	}
	return time.Now().In(loc).Format("2006-01-02 15:04:05"), nil
}

// Helper to parse JSON arguments if needed in future tools
func parseArgs(args string, v interface{}) error {
	return json.Unmarshal([]byte(args), v)
}
