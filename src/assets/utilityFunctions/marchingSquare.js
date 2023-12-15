// Marching Square algorithm: An algorithm that generates contours (isolines) for a two-dimensional scalar field.
//
// Please refer to the following link for details:
// https://en.wikipedia.org/wiki/Marching_squares
//
// Input:
// - discreteData: A 2D array storing values on a grid
// - isoValue: The value to draw the isoline on
//
// Output:
// An array of isoline segments in the format of
// [
//	[ [x1, y1], [x2, y2] ],
// 	[ [x1, y1], [x2, y2] ]...
// ]

export function marchingSquare(discreteData, isoValue) {
	let columnN = discreteData[0].length;
	let rowN = discreteData.length;
	let result = [];

	//  discreteData:
	//
	//  ┌> latitude increases
	//
	//  │        │        │        │
	//  ├────────┼────────┼────────┼─
	// -> [2][0]-> [2][1]-> [2][2]->
	//  ├────────┼────────┼────────┼─
	// -> [1][0]-> [1][1]-> [1][2]->
	//  ├────────┼────────┼────────┼─
	//  │ [0][0]-> [0][1]-> [0][2]->
	//  └────────┴────────┴────────┴─ -> longitude increases

	for (let row = 0; row < rowN - 1; row++) {
		for (let col = 0; col < columnN - 1; col++) {
			// Drawing isoline for the following square surrounded by four discreteData values:
			//
			// [row+1][col] ┌────┐ [row+1][col+1]
			//              │    │
			//   [row][col] └────┘ [row][col+1]
			//
			// How each side is numbered:
			//
			// ┌─ 0 ─┐
			// 3     1
			// └─ 2 ─┘

			// Step 1: Store corner values
			let cornerValues = [
				discreteData[row + 1][col],
				discreteData[row + 1][col + 1],
				discreteData[row][col + 1],
				discreteData[row][col],
			];

			// Step 2: Compare the corner values to the iso-value to make a binary representaion.
			let cornerBinary = cornerValues.map((val) => {
				return val > isoValue ? 1 : 0;
			});

			// Step 3: Look up the binary representaion in basicLineTable to determine a line pattern.
			let sum = 0;
			cornerBinary.forEach((val, ind) => {
				sum += val * 2 ** ind;
			});
			let linePattern = linePatternTable[sum];

			// - Consider saddle points
			if (sum === 5) {
				if (cornerValues.reduce((a, b) => a + b) / 4 >= isoValue) {
					linePattern = [
						[0, 3],
						[1, 2],
					];
				} else {
					linePattern = [
						[0, 1],
						[2, 3],
					];
				}
			} else if (sum === 10) {
				if (cornerValues.reduce((a, b) => a + b) / 4 >= isoValue) {
					linePattern = [
						[0, 1],
						[2, 3],
					];
				} else {
					linePattern = [
						[0, 3],
						[1, 2],
					];
				}
			}

			// Step 4: Use linear interpolation to get more precise isoline segments,
			// and then push those segments into result.

			// - Calculate the linear interpolation values for each side.
			let interpoValues = [];
			for (let k = 0; k < 4; k++) {
				let interpolate_tmp = linearInterpolation(
					cornerValues[k],
					cornerValues[(k + 1) % 4],
					isoValue
				);
				interpoValues.push(interpolate_tmp);
			}

			// - Flip the interpolation values for side 1 and side 2.
			interpoValues[1] = 1 - interpoValues[1];
			interpoValues[2] = 1 - interpoValues[2];

			// - Turn line patterns into actual coordinates.
			let colrow = [col, row];
			linePattern.forEach((line) => {
				let endPoint0 = lineEndPoints[line[0]].map((code, ind) => {
					if (code === 0.5) {
						return colrow[ind] + interpoValues[line[0]];
					}
					return colrow[ind] + code;
				});

				let endPoint1 = lineEndPoints[line[1]].map((code, ind) => {
					if (code === 0.5) {
						return colrow[ind] + interpoValues[line[1]];
					}
					return colrow[ind] + code;
				});

				result.push([endPoint0, endPoint1]);
			});
		}
	}

	return result;
}

let linePatternTable = [
	[],
	[[0, 3]],
	[[0, 1]],
	[[1, 3]],
	[[1, 2]],
	[
		[0, 1],
		[2, 3],
	],
	[[0, 2]],
	[[2, 3]],
	[[2, 3]],
	[[0, 2]],
	[
		[0, 3],
		[1, 2],
	],
	[[1, 2]],
	[[1, 3]],
	[[0, 1]],
	[[0, 3]],
	[],
];

// End point coordinates
// - A value of 0.5 means the exact value is determined by linear interpolation
let lineEndPoints = [
	[0.5, 1], // End point coordinate on side 0
	[1, 0.5], // End point coordinate on side 1...
	[0.5, 0],
	[0, 0.5],
];

function linearInterpolation(v1, v2, v_iso) {
	if (v2 === v1) {
		return Infinity;
	}
	return (v_iso - v1) / (v2 - v1);
}

// Linear interpolation examples:
// v_iso === v1        -> return 0
// v_iso === v2        -> return 1
// v_iso === (v1+v2)/2 -> return 0.5
