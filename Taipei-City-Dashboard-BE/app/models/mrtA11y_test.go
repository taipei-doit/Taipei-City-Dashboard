package models

import (
	"fmt"
	"os"
	"testing"

	"TaipeiCityDashboardBE/global"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// initTestDB sets up DBDashboard for unit tests against the local dashboard database.
// Env vars override the defaults (host=127.0.0.1, port=5432, user=current OS user, db=dashboard, no password, sslmode=disable).
func initTestDB(t *testing.T) {
	t.Helper()
	if DBDashboard != nil {
		return
	}
	cfg := global.DatabaseConfig{
		Host:     getTestEnv("DB_DASHBOARD_HOST", "127.0.0.1"),
		Port:     getTestEnv("DB_DASHBOARD_PORT", "5432"),
		User:     getTestEnv("DB_DASHBOARD_USER", os.Getenv("USER")),
		Password: getTestEnv("DB_DASHBOARD_PASSWORD", ""),
		DBName:   getTestEnv("DB_DASHBOARD_DBNAME", "dashboard"),
		SSLMode:  getTestEnv("DB_DASHBOARD_SSLMODE", "disable"),
	}
	dsn := fmt.Sprintf(
		"host=%s port=%s user=%s dbname=%s password=%s sslmode=%s",
		cfg.Host, cfg.Port, cfg.User, cfg.DBName, cfg.Password, cfg.SSLMode,
	)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		t.Skipf("skip: cannot connect to test dashboard DB (%v)", err)
	}
	DBDashboard = db
}

func getTestEnv(key, fallback string) string {
	if v, ok := os.LookupEnv(key); ok {
		return v
	}
	return fallback
}

// ─── C1: alert-count ────────────────────────────────────────────────────────

func TestGetMrtAlertCount_ReturnsActiveCount(t *testing.T) {
	initTestDB(t)

	got, err := GetMrtAlertCount()
	if err != nil {
		t.Fatalf("GetMrtAlertCount() error = %v", err)
	}
	if len(got) != 1 {
		t.Fatalf("expected 1 outer data item, got %d", len(got))
	}
	if len(got[0].Data) != 1 {
		t.Fatalf("expected 1 data point, got %d", len(got[0].Data))
	}
	if got[0].Data[0].Xaxis != "今日異常設施" {
		t.Errorf("x = %q, want %q", got[0].Data[0].Xaxis, "今日異常設施")
	}
	// 5 active rows in fake data
	if got[0].Data[0].Data != 5 {
		t.Errorf("y = %v, want 5", got[0].Data[0].Data)
	}
}

// ─── C2: alert-by-line ──────────────────────────────────────────────────────

func TestGetMrtAlertByLine_ReturnsLineCategories(t *testing.T) {
	initTestDB(t)

	data, categories, err := GetMrtAlertByLine()
	if err != nil {
		t.Fatalf("GetMrtAlertByLine() error = %v", err)
	}
	if len(categories) == 0 {
		t.Fatal("categories should not be empty")
	}
	// Fake data has alerts on 板南線 (3 stations) and 淡水信義線 (2 stations) — only active rows
	if categories[0] != "板南線" {
		t.Errorf("first category = %q, want %q", categories[0], "板南線")
	}
	if len(data) != 1 {
		t.Fatalf("expected 1 series (異常站數), got %d", len(data))
	}
	if data[0].Name != "異常站數" {
		t.Errorf("series name = %q, want %q", data[0].Name, "異常站數")
	}
	if data[0].Data[0] != 3 {
		t.Errorf("板南線 count = %d, want 3", data[0].Data[0])
	}
}

// ─── C3: alert-by-type ──────────────────────────────────────────────────────

func TestGetMrtAlertByType_ReturnsEquipmentBreakdown(t *testing.T) {
	initTestDB(t)

	data, categories, err := GetMrtAlertByType()
	if err != nil {
		t.Fatalf("GetMrtAlertByType() error = %v", err)
	}
	if len(data) == 0 {
		t.Fatal("data should not be empty")
	}
	// 電梯 (3 active), 坡道 (1 active), 月臺隙縫板 (1 active) — sorted DESC
	if data[0].Name != "電梯" {
		t.Errorf("first type = %q, want 電梯", data[0].Name)
	}
	if data[0].Data[0] != 3 {
		t.Errorf("電梯 count = %d, want 3", data[0].Data[0])
	}
	if len(categories) != len(data) {
		t.Errorf("categories len %d != data len %d", len(categories), len(data))
	}
}

// ─── C4: station-overview ───────────────────────────────────────────────────

func TestGetMrtStationOverview_ReturnsNormalAndAlert(t *testing.T) {
	initTestDB(t)

	rows, err := GetMrtStationOverview()
	if err != nil {
		t.Fatalf("GetMrtStationOverview() error = %v", err)
	}
	if len(rows) == 0 {
		t.Fatal("rows should not be empty")
	}

	totals := map[string]float64{}
	for _, r := range rows {
		totals[r.Type] += r.Value
		if r.Icon != "mrt_station" {
			t.Errorf("icon = %q, want %q", r.Icon, "mrt_station")
		}
	}
	// 7 elevator stations; 4 have active alerts (台北車站, 市政府, 忠孝復興, 中山)
	// 古亭 has only closed alert so it counts as normal
	if totals["alert"] != 4 {
		t.Errorf("alert stations = %v, want 4", totals["alert"])
	}
	if totals["normal"] != 3 {
		t.Errorf("normal stations = %v, want 3", totals["normal"])
	}
}
