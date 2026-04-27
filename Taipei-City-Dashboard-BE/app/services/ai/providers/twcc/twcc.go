package twcc

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"TaipeiCityDashboardBE/logs"
	"github.com/tmc/langchaingo/llms"
)

type TWCC struct {
	APIKey      string
	BaseURL     string
	ModelName   string
	HTTPClient  *http.Client
	Temperature float64
	MaxTokens   int
}

// Ensure TWCC implements llms.Model
var _ llms.Model = (*TWCC)(nil)

func New(apiKey, baseURL, model string, timeout int) *TWCC {
	return &TWCC{
		APIKey:     apiKey,
		BaseURL:    baseURL,
		ModelName:  model,
		HTTPClient: &http.Client{Timeout: time.Duration(timeout) * time.Second},
		Temperature: 0.7,
		MaxTokens:   350,
	}
}

func (m *TWCC) GenerateContent(ctx context.Context, messages []llms.MessageContent, options ...llms.CallOption) (*llms.ContentResponse, error) {
	opts := llms.CallOptions{}
	for _, opt := range options {
		opt(&opts)
	}

	twccMessages := m.toTWCCMessages(messages)
	twccParams := m.toTWCCParameters(&opts)
	isStreaming := opts.StreamingFunc != nil

	reqBody := TWCCRequest{
		Model:      m.ModelName,
		Messages:   twccMessages,
		Parameters: twccParams,
		Stream:     isStreaming,
		Tools:      m.toTWCCTools(opts.Tools),
	}
	if opts.ToolChoice != nil {
		reqBody.ToolChoice = opts.ToolChoice
	} else if len(reqBody.Tools) > 0 {
		reqBody.ToolChoice = "auto"
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	logs.FInfo("TWCC Outgoing Request: %s", string(jsonData))

	resp, err := m.doRequest(ctx, jsonData, isStreaming)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if isStreaming {
		return m.handleStreamingResponse(ctx, resp.Body, &opts)
	}
	return m.handleStandardResponse(resp.Body)
}

// toTWCCMessages converts langchaingo messages to TWCC format with XML cleanup.
func (m *TWCC) toTWCCMessages(messages []llms.MessageContent) []TWCCMessage {
	twccMessages := make([]TWCCMessage, 0, len(messages))
	for _, mc := range messages {
		role := m.mapRole(mc.Role)
		var toolCallID, toolName string
		var twccToolCalls []TWCCToolCall
		var contentText string

		for _, part := range mc.Parts {
			switch p := part.(type) {
			case llms.TextContent:
				contentText = cleanXML(p.Text)
			case llms.ToolCall:
				twccToolCalls = append(twccToolCalls, TWCCToolCall{
					ID:   p.ID,
					Type: p.Type,
					Function: struct {
						Name      string `json:"name"`
						Arguments string `json:"arguments"`
					}{
						Name:      p.FunctionCall.Name,
						Arguments: cleanXML(p.FunctionCall.Arguments),
					},
				})
			case llms.ToolCallResponse:
				toolCallID, toolName = p.ToolCallID, p.Name
				contentText = cleanXML(p.Content)
			}
		}

		msg := TWCCMessage{
			Role: role, ToolCalls: twccToolCalls, ToolCallID: toolCallID, Name: toolName,
		}

		// AFS Protocol: assistant with tools MUST have content: null if no text
		if role == "assistant" && len(twccToolCalls) > 0 && contentText == "" {
			msg.Content = nil
		} else {
			msg.Content = strPtr(contentText)
		}
		twccMessages = append(twccMessages, msg)
	}
	return twccMessages
}

func (m *TWCC) mapRole(role llms.ChatMessageType) string {
	switch role {
	case llms.ChatMessageTypeHuman: return "user"
	case llms.ChatMessageTypeAI: return "assistant"
	case llms.ChatMessageTypeSystem: return "system"
	case llms.ChatMessageTypeTool: return "tool"
	default: return string(role)
	}
}

func (m *TWCC) toTWCCParameters(opts *llms.CallOptions) TWCCParameters {
	p := TWCCParameters{Stream: opts.StreamingFunc != nil}
	meta := opts.Metadata

	if v, ok := meta["max_new_tokens"].(int); ok { p.MaxNewTokens = &v }
	if v, ok := meta["temperature"].(float64); ok { p.Temperature = &v }
	if v, ok := meta["top_p"].(float64); ok { p.TopP = &v }
	if v, ok := meta["top_k"].(int); ok { p.TopK = &v }
	if v, ok := meta["frequence_penalty"].(float64); ok { p.FrequencePenalty = &v }
	if v, ok := meta["stop_sequences"].([]string); ok { p.StopSequences = v }
	if v, ok := meta["seed"].(int); ok { p.Seed = &v }
	
	return p
}

func (m *TWCC) toTWCCTools(tools []llms.Tool) []TWCCTool {
	if len(tools) == 0 { return nil }
	twccTools := make([]TWCCTool, 0, len(tools))
	for _, t := range tools {
		params := t.Function.Parameters
		if params == nil {
			params = map[string]interface{}{"type": "object", "properties": map[string]interface{}{}}
		}
		twccTools = append(twccTools, TWCCTool{
			Type: t.Type,
			Function: TWCCToolFunction{
				Name: t.Function.Name, Description: t.Function.Description, Parameters: params,
			},
		})
	}
	return twccTools
}

func (m *TWCC) doRequest(ctx context.Context, body []byte, isStreaming bool) (*http.Response, error) {
	endpoint := fmt.Sprintf("%s/models/conversation", m.BaseURL)
	req, err := http.NewRequestWithContext(ctx, "POST", endpoint, bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-KEY", m.APIKey)

	client := m.HTTPClient
	if isStreaming { client = &http.Client{Timeout: 0} }

	resp, err := client.Do(req)
	if err != nil { return nil, fmt.Errorf("failed to send request to TWCC: %v", err) }

	if resp.StatusCode != http.StatusOK {
		raw, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("TWCC API returned error status %d: %s", resp.StatusCode, string(raw))
	}
	return resp, nil
}

// handleStreamingResponse manages the SSE flow using a dedicated processor.
func (m *TWCC) handleStreamingResponse(ctx context.Context, body io.Reader, opts *llms.CallOptions) (*llms.ContentResponse, error) {
	reader := bufio.NewReader(body)
	proc := &streamProcessor{
		toolCallsMap: make(map[int]*TWCCToolCall),
		streamingFunc: opts.StreamingFunc,
	}

	for {
		line, err := reader.ReadString('\n')
		if line != "" {
			if stop := proc.processLine(ctx, line); stop { break }
		}
		if err != nil {
			if err == io.EOF { break }
			return nil, fmt.Errorf("error reading stream: %v", err)
		}
	}

	proc.finalize(ctx)
	return proc.toContentResponse(m.ModelName), nil
}

type streamProcessor struct {
	isToolCalling      bool
	detectionConfirmed bool
	lineBuffer         []string
	contentBuffer      strings.Builder
	toolCallsMap       map[int]*TWCCToolCall
	fullContent        strings.Builder
	lastUsage          *TWCCStreamResponse
	streamingFunc      func(context.Context, []byte) error
}

func (p *streamProcessor) processLine(ctx context.Context, line string) bool {
	trimmed := strings.TrimSpace(line)
	if !strings.HasPrefix(trimmed, "data:") {
		p.handleControlLine(ctx, line)
		return false
	}

	jsonData := strings.TrimSpace(strings.TrimPrefix(trimmed, "data:"))
	if jsonData == "[DONE]" {
		p.handleDone(ctx, line)
		return true
	}

	var chunk TWCCStreamResponse
	if err := json.Unmarshal([]byte(jsonData), &chunk); err != nil {
		return false
	}

	p.detectType(&chunk)
	p.processChunk(ctx, &chunk, line)
	return false
}

func (p *streamProcessor) handleControlLine(ctx context.Context, line string) {
	if !p.detectionConfirmed {
		p.lineBuffer = append(p.lineBuffer, line)
	} else if !p.isToolCalling {
		p.streamingFunc(ctx, []byte(line))
	}
}

func (p *streamProcessor) handleDone(ctx context.Context, line string) {
	if !p.detectionConfirmed {
		p.isToolCalling = false
		p.detectionConfirmed = true
		p.flushBuffer(ctx)
	}
	if !p.isToolCalling {
		p.streamingFunc(ctx, []byte(line))
	}
}

func (p *streamProcessor) detectType(chunk *TWCCStreamResponse) {
	if p.detectionConfirmed { return }

	// A. Structural Check
	hasTools := len(chunk.ToolCalls) > 0 || (len(chunk.Choices) > 0 && (len(chunk.Choices[0].Delta.ToolCalls) > 0 || chunk.Choices[0].FinishReason == "tool_calls"))
	if hasTools {
		p.isToolCalling, p.detectionConfirmed = true, true
		return
	}

	// B. Heuristic Check (Wait for enough content or XML tags)
	text := chunk.GeneratedText
	if len(chunk.Choices) > 0 { text = chunk.Choices[0].Delta.Content }
	p.contentBuffer.WriteString(text)
	
	combined := p.contentBuffer.String()
	if strings.Contains(combined, "<function=") || strings.Contains(combined, "tool<function") {
		p.isToolCalling, p.detectionConfirmed = true, true
	} else if len(combined) > 64 {
		p.isToolCalling, p.detectionConfirmed = false, true
	}
}

func (p *streamProcessor) processChunk(ctx context.Context, chunk *TWCCStreamResponse, rawLine string) {
	text := chunk.GeneratedText
	if len(chunk.Choices) > 0 { text = chunk.Choices[0].Delta.Content }
	p.fullContent.WriteString(text)

	if chunk.PromptTokens > 0 || chunk.Usage != nil { p.lastUsage = chunk }

	if !p.detectionConfirmed {
		p.lineBuffer = append(p.lineBuffer, rawLine)
		return
	}

	if p.isToolCalling {
		p.accumulateTools(chunk)
	} else {
		p.flushBuffer(ctx)
		p.streamingFunc(ctx, []byte(rawLine))
	}
}

func (p *streamProcessor) accumulateTools(chunk *TWCCStreamResponse) {
	// Source deduplication: Prefer delta
	source := chunk.ToolCalls
	if len(chunk.Choices) > 0 && len(chunk.Choices[0].Delta.ToolCalls) > 0 {
		source = chunk.Choices[0].Delta.ToolCalls
	}

	for _, tc := range source {
		idx := 0
		if tc.Index != nil { idx = *tc.Index }

		if _, exists := p.toolCallsMap[idx]; !exists {
			p.toolCallsMap[idx] = &TWCCToolCall{ID: tc.ID, Type: tc.Type}
			p.toolCallsMap[idx].Function.Name = tc.Function.Name
		}
		p.toolCallsMap[idx].Function.Arguments += cleanXML(tc.Function.Arguments)
		if tc.ID != "" { p.toolCallsMap[idx].ID = tc.ID }
		if tc.Function.Name != "" { p.toolCallsMap[idx].Function.Name = tc.Function.Name }
	}
}

func (p *streamProcessor) flushBuffer(ctx context.Context) {
	if len(p.lineBuffer) == 0 { return }
	for _, b := range p.lineBuffer { p.streamingFunc(ctx, []byte(b)) }
	p.lineBuffer = nil
}

func (p *streamProcessor) finalize(ctx context.Context) {
	if !p.detectionConfirmed {
		p.isToolCalling = false
		p.flushBuffer(ctx)
	}
}

func (p *streamProcessor) toContentResponse(model string) *llms.ContentResponse {
	resp := &llms.ContentResponse{
		Choices: []*llms.ContentChoice{{
			Content: p.fullContent.String(),
			GenerationInfo: map[string]interface{}{"model": model},
		}},
	}

	if p.isToolCalling {
		tools := make([]llms.ToolCall, 0)
		for _, tc := range p.toolCallsMap {
			tools = append(tools, llms.ToolCall{
				ID: tc.ID, Type: tc.Type,
				FunctionCall: &llms.FunctionCall{Name: tc.Function.Name, Arguments: tc.Function.Arguments},
			})
		}
		// Heuristic XML fallback
		if len(tools) == 0 {
			extracted, cleaned := extractXMLToolCalls(p.fullContent.String())
			if len(extracted) > 0 {
				tools = extracted
				resp.Choices[0].Content = cleaned
			}
		}
		resp.Choices[0].GenerationInfo["tool_calls"] = tools
	}

	if p.lastUsage != nil {
		u := p.lastUsage
		it, ot, tt := u.PromptTokens, u.GeneratedTokens, u.TotalTokens
		if u.Usage != nil {
			if it == 0 { it = u.Usage.PromptTokens }
			if ot == 0 { ot = u.Usage.GeneratedTokens }
			tt = it + ot
		}
		resp.Choices[0].GenerationInfo["usage"] = map[string]interface{}{
			"input_tokens": it, "output_tokens": ot, "total_tokens": tt,
		}
	}
	return resp
}

func (m *TWCC) handleStandardResponse(body io.Reader) (*llms.ContentResponse, error) {
	raw, _ := io.ReadAll(body)
	logs.FInfo("TWCC Raw Response: %s", string(raw))

	var tr TWCCResponse
	if err := json.Unmarshal(raw, &tr); err != nil {
		return nil, fmt.Errorf("failed to unmarshal: %v", err)
	}

	content := tr.GeneratedText
	var tools []llms.ToolCall

	// Extraction logic... (flattened)
	if len(tr.ToolCalls) > 0 {
		for _, tc := range tr.ToolCalls {
			tools = append(tools, llms.ToolCall{
				ID: tc.ID, Type: tc.Type,
				FunctionCall: &llms.FunctionCall{Name: tc.Function.Name, Arguments: tc.Function.Arguments},
			})
		}
	} else if len(tr.Choices) > 0 {
		c := tr.Choices[0]
		if c.Message.Content != "" { content = c.Message.Content }
		for _, tc := range c.Message.ToolCalls {
			tools = append(tools, llms.ToolCall{
				ID: tc.ID, Type: tc.Type,
				FunctionCall: &llms.FunctionCall{Name: tc.Function.Name, Arguments: tc.Function.Arguments},
			})
		}
	}

	if len(tools) == 0 && (strings.Contains(content, "<function=") || strings.Contains(content, "tool<")) {
		tools, content = extractXMLToolCalls(content)
	}

	return &llms.ContentResponse{
		Choices: []*llms.ContentChoice{{
			Content: content,
			GenerationInfo: map[string]interface{}{
				"model": m.ModelName, "tool_calls": tools,
				"usage": map[string]interface{}{
					"input_tokens": tr.PromptTokens, "output_tokens": tr.GeneratedTokens, "total_tokens": tr.TotalTokens,
				},
			},
		}},
	}, nil
}

// extractXMLToolCalls identifies <function=NAME>{ARGS}</function> in text,
// extracts them as ToolCalls, and returns the text with tags removed.
func extractXMLToolCalls(text string) ([]llms.ToolCall, string) {
	var toolCalls []llms.ToolCall
	remainingText := text

	// Basic regex-free parsing for reliability with AFS fragments
	for {
		startTag := "<function="
		startIdx := strings.Index(remainingText, startTag)
		if startIdx == -1 {
			startTag = "tool<function="
			startIdx = strings.Index(remainingText, startTag)
			if startIdx == -1 { break }
		}

		nameEndIdx := strings.Index(remainingText[startIdx:], ">")
		if nameEndIdx == -1 { break }
		nameEndIdx += startIdx

		funcName := remainingText[startIdx+len(startTag) : nameEndIdx]
		endTag := "</function>"
		endIdx := strings.Index(remainingText[nameEndIdx:], endTag)
		if endIdx == -1 { break }
		endIdx += nameEndIdx

		args := remainingText[nameEndIdx+1 : endIdx]
		toolCalls = append(toolCalls, llms.ToolCall{
			ID: fmt.Sprintf("call_%d", time.Now().UnixNano()), Type: "function",
			FunctionCall: &llms.FunctionCall{Name: funcName, Arguments: args},
		})
		remainingText = remainingText[:startIdx] + remainingText[endIdx+len(endTag):]
	}
	return toolCalls, strings.TrimSpace(remainingText)
}

func (m *TWCC) Call(ctx context.Context, prompt string, options ...llms.CallOption) (string, error) {
	msg := llms.MessageContent{Role: llms.ChatMessageTypeHuman, Parts: []llms.ContentPart{llms.TextContent{Text: prompt}}}
	resp, err := m.GenerateContent(ctx, []llms.MessageContent{msg}, options...)
	if err != nil { return "", err }
	return resp.Choices[0].Content, nil
}

func strPtr(s string) *string { return &s }

// cleanXML removes hallucinated XML tags from a string.
func cleanXML(s string) string {
	for {
		startIdx := strings.Index(s, "<function=")
		if startIdx == -1 {
			startIdx = strings.Index(s, "tool<function=")
			if startIdx == -1 { break }
		}
		endIdx := strings.Index(s[startIdx:], ">")
		if endIdx == -1 { break }
		endIdx += startIdx
		s = s[:startIdx] + s[endIdx+1:]
	}
	return strings.ReplaceAll(s, "</function>", "")
}

// isPotentialToolPrefix checks if the string ends with a potential start of an XML tool call tag.
func isPotentialToolPrefix(s string) bool {
	if len(s) > 20 { s = s[len(s)-20:] }
	s = strings.ToLower(s)
	prefixes := []string{" tool<", "tool<", "<func", "<f", " <"}
	for _, p := range prefixes {
		if strings.HasSuffix(s, p) { return true }
	}
	return strings.HasSuffix(s, " tool")
}
