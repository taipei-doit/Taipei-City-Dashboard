package controllers

import (
	"database/sql"
	"math"
	"net/http"

	// "github.com/lib/pq"
	"fmt"
	"log"

	"github.com/gin-gonic/gin"
)

type MapInput struct {
	Lng float64 `json:"lng"`
	Lat float64 `json:"lat"`
}

// the struct of fake info is defined here
type Location struct {
	Name string  `json:"name"`
	Lat  float64 `json:"lat"`
	Lng  float64 `json:"lng"`
}


type Hospital struct {
    Id      int
    Name    string
	Level    string
	Address string
    X       float64
    Y       float64
}

type Library struct{
	Id      int
    Name    string
	Address string
    X       float64
    Y       float64
}

type Shopping struct{
	Id      int
    Name    string
	Address string
    X       float64
    Y       float64
}

func GetScopeInfoHandler(c *gin.Context){
	var req struct {
		Lat float64 `json:"lat"`
		Lng float64 `json:"lng"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	// get the 4 point
	distanceKm :=1.6
	latOffset := distanceKm / 111.0 // 緯度每度約 111 公里

	// 經度的偏移需考慮緯度的餘弦值
	lngOffset := distanceKm / (111.0 * math.Cos(req.Lat*math.Pi/180.0))

	// take data from postgresql
	// setting the connection information
	host := "codefest2025.rm-rf.uk"
    port := 5433
    user := "postgres"
    password := "mGPuAE2JTDDmdui8"
    dbname := "dashboard"

	// combine the information
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",host, port, user, password, dbname)
	
	// begin connection
	db, err := sql.Open("postgres", psqlInfo)
    if err != nil {
        log.Fatalf("連線錯誤: %v\n", err)
    }
    defer db.Close()

	// test connection
	err = db.Ping()
    if err != nil {
        log.Fatalf("無法連線到資料庫: %v\n", err)
    }

    fmt.Println("成功連上資料庫！")

	// select hospital information in new taipei city
	northLat := req.Lat + latOffset
	southLat := req.Lat - latOffset
	eastLng := req.Lng + lngOffset
	westLng := req.Lng - lngOffset

	hospitalRows, hospitalErr := db.Query(
    "SELECT id, name, address, type, x, y FROM nt_hospital WHERE y BETWEEN  $1 AND $2 AND x BETWEEN $3 AND $4",
    southLat, northLat, westLng, eastLng,
)

	// fmt.Println(rows)
    if hospitalErr != nil {
        log.Fatal("查詢失敗:", hospitalErr)
    }
    defer hospitalRows.Close()

	var hospitals []Hospital
	
	// outputtest
	for hospitalRows.Next() {
        var h Hospital
        hospitalErr := hospitalRows.Scan(&h.Id, &h.Name, &h.Level, &h.Address, &h.X, &h.Y)
        if hospitalErr != nil {
            log.Println("資料轉換錯誤hospital:", hospitalErr)
            continue
        }
		hospitals = append(hospitals, h)
		// fmt.Print(hospitals)
        // fmt.Printf("ID: %d, 名稱: %s, 種類: %s, 地址: %s, 緯度: %.6f, 經度: %.6f\n", h.id, h.name, h.level, h.address, h.x, h.y)
    }

	// select library information
	libraryRows, errLibrary:= db.Query(
    "SELECT id, name, address, x, y FROM nt_library WHERE y BETWEEN  $1 AND $2 AND x BETWEEN $3 AND $4",
    southLat, northLat, westLng, eastLng,
	)

	if errLibrary != nil {
        log.Fatal("查詢失敗:", err)
    }
    defer libraryRows.Close()

	var libraries []Library
	for libraryRows.Next() {
        var lib Library
        errLibrary := libraryRows.Scan(&lib.Id, &lib.Name, &lib.Address, &lib.X, &lib.Y)
        if errLibrary != nil {
            log.Println("lib資料轉換錯誤:", errLibrary)
            continue
        }
		libraries = append(libraries, lib)
 // fmt.Printf("ID: %d, 名稱: %s, 種類: %s, 地址: %s, 緯度: %.6f, 經度: %.6f\n", h.id, h.name, h.level, h.address, h.x, h.y)
    }

	// select shopping mall information in new taipei city
	shoppingRows, errShopping:= db.Query(
    "SELECT id, name, address, x, y FROM nt_shopping WHERE y BETWEEN  $1 AND $2 AND x BETWEEN $3 AND $4",
    southLat, northLat, westLng, eastLng,
	)
	if errShopping != nil {
        log.Fatal("查詢失敗:", err)
    }
    defer shoppingRows.Close()
	var shoppingMalls []Shopping
	for shoppingRows.Next(){
		var shop Shopping
        errShopping := shoppingRows.Scan(&shop.Id, &shop.Name, &shop.Address, &shop.X, &shop.Y)
        if errShopping != nil {
            log.Println("shop資料轉換錯誤:", errShopping)
            continue
        }
		shoppingMalls = append(shoppingMalls, shop)
	}

	// select hospital information in taipei city
	hospitalInTaipeiRows, errHospitalIntaipei:=db.Query(
    "SELECT id, name, address, type, x, y FROM t_hospital WHERE y BETWEEN  $1 AND $2 AND x BETWEEN $3 AND $4",
    southLat, northLat, westLng, eastLng,
	)
	if errHospitalIntaipei != nil {
        log.Fatal("查詢失敗:", err)
    }
    defer hospitalInTaipeiRows.Close()
	var hospitalsInTaipei []Hospital
	for hospitalInTaipeiRows.Next(){
		var hospitalInTaipei Hospital
        errHospitalIntaipei := hospitalInTaipeiRows.Scan(&hospitalInTaipei.Id, &hospitalInTaipei.Name, &hospitalInTaipei.Level, &hospitalInTaipei.Address, &hospitalInTaipei.X, &hospitalInTaipei.Y)
        if errHospitalIntaipei != nil {
            log.Println("資料轉換錯誤hospital:", hospitalErr)
            continue
        }
		hospitalsInTaipei = append(hospitalsInTaipei, hospitalInTaipei)
		// fmt.Print(hospitals)
	}

	// select library information in taipei city
// 	libraryInTaipeiRows, errLibraryInTaipei:= db.Query(
//     "SELECT id, name, address, x, y FROM t_library WHERE y BETWEEN  $1 AND $2 AND x BETWEEN $3 AND $4",
//     southLat, northLat, westLng, eastLng,
// 	)

// 	if errLibraryInTaipei != nil {
//         log.Fatal("查詢失敗:", err)
//     }
//     defer libraryInTaipeiRows.Close()

// 	var librariesInTaipei []Library
// 	for libraryInTaipeiRows.Next() {
//         var libraryInTaipei Library
//         errLibraryInTaipei := libraryRows.Scan(&libraryInTaipei.Id, &libraryInTaipei.Name, &libraryInTaipei.Address, &libraryInTaipei.X, &libraryInTaipei.Y)
//         if errLibraryInTaipei != nil {
//             log.Println("lib資料轉換錯誤:", errLibraryInTaipei)
//             continue
//         }
// 		librariesInTaipei = append(librariesInTaipei, libraryInTaipei)
//  // fmt.Printf("ID: %d, 名稱: %s, 種類: %s, 地址: %s, 緯度: %.6f, 經度: %.6f\n", h.id, h.name, h.level, h.address, h.x, h.y)
//     }

// 	// select shopping information in taipei city
	shoppingInTaipeiRows, errshopInTaipei:=(
    "SELECT id, name, address, x, y FROM t_shopping WHERE y BETWEEN  $1 AND $2 AND x BETWEEN $3 AND $4",
    southLat, northLat, westLng, eastLng,
	)
	if errshopInTaipei != nil {
        log.Fatal("查詢失敗 Taipei Shop:", err)
    }
	defer shoppingInTaipeiRows.Close()
	var shoppingMallsInTaipei []Shopping
	for shoppingInTaipeiRows.Next(){
		var shoppingMallInTaipei Shopping
        errshopInTaipei := shoppingInTaipeiRows.Scan(&shoppingMallInTaipei.Id, &shoppingMallInTaipei.Name, &shoppingMallInTaipei.Address, &shshoppingMallInTaipeiop.X, &shoppingMallInTaipei.Y)
        if errshopInTaipei != nil {
            log.Println("shop資料轉換錯誤:", errshopInTaipei)
            continue
        }
		shoppingMallsInTaipei = append(shoppingMallsInTaipei, shoppingMallInTaipei)
	}



	

	// TODO: 根據經緯度查資料庫，回傳 1.6 公里範圍內資料
	c.JSON(http.StatusOK, gin.H{
		"data": gin.H{
			"hospital": hospitals,
			"library": libraries,
			"shopping": shoppingMalls,
			"hospitalInTaipei": hospitalsInTaipei,
			// "libraryInTaipei":librariesInTaipei,
			"shoppingInTaipei": shoppingMallsIntaipei,
		},
	})
}

// haversine function calculate the distance
func haversine(lat1, lng1, lat2, lng2 float64) float64 {
	const R = 6371 // 地球半徑 (km)

	dLat := (lat2 - lat1) * math.Pi / 180.0
	dLng := (lng2 - lng1) * math.Pi / 180.0

	lat1Rad := lat1 * math.Pi / 180.0
	lat2Rad := lat2 * math.Pi / 180.0

	a := math.Sin(dLat/2)*math.Sin(dLat/2) +
		math.Sin(dLng/2)*math.Sin(dLng/2)*math.Cos(lat1Rad)*math.Cos(lat2Rad)
	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))

	return R * c
}
