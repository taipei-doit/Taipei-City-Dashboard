function parseUnit(unit) {
	if (typeof unit !== "string") return unit;

	try {
		const parsed = JSON.parse(unit);
		return parsed && typeof parsed === "object" ? parsed : unit;
	} catch {
		return unit;
	}
}

export function getChartUnit(unit, dimension = "value") {
	const parsedUnit = parseUnit(unit);
	if (typeof parsedUnit === "string") return parsedUnit.trim();
	if (!parsedUnit || typeof parsedUnit !== "object") return "";

	const dimensionUnit = parsedUnit[dimension];
	if (typeof dimensionUnit === "string" && dimensionUnit.trim()) {
		return dimensionUnit.trim();
	}

	const valueUnit = parsedUnit.value;
	if (typeof valueUnit === "string" && valueUnit.trim()) {
		return valueUnit.trim();
	}

	if (dimension === "value") {
		for (const key of ["y", "y1", "y2", "x", "z"]) {
			const fallbackUnit = parsedUnit[key];
			if (typeof fallbackUnit === "string" && fallbackUnit.trim()) {
				return fallbackUnit.trim();
			}
		}
	}

	return "";
}

export function getExplicitChartUnit(unit, dimension) {
	const parsedUnit = parseUnit(unit);
	if (!parsedUnit || typeof parsedUnit !== "object") return "";

	const dimensionUnit = parsedUnit[dimension];
	return typeof dimensionUnit === "string" ? dimensionUnit.trim() : "";
}

export function getAxisTitle(unit, dimension) {
	return getChartUnit(unit, dimension);
}

const AXIS_TITLE_FONT_SIZE = 11;
const AXIS_TITLE_LINE_HEIGHT = 1.3;

function verticalTitleConfig(lines) {
	if (!lines.length) {
		return { text: "", rotate: 0, offsetY: 0 };
	}

	return {
		text: lines,
		rotate: 0,
		offsetY:
			-((lines.length - 1) * AXIS_TITLE_FONT_SIZE * AXIS_TITLE_LINE_HEIGHT) /
			2,
	};
}

export function toVerticalAxisTitle(text) {
	const value = typeof text === "string" ? text.trim() : "";
	return verticalTitleConfig(Array.from(value));
}

export function toVerticalDualAxisTitle(seriesName, unit) {
	const category = typeof seriesName === "string" ? seriesName.trim() : "";
	const unitText = typeof unit === "string" ? unit.trim() : "";
	const lines = Array.from(category);

	if (category && unitText) lines.push(" ");
	lines.push(...Array.from(unitText));

	return verticalTitleConfig(lines);
}

export function alignVerticalAxisTitles(chartContext) {
	const align = () => {
		const root = chartContext?.el || chartContext?.w?.globals?.dom?.baseEl;
		if (!root) return;

		root.querySelectorAll(".apexcharts-yaxis-title-text").forEach((text) => {
			const x = text.getAttribute("x");
			if (x == null) return;
			text.querySelectorAll("tspan").forEach((tspan) => {
				tspan.setAttribute("x", x);
			});
		});
	};

	align();
	requestAnimationFrame(align);
}

export function formatValueWithUnit(value, unit, dimension = "value") {
	const valueUnit = getChartUnit(unit, dimension);
	return valueUnit ? `${value} ${valueUnit}` : `${value}`;
}
