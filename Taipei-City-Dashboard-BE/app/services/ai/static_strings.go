package ai

// StaticUITranslations contains the master list of fixed UI strings for the dashboard.
// These are keys used by the frontend and their original Traditional Chinese values.
var StaticUITranslations = map[string]string{
	// Navbar & General
	"nav.dashboard": "儀表板",
	"nav.map":       "地圖瀏覽",
	"nav.analysis":  "數據分析",
	"nav.search":    "搜尋",
	"label.language": "語系 / Language",

	// UI Titles
	"title.component_platform": "組件瀏覽平台",
	"title.dashboard_overview": "儀表板總覽",
	"title.map_comparison":     "地圖交叉比對",

	// Sidebar Categories
	"taipei": "臺北市",
	"metrotaipei": "雙北",
	"sidebar.filter_map": "篩選地圖",
	"sidebar.spatial_data": "空間資料",
	"sidebar.personal_dashboards": "私人儀表板",
	"sidebar.personal":           "我的儀表板",
	"sidebar.favorites":          "我的收藏",
	"sidebar.public":             "公共儀表板",
	"sidebar.taipei":             "臺北儀表板",
	"sidebar.metrotaipei":        "雙北儀表板",
	"sidebar.metro":              "臺北捷運",

	// Sidebar Shorts/Labels
	"sidebar.personal_short":      "私人",
	"sidebar.fav_short":           "最愛",
	"sidebar.public_short":        "公共",
	"sidebar.taipei_short":        "臺北",
	"sidebar.metrotaipei_short":   "雙北",
	"sidebar.favorite_components": "收藏組件",
	"label.no_personal_dashboards": "尚無個人儀表板",
	"label.none":                  "尚無",
	"sidebar.recent":              "最近瀏覽",
	"sidebar.settings":            "系統設定",
	"sidebar.logout":              "登出",

	// Buttons
	"btn.add":        "新增",
	"btn.save":       "儲存",
	"btn.cancel":     "取消",
	"btn.edit":       "編輯",
	"btn.delete":     "刪除",
	"btn.confirm":    "確認",
	"btn.dark_mode":  "切換深色模式",
	"btn.light_mode": "切換淺色模式",

	// Common Labels
	"label.loading": "讀取中...",
	"label.no_data": "暫無資料",
	"label.error":   "發生錯誤",
	"label.success": "操作成功",
	"label.tech_doc": "技術文件",
	"label.contributors": "專案貢獻者",
	"label.user_settings": "用戶設定",
	"label.admin_panel": "管理員後臺",
	"label.back_to_dashboard": "返回儀表板",
	"label.login": "登入",

	"recommend.title":           "今日推薦",
	"recommend.toggle_expand":  "展開今日推薦",
	"recommend.toggle_collapse": "收合今日推薦",
}
