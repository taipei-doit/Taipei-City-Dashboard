package models

import (
	"TaipeiCityDashboardBE/global"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math"
	"net/http"
	"path/filepath"

	"github.com/sugarme/tokenizer"
	"github.com/sugarme/tokenizer/pretrained"
	ort "github.com/yalue/onnxruntime_go"
)


type QdrantQueryRequest struct {
	Query          []float32 `json:"query"`
	Limit          int       `json:"limit"`
	ScoreThreshold float32   `json:"score_threshold,omitempty"`
	WithPayload    bool      `json:"with_payload"`
}

type QdrantPoint struct {
	Score   float64                `json:"score"`
	Payload map[string]interface{} `json:"payload"`
}

type QdrantQueryResponse struct {
	Result struct {
		Points []QdrantPoint `json:"points"`
	} `json:"result"`
	Status string  `json:"status"`
	Time   float64 `json:"time"`
}

func queryQdrant(queryVector []float32, limit int, scoreThreshold float64) (QdrantQueryResponse, error) {
	var result QdrantQueryResponse

	QdrantConfig := global.Qdrant

	reqBody := QdrantQueryRequest{
		Query:          queryVector,
		Limit:          limit,
		ScoreThreshold: float32(scoreThreshold),
		WithPayload:    true,
	}

	bodyBytes, err := json.Marshal(reqBody)
	if err != nil {
		return result, fmt.Errorf("marshal request body error: %w", err)
	}

	url := fmt.Sprintf("%s/collections/%s/points/query", QdrantConfig.Url, QdrantConfig.Collection)

	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(bodyBytes))
	if err != nil {
		return result, fmt.Errorf("new request error: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("api-key", QdrantConfig.ApiKey)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return result, fmt.Errorf("http request error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		// 如果想看錯誤內容，也可以在這裡讀一次 body
		b, _ := io.ReadAll(resp.Body)
		return result, fmt.Errorf("qdrant returned status %s, body=%s", resp.Status, string(b))
	}

	// 先把原始回應整包讀出來（方便 debug）
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return result, fmt.Errorf("read response body error: %w", err)
	}

	// fmt.Println("=== Qdrant 原始回應 ===")
	// fmt.Println(string(respBody))
	// fmt.Println("=======================")

	if err := json.Unmarshal(respBody, &result); err != nil {
		return result, fmt.Errorf("decode response error: %w", err)
	}

	return result, nil
}

func InitLmSession() *ort.DynamicSession[int64, float32] {
	LMConfig := global.LM

	// 1) ONNX Runtime 初始化
	ort.SetSharedLibraryPath("/usr/lib/libonnxruntime.so") // 設定共享函式庫路徑

	if err := ort.InitializeEnvironment(); err != nil {
		log.Fatalf("InitializeEnvironment error: %v", err)
	}

	// 2) 模型路徑
	modelDir := LMConfig.ModelPath
	modelPath := filepath.Join(modelDir, "model.onnx")

	// 3) 檢查 I/O 資訊
	// inputsInfo, outputsInfo, err := ort.GetInputOutputInfo(modelPath)
	// if err != nil {
	// 	log.Fatalf("GetInputOutputInfo error: %v", err)
	// }

	// fmt.Println("== Inputs ==")
	// for _, in := range inputsInfo {
	// 	fmt.Println("  ", in.String())
	// }
	// fmt.Println("== Outputs ==")
	// for _, out := range outputsInfo {
	// 	fmt.Println("  ", out.String())
	// }

	// 4) 建立 DynamicSession：input / output 名稱
	inputNames := []string{"input_ids", "attention_mask"}
	outputNames := []string{"last_hidden_state"}

	session, err := ort.NewDynamicSession[int64, float32](modelPath, inputNames, outputNames)
	if err != nil {
		log.Fatalf("NewDynamicSession error: %v", err)
	}

	return session
}

