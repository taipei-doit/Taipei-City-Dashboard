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

export function formatValueWithUnit(value, unit, dimension = "value") {
	const valueUnit = getChartUnit(unit, dimension);
	return valueUnit ? `${value} ${valueUnit}` : `${value}`;
}
