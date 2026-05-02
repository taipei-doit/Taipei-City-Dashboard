// Package actions 提供 AI function-call 工具回傳 FE 副作用指令的 ctx-based accumulator。
//
// 設計動機：function tool 簽名是 func(ctx, args) (string, error)，回傳字串是給 LLM 看的；
// 但有些 tool（例如 plan_route_to_nearest_eco_facility）需要額外指示 FE 切圖層、畫路線。
// 透過 ctx 攜帶一個 *[]ChatAction，tool 執行時 Append、controller 在收完 ChatWithTWCC 後 Collect，
// 一起塞進 HTTP response 的 actions 欄位給 FE 解析，無需改 ChatWithTWCC 簽名。
//
// 此包與 services/ai 與 services/ai/tools 兩側解耦，避免 import cycle。
package actions

import "context"

// ChatAction 是 LLM tool 在執行時要求 FE 做的副作用指令。
type ChatAction struct {
	Type         string `json:"type"`                    // "show_layer" | "draw_route"
	FacilityType string `json:"facility_type,omitempty"` // "restaurant" | "green_store" | "food_bank"
	To           *Point `json:"to,omitempty"`            // draw_route 終點
	DistanceM    int    `json:"distance_m,omitempty"`    // 直線距離（FE 會用 Mapbox 結果覆蓋）
	DurationS    int    `json:"duration_s,omitempty"`    // 粗估步行秒數
}

// Point 是地圖座標 + 顯示名稱。
type Point struct {
	Lat  float64 `json:"lat"`
	Lng  float64 `json:"lng"`
	Name string  `json:"name"`
}

type ctxKey struct{}

// With 以 ctx 包一個空的 actions accumulator。每個 chat 呼叫前呼叫一次。
func With(ctx context.Context) context.Context {
	acc := make([]ChatAction, 0)
	return context.WithValue(ctx, ctxKey{}, &acc)
}

// Append 寫一筆 action 到 accumulator；若 ctx 沒被 With 包過則 no-op。
func Append(ctx context.Context, a ChatAction) {
	if acc, ok := ctx.Value(ctxKey{}).(*[]ChatAction); ok && acc != nil {
		*acc = append(*acc, a)
	}
}

// Collect 取出累積的 actions；若 ctx 沒被 With 包過回傳 nil。
func Collect(ctx context.Context) []ChatAction {
	if acc, ok := ctx.Value(ctxKey{}).(*[]ChatAction); ok && acc != nil {
		return *acc
	}
	return nil
}
