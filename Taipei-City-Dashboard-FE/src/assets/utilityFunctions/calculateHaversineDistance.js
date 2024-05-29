/**
 * @typedef {Object} Coordinates
 * @property {number} latitude - The latitude of the coordinate.
 * @property {number} longitude - The longitude of the coordinate.
 */

/**
 * Calculates the Haversine distance between two points.
 *
 * @param {Coordinates} point1 - The first set of coordinates.
 * @param {Coordinates} point2 - The second set of coordinates.
 * @returns {number|null} The distance in kilometers between the two coordinates.
 */
export function calculateHaversineDistance(point1, point2) {
	const earthRadiusKm = 6371; // Radius of the Earth in kilometers

	try {
		// Check if inputs are numbers
		if (
			isNaN(point1.latitude) ||
			isNaN(point1.longitude) ||
			isNaN(point2.latitude) ||
			isNaN(point2.longitude)
		) {
			throw new Error("All arguments must be numbers.");
		}

		// Check if latitude and longitude values are within valid range
		if (
			point1.latitude < -90 ||
			point1.latitude > 90 ||
			point2.latitude < -90 ||
			point2.latitude > 90 ||
			point1.longitude < -180 ||
			point1.longitude > 180 ||
			point2.longitude < -180 ||
			point2.longitude > 180
		) {
			throw new Error(
				"Latitude must be between -90 and 90, and longitude must be between -180 and 180."
			);
		}

		// Convert degrees to radians
		const deltaLatitude =
			((point2.latitude - point1.latitude) * Math.PI) / 180;
		const deltaLongitude =
			((point2.longitude - point1.longitude) * Math.PI) / 180;

		// Apply Haversine formula
		const halfChordLengthSquared =
			Math.sin(deltaLatitude / 2) * Math.sin(deltaLatitude / 2) +
			Math.cos((point1.latitude * Math.PI) / 180) *
				Math.cos((point2.latitude * Math.PI) / 180) *
				Math.sin(deltaLongitude / 2) *
				Math.sin(deltaLongitude / 2);

		// Calculate the angular distance in radians
		const angularDistance =
			2 *
			Math.atan2(
				Math.sqrt(halfChordLengthSquared),
				Math.sqrt(1 - halfChordLengthSquared)
			);

		// Convert the angular distance to kilometers
		const distanceKm = earthRadiusKm * angularDistance; // Distance in kilometers

		return distanceKm;
	} catch (error) {
		console.error(error.message);
		return null; // Return null in case of an error
	}
}
