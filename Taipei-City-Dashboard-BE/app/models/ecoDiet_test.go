package models

import (
	"sort"
	"testing"
)

// 市民綠色飲食行為流程儀表板 — model layer tests
// 假資料：scripts/eco_diet_seed.sql；assertable counts 在 §Step 2 完成回報已記錄。
//
// initTestDB / getTestEnv 來自同 package 的 mrtA11y_test.go，無需重定義。

// ─── C1a: GET /eco_diet/restaurant/points ───────────────────────────

func TestGetEcoRestaurantPoints_Returns13RowsWithGeoAndActions(t *testing.T) {
	initTestDB(t)

	rows, err := GetEcoRestaurantPoints()
	if err != nil {
		t.Fatalf("GetEcoRestaurantPoints() error = %v", err)
	}
	// Seed: 臺北 7 + 新北 6 = 13
	if len(rows) != 13 {
		t.Fatalf("expected 13 rows, got %d", len(rows))
	}

	cityCounts := map[string]int{}
	var sawTaipeiActions, sawNewTaipeiEmptyActions bool
	for _, r := range rows {
		cityCounts[r.City]++
		if r.Lng == 0 || r.Lat == 0 {
			t.Errorf("row %s missing lng/lat", r.Name)
		}
		if r.City == "臺北市" && len(r.EnvActions) > 0 {
			sawTaipeiActions = true
		}
		if r.City == "新北市" && len(r.EnvActions) == 0 {
			sawNewTaipeiEmptyActions = true
		}
	}
	if cityCounts["臺北市"] != 7 {
		t.Errorf("臺北市 count = %d, want 7", cityCounts["臺北市"])
	}
	if cityCounts["新北市"] != 6 {
		t.Errorf("新北市 count = %d, want 6", cityCounts["新北市"])
	}
	if !sawTaipeiActions {
		t.Error("expected at least one Taipei row with non-empty env_actions")
	}
	if !sawNewTaipeiEmptyActions {
		t.Error("expected New Taipei rows to have empty env_actions ([])")
	}
}

// TestGetEcoRestaurantPoints_NullGeoIncludedAsZeroSentinel covers MVP mode where
// DE has not yet geocoded (lng/lat = NULL). BE must include the row anyway with
// lng=0, lat=0 acting as a sentinel; FE detects (0,0) and skips map marker.
func TestGetEcoRestaurantPoints_NullGeoIncludedAsZeroSentinel(t *testing.T) {
	initTestDB(t)

	const fixtureSeqNo = "__null_geo_test__"
	if err := DBDashboard.Exec(`
		INSERT INTO eco_restaurant
		  (source_dataset, seq_no, name, address, city, district, tel,
		   env_actions, lng, lat, data_time)
		VALUES
		  ('tpe_00002761', ?, 'NULL_GEO_FIXTURE', '臺北市測試區測試路2號',
		   '臺北市', '測試區', NULL, ARRAY[]::TEXT[], NULL, NULL, '2026-05-01 10:00:00+08')
	`, fixtureSeqNo).Error; err != nil {
		t.Fatalf("insert fixture: %v", err)
	}
	t.Cleanup(func() {
		_ = DBDashboard.Exec(`DELETE FROM eco_restaurant WHERE seq_no = ?`, fixtureSeqNo).Error
	})

	rows, err := GetEcoRestaurantPoints()
	if err != nil {
		t.Fatalf("GetEcoRestaurantPoints() error = %v", err)
	}
	var found *EcoRestaurantPoint
	for i := range rows {
		if rows[i].SeqNo == fixtureSeqNo {
			found = &rows[i]
			break
		}
	}
	if found == nil {
		t.Fatalf("fixture row with seq_no=%q not returned (filter regression)", fixtureSeqNo)
	}
	if found.Lng != 0 || found.Lat != 0 {
		t.Errorf("Lng/Lat = (%v,%v), want (0,0) sentinel for NULL", found.Lng, found.Lat)
	}
}

