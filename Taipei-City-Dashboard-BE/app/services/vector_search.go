package services

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/global"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"sort"
)

// ComponentResult 定義回傳給 LLM 與前端的最小化結構
type ComponentResult struct {
	ID    interface{} `json:"id"`
	Index string      `json:"index"`
	Name  string      `json:"name"`
	City  string      `json:"city"`
	Score float32     `json:"score"`
}

// SearchQdrantComponents 執行向量搜尋、去重與排序
func SearchQdrantComponents(ctx context.Context, query string, limit int, scoreThreshold float32) ([]ComponentResult, error) {
	// 1. 將使用者的文字轉為向量 (呼叫原有的 Embedding 模型)
	vector, err := models.GenVector(query)
	if err != nil {
		return nil, fmt.Errorf("failed to generate vector: %w", err)
	}

	// 2. 準備 Qdrant 搜尋請求
	// 為了避免去重後數量不足，向 Qdrant 請求的數量稍微放大 (例如 limit * 2)
	fetchLimit := limit * 2
	
	collectionName := os.Getenv("QDRANT_COLLECTION_NAME")
	if collectionName == "" {
		collectionName = "query_charts"
	}

	searchURL := fmt.Sprintf("%s/collections/%s/points/search", global.Qdrant.Url, collectionName)
	
	qdrantReqBody := map[string]interface{}{
		"vector":          vector,
		"limit":           fetchLimit,
		"with_payload":    true,
		"score_threshold": scoreThreshold,
	}

	reqBytes, _ := json.Marshal(qdrantReqBody)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, searchURL, bytes.NewBuffer(reqBytes))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	if global.Qdrant.ApiKey != "" {
		req.Header.Set("api-key", global.Qdrant.ApiKey)
	}

	// 3. 發送請求至 Qdrant
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("qdrant search failed: %s", string(bodyBytes))
	}

	// 4. 解析 Qdrant 回傳結果
	var qdrantResp struct {
		Result []struct {
			Id      interface{}            `json:"id"`
			Score   float32                `json:"score"`
			Payload map[string]interface{} `json:"payload"`
		} `json:"result"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&qdrantResp); err != nil {
		return nil, err
	}

	// 5. 執行去重複邏輯 (移植自前端 Vue 的 reduce 邏輯)
	uniqueMap := make(map[string]ComponentResult)

	for _, hit := range qdrantResp.Result {
		// 安全轉型 Payload
		index, _ := hit.Payload["index"].(string)
		city, _ := hit.Payload["city"].(string)
		name, _ := hit.Payload["name"].(string)

		comp := ComponentResult{
			ID:    hit.Id,
			Index: index,
			Name:  name,
			City:  city,
			Score: hit.Score,
		}

		if exist, found := uniqueMap[index]; found {
			// 如果已存在，但現在的是 metrotaipei，就覆蓋
			if comp.City == "metrotaipei" {
				uniqueMap[index] = comp
			} else {
				// 保留原本的，不做事
				_ = exist
			}
		} else {
			// 如果還沒放過，直接放
			uniqueMap[index] = comp
		}
	}

	// 6. 將 Map 轉回 Slice 並根據分數排序 (移植自前端 Vue 的 sort 邏輯)
	var finalResults []ComponentResult
	for _, v := range uniqueMap {
		finalResults = append(finalResults, v)
	}

	sort.Slice(finalResults, func(i, j int) bool {
		return finalResults[i].Score > finalResults[j].Score // 降冪排序
	})

	// 7. 裁切至指定的 Limit 數量
	if len(finalResults) > limit {
		finalResults = finalResults[:limit]
	}

	return finalResults, nil
}