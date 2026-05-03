


本專案沒有硬性規定 commit message 應該如何撰寫，請遵循一般常理(best practice)即可。然而，我們有要求所有的 commit 必須被簽名驗證(signed and verified)。簽名過的 commits 在 GitHub 上會有一個小的已驗證(verified)圖示顯示在 commit message 旁邊。如果你對如何簽名 commit 不熟悉，請參考 GitHub 的 [這個指南](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits)。

## 在開啟 pull request 之前

在開啟 pull request 之前，請確保以下事項屬實：

**_looks_one_** 已確認過程式檢查器（Pylint）並解決所有能解決的提示

**_looks_two_** 程式已經過充分測試，並且沒有在開發途中引入錯誤

**_looks_3_** pull request 將完全解決該 issue(s)

**_looks_4_** pull request 僅解決該 issue(s)，沒有進行其他修改


## 提交和後續審查

當你準備好時，請開立一個 pull request 並填寫 pull request 模板。如果你希望被歸屬於這個專案，也請記得在模板中填寫一些個人資料。

我們已設定多個 GitHub actions 來自動檢查你的 pull request。如果有任何檢查未通過，請解決。當所有檢查都通過後，我們團隊的成員將審查你的程式。

如果 pull request 嚴重違反了本協作指南中的任何準則，則可能會立即被拒絕。

如果只有輕微問題，我們將在 pull request 的評論中留言需要修改的項目。請定期檢查你的 pull request 並完成任何所需的修改。當所有問題都得到解決後，pull request 將合併到官方 repository 中。