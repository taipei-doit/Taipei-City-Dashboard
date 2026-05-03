## Commits

本專案沒有硬性規定 commit message 應該如何撰寫，請遵循一般常理(best practice)即可。然而，我們有要求所有的 commit 必須被簽名驗證(signed and verified)。簽名過的 commits 在 GitHub 上會有一個小的已驗證(verified)圖示顯示在 commit message 旁邊。如果您對如何簽名 commit 不熟悉，請參考 GitHub 的 [這個指南](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits)。

## 在開啟 pull request 之前

在開啟 pull request 之前，請確保以下事項屬實：

**_looks_one_** 已跑過程式檢查器（gopls）並已解決所有問題

**_looks_two_** 程式已經過充分測試，並且沒有在開發途中引入錯誤

**_looks_3_** pull request 將完全解決該 issue(s)

**_looks_4_** pull request 僅解決該 issue(s)，沒有進行其他修改

> **t01**
> 上述準則的英文版本：
>
> **_looks_one_** The code linter has been run (`npm run lint`) and issues have all been resolved
>
> **_looks_two_** The code has been thoroughly tested and no visible bugs have been introduced
>
> **_looks_3_** The pull request will completely resolve the issue(s) mentioned
>
> **_looks_4_** The pull request only resolves the issue(s) mentioned and nothing more

## 提交和後續審查

當您準備好時，請開立一個 pull request 並填寫 pull request 模板。如果您希望被歸屬於這個專案，也請記得在模板中填寫一些個人資料。

我們已設定多個 GitHub actions 來自動檢查您的 pull request。如果有任何檢查未通過，請解決。當所有檢查都通過後，我們團隊的成員將審查您的程式。

> **t02**
> 由於本專案也包含前端程式碼，我們的 GitHub Actions 也會檢查前端程式碼。如果您只對後端做出貢獻，但前端相關測試失敗，請先檢查您的 pull request 是否修改了任何前端程式碼。如果沒有，請標記程式庫管理員 ([@igorho2000](https://github.com/igorho2000)) 解決。

如果 pull request 嚴重違反了本協作指南中的任何準則，則可能會立即被拒絕。

如果只有輕微問題，我們將在 pull request 的評論中留言需要修改的項目。請定期檢查您的 pull request 並完成任何所需的修改。當所有問題都得到解決後，pull request 將合併到官方 repository 中。
