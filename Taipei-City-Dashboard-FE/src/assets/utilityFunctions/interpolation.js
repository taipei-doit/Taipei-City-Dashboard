// This function estimates the values at target points based on the values at nearby data points,
// taking into account the distances between them. The weighted average ensures that closer data
// points have a stronger influence on the interpolated value.

// Input:
// 1. dataPoints
// An array that contains n objects in the format of {x, y, value}
// 2. targetPoints
// An array that contains m objects in the format of {x, y}
//
// Output:
// 1. answers
// An array that contains m values, representing the predicted value on each of the target coordinates.

export function interpolation(dataPoints, targetPoints) {
	const pointCount = dataPoints.length;
	let answers = [];
	for (let k = 0; k < targetPoints.length; k++) {
		if (dataPoints.includes(targetPoints[k])) {
			answers.push(dataPoints[dataPoints.indexOf(targetPoints[k])].value);
		} else {
			let weight_sum = 0;
			let weight_value = 0;
			for (let i = 0; i < pointCount; i++) {
				let weight =
					1 /
					((dataPoints[i].x - targetPoints[k].x) ** 2 +
						(dataPoints[i].y - targetPoints[k].y) ** 2);
				weight_sum += weight;
				weight_value += weight * dataPoints[i].value;
			}
			weight_value = weight_value / weight_sum;
			answers.push(weight_value);
		}
	}
	return answers;
}
