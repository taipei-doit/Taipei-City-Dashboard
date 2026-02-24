// 取得擁擠程度對應的顏色
export const getCrowdColor = (level) => {
	switch (level) {
		case "1":
			return "🟩";
		case "2":
			return "🟨";
		case "3":
			return "🟧";
		case "4":
			return "🟥";
		default:
			return "⬜";
	}
};

// 各捷運路線對應顏色
export const mrtLineColor = {
	metro_br_line: "#C48C31",
	metro_bl_line: "#0070BD",
	metro_g_line: "#038258",
	metro_o_line: "#F5B41C",
	metro_r_line: "#E1002C",
};
