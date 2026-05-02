# 行人安全地圖 — 環境設定指南

> 適用分支：`feature/pedestrian-safety`
> 前提：已完成官方 Docker 環境設定（能跑起來基本 Dashboard）

---

## 一、拉最新程式碼

```powershell
git fetch origin
git checkout feature/pedestrian-safety
git pull origin feature/pedestrian-safety
```

---

## 二、Import 行人事故資料（dump 檔，約 12MB）

> dump 本身會自動建表，不需要先跑 setup_pedestrian_tables.sql

```powershell
docker exec -i postgres-data psql -U postgres -d dashboard < Taipei-City-Dashboard-DE/pedestrian_all.sql
```

看到下面這樣就成功了（有些 `already exists` 警告可以忽略）：
```
SET
SET
...
COPY 29
COPY 12
```

---

## 三、設定儀表板組件

```powershell
docker exec -i postgres-manager psql -U postgres -d dashboardmanager < Taipei-City-Dashboard-DE/setup_pedestrian_components.sql
```

---

## 四、重新啟動前端容器

```powershell
docker restart dashboard-fe
```

然後在瀏覽器按 **Ctrl+Shift+R**（強制重新整理）。

---

## 確認功能

| 功能 | 網址 |
|------|------|
| 行人安全地圖 | `http://localhost:8080/mapview?index=pedestrian-safety&city=metrotaipei` |

地圖上應該可以看到：
- 熱點圖（事故密度 heatmap）
- 開啟組件後有 AI 路口安全分析按鈕

---

## 常見問題

**Q：跑 pedestrian_all.sql 出現 `already exists` 錯誤？**
- 正常！dump 會建表，若表已存在就跳過，資料仍會正確匯入
- 確認最後有出現 `COPY xxx` 訊息代表資料有進去

**Q：行政區圖（DistrictChart）是空的？**
- 確認 `metro_district_boundaries` 有資料：
  ```powershell
  docker exec postgres-data psql -U postgres -d dashboard -c "SELECT COUNT(*) FROM public.metro_district_boundaries;"
  ```
  應該要是 41（台北 12 + 新北 29）。若是 0，重新跑步驟二

**Q：組件顯示 400 錯誤？**
- 確認各表有資料：
  ```powershell
  docker exec postgres-data psql -U postgres -d dashboard -c "SELECT COUNT(*) FROM public.traffic_pedestrian_accident_taipei;"
  docker exec postgres-data psql -U postgres -d dashboard -c "SELECT COUNT(*) FROM public.traffic_pedestrian_hotspot;"
  ```
  如果是 0，重跑步驟二

**Q：組件設定沒有出現？**
- 步驟三的 `setup_pedestrian_components.sql` 可能沒跑，補跑一次

**Q：AI 分析按鈕沒有回應？**
- 確認 `.env` 裡有設定 `ANTHROPIC_API_KEY`
