<script setup>
import { onMounted } from "vue";
import { useContentStore } from "../store/contentStore";
import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";

const contentStore = useContentStore();

const CHART_BASE = "src/dashboardComponent/components";

// ── 為每個圖表手調的假資料（盡量貼近真實案例的形狀） ───────────────────────────
function buildMockConfig(entry) {
	return {
		id: `catalog-${entry.en}`,
		index: `catalog_${entry.en}`,
		city: entry.activeCity || "taipei",
		name: `${entry.zh} ｜ ${entry.en}`,
		source: "示範資料",
		time_from: "demo",
		time_to: null,
		update_freq: null,
		update_freq_unit: null,
		chart_config: entry.config,
		chart_data: entry.chart_data,
		map_config: [null],
		short_desc: entry.desc,
		long_desc: entry.desc,
		use_case: "",
		links: [],
		contributors: [],
	};
}

const chartCatalog = [
	{
		en: "DonutChart",
		zh: "圓餅圖",
		path: `${CHART_BASE}/DonutChart.vue`,
		dataTypes: ["two_d"],
		desc: "圓環比例圖，少量分類在整體中的占比。",
		config: {
			types: ["DonutChart"],
			color: ["#67baca", "#5a8965", "#477653", "#2e5c4a", "#1a4034"],
			unit: "件",
		},
		chart_data: [{ name: "", data: [
			{ x: "公劃地區內事業", y: 801 },
			{ x: "公告自劃單元", y: 584 },
			{ x: "核准自劃單元", y: 429 },
			{ x: "公劃更新地區", y: 293 },
			{ x: "都市計畫劃定更新地區", y: 65 },
		] }],
	},
	{
		en: "BarChart",
		zh: "橫向長條圖",
		path: `${CHART_BASE}/BarChart.vue`,
		dataTypes: ["two_d"],
		desc: "水平排列的長條圖；類別名稱較長時優先選用。",
		config: {
			types: ["BarChart"],
			color: ["#5a9cf8", "#5fcf80", "#f6c344", "#a37cf6", "#ec7cb1", "#67baca"],
			unit: "家",
		},
		chart_data: [{ name: "", data: [
			{ x: "板橋區", y: 78 },
			{ x: "新莊區", y: 62 },
			{ x: "信義區", y: 51 },
			{ x: "大安區", y: 47 },
			{ x: "中山區", y: 44 },
		] }],
	},
	{
		en: "ColumnChart",
		zh: "縱向長條圖",
		path: `${CHART_BASE}/ColumnChart.vue`,
		dataTypes: ["two_d", "three_d"],
		desc: "垂直長條圖；可比較多個 series 在同一類別下的數值。",
		config: {
			types: ["ColumnChart"],
			color: ["#4B96FA", "#F1C40F"],
			categories: ["2019", "2020", "2021", "2022", "2023"],
			unit: "人",
		},
		chart_data: [
			{ name: "男生", data: [3129, 3056, 3610, 5001, 5440] },
			{ name: "女生", data: [17000, 16433, 17144, 17506, 17812] },
		],
	},
	{
		en: "BarPercentChart",
		zh: "長條圖（%）",
		path: `${CHART_BASE}/BarPercentChart.vue`,
		dataTypes: ["three_d", "percent"],
		desc: "百分比堆疊長條圖；呈現每個類別內部組成比例。",
		config: {
			types: ["BarPercentChart"],
			color: ["#5fcf80", "#5a9cf8", "#f6c344"],
			categories: ["臺北", "新北", "桃園"],
			unit: "%",
		},
		chart_data: [
			{ name: "資源垃圾", data: [42, 38, 35] },
			{ name: "一般垃圾", data: [50, 55, 58] },
			{ name: "廚餘", data: [8, 7, 7] },
		],
	},
	{
		en: "TreemapChart",
		zh: "矩形圖",
		path: `${CHART_BASE}/TreemapChart.vue`,
		dataTypes: ["two_d"],
		desc: "以矩形面積表達數值大小；適合多分類的層級資料。",
		config: {
			types: ["TreemapChart"],
			color: ["#7fb069", "#a8c686", "#dde7c7", "#e9b384", "#f4978e"],
			unit: "公頃",
		},
		chart_data: [{ name: "", data: [
			{ x: "保護區", y: 68.95 },
			{ x: "其他", y: 54.98 },
			{ x: "住宅用地", y: 38.33 },
			{ x: "水域", y: 20.29 },
			{ x: "綠地", y: 12.99 },
			{ x: "文教用地", y: 11.64 },
			{ x: "商業用地", y: 9.29 },
			{ x: "交通用地", y: 7.97 },
		] }],
	},
	{
		en: "DistrictChart",
		zh: "行政區圖",
		path: `${CHART_BASE}/DistrictChart.vue`,
		dataTypes: ["two_d", "three_d"],
		desc: "雙北行政區輿圖；依數值熱度填色（多深、少淺）。",
		activeCity: "taipei",
		config: {
			types: ["DistrictChart"],
			color: ["#5a9cf8"],
			unit: "間",
		},
		chart_data: [{ name: "", data: [
			{ x: "北投區", y: 16394 },
			{ x: "士林區", y: 19788 },
			{ x: "內湖區", y: 15444 },
			{ x: "南港區", y: 8440 },
			{ x: "松山區", y: 7721 },
			{ x: "信義區", y: 12989 },
			{ x: "中山區", y: 13203 },
			{ x: "大同區", y: 6090 },
			{ x: "中正區", y: 8410 },
			{ x: "萬華區", y: 8025 },
			{ x: "大安區", y: 13017 },
			{ x: "文山區", y: 11553 },
		] }],
	},
	{
		en: "TimelineSeparateChart",
		zh: "折線圖（比較）",
		path: `${CHART_BASE}/TimelineSeparateChart.vue`,
		dataTypes: ["time"],
		desc: "多條時間序列折線各自呈現；比較不同指標走勢。",
		config: {
			types: ["TimelineSeparateChart"],
			color: ["#E06666", "#00A9E0"],
			unit: "件",
		},
		chart_data: [
			{ name: "發生件數", data: [
				{ y: 4623, x: "2024-05-01T00:00:00+08:00" },
				{ y: 3685, x: "2024-04-01T00:00:00+08:00" },
				{ y: 3527, x: "2024-03-01T00:00:00+08:00" },
				{ y: 3924, x: "2024-02-01T00:00:00+08:00" },
				{ y: 4409, x: "2024-01-01T00:00:00+08:00" },
			] },
			{ name: "破獲件數", data: [
				{ y: 3701, x: "2024-05-01T00:00:00+08:00" },
				{ y: 3012, x: "2024-04-01T00:00:00+08:00" },
				{ y: 2854, x: "2024-03-01T00:00:00+08:00" },
				{ y: 3120, x: "2024-02-01T00:00:00+08:00" },
				{ y: 3502, x: "2024-01-01T00:00:00+08:00" },
			] },
		],
	},
	{
		en: "TimelineStackedChart",
		zh: "折線圖（堆疊）",
		path: `${CHART_BASE}/TimelineStackedChart.vue`,
		dataTypes: ["time"],
		desc: "多條時間序列以堆疊方式呈現累積總量。",
		config: {
			types: ["TimelineStackedChart"],
			color: ["#5fcf80", "#5a9cf8", "#f6c344"],
			unit: "公噸",
		},
		chart_data: [
			{ name: "資源回收", data: [
				{ y: 412, x: "2023-01-01T00:00:00+08:00" },
				{ y: 425, x: "2023-04-01T00:00:00+08:00" },
				{ y: 438, x: "2023-07-01T00:00:00+08:00" },
				{ y: 445, x: "2023-10-01T00:00:00+08:00" },
				{ y: 460, x: "2024-01-01T00:00:00+08:00" },
			] },
			{ name: "一般垃圾", data: [
				{ y: 698, x: "2023-01-01T00:00:00+08:00" },
				{ y: 685, x: "2023-04-01T00:00:00+08:00" },
				{ y: 672, x: "2023-07-01T00:00:00+08:00" },
				{ y: 658, x: "2023-10-01T00:00:00+08:00" },
				{ y: 642, x: "2024-01-01T00:00:00+08:00" },
			] },
			{ name: "廚餘", data: [
				{ y: 64, x: "2023-01-01T00:00:00+08:00" },
				{ y: 65, x: "2023-04-01T00:00:00+08:00" },
				{ y: 63, x: "2023-07-01T00:00:00+08:00" },
				{ y: 60, x: "2023-10-01T00:00:00+08:00" },
				{ y: 58, x: "2024-01-01T00:00:00+08:00" },
			] },
		],
	},
	{
		en: "ColumnLineChart",
		zh: "長條折線圖",
		path: `${CHART_BASE}/ColumnLineChart.vue`,
		dataTypes: ["time"],
		desc: "長條 + 折線雙軸組合；常用於量＋率或主＋副指標。",
		config: {
			types: ["ColumnLineChart"],
			color: ["#5a9cf8", "#f6c344"],
			unit: "件",
		},
		chart_data: [
			{ name: "申辦件數", data: [
				{ y: 280, x: "2024-01-01T00:00:00+08:00" },
				{ y: 312, x: "2024-02-01T00:00:00+08:00" },
				{ y: 295, x: "2024-03-01T00:00:00+08:00" },
				{ y: 340, x: "2024-04-01T00:00:00+08:00" },
				{ y: 388, x: "2024-05-01T00:00:00+08:00" },
			] },
			{ name: "結案率", data: [
				{ y: 92, x: "2024-01-01T00:00:00+08:00" },
				{ y: 88, x: "2024-02-01T00:00:00+08:00" },
				{ y: 90, x: "2024-03-01T00:00:00+08:00" },
				{ y: 94, x: "2024-04-01T00:00:00+08:00" },
				{ y: 91, x: "2024-05-01T00:00:00+08:00" },
			] },
		],
	},
	{
		en: "GuageChart",
		zh: "量表圖",
		path: `${CHART_BASE}/GuageChart.vue`,
		dataTypes: ["percent"],
		desc: "弧形量表；單一指標相對於目標的百分比。",
		config: {
			types: ["GuageChart"],
			color: ["#ff9800"],
			categories: ["啟動抽水站"],
			unit: "站",
		},
		chart_data: [
			{ name: "啟動中", data: [12] },
			{ name: "未啟動", data: [64] },
		],
	},
	{
		en: "RadarChart",
		zh: "雷達圖",
		path: `${CHART_BASE}/RadarChart.vue`,
		dataTypes: ["two_d", "three_d"],
		desc: "多軸雷達；多個面向的綜合評分輪廓。",
		config: {
			types: ["RadarChart"],
			color: ["#5fcf80", "#5a9cf8"],
			categories: ["交通", "綠地", "醫療", "教育", "治安", "經濟"],
			unit: "分",
		},
		chart_data: [
			{ name: "臺北市", data: [85, 70, 90, 88, 80, 92] },
			{ name: "新北市", data: [78, 82, 80, 82, 84, 86] },
		],
	},
	{
		en: "HeatmapChart",
		zh: "熱力圖",
		path: `${CHART_BASE}/HeatmapChart.vue`,
		dataTypes: ["three_d"],
		desc: "二維格子熱力圖；以顏色深淺呈現數值密度。",
		config: {
			types: ["HeatmapChart"],
			color: ["#5fcf80", "#a8c686", "#dde7c7"],
			categories: ["週一", "週二", "週三", "週四", "週五", "週六", "週日"],
			unit: "次",
		},
		chart_data: [
			{ name: "06-09 時", data: [42, 45, 41, 47, 50, 18, 12] },
			{ name: "09-12 時", data: [33, 36, 35, 38, 41, 25, 22] },
			{ name: "12-15 時", data: [28, 30, 32, 34, 38, 40, 38] },
			{ name: "15-18 時", data: [55, 58, 56, 60, 64, 48, 42] },
			{ name: "18-21 時", data: [62, 65, 63, 67, 70, 55, 50] },
		],
	},
	{
		en: "PolarAreaChart",
		zh: "極座標圖",
		path: `${CHART_BASE}/PolarAreaChart.vue`,
		dataTypes: ["two_d", "three_d"],
		desc: "圓形扇區圖；扇形角度與半徑同時表達分類與數值。",
		config: {
			types: ["PolarAreaChart"],
			color: ["#FFEB9A", "#F1C40F", "#AC8B08"],
			categories: ["北投", "士林", "內湖", "南港", "松山", "信義", "中山", "大同", "中正", "萬華", "大安", "文山"],
			unit: "處",
		},
		chart_data: [
			{ name: "尿布台", data: [32, 36, 19, 27, 31, 38, 23, 27, 58, 25, 31, 39] },
			{ name: "置物空間", data: [31, 34, 18, 26, 31, 34, 20, 24, 61, 26, 28, 42] },
			{ name: "嬰兒車停放空間", data: [22, 29, 13, 22, 26, 24, 13, 21, 49, 21, 25, 29] },
		],
	},
	{
		en: "BarChartWithGoal",
		zh: "長條圖（目標）",
		path: `${CHART_BASE}/BarChartWithGoal.vue`,
		dataTypes: ["percent"],
		desc: "長條圖搭配目標線；呈現實際值與達標水準。",
		config: {
			types: ["BarChartWithGoal"],
			color: ["#81bcf5", "#ed5a5a"],
			categories: ["正常水位站點"],
			unit: "站",
		},
		chart_data: [
			{ name: "水位正常", data: [128] },
			{ name: "警戒水位站", data: [7] },
		],
	},
	{
		en: "IconPercentChart",
		zh: "圖示比例圖",
		path: `${CHART_BASE}/IconPercentChart.vue`,
		dataTypes: ["percent"],
		desc: "用圖示堆疊代表百分比；重視視覺直觀的場景適用。",
		config: {
			types: ["IconPercentChart"],
			color: ["#4B96FA", "#F1C40F"],
			categories: ["2020", "2021", "2022", "2023", "2024"],
			unit: "人",
		},
		chart_data: [
			{ name: "男生", icon: "man", data: [3056, 3610, 5001, 5440, 5810] },
			{ name: "女生", icon: "woman", data: [16433, 17144, 17506, 17812, 18120] },
		],
	},
	{
		en: "IndicatorChart",
		zh: "指標圖",
		path: `${CHART_BASE}/IndicatorChart.vue`,
		dataTypes: ["three_d"],
		desc: "單一大數字＋次要對比指標；KPI 卡風格。",
		config: {
			types: ["IndicatorChart"],
			color: ["#008000", "#F0C807", "#FF0000"],
			categories: ["陽明", "大同", "松山", "古亭", "萬華", "中山", "士林"],
			unit: "μg/m³",
		},
		chart_data: [
			{ name: "良好", data: [35, 0, 0, 45, 0, 0, 48] },
			{ name: "普通", data: [0, 66, 73, 0, 73, 61, 0] },
			{ name: "不良", data: [0, 0, 0, 0, 0, 0, 0] },
		],
	},
	{
		en: "MapLegend",
		zh: "地圖圖例",
		path: `${CHART_BASE}/MapLegend.vue`,
		dataTypes: ["map_legend"],
		desc: "地圖搭配的色彩 / 圖示圖例；與 mapStore 的 layer 對齊。",
		config: {
			types: ["MapLegend"],
			color: ["#5fcf80", "#5a9cf8"],
			unit: "家",
		},
		chart_data: [
			{ name: "臺北市", type: "circle", icon: "circle", value: 479 },
			{ name: "新北市", type: "circle", icon: "circle", value: 749 },
		],
	},
	{
		en: "TextUnitChart",
		zh: "文字單位圖",
		path: `${CHART_BASE}/TextUnitChart.vue`,
		dataTypes: ["three_d"],
		desc: "純文字＋單位卡；用於關鍵數字呈現（多卡並列）。",
		config: {
			types: ["TextUnitChart"],
			color: ["#888787", "#5fcf80", "#888787"],
			unit: "家",
		},
		chart_data: [
			{ name: "臺北市", data: [479], icon: "家" },
			{ name: "新北市", data: [749], icon: "家" },
		],
	},
	{
		en: "MetroChart",
		zh: "捷運行駛圖",
		path: `${CHART_BASE}/MetroChart.vue`,
		dataTypes: ["two_d"],
		desc: "臺北捷運路線示意圖；資料須用 A/D 方向 + 站碼（如 AO15、DO03），第一筆 station 字首決定要 render 哪條線。",
		config: {
			types: ["MetroChart"],
			color: ["#f8b133"],
			unit: "人",
		},
		chart_data: [{ name: "", data: [
			{ x: "AO15", y: 222222 },
			{ x: "AO05", y: 111121 },
			{ x: "AO25", y: 112111 },
			{ x: "AO10", y: 111112 },
			{ x: "AO02", y: 123411 },
			{ x: "DO15", y: 211111 },
			{ x: "DO05", y: 121111 },
		] }],
	},
	{
		en: "SpeedometerChart",
		zh: "儀表板圖（暫不使用）",
		path: `${CHART_BASE}/SpeedometerChart.vue`,
		dataTypes: [],
		desc: "在 utilities/chartTypes.ts 標註「暫時不用」，無預覽。",
		config: null,
		chart_data: null,
	},
];

