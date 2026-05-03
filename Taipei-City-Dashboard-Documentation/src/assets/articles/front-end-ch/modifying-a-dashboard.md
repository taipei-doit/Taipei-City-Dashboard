> **i01**
> 本文章中的所有函式（標題）都位於 `contentStore` 中。

## createDashboard（新增儀表板）

[`POST` `/api/v1/dashboard`](/back-end/dashboard-apis)

展開側邊欄並點擊藍色的「新增」按鈕。這將打開一個彈跳視窗，您可以輸入新的儀表板名稱、圖示和組件。點擊藍色按鈕以確認新增。

## editCurrentDashboard（儀表板設定）

[`PATCH` `/api/v1/dashboard/:index`](/back-end/dashboard-apis)

找到設定列並點擊新增組件圖示旁邊的齒輪圖示 **_settings_**。這將打開一個彈跳視窗以進行儀表板設定。

## deleteCurrentDashboard（刪除儀表板）

[`DEL` `/api/v1/dashboard/:index`](/back-end/dashboard-apis)

在儀表板設定中，勾選選取框以表示您希望刪除當前儀表板，視窗中將出現一個紅色的刪除按鈕，點擊後以刪除儀表板。

## deleteComponent（刪除組件）

[`PATCH` `/api/v1/dashboard/:index`](/back-end/dashboard-apis)

在儀表板頁面(/dashboard)中，每個組件的右上角有一個刪除圖示 **_delete_**。點擊該圖示將從當前儀表板中刪除該組件。

## favoriteComponent / unfavoriteComponent（收藏或取消收藏組件）

[`PATCH` `/api/v1/dashboard/:favorite-dashboard-index`](/back-end/dashboard-apis)

在儀表板頁面(/dashboard)中，每個組件的右上角有一個愛心圖示 **_favorite_**。如果圖示是灰色的，點擊它會將該組件加入收藏。相反，如果圖示是粉紅色的，點擊它將使該組件從收藏儀表板中移除。
