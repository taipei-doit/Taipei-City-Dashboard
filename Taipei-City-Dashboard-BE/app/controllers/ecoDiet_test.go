package controllers

import (
	"strings"
	"testing"

	"TaipeiCityDashboardBE/app/models"
)

// Tests for the ai-summary prompt builders. These exercise the pure string-
// formatting layer with hand-crafted in-memory inputs, so they don't depend on
// DB seeding or the LLM service. The DB queries themselves are covered by
// app/models/ecoDiet_test.go.

func ptrStr(s string) *string { return &s }

func TestEcoDietMapToLines_SortedAscByKey(t *testing.T) {
	out := ecoDietMapToLines(map[string]int{
		"新北市": 5,
		"臺北市": 7,
	}, "家")
	idxTpe := strings.Index(out, "臺北市")
	idxNtp := strings.Index(out, "新北市")
	if idxTpe < 0 || idxNtp < 0 {
		t.Fatalf("missing city in output: %q", out)
	}
	// "新北市" 開頭注音排序在 "臺北市" 之前嗎？此處用 byte sort（Go 預設）：
	// "新" U+65B0, "臺" U+81FA → "新" 在前。確認 deterministic 排序。
	if idxNtp > idxTpe {
		t.Errorf("expected 新北市 before 臺北市 by byte order, got %q", out)
	}
	if !strings.Contains(out, "5 家") || !strings.Contains(out, "7 家") {
		t.Errorf("output missing values, got %q", out)
	}
}

func TestEcoDietMapToLines_EmptyReturnsPlaceholder(t *testing.T) {
	out := ecoDietMapToLines(map[string]int{}, "家")
	if !strings.Contains(out, "（無資料）") {
		t.Errorf("empty map should return placeholder, got %q", out)
	}
}

func TestEcoDietTopNLines_OrdersByValueDescThenKeyAsc(t *testing.T) {
	out := ecoDietTopNLines(map[string]int{
		"a": 1,
		"b": 3,
		"c": 3,
		"d": 5,
	}, 3, "次")
	lines := strings.Split(strings.TrimRight(out, "\n"), "\n")
	if len(lines) != 3 {
		t.Fatalf("expected top-3 lines, got %d (%q)", len(lines), out)
	}
	// d=5, b=3 (key asc tie-break), c=3
	if !strings.HasPrefix(lines[0], "  - d：5") {
		t.Errorf("rank 1 wrong, got %q", lines[0])
	}
	if !strings.HasPrefix(lines[1], "  - b：3") {
		t.Errorf("rank 2 wrong, got %q", lines[1])
	}
	if !strings.HasPrefix(lines[2], "  - c：3") {
		t.Errorf("rank 3 wrong, got %q", lines[2])
	}
}

func TestEcoDietTopNLines_EmptyReturnsEmpty(t *testing.T) {
	if got := ecoDietTopNLines(nil, 5, "次"); got != "" {
		t.Errorf("empty map should return empty string, got %q", got)
	}
}

func TestEcoDietRestaurantPointsPrompt_IncludesKeyFields(t *testing.T) {
	tpeDistrict := "信義區"
	ntpDistrict := "板橋區"
	rows := []models.EcoRestaurantPoint{
		{City: "臺北市", District: &tpeDistrict, EnvActions: []string{"自備餐具", "減少一次用品"}},
		{City: "臺北市", District: &tpeDistrict, EnvActions: []string{"自備餐具"}},
		{City: "新北市", District: &ntpDistrict, EnvActions: nil},
	}
	out := ecoDietRestaurantPointsPrompt(rows)
	for _, want := range []string{
		"C1a｜環保餐廳點位", "總筆數：3 家", "臺北市", "新北市",
		"信義區", "自備餐具", "【角色限制】",
	} {
		if !strings.Contains(out, want) {
			t.Errorf("prompt missing %q\n--- output ---\n%s", want, out)
		}
	}
}

func TestEcoDietRestaurantDensityPrompt_SumsTotal(t *testing.T) {
	out := ecoDietRestaurantDensityPrompt([]models.TwoDimensionalDataOutput{
		{Data: []models.TwoDimensionalData{
			{Xaxis: "信義區", Data: 5},
			{Xaxis: "大安區", Data: 3},
		}},
	})
	for _, want := range []string{"C1b｜環保餐廳行政區密度", "合計：8 家", "信義區", "大安區"} {
		if !strings.Contains(out, want) {
			t.Errorf("prompt missing %q\n--- output ---\n%s", want, out)
		}
	}
}

func TestEcoDietRestaurantCountByCityPrompt_HandlesEmpty(t *testing.T) {
	out := ecoDietRestaurantCountByCityPrompt(nil)
	if !strings.Contains(out, "C2｜雙城環保餐廳家數") || !strings.Contains(out, "（無資料）") {
		t.Errorf("empty case should still emit C2 header + placeholder, got %q", out)
	}
}

func TestEcoDietGreenStorePointsPrompt_UnclassifiedFallback(t *testing.T) {
	storeType := "綠色商店"
	rows := []models.GreenStorePoint{
		{City: "臺北市", StoreType: &storeType},
		{City: "新北市", StoreType: nil}, // → "（未分類）"
	}
	out := ecoDietGreenStorePointsPrompt(rows)
	for _, want := range []string{"C4｜綠色商店點位", "綠色商店", "（未分類）"} {
		if !strings.Contains(out, want) {
			t.Errorf("prompt missing %q\n--- output ---\n%s", want, out)
		}
	}
}

func TestEcoDietWasteYearlyPrompt_RendersYearRangeAndSeries(t *testing.T) {
	out := ecoDietWasteYearlyPrompt(
		[]models.ThreeDimensionalDataOutput{
			{Name: "臺北市-廚餘量", Data: []int{100, 110, 120}},
			{Name: "新北市-廚餘量", Data: []int{200, 210, 220}},
		},
		[]string{"2021", "2022", "2023"},
	)
	for _, want := range []string{
		"C5｜雙北年度廢棄物趨勢", "年度範圍：2021 ~ 2023",
		"臺北市-廚餘量", "新北市-廚餘量", "2021=100", "2023=220",
	} {
		if !strings.Contains(out, want) {
			t.Errorf("prompt missing %q\n--- output ---\n%s", want, out)
		}
	}
}

func TestEcoDietFoodBankPointsPrompt_NewTaipeiOrgTypeBucket(t *testing.T) {
	tpeOrg := "社福機構"
	rows := []models.FoodBankPoint{
		{City: "臺北市", OrgType: &tpeOrg},
		{City: "新北市", OrgType: nil}, // 新北側 org_type 永遠 NULL
	}
	out := ecoDietFoodBankPointsPrompt(rows)
	for _, want := range []string{"C7a｜實物銀行點位", "社福機構", "（未分類）", "總筆數：2 處"} {
		if !strings.Contains(out, want) {
			t.Errorf("prompt missing %q\n--- output ---\n%s", want, out)
		}
	}
}

func TestBuildEcoDietComponentPrompt_UnknownComponentReturnsError(t *testing.T) {
	_, err := buildEcoDietComponentPrompt("eco-diet-zzz")
	if err == nil {
		t.Fatal("expected error for unknown component_id, got nil")
	}
	if !strings.Contains(err.Error(), "unknown component_id") {
		t.Errorf("error msg should mention unknown component_id, got %q", err.Error())
	}
}
