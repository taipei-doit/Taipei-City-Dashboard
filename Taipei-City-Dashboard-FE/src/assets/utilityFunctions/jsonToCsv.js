export function jsonToCsv(data, chart_config) {
	let csv = "";

	// 2D Data
	if (data.length === 1 && !chart_config.categories) {
		csv += "keys,values\n";
		data[0].data.forEach((element) => {
			csv += `${element.x},${element.y}\n`;
		});
	}
	// Time Data
	else if (!chart_config.categories) {
		csv += " ,";
		for (let j = -1; j < data[0].data.length; j++) {
			for (let k = 0; k < data.length; k++) {
				if (j === -1) {
					if (k === data.length - 1) {
						csv += `${data[k].name}\n`;
					} else {
						csv += `${data[k].name},`;
					}
					continue;
				}
				if (k === 0) {
					csv += `${data[k].data[j].x},`;
				}
				if (k === data.length - 1) {
					csv += `${data[k].data[j].y}\n`;
				} else {
					csv += `${data[k].data[j].y},`;
				}
			}
		}
	} // 3D Data / Guage Data
	else {
		csv += " ,";
		for (let j = -1; j < data[0].data.length; j++) {
			for (let k = 0; k < data.length; k++) {
				if (j === -1) {
					if (k === data.length - 1) {
						csv += `${data[k].name}\n`;
					} else {
						csv += `${data[k].name},`;
					}
					continue;
				}
				if (k === 0) {
					csv += `${chart_config.categories[j]},`;
				}
				if (k === data.length - 1) {
					csv += `${data[k].data[j]}\n`;
				} else {
					csv += `${data[k].data[j]},`;
				}
			}
		}
	}

	return csv;
}