const wrapperCatalog = [
	{
		zh: "儀表板組件殼",
		en: "DashboardComponent",
		path: "src/dashboardComponent/DashboardComponent.vue",
		desc: "所有元件的外殼：標題、城市 tag、圖表切換、toggle、footer 一條龍。透過 chart_config.types 決定要 render 哪些圖表元件。",
	},
	{
		zh: "標籤膠囊",
		en: "ComponentTag",
		path: "src/dashboardComponent/components/ComponentTag.vue",
		desc: "城市色標籤、icon＋文字 chip。outline / fill / small / city-tag-item 四種模式。",
	},
	{
		zh: "Tag Tooltip",
		en: "TagTooltip",
		path: "src/dashboardComponent/components/TagTooltip.vue",
		desc: "header tag 的 hover 提示，列出篩選地圖／空間資料／歷史資料三類能力。",
	},
	{
		zh: "城市管理工具",
		en: "CityManager",
		path: "src/dashboardComponent/utilities/cityManager.ts",
		desc: "全站「臺北 / 新北 / 雙北 / 桃園」設定中心，提供 select/tag list 與啟用狀態。",
	},
];

const dialogCatalog = [
	{
		zh: "更多資訊",
		en: "MoreInfo",
		path: "src/components/dialogs/MoreInfo.vue",
		desc: "點 footer「組件資訊」彈出的 dialog；支援 city_tag_override。",
	},
	{
		zh: "回報問題",
		en: "ReportIssue",
		path: "src/components/dialogs/ReportIssue.vue",
		desc: "需登入；提交資料正確性／樣式異常等回報。",
	},
	{
		zh: "資料下載",
		en: "DownloadData",
		path: "src/components/dialogs/DownloadData.vue",
		desc: "MoreInfo 內部叫起，下載原始資料。",
	},
	{
		zh: "內嵌分享",
		en: "EmbedComponent",
		path: "src/components/dialogs/EmbedComponent.vue",
		desc: "產生 iframe embed 連結。",
	},
	{
		zh: "Dialog 容器",
		en: "DialogContainer",
		path: "src/components/dialogs/DialogContainer.vue",
		desc: "所有 dialog 的共用外殼，配 dialogStore 的 show/hide 狀態。",
	},
];

