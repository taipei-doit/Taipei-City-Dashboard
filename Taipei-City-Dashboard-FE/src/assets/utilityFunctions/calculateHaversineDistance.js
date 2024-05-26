/**
 * 
 * @param {*} latitude1 
 * @param {*} longitude1 
 * @param {*} latitude2 
 * @param {*} longitude2 
 * @returns The distance in kilometers between the two coordinates
 */
export function calculateHaversineDistance(
	latitude1,
	longitude1,
	latitude2,
	longitude2
) {
	const earthRadiusKm = 6371; // Radius of the Earth in kilometers

	try {
		// Check if inputs are numbers
		if (
			isNaN(latitude1) ||
			isNaN(longitude1) ||
			isNaN(latitude2) ||
			isNaN(longitude2)
		) {
			throw new Error("All arguments must be numbers.");
		}

		// Check if latitude and longitude values are within valid range
		if (
			latitude1 < -90 ||
			latitude1 > 90 ||
			latitude2 < -90 ||
			latitude2 > 90 ||
			longitude1 < -180 ||
			longitude1 > 180 ||
			longitude2 < -180 ||
			longitude2 > 180
		) {
			throw new Error(
				"Latitude must be between -90 and 90, and longitude must be between -180 and 180."
			);
		}

		// Convert degrees to radians
		const deltaLatitude = ((latitude2 - latitude1) * Math.PI) / 180;
		const deltaLongitude = ((longitude2 - longitude1) * Math.PI) / 180;

		// Apply Haversine formula
		const halfChordLengthSquared =
			Math.sin(deltaLatitude / 2) * Math.sin(deltaLatitude / 2) +
			Math.cos((latitude1 * Math.PI) / 180) *
				Math.cos((latitude2 * Math.PI) / 180) *
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


