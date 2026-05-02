# 臺北城市儀表板：組件開發與資料寫入指南
本文件記錄了「循環杯門市分佈」組件的開發流程，可作為後續新增資料組件的參考手冊。

## 一、 核心工作流 (Workflow)

1. **資料預處理 (Pre-processing)**：
   - 讀取原始資料（如 ODS/CSV）。
   - 進行資料清洗（如使用 Regex 擷取地址中的「行政區」）。
   - 統計各區數量並產出乾淨的 CSV。

2. **資料庫寫入 (Data Import)**：
   - 在 `dashboard` 資料庫建立資料表（如 `reusable_cup_stats`）。
   - 將清洗後的統計資料寫入該表。

3. **組件與圖表配置 (Metadata Configuration)**：
   - 在 `dashboardmanager` 資料庫註冊組件基本資訊 (`components`)。
   - 設定 SQL 查詢邏輯 (`query_charts`)。
   - 設定圖表呈現樣式 (`component_charts`)。

4. **儀表板整合 (Dashboard Integration)**：
   - 建立或指定儀表板 (`dashboards`) 並關聯組件。
   - 將儀表板分配至顯示群組 (`dashboard_groups`) 以顯示於選單。

---

## 二、 SQL 寫入範例與欄位說明

### 1. 資料庫：`dashboard` (存放實際統計數據)
**範例指令：**
```sql
CREATE TABLE public.reusable_cup_stats (
    district VARCHAR(50), -- 行政區名稱 (如：文山區)
    count INTEGER,        -- 門市數量
    city VARCHAR(50)      -- 城市名稱 (如：臺北市)
);

INSERT INTO public.reusable_cup_stats (district, count, city) 
VALUES ('文山區', 53, '臺北市');
```

### 2. 資料庫：`dashboardmanager` (存放組件配置)

#### (A) `components` 表：定義組件識別碼
| 欄位 | 說明 | 範例 |
| :--- | :--- | :--- |
| `id` | 唯一數字 ID | `301` |
| `index` | 唯一字串識別碼 | `taipei_reusable_cup` |
| `name` | 顯示在前端的組件標題 | `臺北市各區循環杯門市數量` |

#### (B) `query_charts` 表：定義資料來源 SQL
| 欄位 | 說明 | 備註 |
| :--- | :--- | :--- |
| `index` | 對應 `components.index` | |
| `query_type` | 資料維度 | 雙北合併請設為 `three_d` |
| `query_chart` | 執行的 SQL 查詢 | 必須回傳 `x_axis`, `y_axis`, `data` |
| `city` | 城市標記 | 雙北合併請設為 `metrotaipei` |

**SQL 要求格式（雙北合併版）：**
```sql
SELECT 
    district as x_axis,   -- X 軸顯示文字 (行政區)
    city as y_axis,        -- 資料分類名稱 (臺北市/新北市)
    count as data          -- 數值
FROM public.reusable_cup_stats
ORDER BY data DESC;
```

#### (C) `component_charts` 表：定義呈現樣式
| 欄位 | 說明 | 範例 |
| :--- | :--- | :--- |
| `index` | 對應 `components.index` | |
| `types` | 支援的圖表類型 (Array) | `ARRAY['DistrictChart', 'BarChart']` |
| `color` | 圖表顏色 (Array，雙北需兩色) | `ARRAY['#4CAF50', '#2196F3']` |
| `unit` | 數值單位 | `間` |

> [!TIP]
> **常見圖表類型名稱 (PascalCase)：**
> - `DistrictChart`：行政區地圖
> - `BarChart`：橫向長條圖
> - `ColumnChart`：縱向柱狀圖
> - `PieChart`：圓餅圖
>
> **雙北合併注意事項：**
> - `query_type` 須設為 `three_d`，讓後端以 `y_axis`（城市）分組產生多系列資料
> - `color` 需至少兩個顏色，分別代表臺北市與新北市
> - `city` 須設為 `metrotaipei`，使組件歸屬於雙北儀表板

#### (D) `dashboard_groups` 表：控制選單顯示
必須將儀表板 ID 與群組 ID 關聯，否則選單不會出現。
- **Group 2**: 臺北市 (Taipei)
- **Group 3**: 新北市 (Metro Taipei)

```sql
INSERT INTO public.dashboard_groups (dashboard_id, group_id) VALUES (400, 2);
```

---

## 二之一、 雙北合併組件 SQL 範例

將原本分開的臺北市與新北市循環杯組件合併為一個雙北組件：

### 1. 資料表（dashboard 資料庫）
```sql
-- reusable_cup_stats 表已包含兩市資料，無需修改
-- 確認資料：
SELECT city, COUNT(*) FROM public.reusable_cup_stats GROUP BY city;
-- 預期：臺北市 12 筆、新北市 27 ��
```

### 2. 組件設定（dashboardmanager 資料庫）

```sql
-- (A) components：合併為單一組件
INSERT INTO public.components (id, index, name)
VALUES (301, 'metrotaipei_reusable_cup', '雙北各區循環杯門市數量')
ON CONFLICT (id) DO UPDATE SET index = EXCLUDED.index, name = EXCLUDED.name;

-- (B) query_charts：使用 three_d 查詢類型，city 設為 metrotaipei
INSERT INTO public.query_charts (index, query_type, query_chart, city)
VALUES (
    'metrotaipei_reusable_cup',
    'three_d',
    'SELECT district as x_axis, city as y_axis, count as data FROM public.reusable_cup_stats ORDER BY data DESC',
    'metrotaipei'
);

-- (C) component_charts：DistrictChart + BarChart，兩個顏色分別代表兩市
INSERT INTO public.component_charts (index, types, color, unit)
VALUES (
    'metrotaipei_reusable_cup',
    ARRAY['DistrictChart', 'BarChart'],
    ARRAY['#4CAF50', '#2196F3'],
    '間'
);
```

### 3. 儀表板關聯
```sql
-- 將合併後的組件加入循環經濟儀表板（假設 dashboard_id = 400）
-- 確保 dashboard_groups 關聯到 Group 3（雙北）
INSERT INTO public.dashboard_groups (dashboard_id, group_id)
VALUES (400, 3)
ON CONFLICT DO NOTHING;
```

---

## 三、 常見問題排除
- **頁面沒出現**：檢查 `dashboard_groups` 是否有正確關聯。
- **圖表沒資料**：檢查 `query_charts.query_chart` 的 SQL 指令是否能正確在 `dashboard` 資料庫執行，且欄位名稱是否為 `x_axis`, `y_axis`, `data`。
- **後端崩潰**：若 API 無法運作，前端將無法讀取任何配置，請確保 `dashboard-be` 容器狀態為 `Up`。
