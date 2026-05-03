## 用戶管理

用戶在 `/admin/user` 頁面中陳列和管理。

[`GET` `/api/v1/user`](/back-end/user-apis) 回傳所有用戶。

[`POST` `/api/v1/user/`](/back-end/user-apis) 建立一個用戶。

[`PATCH` `/api/v1/user/:id`](/back-end/user-apis) 修改一個用戶。

## 儀表板管理

公開儀表板在 `/admin/dashboard` 頁面中陳列和管理。個人儀表板的 Index 是自動生成的，但管理員可以指定公開儀表板的 Index。

[`GET` `/api/v1/dashboard`](/back-end/dashboard-apis) 回傳所有公開儀表板。

[`GET` `/api/v1/dashboard/check-index/:index-to-check`](/back-end/dashboard-apis) 檢查一個 Index 是否可用。

[`POST` `/api/v1/dashboard/public/:city`](/back-end/dashboard-apis) 建立一個公開儀表板。

[`PATCH` `/api/v1/dashboard/:index`](/back-end/dashboard-apis) 修改一個公開儀表板。

[`DEL` `/api/v1/dashboard/:index`](/back-end/dashboard-apis) 刪除一個公開儀表板。

## 組件管理

組件在 `/admin/component` 頁面中陳列和管理。目前，建立和刪除組件功能仍在開發中，因此現在組件仍然需要在資料庫中手動建立和刪除。

[`GET` `/api/v1/component`](/back-end/component-config-apis) 回傳所有組件。

[`PATCH` `/api/v1/component/:id?city=`](/back-end/component-config-apis) 修改一個組件。

[`PATCH` `/api/v1/component/:id?city=/chart`](/back-end/component-config-apis) 修改一個組件的圖表設定。

[`PATCH` `/api/v1/component/:id?city=/map`](/back-end/component-config-apis) 修改一個組件的地圖設定。

## 問題管理

用戶回報的問題在 `/admin/issue` 頁面中陳列和管理。

[`GET` `/api/v1/issue`](/back-end/issue-apis) 回傳所有問題。

[`PATCH` `/api/v1/issue/:id`](/back-end/issue-apis) 修改一個問題。

## 貢獻者管理

貢獻者在 `/admin/contributor` 頁面中陳列和管理。

[`GET` `/api/v1/contributor`](/back-end/contributor-apis) 回傳所有貢獻者。

[`POST` `/api/v1/contributor`](/back-end/contributor-apis) 建立一個貢獻者。

[`PATCH` `/api/v1/contributor/:id`](/back-end/contributor-apis) 修改一個貢獻者。

[`DEL` `/api/v1/contributor/:id`](/back-end/contributor-apis) 刪除一個貢獻者。
