/* eslint-disable indent */
export function getComponentDataTimeframe(time_from, time_to) {
	const tzoffset = new Date().getTimezoneOffset() * 60000;
	const nowTimeFrom = new Date(Date.now());
	const nowTimeTo = new Date(Date.now());
	let parsedTimeFrom = "";
	let parsedTimeTo = "";

	if (time_from.split("_")[1] === "start") {
		switch (time_from.split("_")[0]) {
			case "day":
				nowTimeFrom.setHours(0, 0, 0, 0);
				break;
			case "week":
				nowTimeFrom.setDate(
					nowTimeFrom.getDate() - nowTimeFrom.getDay() + 1
				);
				break;
			case "month":
				nowTimeFrom.setDate(1);
				break;
			case "halfyear":
				nowTimeFrom.setMonth(
					Math.floor(nowTimeFrom.getMonth() / 6) * 6
				);
				break;
			case "year":
				nowTimeFrom.setMonth(0, 1);
				break;
			default:
				break;
		}
	} else if (time_from.split("_")[1] === "ago") {
		switch (time_from.split("_")[0]) {
			case "day":
				nowTimeFrom.setDate(nowTimeFrom.getDate() - 1);
				break;
			case "week":
				nowTimeFrom.setDate(nowTimeFrom.getDate() - 7);
				break;
			case "month":
				nowTimeFrom.setMonth(nowTimeFrom.getMonth() - 1);
				break;
			case "halfyear":
				nowTimeFrom.setMonth(nowTimeFrom.getMonth() - 6);
				break;
			case "year":
				nowTimeFrom.setFullYear(nowTimeFrom.getFullYear() - 1);
				break;
			default:
				break;
		}
	}

	parsedTimeFrom = new Date(nowTimeFrom - tzoffset)
		.toISOString()
		.split(".")[0]
		.replace("T", " ");

	if (time_to === "now") {
		// let parsedTimeTo be the current time formated YYYY-MM-DD HH:MM:SS and in UTC+8
		parsedTimeTo = new Date(nowTimeTo - tzoffset)
			.toISOString()
			.split(".")[0]
			.replace("T", " ");
	}
	return { parsedTimeFrom, parsedTimeTo };
}
