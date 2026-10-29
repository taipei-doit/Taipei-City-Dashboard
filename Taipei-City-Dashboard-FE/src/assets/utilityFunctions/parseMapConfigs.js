const LEGEND_TYPES = new Set([
	"circle",
	"fill",
	"fill-extrusion",
	"line",
	"symbol",
]);

const PRIMARY_COLOR_KEYS = {
	circle: "circle-color",
	fill: "fill-color",
	"fill-extrusion": "fill-extrusion-color",
	line: "line-color",
};

const MAP_LEGEND_ICONS = new Set([
	"triangle_white",
	"triangle_green",
	"bus",
	"cctv",
	"metro",
	"train",
	"live",
	"youbike_elec",
	"bike_red",
	"bike_orange",
	"bike_green",
]);

function formatValue(value) {
	if (Array.isArray(value)) return value.map(formatValue).join("、");
	if (value === null || value === undefined || value === "") return "未設定";
	return String(value);
}

function getFieldName(expression) {
	if (!Array.isArray(expression)) return null;
	if (expression[0] === "get") return expression[1];

	for (const item of expression.slice(1)) {
		const field = getFieldName(item);
		if (field) return field;
	}
	return null;
}

function formatCondition(condition) {
	if (!Array.isArray(condition)) return formatValue(condition);

	const [operator, ...args] = condition;
	if (operator === "all" || operator === "any") {
		return args
			.map(formatCondition)
			.filter(Boolean)
			.join(operator === "all" ? " 且 " : " 或 ");
	}

	if (["==", "<", "<=", ">", ">="].includes(operator)) {
		const symbols = {
			"==": "=",
			"<": "<",
			"<=": "≤",
			">": ">",
			">=": "≥",
		};
		const leftField = getFieldName(args[0]);
		const rightField = getFieldName(args[1]);
		const value = leftField ? args[1] : args[0];
		if (leftField || rightField) return `${symbols[operator]} ${formatValue(value)}`;
	}

	return "符合條件";
}

function parseMatchExpression(expression) {
	const items = [];
	for (let index = 2; index < expression.length - 1; index += 2) {
		items.push({
			label: formatValue(expression[index]),
			color: expression[index + 1],
		});
	}
	return items;
}

function getSimpleUpperBound(condition) {
	if (
		!Array.isArray(condition) ||
		!["<", "<="].includes(condition[0]) ||
		!getFieldName(condition[1])
	) {
		return null;
	}
	return {
		operator: condition[0],
		value: condition[2],
		field: getFieldName(condition[1]),
	};
}

function parseCaseExpression(expression) {
	const items = [];
	let previousBound = null;

	for (let index = 1; index < expression.length - 1; index += 2) {
		const condition = expression[index];
		const bound = getSimpleUpperBound(condition);
		let label = formatCondition(condition);

		if (bound && previousBound && bound.field === previousBound.field) {
			const lowerOperator = previousBound.operator === "<=" ? ">" : "≥";
			const upperOperator = bound.operator === "<=" ? "≤" : "<";
			label = `${lowerOperator} ${formatValue(previousBound.value)} 且 ${upperOperator} ${formatValue(bound.value)}`;
		}

		items.push({ label, color: expression[index + 1] });
		previousBound = bound;
	}

	if (previousBound) {
		items.push({
			label: `${previousBound.operator === "<=" ? ">" : "≥"} ${formatValue(previousBound.value)}`,
			color: expression[expression.length - 1],
		});
	}
	return items;
}

function parseInterpolateExpression(expression) {
	if (getFieldName(expression[2]) === null) {
		return [{ label: "全部", color: expression[expression.length - 1] }];
	}

	const stops = [];
	const colors = [];
	for (let index = 3; index < expression.length; index += 2) {
		stops.push(expression[index]);
		colors.push(expression[index + 1]);
	}
	if (!colors.length) return [];

	return [
		{
			label: `${formatValue(stops[0])} – ${formatValue(stops.at(-1))}`,
			color: colors[0],
			colors,
			stops,
			continuous: true,
		},
	];
}

