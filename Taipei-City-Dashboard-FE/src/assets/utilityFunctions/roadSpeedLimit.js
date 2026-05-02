// Taipei open data: roads and sections with speed limits differing from 50 km/h.
const TAIPEI_DEFAULT_SPEED_LIMIT = "50(公里/小時)";

const TAIPEI_ROAD_SPEED_LIMITS = [
	{
		category: "堤外便道",
		segment: "淡水河右岸(民生西路至桂林路)",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "中央分隔路型",
		segment: "市民大道平面道路一段至六段",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "中央分隔路型",
		segment: "市民大道平面道路七段至八段",
		speedLimit: "50(公里/小時)",
	},
	{
		category: "山區道路",
		segment: "含仰德大道、格致路、陽明路一段、湖山路一段、竹子湖路(以上路名統稱陽金公路)",
		speedLimit: "40(公里/小時)",
	},
	{ category: "山區道路", segment: "行義路", speedLimit: "40(公里/小時)" },
	{
		category: "山區道路",
		segment: "泉源路、新民路",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "山區道路",
		segment: "稻香路、公館路",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "山區道路",
		segment: "指南路二段、萬壽路",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "山區道路",
		segment: "萬美街、萬樂街",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "山區道路",
		segment: "萬寧街、萬利街",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "山區道路",
		segment: "臥龍街、和平東路四段",
		speedLimit: "40(公里/小時)",
	},
	{ category: "山區道路", segment: "碧山路", speedLimit: "40(公里/小時)" },
	{
		category: "山區道路",
		segment: "舊莊街二段",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "堤頂大道(快速道路段)",
		speedLimit: "70(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "大業路(大度路至中央北路)",
		speedLimit: "快車道60(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "大度路(立德路至大業路)",
		speedLimit: "快車道70(公里/小時)、慢車道50(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "承德路五、六、七段",
		speedLimit: "60(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "環東大道(高架段)(直線段)",
		speedLimit: "直線段80(公里/小時)、曲線段60(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "水源快速道路(直線段)",
		speedLimit: "直線段60(公里/小時)、曲線段50(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "環河快速道路(高架段)",
		speedLimit: "直線段70(公里/小時)、曲線段50-60(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "新生高架道路(直線段)(南京東路-民族東路)",
		speedLimit: "70(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "基隆路高架道路",
		speedLimit: "60(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "建國高架道路",
		speedLimit: "70(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "市民大道高架道路",
		speedLimit: "80(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "洲美快速道路",
		speedLimit: "80(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "信義快速道路(匝道)",
		speedLimit: "40(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "信義快速道路(北往南方向(往文山)象山隧道與橋樑段)",
		speedLimit: "60(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "信義快速道路(文山隧道)",
		speedLimit: "70(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "信義快速道路(交流道)",
		speedLimit: "60(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "信義快速道路(南往北方向(往信義)文山隧道至橋樑段)",
		speedLimit: "70(公里/小時)",
	},
	{
		category: "速限高於50公里/小時路段",
		segment: "信義快速道路(象山隧道)",
		speedLimit: "50-70(公里/小時)",
	},
];

const SECTION_NUMBER_MAP = {
	一: 1,
	二: 2,
	三: 3,
	四: 4,
	五: 5,
	六: 6,
	七: 7,
	八: 8,
	九: 9,
	十: 10,
};
const NUMBER_TO_SECTION_TEXT = Object.fromEntries(
	Object.entries(SECTION_NUMBER_MAP).map(([text, number]) => [number, text]),
);

function formatSpeedLimitText(speedLimit) {
	return String(speedLimit || "")
		.replace(/\(公里\/小時\)/g, "")
		.replace(/、/g, " / ");
}

function createDefaultSpeedLimit(roadName = "") {
	return {
		speedLimit: TAIPEI_DEFAULT_SPEED_LIMIT,
		speedLimitText: formatSpeedLimitText(TAIPEI_DEFAULT_SPEED_LIMIT),
		roadName,
		segment: "",
		category: "法定速限",
		isDefault: true,
		isMultiple: false,
	};
}

function normalizeDigits(value) {
	return String(value || "")
		.replace(/[０-９]/g, (digit) =>
			String(digit.charCodeAt(0) - 0xff10),
		)
		.replace(/([0-9]+)段/g, (match, section) => {
			const number = Number(section);
			return `${NUMBER_TO_SECTION_TEXT[number] || section}段`;
		});
}

function normalizeRoadText(value) {
	return normalizeDigits(value)
		.replace(/臺/g, "台")
		.replace(/平面道路/g, "")
		.replace(/[()（）【】\s]/g, "")
		.replace(/\[/g, "")
		.replace(/\]/g, "")
		.replace(/[，,]/g, "、");
}

function removeParenthetical(value) {
	let text = String(value || "");
	let previous = "";

	while (text !== previous) {
		previous = text;
		text = text.replace(/[（(][^（）()]*[）)]/g, "");
	}

	return text;
}

function stripAdminArea(value) {
	return String(value || "").replace(/^.*?[縣市].*?[鄉鎮市區]/, "");
}

