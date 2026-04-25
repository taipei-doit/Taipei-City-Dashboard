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
// Env vars override the defaults (host=127.0.0.1, port=5432, user=$USER, db=dashboard, no password, sslmode=disable).
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
	if len(got) != 1 || len(got[0].Data) != 1 {
		t.Fatalf("expected 1 outer + 1 data point, got %+v", got)
	}
	if got[0].Data[0].Xaxis != "今日異常公告" {
		t.Errorf("x = %q, want %q", got[0].Data[0].Xaxis, "今日異常公告")
	}
	// fake data: 4 active rows
	if got[0].Data[0].Data != 4 {
		t.Errorf("y = %v, want 4", got[0].Data[0].Data)
	}
}

// ─── C2: alert-by-line (current) ────────────────────────────────────────────

func TestGetMrtAlertByLine_ReturnsLineCategories(t *testing.T) {
	initTestDB(t)

	data, categories, err := GetMrtAlertByLine()
	if err != nil {
		t.Fatalf("GetMrtAlertByLine() error = %v", err)
	}
	// Fake data: 板南線 (台北車, 市政府) = 2; 淡水信義線 (中山, 奇岩) = 2.
	// Both tie at 2, so order is DB-dependent, only assert presence and totals.
	if len(categories) != 2 {
		t.Fatalf("expected 2 lines, got %d: %v", len(categories), categories)
	}
	wantLines := map[string]bool{"板南線": true, "淡水信義線": true}
	for _, c := range categories {
		if !wantLines[c] {
			t.Errorf("unexpected line %q in categories", c)
		}
	}
	if len(data) != 1 || data[0].Name != "異常站數" {
		t.Fatalf("series shape wrong: %+v", data)
	}
	total := 0
	for _, n := range data[0].Data {
		total += n
	}
	if total != 4 {
		t.Errorf("total active stations = %d, want 4", total)
	}
}

// ─── C3: alert-trend-30d (history with DISTINCT) ────────────────────────────

func TestGetMrtAlertTrend30d_DedupesHistory(t *testing.T) {
	initTestDB(t)

	data, categories, err := GetMrtAlertTrend30d()
	if err != nil {
		t.Fatalf("GetMrtAlertTrend30d() error = %v", err)
	}
	// Fake data has a deliberate duplicate row in history for 板南線/台北車/2026-04-25 08:00.
	// DISTINCT (publish_time, line, station, description) should dedupe it:
	//   板南線 = 4 unique events (1 dup folded), 淡水信義線 = 3, 松山新店線 = 2 → total 9.
	if len(categories) != 3 {
		t.Fatalf("expected 3 lines, got %d: %v", len(categories), categories)
	}
	if categories[0] != "板南線" {
		t.Errorf("first (most events) = %q, want 板南線", categories[0])
	}
	if len(data) != 1 || data[0].Name != "近30天公告數" {
		t.Fatalf("series shape wrong: %+v", data)
	}
	total := 0
	for _, n := range data[0].Data {
		total += n
	}
	if total != 9 {
		t.Errorf("total distinct events = %d, want 9 (DISTINCT may not be working)", total)
	}
	// First bucket is 板南線, must be 4 (would be 5 without DISTINCT — that's the regression we're guarding).
	if data[0].Data[0] != 4 {
		t.Errorf("板南線 distinct events = %d, want 4", data[0].Data[0])
	}
}

// ─── C4: stations (point array) ─────────────────────────────────────────────

func TestGetMrtStations_ReturnsAllExitsWithAlertStatus(t *testing.T) {
	initTestDB(t)

	rows, err := GetMrtStations()
	if err != nil {
		t.Fatalf("GetMrtStations() error = %v", err)
	}
	// Fake elevator: 9 exits across 7 stations. 6 exits belong to stations with active alerts
	// (台北車 ×2 + 市政府 ×2 + 中山 ×1 + 奇岩 ×1), 3 are normal (劍潭 + 南港 + 古亭).
	if len(rows) != 9 {
		t.Fatalf("expected 9 exits, got %d", len(rows))
	}

	counts := map[string]int{}
	var sawAlertedRow bool
	for _, r := range rows {
		counts[r.AlertStatus]++
		if r.AlertStatus == "active" {
			if r.AlertDescription == nil {
				t.Errorf("active row %s/%s missing description", r.Station, r.ExitNo)
			}
			if r.AlertPublishTime == nil {
				t.Errorf("active row %s/%s missing publish_time", r.Station, r.ExitNo)
			}
			sawAlertedRow = true
		}
	}
	if counts["active"] != 6 {
		t.Errorf("active exits = %d, want 6", counts["active"])
	}
	if counts["normal"] != 3 {
		t.Errorf("normal exits = %d, want 3", counts["normal"])
	}
	if !sawAlertedRow {
		t.Error("expected at least one row with alert details populated")
	}

	// Order check: active rows come before normal rows (ORDER BY alert_status DESC).
	seenNormal := false
	for _, r := range rows {
		if r.AlertStatus == "normal" {
			seenNormal = true
		} else if seenNormal {
			t.Errorf("active row appeared after normal row — ORDER BY broken")
			break
		}
	}
}
