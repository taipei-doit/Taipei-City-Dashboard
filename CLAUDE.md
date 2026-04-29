# CLAUDE.md

本檔案給 Claude Code 使用。協作者是前端工程師，只負責 `Taipei-City-Dashboard-FE/` 子專案。

## 1. 語言

YOU MUST respond in 繁體中文 (zh-TW). NEVER use 簡體中文 (zh-CN)。

## 2. 專案概覽（MUST read first）

先讀 [.claude/projects/ProjectOverview.md](./.claude/projects/ProjectOverview.md)──包含 monorepo 結構、FE 技術棧、目錄組織、資料流、設計哲學。

## 3. 工作邊界（重要）

這是 monorepo，協作者**只在 `Taipei-City-Dashboard-FE/`** 工作：

| 路徑 | 可動嗎 |
|---|:-:|
| `Taipei-City-Dashboard-FE/` | ✅ |
| `Taipei-City-Dashboard-BE/`（Go）| ❌ |
| `Taipei-City-Dashboard-DE/`（資料工程）| ❌ |
| `db-sample-data/` | ❌ |
| `docker/`、`helm-chart/` | ❌ |
| `.github/`、`.vscode/` | 僅必要時；先問 |
| `docs/`、`.claude/` | ✅（看指令性質）|
| 根目錄 `CLAUDE.md`、`README.md`、`.claude/projects/ProjectOverview.md` | 僅使用者明確要求才改 |

若必須跨專案改動，先在 `docs/` 寫架構決議並告知使用者，不要默默動手。

## 4. 開發規則（MUST read）

這兩份 rules 是硬規範，每個檔案都要符合：

- [.claude/rules/code-style.md](./.claude/rules/code-style.md) — Vue 元件骨架、命名、CSS 撰寫順序
- [.claude/rules/uiux.md](./.claude/rules/uiux.md) — 設計原則、CSS variables、字體層級

## 5. 開發指令

工作目錄是 `Taipei-City-Dashboard-FE/`：

```bash
cd Taipei-City-Dashboard-FE

npm install              # 首次
npm run dev              # Vite dev server（預設 port 5173）
npm run build            # eslint --fix 後 production build
npm run build:test       # test 模式 build
npm run lint             # ESLint auto-fix
npm run preview          # Vite preview（看 build 結果）
```

**交付前必跑**：`npm run lint` 確認無錯誤。

## 6. 視覺一致性預設（重要）

**任何新 UI（View / 組件 / 對話框）動手寫之前**：

### Step 0：觀摩既有實作（MANDATORY）

必須先讀至少一個既有同類型檔案，並在對話中向使用者回報「你打算重用哪些殼、自幹哪些、明確偏離點」。沒有 Step 0 直接開工 = 很可能做出跟系統視覺脫節的東西。

| 要做什麼 | Step 0 必讀 |
|---|---|
| 新 View（有圖表）| `src/views/DashboardView.vue` + `src/dashboardComponent/DashboardComponent.vue` |
| 新 View（有地圖）| `src/views/MapView.vue` + `src/components/map/MapContainer.vue` |
| 新圖表卡片 | 一個既有 `src/dashboardComponent/components/*.vue`（例 `ColumnChart.vue`） |
| 新地圖層 | `src/store/mapStore.js` 的 `addMapLayer` / `initializeBasicLayers` |
| 新彈跳視窗 | `src/components/dialogs/MoreInfo.vue` + `src/store/dialogStore.js` |

### Step 0.5：盤點 `src/components/utilities/` 與 `src/components/dialogs/`（**強制**）

任何 view / 組件 / 對話框開工前，**必先**掃 `Taipei-City-Dashboard-FE/src/components/utilities/` 與 `src/components/dialogs/` 兩個資料夾，列出可重用的元件──**不得自己生成已存在的元件**。常見撞名重做：bars 內的 NavBar / SideBar / SettingsBar、miscellaneous 內的 SideBarTab、forms / buttons / loading 通用元件、dialogs 內的各式彈窗。

判定：能直接用就 import；需小改先在對話中說明擴 props / slot 方案再改原檔；真不適用才自幹，且要列出原因。

### 重用優先原則

- **預設**：重用既有殼（`DashboardComponent`、`MapContainer`、`ColumnChart` 等 `dashboardComponent/components/*`、`ComponentTag`、`dialogStore`）+ 上述 Step 0.5 盤點到的 `utilities/**` / `dialogs/**` 元件
- **Opt-out 條件**：使用者明示「獨立 demo 頁」「不要用共用元件」才自幹；此時必須在對話中列出「本頁 vs 既有儀表板」的差異對照表

## 7. Workflow：建組件／地圖／頁面

依需求對應下列 skill（Claude Code 會在關鍵字命中時自動觸發；你也可以主動呼叫）：

