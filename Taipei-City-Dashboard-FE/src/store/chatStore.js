import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import http from "../router/axios";

// ---------------------------------------------------------------
// RAG tool definition – sent to the backend so the LLM knows it
// can call search_policy_knowledge during the conversation.
// ---------------------------------------------------------------
const ragToolDefinition = {
	type: "function",
	function: {
		name: "search_policy_knowledge",
		description: "搜尋環保節能政策知識庫。當用戶詢問關於節能家電補助、貨物稅退稅、太陽光電補助、環保補助等政策問題時使用此工具。",
		parameters: {
			type: "object",
			properties: {
				query: {
					type: "string",
					description: "用於搜尋知識庫的查詢字串，應包含用戶問題的關鍵概念"
				}
			},
			required: ["query"]
		}
	}
};

// Keywords that indicate the user is asking about policy/subsidy topics
const policyKeywords = [
	"補助", "退稅", "貨物稅", "節能", "省電", "太陽能", "太陽光電",
	"光電", "電冰箱", "冷氣", "除濕機", "家電", "環保", "綠能",
	"再生能源", "申請", "減徵", "退還", "能源效率", "節電",
	"汰換", "碳", "淨零", "solar", "subsidy", "rebate", "refund"
];

/**
 * Detect whether a user message is about policy/subsidy topics
 * that should be routed through the AI RAG pipeline.
 */
function isPolicyQuery(text) {
	const lower = text.toLowerCase();
	return policyKeywords.some(kw => lower.includes(kw));
}

