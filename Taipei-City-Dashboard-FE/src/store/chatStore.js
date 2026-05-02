import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import http from "../router/axios";

export const useChatStore = defineStore('chat', () => {
	const AGENT_SESSION_KEY = 'agentSessionId';
	const agentSessionId = ref(sessionStorage.getItem(AGENT_SESSION_KEY) || '');
	const isAgentThinking = ref(false);

  	// 預設訊息
  	const defaultChatData = [
    	{
      		id: 1,
      		role: 'bot',
	  		isDefault: true,
      		content:
	        '您好，我是【臺北城市儀表板】小幫手 Agent，很高興為您服務！\n\n您可以直接用自然語言描述需求，例如：\n• 我想看臺北市高齡人口與醫療資源\n• 幫我找適合做交通壅塞觀測的組件\n\n我會先檢索相關資料，再提供建議與可建立的儀表板組件。',
    	},
  	];

	const recommendComponents = ref(null)

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

	const buildAgentHistory = () => {
		const validMessages = chatData.value
			.filter((item) => !item.isDefault && (item.role === 'user' || item.role === 'bot') && item.content)
			.map((item) => ({
				role: item.role === 'bot' ? 'assistant' : 'user',
				content: item.content,
			}));

		if (validMessages.length > 12) {
			return validMessages.slice(-12);
		}

		return validMessages;
	};

	const fallbackVectorSearch = async (newChatData) => {
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

			const result = Array.from(
				recommendComponents.value.reduce((map, item) => {
					const key = item.index;
					const exist = map.get(key);

					if (!exist) {
						map.set(key, item);
						return map;
					}

					if (item.city === 'metrotaipei') {
						map.set(key, item);
					}

					return map;
				}, new Map()).values()
			);

			recommendComponents.value = result;
		} catch (error) {
			console.error("VectorAnalysisError :", error);
		}

		if (recommendComponents.value && recommendComponents.value?.length > 0) {
			topK = [...recommendComponents.value].sort((a, b) => b.score - a.score);
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, button: [{ id:1, text:'建立儀表板' }], content: `我已先用向量檢索幫您找到相近組件，您可以直接建立推薦儀表板。`, relations: topK });
		} else {
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: `很抱歉，目前找不到相似組件，請換個描述方式再試一次。` });
		}
	};

	const removeMarkdownTables = (text) => {
		if (!text) return '';
		const tablePattern = /(?:\r?\n)?\|[^\n]*\|\r?\n\|[-:\s|]+\|\r?\n(?:\|[^\n]*\|\r?\n)*/g;
		return text
			.replaceAll(tablePattern, '\n')
			.replaceAll(/\n{3,}/g, '\n\n')
			.trim();
	};

	const synchronizeContentWithReferences = (content, references) => {
		if (!content || !Array.isArray(references) || references.length === 0) {
			return content || '';
		}

		const numberedListLines = references
			.map((item, index) => {
				const name = String(item?.name || '').trim();
				if (!name) return '';
				return `${index + 1}. ${name}`;
			})
			.filter(Boolean);

		if (numberedListLines.length === 0) {
			return content;
		}

		const lines = content.split('\n');
		const numberLinePattern = /^\s*\d+\.\s*.+\s*$/;
		const rebuilt = [];
		let inserted = false;

		for (const line of lines) {
			if (numberLinePattern.test(line.trim())) {
				if (!inserted) {
					rebuilt.push(...numberedListLines);
					inserted = true;
				}
				continue;
			}

			rebuilt.push(line);
		}

		if (!inserted) {
			return content;
		}

		return rebuilt.join('\n').replaceAll(/\n{3,}/g, '\n\n').trim();
	};

  	const addQueryData = async (newChatData) => {
		const historyBeforeSend = buildAgentHistory();

    	chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });
		recommendComponents.value = [];
		isAgentThinking.value = true;

		try {
			const response = await http.post("/ai/assistant/chat", {
				session: agentSessionId.value,
				message: newChatData.content,
				history: historyBeforeSend,
			});

			const data = response?.data?.data;
			if (data?.session) {
				agentSessionId.value = data.session;
				sessionStorage.setItem(AGENT_SESSION_KEY, data.session);
			}

			const cleanedContent = removeMarkdownTables(data?.content || '');
			const synchronizedContent = synchronizeContentWithReferences(cleanedContent, data?.references || []);
			if (synchronizedContent) {
				chatData.value.push({
					id: chatData.value.length + 1,
					role: 'bot',
					isDefault: false,
					content: synchronizedContent,
				});
			}

			if (Array.isArray(data?.references) && data.references.length > 0) {
				recommendComponents.value = data.references;
				chatData.value.push({
					id: chatData.value.length + 1,
					role: 'bot',
					isDefault: false,
					content: '',
					button: [{ id: 1, text: '建立儀表板' }],
					relations: data.references,
					showRelationTable: true,
				});
			} else if (!cleanedContent) {
				chatData.value.push({
					id: chatData.value.length + 1,
					role: 'bot',
					isDefault: false,
					content: data?.content || '目前沒有找到可用參考資料，請再描述一次需求。',
				});
			}

			saveChatLog(newChatData.content, {
				answer: synchronizedContent || '',
				references: data?.references || [],
				session: data?.session || agentSessionId.value,
			});
		} catch (error) {
			console.error("AgentChatError :", error);
			await fallbackVectorSearch(newChatData);
			saveChatLog(newChatData.content, recommendComponents.value || []);
		} finally {
			isAgentThinking.value = false;
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

	return { chatData, addChatData, addQueryData, saveChatLog, isAgentThinking }
})
