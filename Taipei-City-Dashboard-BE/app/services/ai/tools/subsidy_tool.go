package tools

import (
    "context"
    "fmt"
    "strings"

    "TaipeiCityDashboardBE/app/models"
    "gorm.io/gorm"
)

type SubsidyArgs struct {
    Query string `json:"query"`
}

func RetrieveSubsidies(ctx context.Context, args string, db *gorm.DB) (string, error) {
    var params SubsidyArgs
    if err := parseArgs(args, &params); err != nil {
        return "", fmt.Errorf("invalid arguments: %v", err)
    }

    var docs []models.SubsidyKB
    
    db.Where("content LIKE ?", "%"+params.Query+"%").
        Limit(3).
        Find(&docs)

    if len(docs) == 0 {
        return "抱歉，找不到相關補助資訊", nil
    }

    var result strings.Builder
    result.WriteString("根據查詢找到以下補助資訊：\n\n")
    for i, doc := range docs {
        result.WriteString(fmt.Sprintf("【結果 %d】\n%s\n\n", i+1, doc.Content))
    }

    return result.String(), nil
}