| 你想做的事 | 用哪個 skill | 入口檔 |
|---|---|---|
| **建新頁面（View）+ 路由** | `page` | [.claude/skills/page/SKILL.md](./.claude/skills/page/SKILL.md) |
| **新增／修改 dashboard 圖表組件** | `chart` | [.claude/skills/chart/SKILL.md](./.claude/skills/chart/SKILL.md) |
| **新增／修改地圖圖層、mapStore** | `map` | [.claude/skills/map/SKILL.md](./.claude/skills/map/SKILL.md) |
| **新增／修改彈跳視窗** | `dialog` | [.claude/skills/dialog/SKILL.md](./.claude/skills/dialog/SKILL.md) |
| **Code review PR / local branch** | `code-review` agent | [.claude/agents/code-review.md](./.claude/agents/code-review.md) |

### 「從零到一」建立新儀表板的完整流程

> 例：使用者說「幫我建一個『災時供水站』地圖頁面，含 AED 分布」

1. **page skill** → 問清楚頁面名稱、路由、layout 類型（DashboardView 式 grid 或 MapView 式左組件右地圖）、組件清單
2. **page skill Step 1** → 在 `src/views/` 建立 View 元件
3. **page skill Step 2** → 註冊路由（**預設加 `meta: { layout: "dashboard" }`** 套用主站殼）
4. **page skill Step 3** → **SideBar 加分頁 link（強制）**──沒 link 等於頁面找不到；demo 頁加在「示範儀表板」section
5. **chart skill**（若有圖表組件）→ 在 `src/dashboardComponent/` 建立圖表 Vue 元件，在 `src/assets/configs/apexcharts/chartTypes.js` 註冊、在 `src/main.js` 全域註冊
6. **map skill**（若含地圖）→ 在 `src/assets/configs/mapbox/mapConfig.js` 的 `maplayerCommonPaint` / `maplayerCommonLayout` 定義新地圖類型
7. **dialog skill**（若需彈跳視窗）→ 在 `dialogStore` 註冊，放在觸發元素旁
8. `npm run lint` + 視覺檢查（dev server）──確認 SideBar link 點得到、NavBar tab 行為正常
9. 若需 code review：觸發 `code-review` agent

page skill 的 SKILL.md 已有完整 8 步驟與 checkbox，照著做即可。**SideBar link 是必經步驟**，不要省。

## 8. 問題輸出規則

每次使用者問架構 / 文件改善類問題，**輸出新檔到 `docs/`，不要直接改原檔**：

| 類型 | 輸出位置 |
|---|---|
| 架構決議 / 文件改善 | `docs/<topic>.md` |
| Code review 報告 | `docs/code-review-reports/<PR>.md`（code-review agent 自動） |
| 其他分類 | `docs/<category>/<filename>.md` |

## 9. 硬禁止（以 `Taipei-City-Dashboard-FE/package.json` 為真相依據）

### 程式碼層

- ❌ `var`（用 `let` / `const`）
- ❌ `console.log`、`debugger` 殘留
- ❌ Hardcoded 顏色（用 `var(--color-*)`）

### 「不在 package.json 中」就是「不存在」──不要引入或假設它存在

- ❌ TailwindCSS / 任何 CSS 框架
- ❌ TypeScript 語法（`interface`、`type`、型別標註 `: string`）
- ❌ 任何 UI component 庫（Material UI、Element Plus、Vuetify、Ant Design）
- ❌ 任何測試框架（vitest / jest / playwright / cypress）
- ❌ Prettier（`rules/code-style.md` 雖有提及，但 package.json 無 prettier、且無 `.prettierrc` 檔；以 package.json 為準）
- ❌ i18n 套件、表單驗證庫等其他未安裝依賴

### 配置檔

- ❌ 修改 `eslint.config.js`（除非使用者明確要求）。注意：專案中**沒有** `.eslintrc.json` 或 `.prettierrc`
- ❌ 修改 `vite.config.js`（除非使用者明確要求）

### 工作邊界

- ❌ 跨越工作邊界動 BE / DE / docker / helm

## 10. 新增依賴前

若要 `npm install <new-package>`，先在對話中說明：
1. 為什麼需要它
2. 替代方案為何不適用
3. bundle size 影響

等使用者確認再安裝。

## 11. 推薦 workflow 對話範本

使用者模糊描述需求時，先問清楚：

> 我要做 XX 組件 / 頁面

**回問模板**：
1. 是**單一圖表組件**（加到既有 Dashboard）還是**整頁**（有自己的路由）？
2. 若整頁：layout 是 Dashboard（純 grid）還是 MapView（左組件+右地圖）？
3. 資料來源：用 `contentStore` 既有 API 流程，還是要接新 API？
4. 組件清單：幾個圖表？有地圖嗎？要彈跳視窗嗎？
5. 雙北整合需求：臺北 only，還是雙北切換？

問完再 follow 對應 skill 的 SKILL.md 流程。

## 12. agent-browser 截圖注意事項

此專案的儀表板 grid 容器（如 `.mrtaccessibilityview-overview`）使用 `overflow-y: scroll`，`agent-browser scroll down <px>` 只滾 window，**對這個 scroll container 無效**。

正確做法：用 `scrollintoview` 把目標組件捲進 viewport，讓 ApexCharts 觸發渲染後再截圖：

```bash
agent-browser scrollintoview ".dashboardcomponent:nth-child(3)"
sleep 3
agent-browser screenshot /tmp/screenshot.png
```
