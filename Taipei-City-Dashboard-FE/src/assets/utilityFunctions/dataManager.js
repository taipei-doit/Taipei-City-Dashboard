
export class DataManager {
	constructor(data) {
		this.obj = data || {};
		this.mapping = [
			{ name: "token", key: "data" },
			{ name: "isso_token", key: "taipei_code" },
			{ name: "user", key: "person" },
			{ name: "user_id", key: "identity" },
		];
	}

	getData(key = "data") {
		const mapItem = this.mapping.find(item => item.key === key);
		if (!mapItem) {
			return null;
		}
		
		return this.obj[mapItem.name] || null;
	}
}