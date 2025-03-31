interface City {
    name: string;
    value: string;
}

interface CityConfig {
    displayName: string;
    enabled: boolean;
    selectList: string[];
    tagList: string[];
}

export class CityManager {
    private cities: City[] = [
        { name: "臺北市", value: "taipei" },
        { name: "新北市", value: "newtaipei" },
        { name: "雙北", value: "metrotaipei" },
        { name: "桃園", value: "taoyuan" },
    ];

    private configs: Map<string, CityConfig> = new Map([
        [
            "taipei",
            {
                displayName: "臺北",
                enabled: true,
                selectList: ["taipei"],
                tagList: ["taipei"],
            },
        ],
        [
            "metrotaipei",
            {
                displayName: "雙北",
                enabled: true,
                selectList: ["metrotaipei", "taipei"],
                tagList: ["metrotaipei", "taipei"],
            },
        ],
        [
            "newtaipei",
            {
                displayName: "新北",
                enabled: false,
                selectList: ["newtaipei"],
                tagList: ["newtaipei"],
            },
        ],
        [
            "taoyuan",
            {
                displayName: "桃園",
                enabled: false,
                selectList: ["taoyuan"],
                tagList: ["taoyuan"],
            },
        ],
    ]);

    constructor(options?: { cities?: City[]; configs?: Map<string, CityConfig> }) {
		if (options?.cities) {
			this.cities = options.cities;
		}
		if (options?.configs) {
			this.configs = options.configs;
		}
	}

    get activeCities() {
        return Array.from(this.configs.entries())
            .filter(([_, config]) => config.enabled)
            .map(([city]) => city);
    }

	get	allConfigs() { 
		return this.configs;
	}

    // Get the configuration for a specific city
	getCityConfig(key: string): CityConfig | undefined {
        return this.configs.get(key);
    }

    // Get the cities list based on the input
    getCities(key: string | string[]): City[] {
        if (!key) return [];

        // Function: Find the complete city object based on the city value
        const findCity = (value: string): City | null => {
            const cityItem = this.cities.find(item => item.value === value);
            return cityItem ? { name: cityItem.name, value } : null;
        };

        // If the input is an array, process multiple cities
        if (Array.isArray(key)) {
            return key
                .map(value => findCity(value))
                .filter((cityObj): cityObj is City => cityObj !== null);
        }

        // Process a single city
        const result = findCity(key);
        return result ? [result] : [];
    }

	// Get the display name of the city
	getDisplayName(key: string): string {
        return this.configs.get(key)?.displayName || key;
    }

	// Get specific city's select list
    getSelectList(key: string): City[] {
        if (!key) return [];
        const selectList = this.configs.get(key)?.selectList;
		if (!selectList) return [];

        return this.getCities(selectList);
    }

    // Get specific city's tag list
    getTagList(key: string): City[] {
        if (!key) return [];
        const tagList = this.configs.get(key)?.tagList;
        return this.getCities(tagList || []);
    }

	// Check if the city is enabled
	isCityEnabled(key: string): boolean {
		const cityConfig = this.configs.get(key);
		return !!cityConfig && cityConfig.enabled;
	}
}