import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import http from "../router/axios";

export const useChatStore = defineStore('chat', () => {
  	// 預設訊息
  	const defaultChatData = [
    	{
      		id: 1,
      		role: 'bot',
	  		isDefault: true,
      		content:
        	'您好，我是【臺北城市儀表板】小幫手，很高興為您服務！\n 您可以： \n\n • 點擊左側既有的儀表板主題，快速查看各主題內容 \n • 輸入您感興趣的主題描述，我會自動為您組建最適合的儀表板 \n\n 如果有想了解的內容，歡迎直接告訴我，我會盡力協助！\n\n 📩 聯絡信箱：tuic@gov.taipei \n 🏢 臺北大數據中心 \n\n',
    	},
  	];

	const recommendComponents = ref(null)
	const isChatLoading = ref(false)

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

	const getSessionId = () => {
		const d = new Date();
		return "session_" +
			d.getFullYear() +
			String(d.getMonth() + 1).padStart(2, "0") +
			String(d.getDate()).padStart(2, "0");
	};

	const requestTWCCAnswer = async (question, componentContext = "") => {
		const response = await http.post("/ai/chat/twcc", {
			session: getSessionId(),
			stream: false,
			messages: [
				{
					role: "system",
					content:
						`你是「臺北城市儀表板」的專屬 AI 小幫手。你的任務是協助使用者理解臺北市的指標數據，並引導其使用儀表板的「組件（Components）」。

請嚴格遵循以下回答準則：
1. **僅限本站範圍**：僅回答與臺北城市資料、公共服務、及儀表板組件相關的問題。若問題超出此範圍，請禮貌地告知你只能提供儀表板相關資訊。
2. **禁止虛構與延伸**：不可虛構本站不存在的數據、功能或政府服務。若無法從已知資訊確認事實，請說明限制並建議使用者「參考下方推薦的組件清單以獲得準確數據」。
3. **組件導向**：本系統會自動檢索組件資料庫。請在回答中適時提及：「您可以參考下方自動推薦的組件清單，點擊『建立儀表板』來查看即時數據內容。」
4. **精簡回覆**：回答要清楚、友善、且盡可能精簡，避免冗長的背景解釋。
5. **語言風格**：使用繁體中文（台灣習慣用語）。${componentContext}`,
				},
				{
					role: "user",
					content: question,
				},
			],
			max_new_tokens: 700,
			temperature: 0.1,
			top_k: 50,
			top_p: 0.9,
			frequence_penalty: 1.05,
		});

		return response.data?.data?.content;
	};

	const requestRecommendComponents = async (question) => {
		const response = await http.post(
			"/vector/component",
			new URLSearchParams({
				query: question,
				limit: 10,
				score: 0.8,
			}),
			{
				headers: {
					"Content-Type": "application/x-www-form-urlencoded",
				},
			}
		);

		const components = response.data?.data?.length > 0 ? response.data.data : [];

		return Array.from(
			components.reduce((map, item) => {
				const key = item.index
				const exist = map.get(key)

				if (!exist) {
					map.set(key, item)
					return map
				}

				if (item.city === 'metrotaipei') {
					map.set(key, item)
				}

				return map
			}, new Map()).values()
		)
	};

  	const addQueryData = async (newChatData) => {
		if (isChatLoading.value) return;
		isChatLoading.value = true;

    	chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });

		recommendComponents.value = [];
		let topK = null;

		try {
			// 1. 先檢索相關組件 (RAG 第一步)
			let components = [];
			try {
				components = await requestRecommendComponents(newChatData.content);
			} catch (err) {
				console.error("VectorAnalysisError :", err);
			}
			recommendComponents.value = components;

			// 2. 準備 Context 餵給 AI
			const componentContext = components.length > 0 
				? `\n\n【目前系統檢索到的相關組件列表】：\n${components.map((c, i) => `${i+1}. ${c.name} (${c.city === 'taipei' ? '臺北市' : '新北市'})`).join('\n')}`
				: "\n\n【目前系統未在資料庫中檢索到直接相關的組件】。";

			// 3. 請求 AI 回答
			let aiContent = "";
			try {
				aiContent = await requestTWCCAnswer(newChatData.content, componentContext);
			} catch (err) {
				console.error("TWCCChatError :", err);
			}

			// 顯示 AI 回覆
			if (aiContent) {
				chatData.value.push({
					id: chatData.value.length + 1,
					role: 'bot',
					isDefault: false,
					content: aiContent,
				});
			} else {
				chatData.value.push({
					id: chatData.value.length + 1,
					role: 'bot',
					isDefault: false,
					content: "AI 回覆服務暫時無法使用，但我仍會嘗試為您推薦相關組件。",
				});
			}

			// 顯示推薦組件清單
			if (recommendComponents.value && recommendComponents.value?.length > 0) {
				topK = [...recommendComponents.value].sort((a, b) => b.score - a.score);
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, button: [{ id:1, text:'建立儀表板' }], content: `以下是根據您的問題，自動為您推薦的「組件清單」。您可以將這些組件整批加入「個人儀表板」，方便日後快速查看與使用。\n`, relations: topK });
			} else if (components.length === 0) {
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: `目前沒有找到相似組件，您可以換個描述再試一次。` });
			}

			// 分析結束後紀錄推薦結果；AI 問答由後端 ai_chatlog 紀錄
			saveChatLog(newChatData.content, recommendComponents.value);
		} finally {
			isChatLoading.value = false;
		}
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

	return { chatData, isChatLoading, addChatData, addQueryData, saveChatLog }
})
