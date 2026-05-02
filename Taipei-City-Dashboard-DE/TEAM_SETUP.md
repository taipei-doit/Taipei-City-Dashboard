# 行人安全地圖 — 環境設定指南

> 適用分支：`feature/pedestrian-safety`
> 前提：已完成官方 Docker 環境設定（能跑起來基本 Dashboard）

---

## 第一次設定（從來沒跑過）

### 步驟一：拉程式碼

```powershell
git fetch origin
git checkout feature/pedestrian-safety
git pull origin feature/pedestrian-safety
```

### 步驟二：Import 行人事故資料（約 12MB）

> dump 本身會自動建表，**不需要**先跑 setup_pedestrian_tables.sql

**PowerShell 限制：不支援 `<` 重導向，必須用以下方式：**

```powershell
docker cp Taipei-City-Dashboard-DE/pedestrian_all.sql postgres-data:/tmp/pedestrian_all.sql
docker exec postgres-data psql -U postgres -d dashboard -f /tmp/pedestrian_all.sql
```

成功的話最後會出現多行 `COPY xxx`，有些 `already exists` 警告可以忽略。

### 步驟三：設定儀表板組件

```powershell
docker cp Taipei-City-Dashboard-DE/setup_pedestrian_components.sql postgres-manager:/tmp/setup.sql
docker exec postgres-manager psql -U postgres -d dashboardmanager -f /tmp/setup.sql
```

### 步驟四：重啟後端與前端

```powershell
docker restart dashboard-be
docker restart dashboard-fe
```

### 步驟五：重新整理瀏覽器

瀏覽器按 **Ctrl+Shift+R**（強制重新整理，不是一般 F5）

---

## 之後有人推新版，要更新

```powershell
git pull origin feature/pedestrian-safety
```

然後重跑步驟三（只需要步驟三，資料庫資料不用重跑）：

```powershell
docker cp Taipei-City-Dashboard-DE/setup_pedestrian_components.sql postgres-manager:/tmp/setup.sql
docker exec postgres-manager psql -U postgres -d dashboardmanager -f /tmp/setup.sql
```

如果後端程式碼也有改（`Taipei-City-Dashboard-BE/` 有變動），加跑：

```powershell
docker restart dashboard-be
```

最後 Ctrl+Shift+R 重整瀏覽器。

---

## 確認功能

| 功能 | 網址 |
|------|------|
| 行人安全地圖 | `http://localhost:8080/mapview?index=pedestrian-safety&city=metrotaipei` |

開啟後應看到：
- 左側：雙北行人事故熱區（行政區分布圖，有顏色深淺）
- 中間：雙北行人事故時段分析（熱力格）
- 右側：雙北行人事故年度趨勢（折線圖）
- 下方：行人事故高風險路口排名 + AI 路口安全報告

---

## 快速驗證資料有沒有進去

```powershell
docker exec postgres-data psql -U postgres -d dashboard -c "SELECT COUNT(*) FROM public.traffic_pedestrian_accident_taipei;"
docker exec postgres-data psql -U postgres -d dashboard -c "SELECT COUNT(*) FROM public.traffic_pedestrian_accident_ntpc;"
docker exec postgres-data psql -U postgres -d dashboard -c "SELECT COUNT(*) FROM public.metro_district_boundaries;"
```

預期結果：
- `traffic_pedestrian_accident_taipei`：數千筆
- `traffic_pedestrian_accident_ntpc`：數千筆
- `metro_district_boundaries`：**41**（台北 12 + 新北 29）

---

## 常見問題

**Q：行政區圖顯示 NaN 或全灰？**
- 步驟三的 `setup_pedestrian_components.sql` 沒有用 `docker cp` 方式執行（PowerShell 直接 `<` 重導向會造成中文字元損毀）
- 重新用 `docker cp` 方式跑步驟三

**Q：組件全部顯示問號（?????）？**
- 同上，`setup_pedestrian_components.sql` 中文字元損毀，重跑步驟三

**Q：跑步驟二出現 `already exists` 錯誤？**
- 正常，可忽略。確認最後有出現 `COPY xxx` 代表資料有進去

**Q：時段分析或年度趨勢顯示錯誤或空白？**
- 確認後端有重啟：`docker restart dashboard-be`
- 再 Ctrl+Shift+R

**Q：AI 分析按鈕沒有回應？**
- 確認 `docker/.env` 裡有設定 `ANTHROPIC_API_KEY`