function getRoadCandidates(segment) {
	const candidates = new Set();
	const source = normalizeDigits(removeParenthetical(segment))
		.replace(/^含/, "")
		.replace(/平面道路/g, "");
	const priorityRoadPattern =
		/含?([^、，,()（）\s]+?(?:快速道路|高架道路))/g;
	const roadPattern =
		/含?([^、，,()（）\s]+?(?:快速道路|高架道路|大道|路|街|橋|便道))/g;
	let match = priorityRoadPattern.exec(source);

	while (match) {
		candidates.add(match[1].replace(/^含/, ""));
		match = priorityRoadPattern.exec(source);
	}

	if (candidates.size) {
		return [...candidates];
	}

	match = roadPattern.exec(source);

	while (match) {
		candidates.add(match[1].replace(/^含/, ""));
		match = roadPattern.exec(source);
	}

	if (!candidates.size && source) {
		candidates.add(source);
	}

	return [...candidates];
}

function getSectionNumber(value) {
	const match = normalizeDigits(value).match(/([一二三四五六七八九十]+)段/);
	if (!match) return null;
	return SECTION_NUMBER_MAP[match[1]] || null;
}

function getRecordSections(segment) {
	const text = normalizeDigits(removeParenthetical(segment))
		.replace(/平面道路/g, "");
	const range = text.match(/([一二三四五六七八九十]+)段至([一二三四五六七八九十]+)段/);
	if (range) {
		const start = SECTION_NUMBER_MAP[range[1]];
		const end = SECTION_NUMBER_MAP[range[2]];
		if (start && end && end >= start) {
			return Array.from(
				{ length: end - start + 1 },
				(_, index) => start + index,
			);
		}
	}

	const list = text.match(/([一二三四五六七八九十](?:、[一二三四五六七八九十])*)段/);
	if (list) {
		return list[1]
			.split("、")
			.map((section) => SECTION_NUMBER_MAP[section])
			.filter(Boolean);
	}

	return [...text.matchAll(/([一二三四五六七八九十]+)段/g)]
		.map((match) => SECTION_NUMBER_MAP[match[1]])
		.filter(Boolean);
}

function getParentheticalDetailScore(segment, normalizedContext) {
	const details = [...String(segment || "").matchAll(/[（(]([^（）()]*)[）)]/g)]
		.map((match) => normalizeRoadText(match[1]))
		.filter(Boolean);

	return details.some((detail) => normalizedContext.includes(detail))
		? 30
		: 0;
}

function doesSectionMatch(segment, context) {
	const recordSections = getRecordSections(segment);
	const currentSection = getSectionNumber(context);

	if (!recordSections.length || !currentSection) return true;
	return recordSections.includes(currentSection);
}

export function extractRoadNameFromAddress(address) {
	const text = normalizeDigits(stripAdminArea(address)).replace(
		/平面道路/g,
		"",
	);
	const priorityMatch = text.match(
		/(.+?(?:快速道路|高架道路)(?:[一二三四五六七八九十]+段)?)/,
	);
	if (priorityMatch?.[1]) return priorityMatch[1];

	const match = text.match(
		/(.+?(?:快速道路|高架道路|大道|路|街|橋|便道)(?:[一二三四五六七八九十]+段)?)/,
	);

	return match?.[1] || "";
}

export function findTaipeiRoadSpeedLimit({ roadName, address }) {
	const resolvedRoadName = roadName || extractRoadNameFromAddress(address);
	const normalizedRoadName = normalizeRoadText(resolvedRoadName);
	const normalizedContext = normalizeRoadText(
		`${resolvedRoadName || ""} ${address || ""}`,
	);

	if (!normalizedRoadName && !normalizedContext) {
		return createDefaultSpeedLimit();
	}

	const scoredMatches = TAIPEI_ROAD_SPEED_LIMITS.map((record) => {
		const normalizedSegment = normalizeRoadText(record.segment);
		const candidates = getRoadCandidates(record.segment)
			.map((candidate) => normalizeRoadText(candidate))
			.filter(Boolean);
		let score = normalizedContext.includes(normalizedSegment) ? 150 : 0;

		candidates.forEach((candidate) => {
			if (candidate === normalizedRoadName) {
				score = Math.max(score, 130);
			} else if (normalizedRoadName.startsWith(candidate)) {
				score = Math.max(score, 115);
			} else if (
				normalizedRoadName &&
				candidate.startsWith(normalizedRoadName)
			) {
				score = Math.max(score, 105);
			} else if (normalizedContext.includes(candidate)) {
				score = Math.max(score, 95);
			}
		});

		if (score > 0 && !doesSectionMatch(record.segment, normalizedContext)) {
			score = 0;
		}

		return {
			...record,
			score: score + getParentheticalDetailScore(
				record.segment,
				normalizedContext,
			),
		};
	}).filter((record) => record.score > 0);

	if (!scoredMatches.length) {
		return createDefaultSpeedLimit(resolvedRoadName);
	}

	const maxScore = Math.max(...scoredMatches.map((record) => record.score));
	const bestMatches = scoredMatches.filter(
		(record) => record.score === maxScore,
	);
	const speedLimits = [...new Set(
		bestMatches.map((record) => record.speedLimit),
	)];

	if (speedLimits.length > 1) {
		return {
			speedLimit: speedLimits.join(" / "),
			speedLimitText: speedLimits.map(formatSpeedLimitText).join(" / "),
			roadName: resolvedRoadName,
			segment: bestMatches.map((record) => record.segment).join("、"),
			category: "依路段",
			isDefault: false,
			isMultiple: true,
		};
	}

	const bestMatch = bestMatches[0];

	return {
		speedLimit: bestMatch.speedLimit,
		speedLimitText: formatSpeedLimitText(bestMatch.speedLimit),
		roadName: resolvedRoadName,
		segment: bestMatch.segment,
		category: bestMatch.category,
		isDefault: false,
		isMultiple: false,
	};
}
