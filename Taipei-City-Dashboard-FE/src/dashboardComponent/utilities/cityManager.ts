interface City {
    name: string;
    value: string;
}

interface CityConfig {
    expandedName: string;
	collapsedName?: string;
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
                expandedName: "臺北儀表板",
				collapsedName: "臺北",
                enabled: true,
                selectList: ["taipei"],
                tagList: ["taipei"],
            },
        ],
        [
            "metrotaipei",
            {
                expandedName: "雙北儀表板示範",
				collapsedName: "雙北",
                enabled: true,
                selectList: ["metrotaipei", "taipei"],
                tagList: ["metrotaipei", "taipei"],
            },
        ],
        [
            "newtaipei",
            {
                expandedName: "新北",
				collapsedName: "新北",
                enabled: false,
                selectList: ["newtaipei"],
                tagList: ["newtaipei"],
            },
        ],
        [
            "taoyuan",
            {
                expandedName: "桃園",
				collapsedName: "新北",
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

	// Get expanded name of the city
	getExpandedNameName(key: string): string {
        return this.configs.get(key)?.expandedName || key;
    }
	// Get collapsed name of the city
	getCollapsedName(key: string): string {
        return this.configs.get(key)?.collapsedName || key;
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