function parseStepExpression(expression) {
	const items = [];
	const firstStop = expression[3];
	if (firstStop === undefined) return [];

	items.push({
		label: `< ${formatValue(firstStop)}`,
		color: expression[2],
	});

	for (let index = 3; index < expression.length; index += 2) {
		const stop = expression[index];
		const nextStop = expression[index + 2];
		items.push({
			label:
				nextStop === undefined
					? `≥ ${formatValue(stop)}`
					: `≥ ${formatValue(stop)} 且 < ${formatValue(nextStop)}`,
			color: expression[index + 1],
		});
	}
	return items;
}

function parseColorValue(value) {
	if (typeof value === "string") return [{ label: "全部", color: value }];
	if (!Array.isArray(value)) return [];

	switch (value[0]) {
	case "match":
		return parseMatchExpression(value);
	case "case":
		return parseCaseExpression(value);
	case "interpolate":
		return parseInterpolateExpression(value);
	case "step":
		return parseStepExpression(value);
	default:
		return [];
	}
}

function parseSymbolLegend(config) {
	if (config.icon === "youbike") {
		return [
			{
				label: "無可還車位",
				iconSrc: "/images/map/bike_red.png",
			},
			{
				label: "無一般自行車可借",
				iconSrc: "/images/map/bike_orange.png",
			},
			{
				label: "可借且可還",
				iconSrc: "/images/map/bike_green.png",
			},
		];
	}

	if (!MAP_LEGEND_ICONS.has(config.icon)) return [];
	return [
		{
			label: "全部",
			iconSrc: `/images/map/${config.icon}.png`,
		},
	];
}

function removeDuplicateItems(items) {
	const keys = new Set();
	return items.filter((item) => {
		if (typeof item.color !== "string" && !item.iconSrc && !item.colors) {
			return false;
		}
		const key = `${item.label}-${item.color}-${item.iconSrc}-${item.colors}`;
		if (keys.has(key)) return false;
		keys.add(key);
		return true;
	});
}

export function buildMapLegend(config) {
	if (!config) return null;

	const type = config.legendType || config.originalType || config.type;
	if (!LEGEND_TYPES.has(type)) return null;

	let items = [];
	if (type === "symbol") {
		items = parseSymbolLegend(config);
	} else {
		const paint = config.paint || {};
		items = parseColorValue(paint[PRIMARY_COLOR_KEYS[type]]);

		if (
			type === "circle" &&
			(!items.length || paint["circle-opacity"] === 0) &&
			paint["circle-stroke-color"]
		) {
			items = [{ label: "全部", color: paint["circle-stroke-color"], hollow: true }];
		}
	}

	const paint = config.paint || {};
	const opacity = paint[`${type}-opacity`];
	const strokeOpacity = paint["circle-stroke-opacity"];
	const width = paint[`${type}-width`];
	const strokeColor =
		type === "circle"
			? paint["circle-stroke-color"]
			: type === "fill"
				? paint["fill-outline-color"]
				: null;

	items = removeDuplicateItems(items).map((item) => ({
		label: item.label,
		kind: type === "fill-extrusion" ? "fill" : type,
		color: item.color || null,
		colors: item.colors || null,
		stops: item.stops || null,
		iconSrc: item.iconSrc || null,
		opacity:
			item.hollow && typeof strokeOpacity === "number"
				? strokeOpacity
				: item.hollow
					? 1
					: typeof opacity === "number"
						? opacity
						: 1,
		width: typeof width === "number" ? width : null,
		strokeColor,
		hollow: item.hollow || false,
		dashed:
			type === "line" &&
			(Boolean(paint["line-dasharray"]) || config.icon === "dash"),
		continuous: item.continuous || false,
	}));

	if (!items.length) return null;
	return {
		title: config.title || "未命名圖層",
		type,
		items,
	};
}

export function parseLegendFromPaint(paint = {}) {
	const colorKey = Object.keys(paint).find((key) => key.endsWith("-color"));
	return colorKey ? parseColorValue(paint[colorKey]) : [];
}
