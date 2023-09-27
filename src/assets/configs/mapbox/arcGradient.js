function hexToRGB(hex) {
	// Remove the hash character if present
	hex = hex.replace(/^#/, "");

	// Parse the hex value to get the RGB components
	const bigint = parseInt(hex, 16);
	const r = (bigint >> 16) & 255;
	const g = (bigint >> 8) & 255;
	const b = bigint & 255;

	return [r, g, b];
}

// function RGBToHex(r, g, b) {
// 	// Convert RGB components to a hexadecimal color string
// 	return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
// }

export function calculateGradientSteps(startColor, endColor, steps) {
	const startRGB = hexToRGB(startColor);
	const endRGB = hexToRGB(endColor);

	const gradientSteps = [];

	for (let i = 0; i < steps; i++) {
		const r =
			Math.round(
				((startRGB[0] + (endRGB[0] - startRGB[0]) * (i / (steps - 1))) /
					255) *
					1000
			) / 1000;
		const g =
			Math.round(
				((startRGB[1] + (endRGB[1] - startRGB[1]) * (i / (steps - 1))) /
					255) *
					1000
			) / 1000;
		const b =
			Math.round(
				((startRGB[2] + (endRGB[2] - startRGB[2]) * (i / (steps - 1))) /
					255) *
					1000
			) / 1000;
		gradientSteps.push(r);
		gradientSteps.push(g);
		gradientSteps.push(b);
	}

	return gradientSteps;
}