// TestGetEcoRestaurantPoints_NullEnvActionsReturnsEmptyArray covers DE plan §5.2 edge case:
// schema permits env_actions NULL, but BE must marshal as `[]` for FE compatibility.
// Inserts a fixture row with NULL env_actions, verifies returned struct has non-nil
// EnvActions of length 0 (so json.Marshal produces `[]`, not `null`).
func TestGetEcoRestaurantPoints_NullEnvActionsReturnsEmptyArray(t *testing.T) {
	initTestDB(t)

	const fixtureSeqNo = "__null_env_test__"
	if err := DBDashboard.Exec(`
		INSERT INTO eco_restaurant
		  (source_dataset, seq_no, name, address, city, district, tel,
		   env_actions, lng, lat, data_time)
		VALUES
		  ('tpe_00002761', ?, 'NULL_ENV_ACTIONS_FIXTURE', '臺北市測試區測試路1號',
		   '臺北市', '測試區', NULL, NULL, 121.5, 25.05, '2026-05-01 10:00:00+08')
	`, fixtureSeqNo).Error; err != nil {
		t.Fatalf("insert fixture: %v", err)
	}
	t.Cleanup(func() {
		_ = DBDashboard.Exec(`DELETE FROM eco_restaurant WHERE seq_no = ?`, fixtureSeqNo).Error
	})

	rows, err := GetEcoRestaurantPoints()
	if err != nil {
		t.Fatalf("GetEcoRestaurantPoints() error = %v", err)
	}
	var found *EcoRestaurantPoint
	for i := range rows {
		if rows[i].SeqNo == fixtureSeqNo {
			found = &rows[i]
			break
		}
	}
	if found == nil {
		t.Fatalf("fixture row with seq_no=%q not returned", fixtureSeqNo)
	}
	if found.EnvActions == nil {
		t.Errorf("EnvActions = nil, want non-nil empty slice (so JSON marshals as `[]`)")
	}
	if len(found.EnvActions) != 0 {
		t.Errorf("EnvActions len = %d, want 0", len(found.EnvActions))
	}
}

// ─── C1b: GET /eco_diet/restaurant/density-by-district ──────────────

func TestGetEcoRestaurantDensityByDistrict_NoFilterCoversBothCities(t *testing.T) {
	initTestDB(t)

	out, err := GetEcoRestaurantDensityByDistrict("")
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(out) != 1 {
		t.Fatalf("expected 1 outer entry, got %d", len(out))
	}
	// Seed: 8 distinct districts (松山, 信義, 大安, 中山, 板橋, 新莊, 中和, 蘆洲)
	if len(out[0].Data) != 8 {
		t.Fatalf("expected 8 districts, got %d: %+v", len(out[0].Data), out[0].Data)
	}

	// Spot-check a few known counts.
	want := map[string]float64{
		"松山區": 2, "信義區": 2, "大安區": 2, "中山區": 1,
		"板橋區": 2, "新莊區": 2, "中和區": 1, "蘆洲區": 1,
	}
	got := map[string]float64{}
	for _, d := range out[0].Data {
		got[d.Xaxis] = d.Data
	}
	for k, v := range want {
		if got[k] != v {
			t.Errorf("district %s: got %v, want %v", k, got[k], v)
		}
	}

	// ORDER BY data DESC: first row should be one of the 2-count districts.
	if out[0].Data[0].Data != 2 {
		t.Errorf("top district count = %v, want 2", out[0].Data[0].Data)
	}
}

func TestGetEcoRestaurantDensityByDistrict_TaipeiOnly(t *testing.T) {
	initTestDB(t)

	out, err := GetEcoRestaurantDensityByDistrict("臺北市")
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	// 臺北 districts: 松山, 信義, 大安, 中山 (4)
	if len(out[0].Data) != 4 {
		t.Fatalf("expected 4 Taipei districts, got %d: %+v", len(out[0].Data), out[0].Data)
	}
	totalY := 0.0
	for _, d := range out[0].Data {
		totalY += d.Data
	}
	if totalY != 7 {
		t.Errorf("Taipei total = %v, want 7", totalY)
	}
}

// ─── C2: GET /eco_diet/restaurant/count-by-city ─────────────────────

func TestGetEcoRestaurantCountByCity_ReturnsTaipeiAndNewTaipei(t *testing.T) {
	initTestDB(t)

	out, err := GetEcoRestaurantCountByCity()
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(out) != 1 || len(out[0].Data) != 2 {
		t.Fatalf("expected 1 outer + 2 city rows, got %+v", out)
	}
	got := map[string]float64{}
	for _, d := range out[0].Data {
		got[d.Xaxis] = d.Data
	}
	if got["臺北市"] != 7 {
		t.Errorf("臺北市 = %v, want 7", got["臺北市"])
	}
	if got["新北市"] != 6 {
		t.Errorf("新北市 = %v, want 6", got["新北市"])
	}
}

