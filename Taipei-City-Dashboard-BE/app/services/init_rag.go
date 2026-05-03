package services

import (
    "fmt"
    "log"
    "path/filepath"

    "TaipeiCityDashboardBE/app/models"
    "gorm.io/gorm"
)

func InitSubsidyKB(db *gorm.DB) error {
    // 1. 创建表
    err := models.CreateSubsidyKBTable(db)
    if err != nil {
        return err
    }

    // 2. 清空舊資料 (每次重啟都重新載入最新 txt 內容)
    db.Session(&gorm.Session{AllowGlobalUpdate: true}).Delete(&models.SubsidyKB{})

    // 3. 读取文本
    filePath := filepath.Join("data", "subsidy", "subsidy.txt")
    text, err := ReadSubsidyText(filePath)
    if err != nil {
        log.Printf("讀取文件失敗: %v", err)
        return err
    }

    // 3. 分块并保存
    chunks := ChunkText(text, 500)
    for i, chunk := range chunks {
        doc := models.SubsidyKB{
            Content: chunk,
            Title:   fmt.Sprintf("補助訊息 - 第 %d 部分", i+1),
            City:    "taipei",
        }
        db.Create(&doc)
    }

    log.Println("✅ 補助知識庫初始化完成")
    return nil
}