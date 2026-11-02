const X_AXIS_LABEL_SPACE = 24;

export function getXAxisLabelOptions(labels = {}) {
	return {
		hideOverlappingLabels: true,
		offsetY: 2,
		...labels,
	};
}

export function getChartHeightWithXAxisLabels(height, hasXAxisLabels = true) {
	const baseHeight = Number.parseFloat(height);
	if (!Number.isFinite(baseHeight)) return height;

	return `${baseHeight + (hasXAxisLabels ? X_AXIS_LABEL_SPACE : 0)}px`;
}