// ─── C3: GET /eco_diet/restaurant/list ──────────────────────────────

func TestGetEcoRestaurantList_NoFilterEqualsPoints(t *testing.T) {
	initTestDB(t)

	rows, err := GetEcoRestaurantList("", "", "")
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(rows) != 13 {
		t.Errorf("no-filter list count = %d, want 13", len(rows))
	}
}

func TestGetEcoRestaurantList_DistrictAndActionFilter(t *testing.T) {
	initTestDB(t)

	// Seed: 松山區 has 2 rows (seq 1 + 7); only seq 1 carries '惜食(善用食材)'.
	rows, err := GetEcoRestaurantList("松山區", "惜食(善用食材)", "")
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(rows) != 1 {
		t.Fatalf("expected 1 row, got %d: %+v", len(rows), rows)
	}
	if rows[0].Name != "《扶風堂》披薩。義麵。吉拉朵" {
		t.Errorf("name = %q, want 《扶風堂》披薩。義麵。吉拉朵", rows[0].Name)
	}
}

func TestGetEcoRestaurantList_ActionFilterExcludesNewTaipei(t *testing.T) {
	initTestDB(t)

	// '惜食(善用食材)' tag exists only in Taipei seed rows (3 rows: seq 1, 2, 5).
	rows, err := GetEcoRestaurantList("", "惜食(善用食材)", "")
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(rows) != 3 {
		t.Fatalf("expected 3 rows for action-only filter, got %d", len(rows))
	}
	for _, r := range rows {
		if r.City != "臺北市" {
			t.Errorf("action filter leaked New Taipei row: %+v", r)
		}
	}
}

// ─── C4: GET /eco_diet/green_store/points ───────────────────────────

func TestGetGreenStorePoints_NoFilterReturnsAll8(t *testing.T) {
	initTestDB(t)

	rows, err := GetGreenStorePoints("", "")
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(rows) != 8 {
		t.Fatalf("expected 8 rows, got %d", len(rows))
	}
	cityCount := map[string]int{}
	for _, r := range rows {
		cityCount[r.City]++
	}
	if cityCount["臺北市"] != 5 || cityCount["新北市"] != 3 {
		t.Errorf("city counts = %v, want 臺北5/新北3", cityCount)
	}
}

func TestGetGreenStorePoints_StoreTypeFilter(t *testing.T) {
	initTestDB(t)

	chain, err := GetGreenStorePoints("連鎖型綠色商店", "")
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(chain) != 5 {
		t.Errorf("連鎖型 count = %d, want 5", len(chain))
	}

	indep, err := GetGreenStorePoints("一般型綠色商店", "")
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(indep) != 3 {
		t.Errorf("一般型 count = %d, want 3", len(indep))
	}
}

// ─── C5: GET /eco_diet/waste/yearly ─────────────────────────────────

func TestGetWasteYearly_Returns8SeriesAcross6Years(t *testing.T) {
	initTestDB(t)

	data, categories, err := GetWasteYearly()
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	// 6 years (2018-2023)
	if len(categories) != 6 {
		t.Fatalf("expected 6 year categories, got %d: %v", len(categories), categories)
	}
	if categories[0] != "2018" || categories[5] != "2023" {
		t.Errorf("year range wrong: %v", categories)
	}
	// 8 series = 2 cities × 4 metrics
	if len(data) != 8 {
		t.Fatalf("expected 8 series, got %d", len(data))
	}
	// Each series has 6 data points
	for _, s := range data {
		if len(s.Data) != 6 {
			t.Errorf("series %s has %d points, want 6", s.Name, len(s.Data))
		}
	}

	// Spot-check known seed values: 臺北市-廚餘量 in 2018 = 62458
	for _, s := range data {
		if s.Name == "臺北市-廚餘量" {
			if s.Data[0] != 62458 {
				t.Errorf("臺北市-廚餘量[2018] = %d, want 62458", s.Data[0])
			}
		}
		if s.Name == "新北市-總產生量" {
			if s.Data[5] != 1460328 {
				t.Errorf("新北市-總產生量[2023] = %d, want 1460328", s.Data[5])
			}
		}
	}

	// Verify all 8 series names are present (city × metric combos).
	wantNames := []string{
		"臺北市-廚餘量", "臺北市-一般垃圾", "臺北市-資源垃圾", "臺北市-總產生量",
		"新北市-廚餘量", "新北市-一般垃圾", "新北市-資源垃圾", "新北市-總產生量",
	}
	gotNames := map[string]bool{}
	for _, s := range data {
		gotNames[s.Name] = true
	}
	for _, n := range wantNames {
		if !gotNames[n] {
			t.Errorf("missing series %q", n)
		}
	}
}