onMounted(() => {
	contentStore.currentDashboard.name = "元件目錄（內部參考）";
	contentStore.currentDashboard.icon = "view_module";
});
</script>

<template>
  <div class="componentscatalog">
    <header class="componentscatalog-header">
      <h1>元件目錄 ｜ Components Catalog</h1>
      <p>
        提供 FE 開發夥伴在排組件時直接挑選用的速查表。圖表名稱對應
        <code>src/dashboardComponent/utilities/chartTypes.ts</code>
        ，資料形式分類取自
        <code>src/assets/configs/apexcharts/chartTypes.js</code>
        的 <code>chartsPerDataType</code>。每張卡使用假資料即時渲染，可直接看到實際視覺效果。
      </p>
    </header>

    <section class="componentscatalog-section">
      <h2>圖表元件 ｜ Chart Components</h2>
      <p class="componentscatalog-section-hint">
        在 <code>chart_config.types</code> 填入英文名即可使用；多個英文名會在組件右上產生切換按鈕。
      </p>
      <div class="componentscatalog-grid">
        <div
          v-for="item in chartCatalog"
          :key="item.en"
          class="componentscatalog-chart-card"
        >
          <DashboardComponent
            v-if="item.config && item.chart_data"
            :config="buildMockConfig(item)"
            mode="default"
            :info-btn="false"
            :footer="false"
            :active-city="item.activeCity || 'taipei'"
            :city-tag="[]"
          />
          <div
            v-else
            class="componentscatalog-chart-card-placeholder"
          >
            <span>block</span>
            <p>{{ item.desc }}</p>
          </div>
          <div class="componentscatalog-chart-card-meta">
            <div class="componentscatalog-chart-card-meta-row">
              <span class="componentscatalog-chart-card-meta-en">{{ item.en }}</span>
              <span
                v-for="t in item.dataTypes"
                :key="t"
                class="componentscatalog-chart-card-meta-tag"
              >{{ t }}</span>
            </div>
            <code>{{ item.path }}</code>
          </div>
        </div>
      </div>
    </section>

    <section class="componentscatalog-section">
      <h2>容器與工具 ｜ Wrappers &amp; Utilities</h2>
      <ul class="componentscatalog-list">
        <li
          v-for="item in wrapperCatalog"
          :key="item.en"
        >
          <div>
            <h3>{{ item.zh }}</h3>
            <h4>{{ item.en }}</h4>
          </div>
          <p>{{ item.desc }}</p>
          <code>{{ item.path }}</code>
        </li>
      </ul>
    </section>

    <section class="componentscatalog-section">
      <h2>對話框 ｜ Dialogs</h2>
      <ul class="componentscatalog-list">
        <li
          v-for="item in dialogCatalog"
          :key="item.en"
        >
          <div>
            <h3>{{ item.zh }}</h3>
            <h4>{{ item.en }}</h4>
          </div>
          <p>{{ item.desc }}</p>
          <code>{{ item.path }}</code>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped lang="scss">
