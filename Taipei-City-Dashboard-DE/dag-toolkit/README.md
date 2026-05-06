# dag-toolkit

跨 LLM 工具包,協助維護者為 **Taipei City Dashboard** 與 **New Taipei City Dashboard** 產生符合既有規範的 Airflow DAG 三件組(`__init__.py`、`<table_name>.py`、`job_config.json`)。

可在 Claude Code、Claude(Web/Projects)、ChatGPT(Custom GPT)、Gemini(Gem),或任何 LLM 對話中使用。

> **使用範圍**:本 toolkit 為「**2026 年雙北儀表板 DAG 整併**」一次性整併工具,僅存活於 `feature/award-dag-integration` 分支,不會合進 `develop`。Team 成員從本分支 checkout 子分支進行整併作業,逐一 PR;整併完成後由維護者人工 merge / 同步至 `sit`,本分支歸檔。

---

## 工作原理

1. 對方 `git fetch && git checkout feature/award-dag-integration`,toolkit 就在 `Taipei-City-Dashboard-DE/dag-toolkit/`
2. 從本分支再開子分支 `feature/dag-<table_name>` 進行該支 DAG 的整併
3. 對方準備好 7 項輸入(DAG 識別、來源、格式 + 樣本、col_map、transform 邏輯、load_behavior)
4. 把 [`PROMPT.md`](./PROMPT.md) 貼進你選用的 LLM(或設成 system instruction)
5. LLM 與對方對話,缺什麼問什麼,通過 cross-check 後輸出 3 個檔的內容
6. 對方把產出 copy 到 `Taipei-City-Dashboard-DE/dags/<proj_folder>/<table_name>/`
7. 對方在本機跑 `python Taipei-City-Dashboard-DE/dag-toolkit/scripts/validate_dag.py <dag_path>`,作為硬性驗證
8. 對方起 docker-compose 跑 DAG,截 4 張圖
9. 對方依 [`pr_template.md`](./pr_template.md) 推 PR(target = `feature/award-dag-integration`),由維護者 review
10. 整併作業結束,維護者人工 merge / 同步進 `sit`

---

## 各家 LLM 用法

> 所有設置都用 toolkit 內檔案,不需另外 clone。從專案根目錄路徑為 `Taipei-City-Dashboard-DE/dag-toolkit/`。

### Claude Code(本機 CLI)

最簡單:在 Taipei-City-Dashboard 專案目錄打開 Claude Code,直接告訴它讀取 PROMPT:

```
請讀取 Taipei-City-Dashboard-DE/dag-toolkit/PROMPT.md 並依照流程協助我新增 DAG
```

或者註冊成專案級 skill(一次性):

```bash
mkdir -p .claude/skills/generate-dag
ln -sf ../../Taipei-City-Dashboard-DE/dag-toolkit/PROMPT.md .claude/skills/generate-dag/SKILL.md
```

之後在該專案的 Claude Code 內輸入 `/generate-dag` 即可。

### Claude(Web/Projects)

1. 建一個新的 Project(claude.ai → New Project)
2. Project Knowledge 上傳:
   - `Taipei-City-Dashboard-DE/dag-toolkit/PROMPT.md`(必)
   - `templates/` 全部
   - `examples/` 全部
   - `pr_template.md`
3. Project Custom Instructions 貼入:`PROMPT.md` 全文
4. 之後在該 Project 內對話即可

### ChatGPT(Custom GPT)

1. ChatGPT → Explore GPTs → Create
2. **Instructions** 欄位貼入 `PROMPT.md` 全文
3. **Knowledge** 上傳 `templates/`、`examples/`、`pr_template.md` 內所有檔案
4. 啟用 Code Interpreter(讓使用者可以下載產出檔)
5. 儲存後使用該 Custom GPT

### Gemini(Gem)

1. Gemini Advanced → Gem Manager → New Gem
2. **System instructions** 貼 `PROMPT.md`
3. 上傳 templates / examples / pr_template.md 為知識檔
4. 儲存後使用該 Gem

### 任何 LLM(快速試用)

直接在對話開頭貼 `PROMPT.md` 全文 + 一個最相近的 example,即可開始。

---

## 對方使用前的準備清單

開始對話前先備齊這 7 項,過程會順很多:

1. **proj_folder** — `proj_city_dashboard` 或 `proj_new_taipei_city_dashboard`
2. **table_name**(=dag_folder=dag_id) — snake_case;新北市資料加 `_ntpe` 後綴
3. **start_date** + **schedule_interval** + **load_behavior**(append / replace / current+history)
4. **來源類型** + URL/RID + 是否需 auth
5. **資料格式** + **資料樣本**(貼 1~5 筆原始 response / CSV 前幾行 / Excel head)
6. **col_map**:`{col_name: pg_type}` 字典(必含 `data_time`)
7. **Transform 處理方法**:rename mapping、時間轉換、geometry 處理、過濾、衍生欄位

---

## Branch 命名規則(每隊一支)

每個得獎團隊使用**一支**子分支,所有該隊負責的 DAG 都累積在同一支分支上(每支 DAG 一個 commit),最後該隊推一個 PR 到 `feature/award-dag-integration`。