// ─── C7a: GET /eco_diet/food_bank/points ────────────────────────────

func TestGetFoodBankPoints_Returns6Rows(t *testing.T) {
	initTestDB(t)

	rows, err := GetFoodBankPoints()
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(rows) != 6 {
		t.Fatalf("expected 6 rows, got %d", len(rows))
	}

	// Seed: 5 Taipei (org_type='實物銀行'), 1 New Taipei (org_type=NULL).
	taipeiOrg, ntpeOrgNull := 0, 0
	for _, r := range rows {
		if r.City == "臺北市" && r.OrgType != nil && *r.OrgType == "實物銀行" {
			taipeiOrg++
		}
		if r.City == "新北市" && r.OrgType == nil {
			ntpeOrgNull++
		}
	}
	if taipeiOrg != 5 {
		t.Errorf("Taipei rows with org_type='實物銀行' = %d, want 5", taipeiOrg)
	}
	if ntpeOrgNull != 1 {
		t.Errorf("New Taipei rows with org_type=NULL = %d, want 1", ntpeOrgNull)
	}
}

// ─── C7b: GET /eco_diet/food_bank/nearby ────────────────────────────

func TestGetFoodBankNearby_Top3FromTaipei101OrderedByDistance(t *testing.T) {
	initTestDB(t)

	// Origin: Taipei 101 = (25.0330, 121.5654)
	// Seed Haversine ordering (psql verified): 信義 337m → 大安 1822m → 中山 3720m → 中正 → 萬華 → 板橋
	rows, err := GetFoodBankNearby(25.0330, 121.5654, 3)
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(rows) != 3 {
		t.Fatalf("expected 3 rows, got %d", len(rows))
	}
	wantOrder := []string{
		"信義社會福利服務中心",
		"大安社會福利服務中心",
		"中山社會福利服務中心",
	}
	for i, r := range rows {
		if r.Name != wantOrder[i] {
			t.Errorf("nearby[%d] = %q, want %q", i, r.Name, wantOrder[i])
		}
	}

	// Distance must be ascending and roughly match psql verification (allow ±10m wiggle for Go float vs psql float).
	if !sort.SliceIsSorted(rows, func(i, j int) bool { return rows[i].DistanceM < rows[j].DistanceM }) {
		t.Errorf("distances not ascending: %+v", []int{rows[0].DistanceM, rows[1].DistanceM, rows[2].DistanceM})
	}
	// 信義 should be < 500m, 大安 in [1500, 2200], 中山 in [3500, 4000]
	if rows[0].DistanceM > 500 {
		t.Errorf("信義 distance = %d, want < 500", rows[0].DistanceM)
	}
	if rows[1].DistanceM < 1500 || rows[1].DistanceM > 2200 {
		t.Errorf("大安 distance = %d, want 1500–2200", rows[1].DistanceM)
	}
	if rows[2].DistanceM < 3500 || rows[2].DistanceM > 4000 {
		t.Errorf("中山 distance = %d, want 3500–4000", rows[2].DistanceM)
	}
}

func TestGetFoodBankNearby_NoLimitReturnsAll6Sorted(t *testing.T) {
	initTestDB(t)

	rows, err := GetFoodBankNearby(25.0330, 121.5654, 0)
	if err != nil {
		t.Fatalf("error = %v", err)
	}
	if len(rows) != 6 {
		t.Fatalf("expected 6 rows when limit=0, got %d", len(rows))
	}
	if !sort.SliceIsSorted(rows, func(i, j int) bool { return rows[i].DistanceM < rows[j].DistanceM }) {
		t.Errorf("distances not ascending across full result")
	}
	// Furthest should be 板橋第一 (the only New Taipei row, ~10km away).
	if rows[5].Name != "板橋第一社會福利服務中心" {
		t.Errorf("furthest = %q, want 板橋第一社會福利服務中心", rows[5].Name)
	}
}