func InitTokenizer() *tokenizer.Tokenizer {
    modelDir := global.LM.ModelPath
    tokenizerPath := filepath.Join(modelDir, "tokenizer.json")
	tk, err := pretrained.FromFile(tokenizerPath)
    if err != nil {
        // 啟動時失敗就報警並停止，這比執行中當機好找原因
        log.Fatalf("Critical: Failed to load tokenizer: %v", err)
    }
    return tk
}

func GenVector(inputText string) ([]float32, error) {
    // 1) 載入 tokenizer.json 直接檢查全域變數，不再讀取檔案
    if global.LMTokenizer == nil {
        return nil, fmt.Errorf("tokenizer is not initialized")
    }
    tk := global.LMTokenizer

	// 2) 將查詢字串轉成 input_ids 與 attention_mask
	text := "query: " + inputText

	enc, err := tk.EncodeSingle(text) // 預設 addSpecialTokens = true
	if err != nil {
		log.Fatalf("tokenize error: %v", err)
	}

	ids := enc.GetIds()                // []int
	attnMask := enc.GetAttentionMask() // []int，1=有效 token, 0=padding

	if len(ids) != len(attnMask) {
		log.Fatalf("ids len %d != attention_mask len %d", len(ids), len(attnMask))
	}

	seqLen := int64(len(ids))
	batchSize := int64(1)

	// 3) 準備 input_ids tensor [1, seq_len] (int64)
	idsShape := ort.NewShape(batchSize, seqLen)
	idsTensor, err := ort.NewEmptyTensor[int64](idsShape)
	if err != nil {
		log.Fatalf("NewEmptyTensor ids error: %v", err)
	}
	defer idsTensor.Destroy()

	idsData := idsTensor.GetData()
	for i, v := range ids {
		idsData[i] = int64(v)
	}

	// 4) 準備 attention_mask tensor [1, seq_len] (int64)
	maskShape := ort.NewShape(batchSize, seqLen)
	maskTensor, err := ort.NewEmptyTensor[int64](maskShape)
	if err != nil {
		log.Fatalf("NewEmptyTensor mask error: %v", err)
	}
	defer maskTensor.Destroy()

	maskData := maskTensor.GetData()
	for i, v := range attnMask {
		maskData[i] = int64(v)
	}

	inputTensors := []*ort.Tensor[int64]{idsTensor, maskTensor}

	// 5) 準備輸出 tensor：last_hidden_state [1, seq_len, 768] (float32)
	hiddenSize := int64(768)
	outShape := ort.NewShape(batchSize, seqLen, hiddenSize)
	outTensor, err := ort.NewEmptyTensor[float32](outShape)
	if err != nil {
		log.Fatalf("NewEmptyTensor output error: %v", err)
	}
	defer outTensor.Destroy()

	outputTensors := []*ort.Tensor[float32]{outTensor}

	session := global.LMSession

	// 6) 跑一次推論
	if err := session.Run(inputTensors, outputTensors); err != nil {
		log.Fatalf("session.Run error: %v", err)
	}

	// 7) 拿出 last_hidden_state 做 mean pooling + L2 normalize
	lastHidden := outTensor.GetData() // 長度 = 1 * seqLen * 768

	embedding := make([]float32, hiddenSize)
	var validCount float32

	for t := 0; t < int(seqLen); t++ {
		if attnMask[t] == 0 {
			continue // 忽略 padding
		}
		validCount += 1.0
		offset := t * int(hiddenSize)
		for d := 0; d < int(hiddenSize); d++ {
			embedding[d] += lastHidden[offset+d]
		}
	}

	// 平均
	if validCount > 0 {
		for d := 0; d < int(hiddenSize); d++ {
			embedding[d] /= validCount
		}
	}

	// L2 normalize
	var norm float64
	for d := 0; d < int(hiddenSize); d++ {
		norm += float64(embedding[d]) * float64(embedding[d])
	}
	
	norm = math.Sqrt(float64(norm))
	if norm > 0 {
		for d := 0; d < int(hiddenSize); d++ {
			embedding[d] = float32(float64(embedding[d]) / norm)
		}
	}

	return embedding, nil
}