.componentscatalog {
	max-height: calc(100vh - 127px);
	max-height: calc(var(--vh) * 100 - 127px);
	margin: var(--font-m) var(--font-m);
	overflow-y: scroll;

	&-header {
		margin-bottom: var(--font-l);

		h1 {
			margin-bottom: var(--font-s);
			color: var(--color-normal-text);
			font-size: var(--font-l);
		}

		p {
			color: var(--color-complement-text);
			font-size: var(--font-s);
			line-height: 1.6;
		}

		code {
			margin: 0 2px;
			padding: 1px 6px;
			border-radius: 3px;
			background-color: var(--color-component-background);
			color: var(--color-highlight);
			font-family: monospace;
			font-size: var(--font-s);
		}
	}

	&-section {
		margin-bottom: calc(var(--font-l) * 1.5);

		h2 {
			margin-bottom: var(--font-s);
			color: var(--color-normal-text);
			font-size: var(--font-m);
		}

		&-hint {
			margin-bottom: var(--font-s);
			color: var(--color-complement-text);
			font-size: var(--font-s);

			code {
				margin: 0 2px;
				padding: 1px 6px;
				border-radius: 3px;
				background-color: var(--color-component-background);
				color: var(--color-highlight);
				font-family: monospace;
				font-size: var(--font-s);
			}
		}
	}

	&-grid {
		display: grid;
		grid-template-columns: 1fr;
		row-gap: var(--font-m);
		column-gap: var(--font-s);

		@media (min-width: 720px) {
			grid-template-columns: 1fr 1fr;
		}

		@media (min-width: 1296px) {
			grid-template-columns: 1fr 1fr 1fr;
		}
	}

	&-chart-card {
		display: flex;
		flex-direction: column;

		&-placeholder {
			height: 330px;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			border: 1px dashed var(--color-border);
			border-radius: 5px;
			background-color: var(--color-component-background);

			span {
				margin-bottom: 8px;
				color: var(--color-complement-text);
				font-family: var(--font-icon);
				font-size: 2rem;
			}

			p {
				color: var(--color-complement-text);
				font-size: var(--font-s);
				text-align: center;
				padding: 0 var(--font-m);
			}
		}

		&-meta {
			padding: 8px 4px 0 4px;

			&-row {
				display: flex;
				flex-wrap: wrap;
				align-items: center;
				gap: 6px;
				margin-bottom: 4px;
			}

			&-en {
				color: var(--color-highlight);
				font-family: monospace;
				font-size: var(--font-s);
			}

			&-tag {
				padding: 1px 6px;
				border-radius: 3px;
				background-color: var(--color-component-background);
				color: var(--color-complement-text);
				font-family: monospace;
				font-size: 11px;
			}

			code {
				display: block;
				color: var(--color-complement-text);
				font-family: monospace;
				font-size: 11px;
				word-break: break-all;
			}
		}
	}

	&-list {
		list-style: none;

		li {
			display: grid;
			grid-template-columns: 200px 1fr;
			column-gap: var(--font-m);
			padding: var(--font-s);
			margin-bottom: 6px;
			border-radius: 5px;
			background-color: var(--color-component-background);

			h3 {
				color: var(--color-normal-text);
				font-size: var(--font-ms);
				font-weight: 500;
			}

			h4 {
				color: var(--color-highlight);
				font-size: var(--font-s);
				font-weight: 400;
				font-family: monospace;
			}

			p {
				grid-column: 2;
				color: var(--color-complement-text);
				font-size: var(--font-s);
				line-height: 1.5;
			}

			code {
				grid-column: 2;
				margin-top: 4px;
				color: var(--color-complement-text);
				font-family: monospace;
				font-size: 11px;
				word-break: break-all;
			}
		}
	}
}
</style>
