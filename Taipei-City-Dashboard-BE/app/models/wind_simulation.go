package models

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"

	"gorm.io/gorm"
)

// WindSimulation 儲存都市風道模擬的結果快照
type WindSimulation struct {
	gorm.Model
	Name      string   `gorm:"column:name;type:varchar(100)" json:"name"`
	WindDir   float64  `gorm:"column:wind_dir" json:"wind_dir"`
	WindSpeed float64  `gorm:"column:wind_speed" json:"wind_speed"`
	GridData  GridData `gorm:"column:grid_data;type:jsonb" json:"grid_data"`
	CreatedBy uint     `gorm:"column:created_by" json:"created_by"`
}

// 定義自定義型別以便實作介面
type GridData []GridCell

type GridCell struct {
	CellID    string  `json:"cellId"`
	Frequency float64 `json:"frequency"`
}

// Value 實作 driver.Valuer，將資料寫入資料庫時轉為 JSON 字串
func (g GridData) Value() (driver.Value, error) {
	return json.Marshal(g)
}

// Scan 實作 sql.Scanner，將從資料庫讀出的 JSON 轉回 Go Struct
func (g *GridData) Scan(value interface{}) error {
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New(fmt.Sprint("Failed to unmarshal JSONB value:", value))
	}
	return json.Unmarshal(bytes, g)
}

func (WindSimulation) TableName() string {
	return "wind_simulations"
}

// --- 資料庫操作函式 ---

func SaveSimulation(sim *WindSimulation) error {
	return DBManager.Create(sim).Error
}

func GetSimulations() ([]WindSimulation, error) {
	var simulations []WindSimulation
	err := DBManager.Omit("grid_data").Order("created_at desc").Find(&simulations).Error
	return simulations, err
}

func GetSimulationByID(id uint) (WindSimulation, error) {
	var sim WindSimulation
	err := DBManager.First(&sim, id).Error
	return sim, err
}

func DeleteSimulation(id uint) error {
	return DBManager.Delete(&WindSimulation{}, id).Error
}