| 得獎名次 | Branch 命名 | 範例 |
| --- | --- | --- |
| 第 1 名 | `feature/team-no1-<teamname>` | `feature/team-no1-smartcity` |
| 第 2 名 | `feature/team-no2-<teamname>` | `feature/team-no2-transportation` |
| 第 3 名 | `feature/team-no3-<teamname>` | `feature/team-no3-environment` |
| 佳作(多隊)| `feature/team-merit01-<teamname>` ... `feature/team-meritNN-<teamname>` | `feature/team-merit01-publicworks`、`feature/team-merit02-tourism` |

**`<teamname>` 規則**:lowercase + hyphen,英文意譯或縮寫,例:`smart-city`、`transportation`、`public-works`、`open-data`。長度 ≤ 20 字元。

> 維護者會發布一份「得獎名次 ↔ teamname 對照表」,team 成員照表用,不要自行命名。

---

## Team 標準工作流程(2026 雙北儀表板 DAG 整併)

以下範例假設你是「第 2 名 transportation 組」,負責 3 支 DAG:

```bash
# 0a. 切到本次整併作業的 toolkit 分支
git fetch origin
git checkout feature/award-dag-integration
git pull origin feature/award-dag-integration

# 0b. 開出你隊的子分支(每隊只開一次,之後一直在同一分支累積)
git checkout -b feature/team-no2-transportation

# 0c. (建議,不強制)起本機 Airflow + Postgres
#     本流程不需要起服務也能完成驗證(改用 test 腳本驗 source URL),
#     但你想實跑看看 DAG parse 沒問題仍可起來。LLM 會在 Step 0 提醒你。
cd Taipei-City-Dashboard-DE/docker/develop
docker compose -f docker-compose.local.yaml up -d 2>/dev/null || true
cd <回專案根>

# === 開始整併第 1 支 DAG ===
# 3a. 用任何 LLM + dag-toolkit/PROMPT.md 產出 4 個檔
#     LLM 會先做環境前置檢查(Step 0,軟性提醒),然後解析資料源、提案、確認後產出
#     4 個檔:__init__.py / <table>.py / job_config.json / test_<table>.py
#     存到 Taipei-City-Dashboard-DE/dags/<proj_folder>/<table_name>/

# 3b. 本機驗證 — 階段 A:純 Python validator
python Taipei-City-Dashboard-DE/dag-toolkit/scripts/validate_dag.py \
    Taipei-City-Dashboard-DE/dags/<proj_folder>/<table_name>
# 必須 Result: PASS 才能進下一步

# 3c. 本機驗證 — 階段 B:跑 test_<table>.py 確認資料源 URL 可達
cd Taipei-City-Dashboard-DE/dags/<proj_folder>/<table_name>
python test_<table_name>.py
# 必須出現 "All tests passed" 才能 commit
cd <回專案根>

# 3d. 該支 DAG commit
git add Taipei-City-Dashboard-DE/dags/<proj_folder>/<table_name>/
git commit -m "feat(<proj_folder>): 新增 DAG <table_name> — <name_cn>"

# === 重複 3a~3d 整完該隊全部 DAG(每支 DAG 一個 commit)===

# 4. 全部整完才推遠端
git push -u origin feature/team-no2-transportation

# 5. 在 GitHub 開一個 PR(包含該隊全部 commit)
#    PR target: feature/team-no2-transportation → feature/award-dag-integration
#    PR description 套用 toolkit 內 pr_template.md(每支 DAG 各貼 validator + test 輸出)
```

**最終 sit 同步**:所有得獎隊伍的 PR 都進 `feature/award-dag-integration` 後,由維護者人工 merge / 同步至 `sit`,team 成員不直接 PR 到 `sit`。

---

## 維護者:一次掃完所有 team 提交的 source URL test

整併期間維護者收到每一個 team 的 PR,可以用 `scan_all_tests.py` 一次跑完該分支全部 DAG 的 source URL 測試,匯總結果:

```bash
# 在 feature/award-dag-integration 分支,merge 完幾個 team 的 PR 之後
python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py
# 預設掃 Taipei-City-Dashboard-DE/dags/ 下全部 test_*.py(同層需有 job_config.json)
```

只掃單一 proj 或單一 DAG:

```bash
python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py \
    Taipei-City-Dashboard-DE/dags/proj_city_dashboard

python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py \
    Taipei-City-Dashboard-DE/dags/proj_city_dashboard/<table_name>
```

輸出範例:

```
掃描 Taipei-City-Dashboard-DE/dags
找到 18 支測試

  RUN  proj_city_dashboard/food_hygiene_grading/test_food_hygiene_grading.py ... ✅ PASS  (1.2s)
  RUN  proj_city_dashboard/aed_locations_geo/test_aed_locations_geo.py ... ❌ FAIL  (3.4s)
  ...

============================================================
總結: PASS 16 / FAIL 2 / 總 18

=== 失敗詳情 ===
--- proj_city_dashboard/aed_locations_geo/... ---
  ❌ FAIL: HTTPSConnectionPool... (URL 已失效)
```

退出碼 0=全過,1=有 FAIL,2=路徑錯。可掛 CI/排程使用。

---

## 維護(限本次整併作業期間)

- 規則需調整時:維護者直接 push 至 `feature/award-dag-integration`,team 成員 `git pull` 即生效;若已開子分支則需 `git rebase feature/award-dag-integration`
- 新增資料源 helper → 在 `Taipei-City-Dashboard-DE/dags/utils/extract_stage.py` 加 → 同步更新 `PROMPT.md` 中的 helper 對照表
- 整併作業完成後,本分支的後續演進(若有)由維護者決定是否獨立保留或重構成永久工具
