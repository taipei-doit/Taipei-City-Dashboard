import { ref, watch } from "vue";
import { defineStore, storeToRefs } from "pinia";
import http from "../router/axios";
import { useAuthStore } from "./authStore";

export const useChatStore = defineStore("chat", () => {
	const authStore = useAuthStore();
	const { user } = storeToRefs(authStore);

	// 預設訊息
	const defaultChatData = [
		{
			id: 1,
			role: "bot",
			isDefault: true,
			content:
				"您好，我是【臺北城市儀表板】小幫手，很高興為您服務！\n 您可以： \n\n • 點擊左側既有的儀表板主題，快速查看各主題內容 \n • 輸入您感興趣的主題描述，我會推薦相關組件，並協助組建最適合的儀表板 \n • 點擊推薦組件清單中的主題按鈕，即可前往查看該主題儀表板  \n\n 如果有想了解的內容，歡迎直接告訴我，我會盡力協助！\n\n 📩 聯絡信箱：tuic@gov.taipei \n 🏢 臺北大數據中心 \n\n",
		},
	];

	const recommendComponents = ref(null);

	// 儲存組件對應主題
	const compToDashIndexMap = ref({});

	// 近一月對話列表與目前開啟的對話
	const chatSessionList = ref([]);
	const activeChatSession = ref(
		sessionStorage.getItem("activeChatSession") || null,
	);

	// 從 sessionStorage 讀取
	const savedChatData = JSON.parse(sessionStorage.getItem("chatData")) || [];

	// 拼接預設訊息 + sessionStorage 的聊天紀錄
	const chatData = ref([...defaultChatData, ...savedChatData]);

	const unescapeHtml = (value) =>
		String(value)
			.replace(/&#34;/g, '"')
			.replace(/&#39;/g, "'")
			.replace(/&lt;/g, "<")
			.replace(/&gt;/g, ">")
			.replace(/&amp;/g, "&");

	const decodeAnswer = (answer) => {
		const raw = unescapeHtml(answer);
		const text = raw.trim();
		const isJsonText =
			(text.startsWith("[") && text.endsWith("]")) ||
			(text.startsWith("{") && text.endsWith("}")) ||
			(text.startsWith('"') && text.endsWith('"'));

		if (!isJsonText) {
			return { kind: "string", value: raw };
		}

		try {
			return { kind: "json", value: JSON.parse(text) };
		} catch {
			return { kind: "string", value: raw };
		}
	};

	const applyDashboardMap = (compList, dashMap) => {
		compList.forEach((comp) => {
			const matched = [];

			Object.entries(dashMap).forEach(([city, cityDashboards]) => {
				cityDashboards.forEach((dash) => {
					if (dash.components.includes(comp.id)) {
						// 避免同名主題重複加入
						if (
							!matched.some(
								(item) =>
									item.index === dash.index &&
									item.city === city,
							)
						) {
							matched.push({
								name: dash.name,
								index: dash.index,
								city: city,
							});
						}
					}
				});
			});

			compToDashIndexMap.value[comp.id] = matched;
		});
	};

	const mapComponentsToDashboards = async (compList) => {
		if (!compList?.length) return;

		try {
			const dashboards = await http.get(`/dashboard/`);
			applyDashboardMap(compList, dashboards.data.data);
		} catch (error) {
			console.error("mapComponentsToDashboards error:", error);
		}
	};

	// 初始化時重建 compToDashIndexMap
	const rebuildCompToDashIndexMap = async () => {
		const allComps = savedChatData.flatMap((msg) => msg.relations || []);
		await mapComponentsToDashboards(allComps);
	};

	// 有舊資料才重建
	if (savedChatData.length > 0) {
		rebuildCompToDashIndexMap();
	}

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

	watch(activeChatSession, (session) => {
		if (session) {
			sessionStorage.setItem("activeChatSession", session);
		} else {
			sessionStorage.removeItem("activeChatSession");
		}
	});

	const addChatData = (newChatData) => {
		chatData.value.push({
			id: chatData.value.length + 1,
			isDefault: false,
			...newChatData,
		});
	};

	// 取得近一月對話列表
	const getChatSessionList = async () => {
		try {
			const response = await http.get("/chatlog/session");
			const sessionListRaw = response.data?.data || [];
			const oneMonthAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;

			chatSessionList.value = sessionListRaw
				.filter(
					(item) =>
						new Date(item.created_at).getTime() >= oneMonthAgo,
				)
				.sort(
					(a, b) =>
						new Date(b.created_at).getTime() -
						new Date(a.created_at).getTime(),
				);
		} catch (error) {
			console.error("getChatSessionList error:", error);
		}
	};

	// 取得指定對話的訊息，並還原成目前聊天內容
	const getChatSessionDetail = async (sessionName) => {
		try {
			const response = await http.get(
				`/chatlog/session/${sessionName}`,
			);
			const logs = [...(response.data?.data || [])].sort(
				(a, b) =>
					new Date(a.created_at) - new Date(b.created_at) ||
					a.id - b.id,
			);

			chatData.value = [...defaultChatData];
			const components = [];

			logs.forEach((item) => {
				if (item.question) {
					addChatData({
						role: "user",
						content: unescapeHtml(item.question),
					});
				}

				if (
					!item.answer ||
					item.answer === "null" ||
					item.answer === "[]"
				) {
					return;
				}

				const decoded = decodeAnswer(item.answer);
				const answerText =
					decoded.kind === "string" || typeof decoded.value === "string"
						? decoded.value
						: "";

				if (answerText) {
					if (item.question === "建立儀表板") {
						addChatData({
							role: "bot",
							content: answerText,
						});
					}
					return;
				}

				if (
					decoded.kind === "json" &&
					Array.isArray(decoded.value) &&
					decoded.value.length > 0
				) {
					const relations = [...decoded.value].sort(
						(a, b) => b.score - a.score,
					);
					components.push(...relations);
					addChatData({
						role: "bot",
						button: [{ id: 1, text: "建立儀表板" }],
						content:
							"您好 😊 \n 以下是根據您的問題，自動為您推薦的「組件清單」。您可以將這些組件整批加入「個人儀表板」，方便日後快速查看與使用。\n",
						relations,
					});
				}
			});

			if (components.length > 0) {
				await mapComponentsToDashboards(components);
			}
		} catch (error) {
			console.error("getChatSessionDetail error:", error);
		}
	};

	const openChatSession = async (session) => {
		activeChatSession.value = session;
		if (!session) {
			chatData.value = [...defaultChatData];
			return;
		}
		await getChatSessionDetail(session);
	};

	const findJsonValueEnd = (text, start) => {
		let depth = 0;
		let inString = false;
		let escaped = false;

		for (let i = start; i < text.length; i++) {
			const ch = text[i];
			if (inString) {
				if (escaped) {
					escaped = false;
				} else if (ch === "\\") {
					escaped = true;
				} else if (ch === '"') {
					inString = false;
				}
				continue;
			}
			if (ch === '"') {
				inString = true;
			} else if (ch === "{" || ch === "[") {
				depth += 1;
			} else if (ch === "}" || ch === "]") {
				depth -= 1;
				if (depth === 0) {
					return i + 1;
				}
			}
		}
		return -1;
	};

	// 只取出 data 陣列裡已經收完的物件，後半段還沒到齊的 JSON 先略過。
	const parsePartialVectorData = (input) => {
		const marker = '"data":';
		const markerAt = input.indexOf(marker);
		if (markerAt < 0) {
			return [];
		}

		let index = markerAt + marker.length;
		while (index < input.length && /\s/.test(input[index])) {
			index += 1;
		}
		if (input[index] !== "[") {
			return [];
		}
		index += 1;

		const items = [];
		while (index < input.length) {
			while (index < input.length && /[\s,]/.test(input[index])) {
				index += 1;
			}
			if (index >= input.length || input[index] === "]") {
				break;
			}
			if (input[index] !== "{") {
				break;
			}
			const end = findJsonValueEnd(input, index);
			if (end < 0) {
				break;
			}
			try {
				items.push(JSON.parse(input.slice(index, end)));
			} catch {
				break;
			}
			index = end;
		}
		return items;
	};

	const dedupeComponents = (list) =>
		Array.from(
			(list || [])
				.reduce((map, item) => {
					const key = item.index;
					const exist = map.get(key);
					if (!exist || item.city === "metrotaipei") {
						map.set(key, item);
					}
					return map;
				}, new Map())
				.values(),
		);

	const readVectorStream = async (response, onItems) => {
		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let pending = "";
		let jsonBuffer = "";

		const consumeBlock = (block) => {
			block.split("\n").forEach((line) => {
				if (!line.startsWith("data:")) {
					return;
				}
				const data = line.slice(5).trimStart();
				if (!data || data === "[DONE]") {
					return;
				}
				jsonBuffer += data;
				onItems(parsePartialVectorData(jsonBuffer));
			});
		};

		while (true) {
			const { value, done } = await reader.read();
			if (done) {
				break;
			}
			pending += decoder.decode(value, { stream: true });
			const parts = pending.split("\n\n");
			pending = parts.pop() ?? "";
			parts.forEach(consumeBlock);
		}
		pending += decoder.decode();
		if (pending) {
			consumeBlock(pending);
		}
		return parsePartialVectorData(jsonBuffer);
	};

	const addQueryData = async (newChatData) => {
		chatData.value.push({
			id: chatData.value.length + 1,
			isDefault: false,
			...newChatData,
		});

		recommendComponents.value = [];
		const sessionName = resolveSessionName();
		let listMessageIndex = -1;
		let dashMap = null;

		const publishList = (list) => {
			const result = dedupeComponents(list).sort(
				(a, b) => b.score - a.score,
			);
			recommendComponents.value = result;
			if (dashMap && result.length) {
				applyDashboardMap(result, dashMap);
			}
			if (!result.length) {
				return;
			}
			if (listMessageIndex < 0) {
				listMessageIndex = chatData.value.length;
				chatData.value.push({
					id: chatData.value.length + 1,
					role: "bot",
					isDefault: false,
					button: [{ id: 1, text: "建立儀表板" }],
					content: `您好 😊 \n 以下是根據您的問題，自動為您推薦的「組件清單」。您可以將這些組件整批加入「個人儀表板」，方便日後快速查看與使用。\n`,
					relations: result,
				});
				return;
			}
			chatData.value[listMessageIndex].relations = result;
		};

		try {
			const dashboardsPromise = http
				.get(`/dashboard/`)
				.then((dashboards) => {
					dashMap = dashboards.data.data;
					if (recommendComponents.value?.length) {
						applyDashboardMap(recommendComponents.value, dashMap);
					}
				})
				.catch((error) => {
					console.error("mapComponentsToDashboards error:", error);
				});
			const base = String(import.meta.env.VITE_API_URL || "").replace(
				/\/$/,
				"",
			);
			const response = await fetch(`${base}/vector/component/stream`, {
				method: "POST",
				headers: {
					"Content-Type": "application/x-www-form-urlencoded",
					Authorization: authStore.token
						? `Bearer ${authStore.token}`
						: "Bearer",
				},
				body: new URLSearchParams({
					query: newChatData.content,
					limit: 10,
					score: 0.8,
					session: sessionName,
				}),
			});

			if (!response.ok) {
				throw new Error(`vector stream failed: ${response.status}`);
			}
			if (!activeChatSession.value) {
				activeChatSession.value = sessionName;
			}

			await readVectorStream(response, publishList);
			await dashboardsPromise;
		} catch (error) {
			console.error("VectorAnalysisError :", error);
		}

		if (recommendComponents.value?.length > 0) {
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

		// 問答紀錄由 /vector/component/stream 在後端寫入，這裡只更新近一月對話列表
		if (user.value?.user_id) {
			await getChatSessionList();
		}
	};

	const resolveSessionName = () => {
		const d = new Date();
		const todayId =
			d.getFullYear() +
			String(d.getMonth() + 1).padStart(2, "0") +
			String(d.getDate()).padStart(2, "0");
		return activeChatSession.value || `session_${todayId}`;
	};

	const saveChatLog = async (question, answer) => {
		try {
			const formData = new FormData();
			const sessionName = resolveSessionName();

			formData.append("session", sessionName);
			formData.append("question", question);
			formData.append("answer", answer);

			await http.post("/chatlog/", formData, {
				headers: {
					"Content-Type": "multipart/form-data",
				},
			});

			if (!activeChatSession.value) {
				activeChatSession.value = sessionName;
			}
		} catch (error) {
			console.error("saveChatLog error:", error);
		}
	};

	return {
		chatData,
		compToDashIndexMap,
		chatSessionList,
		activeChatSession,
		addChatData,
		addQueryData,
		saveChatLog,
		getChatSessionList,
		openChatSession,
	};
});
