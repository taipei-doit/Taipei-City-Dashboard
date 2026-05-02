package services

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/logs"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"
)

const overpassEndpoint = "https://overpass-api.de/api/interpreter"

var cuisineMatchers = []struct {
	pattern *regexp.Regexp
	label   string
}{
	{regexp.MustCompile(`(?i)(vietnamese|pho|banh\s*mi)`), "越南料理"},
	{regexp.MustCompile(`(?i)(thai|thailand)`), "泰式料理"},
	{regexp.MustCompile(`(?i)(indian|india|curry)`), "印度料理"},
	{regexp.MustCompile(`(?i)(japanese|japan|ramen|sushi|izakaya)`), "日式料理"},
	{regexp.MustCompile(`(?i)(korean|korea)`), "韓式料理"},
	{regexp.MustCompile(`(?i)(italian|pizza|pasta)`), "義式料理"},
	{regexp.MustCompile(`(?i)(french|france)`), "法式料理"},
	{regexp.MustCompile(`(?i)(mexican|mexico|taco|burrito)`), "墨西哥料理"},
	{regexp.MustCompile(`(?i)(middle[_ ]?eastern|lebanese|arab|persian)`), "中東料理"},
	{regexp.MustCompile(`(?i)(turkish|turkiye|kebab)`), "土耳其料理"},
	{regexp.MustCompile(`(?i)(indonesian|indonesia)`), "印尼料理"},
	{regexp.MustCompile(`(?i)(malaysian|malaysia)`), "馬來西亞料理"},
	{regexp.MustCompile(`(?i)(filipino|philippines|pinoy)`), "菲律賓料理"},
	{regexp.MustCompile(`(?i)(american|burger|bbq)`), "美式料理"},
	{regexp.MustCompile(`(?i)(spanish|spain|tapas)`), "西班牙料理"},
}

type overpassResponse struct {
	Elements []struct {
		Type   string `json:"type"`
		ID     int64  `json:"id"`
		Lat    float64 `json:"lat"`
		Lon    float64 `json:"lon"`
		Center *struct {
			Lat float64 `json:"lat"`
			Lon float64 `json:"lon"`
		} `json:"center"`
		Tags map[string]string `json:"tags"`
	} `json:"elements"`
}

func SyncForeignCuisineData(ctx context.Context, city string) (int, error) {
	if city == "" {
		city = "taipei"
	}

	if err := models.EnsureForeignCuisineTable(); err != nil {
		return 0, err
	}

	rows, err := fetchFromOverpass(ctx, city)
	if err != nil {
		return 0, err
	}

	if err := models.UpsertForeignCuisineRestaurants(rows); err != nil {
		return 0, err
	}

	logs.FInfo("Foreign cuisine sync completed: city=%s, rows=%d", city, len(rows))
	return len(rows), nil
}

func fetchFromOverpass(ctx context.Context, city string) ([]models.ForeignCuisineRestaurant, error) {
	bbox := "24.96,121.45,25.22,121.66" // Taipei City
	if city == "metrotaipei" {
		bbox = "24.80,121.25,25.30,122.05" // Metro Taipei (Taipei + New Taipei)
	}

	query := fmt.Sprintf(`
[out:json][timeout:45];
(
  node["amenity"="restaurant"]["cuisine"](%s);
  way["amenity"="restaurant"]["cuisine"](%s);
);
out center tags;
`, bbox, bbox)

	form := url.Values{}
	form.Set("data", query)

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, overpassEndpoint, strings.NewReader(form.Encode()))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", "Taipei-City-Dashboard/1.0")

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("overpass request failed: status=%d body=%s", resp.StatusCode, string(body))
	}

	var payload overpassResponse
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return nil, err
	}

	now := time.Now()
	rows := make([]models.ForeignCuisineRestaurant, 0, len(payload.Elements))
	for _, el := range payload.Elements {
		cuisineRaw := strings.TrimSpace(el.Tags["cuisine"])
		if cuisineRaw == "" || !isLikelyForeignCuisine(cuisineRaw) {
			continue
		}

		lon := el.Lon
		lat := el.Lat
		if el.Center != nil {
			lon = el.Center.Lon
			lat = el.Center.Lat
		}
		if lon == 0 || lat == 0 {
			continue
		}

		name := strings.TrimSpace(el.Tags["name"])
		if name == "" {
			name = "未命名餐廳"
		}

		address := strings.TrimSpace(strings.Join([]string{
			el.Tags["addr:postcode"],
			el.Tags["addr:city"],
			el.Tags["addr:district"],
			el.Tags["addr:street"],
			el.Tags["addr:housenumber"],
		}, " "))

		rows = append(rows, models.ForeignCuisineRestaurant{
			City:       city,
			Source:     "overpass_osm",
			SourceID:   fmt.Sprintf("%s_%d", el.Type, el.ID),
			Name:       name,
			CuisineRaw: cuisineRaw,
			CuisineZh:  normalizeCuisine(cuisineRaw),
			Address:    strings.TrimSpace(address),
			District:   strings.TrimSpace(el.Tags["addr:district"]),
			Lon:        lon,
			Lat:        lat,
			CreatedAt:  now,
			UpdatedAt:  now,
		})
	}

	return rows, nil
}

func normalizeCuisine(raw string) string {
	for _, m := range cuisineMatchers {
		if m.pattern.MatchString(raw) {
			return m.label
		}
	}
	return "其他異國料理"
}

func isLikelyForeignCuisine(raw string) bool {
	for _, m := range cuisineMatchers {
		if m.pattern.MatchString(raw) {
			return true
		}
	}
	return false
}
