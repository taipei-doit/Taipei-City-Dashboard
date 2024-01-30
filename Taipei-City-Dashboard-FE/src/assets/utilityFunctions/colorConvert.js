// https://css-tricks.com/converting-color-spaces-in-javascript/

// 1. Transforms Color from hex (#aaaaaa) to rgb (red, green, blue)
export const hexToRGB = (h) => {
	let r = 0,
		g = 0,
		b = 0;
	if (h.length == 4) {
		// 3 digits
		r = "0x" + h[1] + h[1];
		g = "0x" + h[2] + h[2];
		b = "0x" + h[3] + h[3];
	} else if (h.length == 7) {
		// 6 digits
		r = "0x" + h[1] + h[2];
		g = "0x" + h[3] + h[4];
		b = "0x" + h[5] + h[6];
	}
	return { r, g, b };
};

// 2. Transforms Color from hex (#aaaaaa) to hsl (hue, saturation, value)
export const hexToHSL = (hex) => {
	if (hex) {
		let { r, g, b } = hexToRGB(hex);
		r /= 255;
		g /= 255;
		b /= 255;
		let max = Math.max(r, g, b),
			min = Math.min(r, g, b),
			h,
			s,
			l = (max + min) / 2;
		if (max == min) {
			h = s = 0;
		} else {
			let d = max - min;
			s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
			switch (max) {
			case r:
				h = (g - b) / d + (g < b ? 6 : 0);
				break;
			case g:
				h = (b - r) / d + 2;
				break;
			case b:
				h = (r - g) / d + 4;
				break;
			}
			h /= 6;
		}
		h = Math.round(360 * h);
		s = Math.round(s * 100);
		l = Math.round(l * 100);
		return `${h},${s}%,${l}%`;
	} else {
		return "0,0%,100%";
	}
};
