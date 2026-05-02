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

## 二、建立資料表結構

```powershell
docker exec -i postgres-data psql -U postgres -d dashboard < Taipei-City-Dashboard-DE/setup_pedestrian_tables.sql
```

---

## 三、取得行人事故資料（擇一）

### 方法 A：從隊友拿 dump 檔（快，推薦）

拿到 `pedestrian_all.sql` 之後：

```powershell
docker exec -i postgres-data psql -U postgres -d dashboard < pedestrian_all.sql
```

### 方法 B：自己從警政署下載（慢，約需 5–10 分鐘）

需先安裝 Python 套件：
```powershell
pip install pandas geopandas shapely pyproj psycopg2-binary requests
```

然後跑：
```powershell
python Taipei-City-Dashboard-DE/run_pedestrian_etl.py
```

---

## 四、設定儀表板組件

```powershell
docker exec -i postgres-manager psql -U postgres -d dashboardmanager < Taipei-City-Dashboard-DE/setup_pedestrian_components.sql
```

---

## 五、重新啟動前端容器

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

**Q：組件顯示 400 錯誤？**

確認各表有資料：
```powershell
docker exec postgres-data psql -U postgres -d dashboard -c "SELECT COUNT(*) FROM public.traffic_pedestrian_accident_taipei;"
docker exec postgres-data psql -U postgres -d dashboard -c "SELECT COUNT(*) FROM public.traffic_pedestrian_hotspot;"
```

如果是 0，表示資料沒有成功匯入，重跑步驟三。

**Q：組件設定沒有出現？**

步驟四的 `setup_pedestrian_components.sql` 可能沒跑，補跑一次。

**Q：AI 分析按鈕沒有回應？**

確認 `.env` 裡有設定 `ANTHROPIC_API_KEY`。