export const useChatStore = defineStore('chat', () => {
  	// 預設訊息
  	const defaultChatData = [
    	{
      		id: 1,
      		role: 'bot',
	  		isDefault: true,
      		content:
        	'您好，我是【臺北城市儀表板】小幫手，很高興為您服務！\n 您可以： \n\n • 點擊左側既有的儀表板主題，快速查看各主題內容 \n • 輸入您感興趣的主題描述，我會自動為您組建最適合的儀表板 \n • 詢問節能補助、太陽光電、家電退稅等環保政策問題 \n\n 如果有想了解的內容，歡迎直接告訴我，我會盡力協助！\n\n 📩 聯絡信箱：tuic@gov.taipei \n 🏢 臺北大數據中心 \n\n',
    	},
  	];

	const recommendComponents = ref(null)
	// AI conversation history for RAG sessions (per browser session)
	const aiSessionId = ref(null)
	const aiMessages = ref([])

  	// 從 sessionStorage 讀取
  	const savedChatData = JSON.parse(sessionStorage.getItem('chatData')) || [];

  	// 拼接預設訊息 + sessionStorage 的聊天紀錄
  	const chatData = ref([...defaultChatData, ...savedChatData]);

  	// 監聽 chatData 的變化，自動同步到 sessionStorage
  	watch(
    	chatData,
    	(newVal) => {
      	// 只存使用者與機器人的聊天訊息，不存重複的預設訊息
      	const userBotMessages = newVal.filter((item) => !item.isDefault)
      	sessionStorage.setItem('chatData', JSON.stringify(userBotMessages))
    	},
    	{ deep: true }
  	);

  	const addChatData = (newChatData) => {
    	chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });
  	};

	// ---------------------------------------------------------------
	// AI RAG Query – routes through /ai/chat/twai with tool calling
	// ---------------------------------------------------------------
	const addAIQueryData = async (newChatData) => {
		chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });

		// Show a thinking indicator
		const thinkingId = chatData.value.length + 1;
		chatData.value.push({ id: thinkingId, role: 'bot', isDefault: false, content: '正在查詢政策知識庫，請稍候...',  isLoading: true });

		try {
			// Build conversation messages for the AI
			const messages = [
				{
					role: "system",
					content: "你是臺北城市儀表板的環保政策助手。當用戶詢問關於節能補助、家電退稅、太陽光電補助等環保政策問題時，請使用 search_policy_knowledge 工具搜尋知識庫，並根據檢索到的資料回答問題。回答時請引用具體的政策內容，包含補助金額、申請條件、申請方式等細節。若知識庫中找不到相關資訊，請誠實告知用戶。請用繁體中文回答。"
				},
				{
					role: "user",
					content: newChatData.content
				}
			];

			const payload = {
				session: aiSessionId.value || undefined,
				stream: false,
				messages: messages,
				tools: [ragToolDefinition],
				tool_choice: "auto",
				temperature: 0.3,
				max_new_tokens: 1024
			};

			const response = await http.post("/ai/chat/twai", payload);

			// Remove thinking indicator
			const thinkingIndex = chatData.value.findIndex(item => item.id === thinkingId);
			if (thinkingIndex !== -1) {
				chatData.value.splice(thinkingIndex, 1);
			}

			if (response.data?.status === "success" && response.data?.data?.content) {
				// Store session ID for potential multi-turn conversations
				if (response.data.data.session) {
					aiSessionId.value = response.data.data.session;
				}

				chatData.value.push({
					id: chatData.value.length + 1,
					role: 'bot',
					isDefault: false,
					content: response.data.data.content,
					isAIResponse: true,
					toolUsed: response.data.data.tool_used || false
				});
			} else {
				chatData.value.push({
					id: chatData.value.length + 1,
					role: 'bot',
					isDefault: false,
					content: '很抱歉，AI 助手目前無法回應，請稍後再試。'
				});
			}

			// Log the conversation
			saveChatLog(newChatData.content, response.data?.data?.content || "AI error");

		} catch (error) {
			console.error("AIQueryError:", error);

			// Remove thinking indicator on error
			const thinkingIndex = chatData.value.findIndex(item => item.id === thinkingId);
			if (thinkingIndex !== -1) {
				chatData.value.splice(thinkingIndex, 1);
			}

			chatData.value.push({
				id: chatData.value.length + 1,
				role: 'bot',
				isDefault: false,
				content: '很抱歉，查詢政策資訊時發生錯誤，請稍後再試。'
			});
		}
	};

	// ---------------------------------------------------------------
	// Component Vector Search – original flow (unchanged)
	// ---------------------------------------------------------------
  	const addQueryData = async (newChatData) => {

		// Route to AI RAG if the query is about policy/subsidy topics
		if (isPolicyQuery(newChatData.content)) {
			return addAIQueryData(newChatData);
		}

    	chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });

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
  				}
			);
			if (response.data?.data?.length > 0) {
				recommendComponents.value = response.data.data;
			}

			// 去除重複項目存到 result
			const result = Array.from(
  				recommendComponents.value.reduce((map, item) => {
    				const key = item.index
    				const exist = map.get(key)

    				// 如果還沒放過，直接放
    				if (!exist) {
      					map.set(key, item)
      					return map
    				}

    				// 如果已存在，但現在的是 metrotaipei，就覆蓋
    				if (item.city === 'metrotaipei') {
      					map.set(key, item)
    				}

    				return map
  				}, new Map()).values()
			)
			// 把 result 蓋回去 recommendComponents
			recommendComponents.value = result

		} catch (error) {
			console.error("VectorAnalysisError :", error);
		}

		if (recommendComponents.value && recommendComponents.value?.length > 0) {
			topK = [...recommendComponents.value].sort((a, b) => b.score - a.score);
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, button: [{ id:1, text:'建立儀表板' }], content: `您好 😊 \n 以下是根據您的問題，自動為您推薦的「組件清單」。您可以將這些組件整批加入「個人儀表板」，方便日後快速查看與使用。\n`, relations: topK });
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: `若您有任何新的查詢或想深入探索的內容，都可以隨時在對話框告訴我～\n 我很樂意再協助您 💬✨` });
		} else {
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: `很抱歉，您提供的描述沒有相似組件，請繼續提問 ! ` });
		}

		// 分析結束後紀錄問答log
		saveChatLog(newChatData.content, recommendComponents.value);
  	};

	const saveChatLog = async(question, answer) => {
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

	return { chatData, addChatData, addQueryData, addAIQueryData, saveChatLog }
})
