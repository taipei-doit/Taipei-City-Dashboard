package services

import (
    "os"
    "strings"
)

// ReadSubsidyText 读取补助文本文件
func ReadSubsidyText(filePath string) (string, error) {
    content, err := os.ReadFile(filePath)
    if err != nil {
        return "", err
    }
    return string(content), nil
}

// ChunkText 将文本分块
func ChunkText(text string, size int) []string {
    var chunks []string
    runes := []rune(text)
    
    for i := 0; i < len(runes); i += size {
        end := i + size
        if end > len(runes) {
            end = len(runes)
        }
        chunk := string(runes[i:end])
        if strings.TrimSpace(chunk) != "" {
            chunks = append(chunks, chunk)
        }
    }
    return chunks
}