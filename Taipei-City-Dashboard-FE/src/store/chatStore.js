import { ref, watch } from "vue";
import { defineStore } from "pinia";
import http from "../router/axios";

export const useChatStore = defineStore("chat", () => {
	// 預設訊息
	const defaultChatData = [
		{
			id: 1,
			role: "bot",
			isDefault: true,
			content:
				"您好，我是【臺北城市儀表板】小幫手，很高興為您服務！\n 您可以： \n\n • 點擊左側既有的儀表板主題，快速查看各主題內容 \n • 輸入您感興趣的主題描述，我會自動為您組建最適合的儀表板 \n\n 如果有想了解的內容，歡迎直接告訴我，我會盡力協助！\n\n 📩 聯絡信箱：tuic@gov.taipei \n 🏢 臺北大數據中心 \n\n",
		},
	];

	const recommendComponents = ref(null);
	const componentListText = ref("");

	// 載入組件清單（只抓一次，快取在 store 內）
	const loadComponentList = async () => {
		if (componentListText.value) return;
		try {
			const res = await http.get("ai/components");
			const items = res.data?.data || [];
			if (items.length === 0) return;
			// 格式：index|名稱|城市|單位，每行一筆
			componentListText.value =
				"可用組件清單（index | 名稱）：\n" +
				items.map((c) => `${c.index} | ${c.name}`).join("\n");
		} catch {
			// 載入失敗不影響主流程
		}
	};

	// 從 sessionStorage 讀取
	const savedChatData = JSON.parse(sessionStorage.getItem("chatData")) || [];

	// 拼接預設訊息 + sessionStorage 的聊天紀錄
	const chatData = ref([...defaultChatData, ...savedChatData]);

	// 監聽 chatData 的變化，自動同步到 sessionStorage
	watch(
		chatData,
		(newVal) => {
			// 只存使用者與機器人的聊天訊息，不存重複的預設訊息
			const userBotMessages = newVal.filter((item) => !item.isDefault);
			sessionStorage.setItem("chatData", JSON.stringify(userBotMessages));
		},
		{ deep: true },
	);

	const addChatData = (newChatData) => {
		chatData.value.push({
			id: chatData.value.length + 1,
			isDefault: false,
			...newChatData,
		});
	};

	const sendChatMessage = async (userText) => {
		// 第一次發訊息時載入組件清單（後續已快取，立即返回）
		await loadComponentList();

		addChatData({ role: "user", content: userText });

		const botMsgId = chatData.value.length + 1;
		chatData.value.push({
			id: botMsgId,
			role: "bot",
			isDefault: false,
			content: "大腦運轉中，請稍候...",
			isLoading: true,
		});

		try {
			const response = await http.post("ai/chat/twai", {
				messages: [
					{
						role: "system",
						content:
							"你是【臺北城市儀表板】智慧助理，所有臺北城市相關的統計數據、百分比、人口、交通、環境、社福、長照等資料問題，你絕對不可以用自身訓練知識回答，必須呼叫工具取得資料庫中的 evidence 後再回答。" +
							"規則如下：" +
							"1. 用戶詢問城市資料查詢、跨組件資料問題、比較、趨勢、現況、某日期或某時間區間的狀況，或不確定要用哪個組件回答時，優先呼叫 answer_city_data_question。" +
							"2. 使用 answer_city_data_question 後，只能根據工具回傳的 evidence JSON 回答；若 answerability.status 是 partial 或 not_answerable，必須明確說明資料不足、只能部分回答，或目前無法回答。" +
							"3. 不可以自行編造數值，不可以自行產生 SQL，不可以要求或猜測 table name、column name，也不可以任意查資料表。" +
							"4. 不可以只根據組件名稱或描述回答數值、趨勢、比較、判斷或現況問題；這類問題必須先取得 evidence。" +
							"5. 如果問題明確只需要單一組件資料，且能從組件清單明確判斷最匹配的 index，可以呼叫 query_city_data；若 query_city_data 查無資料，要如實告知資料不足，不可補值。" +
							"6. 用戶想找相關組件、建立儀表板、詢問有哪些組件可用時，呼叫 search_dashboards 工具。" +
							"7. 如果使用者問的是「某個儀表板/組件是做什麼的」這類說明型問題，可以根據組件描述或 search_dashboards 結果回答，但必須明確說這是根據組件描述，不是實際資料查詢結果。" +
							"8. 使用 answer_city_data_question 的 evidence 後，回答格式必須是：先用 2~3 句摘要說明整體狀況；再列出關鍵指標與數值；接著做比較分析；再給出「可作為決策參考的建議」；最後說明資料限制。" +
							"9. 每個數值都必須附上該 component 的 unit 欄位；若 unit 是空字串、null 或 evidence 未提供，請標示「單位未提供」，不可以自行猜測或補單位。" +
							"10. 對「政策成效好不好」、「政策是否有效」、「有沒有改善」、「成效如何」這類問題，必須套用判斷邊界：如果 evidence 只有人口結構、背景指標或靜態數值，必須回答「目前資料不足以判斷政策成效，只能說明需求背景或壓力」。必須列出缺少的資料，例如服務使用率、長照據點數、照護人力、等待時間、床位數、服務滿意度、時間序列或政策前後比較。" +
							"11. 只能使用與 user_question 直接相關的 components；不可把所有檢索結果都納入主要分析。與問題無關的 components（例如長照問題中的電動巴士、自行車道路等）不可納入主要分析，可簡短說「部分檢索結果與問題關聯較低，未納入判斷」。" +
							"12. 比較分析必須根據 evidence 中實際存在的數值，例如哪些指標較高、哪些行政區數值較高或較需要優先關注；如果 evidence 沒有時間序列、服務資源、政策投入或成效資料，不能判斷政策成效，只能說資料不足。" +
							"13. 建議只能作為決策參考，不能說成最終決策或政策結論；所有建議都要連回 evidence 中看到的資料差異。若 evidence 不足，只能建議後續需要補充哪些資料或進一步檢視哪些指標，不可以憑空建議加強宣傳、增加預算或調整政策。" +
							"14. 對老化指數等 unit 空白或非百分比的指標，不可以自動加 %；若 evidence 沒有 unit，請寫「單位未提供」。可以用保守語句說明老化指數代表老年人口相對幼年人口的比例概念，但不能把它改寫成百分比。" +
							"15. 凡使用 query_city_data 取得資料後，回覆結尾必須加上一行：「📊 資料來源組件：{name}」（name 為組件清單中對應的中文名稱）。凡使用 answer_city_data_question 取得 evidence 後，回覆結尾必須列出使用的 components 名稱。\n\n" +
							componentListText.value,
					},
					{ role: "user", content: userText },
				],
				stream: false,
				tools: [
					{
						type: "function",
						function: {
							name: "search_dashboards",
							description:
								"搜尋與用戶描述相關的臺北城市儀表板組件清單，當用戶想瀏覽或建立儀表板時使用",
							parameters: {
								type: "object",
								properties: {
									query: {
										type: "string",
										description:
											"用戶查詢的關鍵字或主題描述",
									},
								},
								required: ["query"],
							},
						},
					},
					{
						type: "function",
						function: {
							name: "answer_city_data_question",
							description:
								"取得可回答城市資料問題的 structured evidence JSON。適用於跨組件資料問題、比較、趨勢、現況、某日期或時間區間的狀況，或不確定應使用哪個組件時。若問題涉及政策成效，必須用 evidence 判斷資料是否足夠；背景指標不足以代表政策成效。工具不接受 SQL、table name 或 column name。",
							parameters: {
								type: "object",
								properties: {
									user_question: {
										type: "string",
										description:
											"使用者的完整自然語言問題，作為 semantic search 與 evidence 組裝依據",
									},
									city: {
										type: "string",
										enum: ["taipei", "metrotaipei"],
										description:
											"城市範圍，taipei 或 metrotaipei，預設 taipei",
									},
									time_from: {
										type: "string",
										description:
											"查詢起始時間，格式 2006-01-02T15:04:05+08:00，不填則由後端預設",
									},
									time_to: {
										type: "string",
										description:
											"查詢結束時間，格式 2006-01-02T15:04:05+08:00，不填則由後端預設",
									},
									top_k: {
										type: "integer",
										description:
											"最多搜尋幾個相關組件，預設 5，最大 8",
										minimum: 1,
										maximum: 8,
									},
									score_threshold: {
										type: "number",
										description:
											"語意搜尋相關性門檻，預設 0.75",
										minimum: 0,
										maximum: 1,
									},
								},
								required: ["user_question"],
							},
						},
					},
					{
						type: "function",
						function: {
							name: "query_city_data",
							description:
								"自動搜尋組件並取得實際數據，用於回答具體數值問題（例如：目前空氣品質、交通流量、停車資訊等），一次呼叫即可完成",
							parameters: {
								type: "object",
								properties: {
									query: {
										type: "string",
										description: "查詢的主題或關鍵字",
									},
									city: {
										type: "string",
										description:
											"城市名稱，taipei 或 metrotaipei，預設 taipei",
									},
									time_from: {
										type: "string",
										description:
											"查詢起始時間，格式 2006-01-02T15:04:05+08:00，不填則預設最近 24 小時",
									},
									time_to: {
										type: "string",
										description:
											"查詢結束時間，格式 2006-01-02T15:04:05+08:00，不填則為現在",
									},
								},
								required: ["query"],
							},
						},
					},
				],
			});

			const data = response.data?.data;
			const aiAnswer = data?.content || "";
			const componentResultsRaw = data?.component_results;

			const targetMsg = chatData.value.find((msg) => msg.id === botMsgId);
			if (!targetMsg) return;

			// 若 AI 呼叫了 search_dashboards，解析組件結果並顯示表格
			if (componentResultsRaw) {
				try {
					const components = JSON.parse(componentResultsRaw);
					if (components.length > 0) {
						targetMsg.content =
							aiAnswer ||
							"以下是根據您的問題，自動為您推薦的「組件清單」。您可以將這些組件整批加入「個人儀表板」。";
						targetMsg.isLoading = false;

						chatData.value.push({
							id: chatData.value.length + 1,
							role: "bot",
							isDefault: false,
							button: [{ id: 1, text: "建立儀表板" }],
							content: null,
							relations: components,
						});

						saveChatLog(userText, components);
						return;
					}
				} catch {
					// JSON 解析失敗，繼續顯示文字回答
				}
			}

			// 一般文字回答
			targetMsg.content = aiAnswer || "抱歉，我沒有得出結論。";
			targetMsg.isLoading = false;
		} catch (error) {
			console.error("AI Chat Error:", error);
			const targetMsg = chatData.value.find((msg) => msg.id === botMsgId);
			if (targetMsg) {
				targetMsg.content = "抱歉，AI 系統目前連線不穩定，請稍後再試！";
				targetMsg.isLoading = false;
			}
		}
	};

	const addQueryData = async (newChatData) => {
		chatData.value.push({
			id: chatData.value.length + 1,
			isDefault: false,
			...newChatData,
		});

		recommendComponents.value = [];
		let topK = null;

		try {
			const response = await http.post(
				"/vector/component",
				new URLSearchParams({
					query: newChatData.content,
					limit: 10,
					score: 0.8,
				}),
				{
					headers: {
						"Content-Type": "application/x-www-form-urlencoded",
					},
				},
			);
			if (response.data?.data?.length > 0) {
				recommendComponents.value = response.data.data;
			}

			// 去除重複項目存到 result
			const result = Array.from(
				recommendComponents.value
					.reduce((map, item) => {
						const key = item.index;
						const exist = map.get(key);

						// 如果還沒放過，直接放
						if (!exist) {
							map.set(key, item);
							return map;
						}

						// 如果已存在，但現在的是 metrotaipei，就覆蓋
						if (item.city === "metrotaipei") {
							map.set(key, item);
						}

						return map;
					}, new Map())
					.values(),
			);
			// 把 result 蓋回去 recommendComponents
			recommendComponents.value = result;
		} catch (error) {
			console.error("VectorAnalysisError :", error);
		}

		if (
			recommendComponents.value &&
			recommendComponents.value?.length > 0
		) {
			topK = [...recommendComponents.value].sort(
				(a, b) => b.score - a.score,
			);
			chatData.value.push({
				id: chatData.value.length + 1,
				role: "bot",
				isDefault: false,
				button: [{ id: 1, text: "建立儀表板" }],
				content: `您好 😊 \n 以下是根據您的問題，自動為您推薦的「組件清單」。您可以將這些組件整批加入「個人儀表板」，方便日後快速查看與使用。\n`,
				relations: topK,
			});
			chatData.value.push({
				id: chatData.value.length + 1,
				role: "bot",
				isDefault: false,
				content: `若您有任何新的查詢或想深入探索的內容，都可以隨時在對話框告訴我～\n 我很樂意再協助您 💬✨`,
			});
		} else {
			chatData.value.push({
				id: chatData.value.length + 1,
				role: "bot",
				isDefault: false,
				content: `很抱歉，您提供的描述沒有相似組件，請繼續提問 ! `,
			});
		}

		// 分析結束後紀錄問答log
		saveChatLog(newChatData.content, recommendComponents.value);
	};

	const saveChatLog = async (question, answer) => {
		try {
			const formData = new FormData();
			const d = new Date();
			const todayId =
				d.getFullYear() +
				String(d.getMonth() + 1).padStart(2, "0") +
				String(d.getDate()).padStart(2, "0");

			formData.append("session", "session_" + todayId);
			formData.append("question", question);
			formData.append("answer", JSON.stringify(answer));

			await http.post("/chatlog/", formData, {
				headers: {
					"Content-Type": "multipart/form-data",
				},
			});
		} catch (error) {
			console.error("saveChatLog error:", error);
		}
	};

	return {
		chatData,
		addChatData,
		addQueryData,
		saveChatLog,
		sendChatMessage,
	};
});
