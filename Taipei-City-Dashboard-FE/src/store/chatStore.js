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
	// 當使用者啟動減碳計算機並等待輸入數據時，設為 true
	const awaitingCarbonInput = ref(false)
	const awaitingEnergySubsidyInput = ref(false)
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

  	const isCarbonRelatedInput = (content) => {
		return /走|步行|大眾運輸|公車|捷運|火車|蔬食|素食|省電|省水|自備餐具|減碳|碳排|碳|樹|大安森林公園|塑膠袋|腳踏車|單車|自行車/i.test(content);
	};
	const isEnergySubsidyRelated = (content) => {
		return /補助|節能|省電|申請|能源|節水|冷氣|冷房|太陽能|綠能|補助金|申請資格|條件|經費|額度|流程|步驟|辦理|核定|審核|補助對象/i.test(content);
	};
	const addQueryData = async (newChatData) => {
		// 如果正在等待使用者提供減碳數據，先判斷是否真的跟減碳有關
		if (awaitingCarbonInput.value) {
			chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });

			if (!isCarbonRelatedInput(newChatData.content)) {
				const reminder = '這個問題超出我的計算範圍囉 🙈\n如需重新開始計算，請點擊下方的「減碳計算機」按鈕來呼叫我！';
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: reminder });
				saveChatLog(newChatData.content, reminder);
				awaitingCarbonInput.value = false;
				return;
			}

			const payload = {
				session: "",
				stream: false,
				messages: [
					{ role: 'user', content: `你是一個減碳計算助手。請根據使用者的行為，合理估算出該行為的二氧化碳減碳量（公斤），並利用下方的「參考資料」，將最終的減碳量換算成大百科或樹木的吸碳當量。

參考資料（僅供比喻換算使用）：
- 1 棵成年樹 / 天 = 0.02 kg
- 1 座大安森林公園 / 日 = 1052 kg
- 1 座大安森林公園 / 年 = 384000 kg

使用者提供：${newChatData.content}

如果輸入內容與減碳無關，才提醒使用者這題無關。只要是走路、大眾運輸、吃素、省水電、減少塑膠袋等有關行為，請你直接利用常理知識「主動估算」減碳量！
請先解析每個行為的減碳量，再加總成總計，全部只用 kg。
回覆格式請包含：
0. 開頭先用自然、活潑、有人味的口吻暖場，像是「太棒了！我幫你整理出來了～」或「很不錯，你今天已經為地球做了不少事！」，不要直接冷冰冰地進入條列。
1. 每項減碳結果，格式為「項目：數量 -> 減碳約 X kg」（請你自行帶入合理係數計算，係數不必寫在回覆裡）
2. 總計，格式為「總計：X kg」
3. 根據總減碳量選擇最合適的比喻：
   - 日常小量減碳，使用「X / 0.02 = 幾棵樹 / 天」，無條件進位到整數，回覆例句如「你今天節省了 1 kg 碳排，這相當於 50 棵樹一整天的吸碳量喔！」
   - 個人年度累積，使用「X / 1052 = 大安森林公園工作天數」，回覆可換算成小時，例句如「你這一年共減碳 500 kg，相當於大安森林公園幫地球工作了 11.4 小時！」
   - 企業或大型活動，使用「X / 384000 = 幾座大安森林公園 / 年」，回覆例句如「本次活動減碳 38400 kg，相當於 0.1 座大安森林公園一年的吸碳量！」
4. 回覆語氣要活潑、鼓勵、繁體中文，並在最後再補一句自然的總結。
` },
				],
			};
			try {
				const resp = await http.post('/ai/chat/twai', payload);
				console.log('API response:', JSON.stringify(resp.data));
				const botContent = resp?.data?.data?.content || '抱歉，我暫時無法計算，請稍後再試。';
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: botContent });
				saveChatLog(newChatData.content, botContent);
			} catch (err) {
				console.error('AI carbon calculation error:', err);
				const reply = '抱歉，計算服務暫時有問題，請稍後再試或提供更完整的資料。';
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: reply });
				saveChatLog(newChatData.content, reply);
			}
			// 處理完畢，重置等待狀態
			awaitingCarbonInput.value = false;
			return;
		}
		if (newChatData.content === '減碳計算機') {
			// push the user query first
			chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });
			// 回覆固定歡迎詞（不呼叫 AI）
			const welcome = `嗨！我是你的 🌍 減碳小幫手！
 
 
 每一個小行動都在為地球加分——不管是今天走路去買咖啡，還是選擇了一餐蔬食，都值得被記錄下來 ✨
 
 請告訴我你今天完成了哪些項目（可以多選）：
 
 - 🚶 走路：XX 步
 - 🚌 大眾運輸：XX 公里
 - 🥗 蔬食餐：XX 餐
 - 💧 省水：XX 公升
 - 🛍️ 少用塑膠袋：XX 個
 
 直接輸入數字或簡單描述就好，我來幫你估算今天的碳減量！
`;
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: welcome });
			saveChatLog(newChatData.content, welcome);
			// 等待使用者提供實際數據以便計算
			awaitingCarbonInput.value = true;
			return;
		}
		// 如果正在等待使用者提供能源補助相關問題
		if (awaitingEnergySubsidyInput.value) {
			chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });

			if (!isEnergySubsidyRelated(newChatData.content)) {
				const reminder = '這個問題超出我的知識範圍囉！若要繼續查補助，請再次點「能源補助顧問」🙌';
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: reminder });
				saveChatLog(newChatData.content, reminder);
				awaitingEnergySubsidyInput.value = false;
				return;
			}

			const payload = {
				session: "",
				stream: false,
				messages: [
					{ role: 'user', content: `你是親切的能源補助顧問。請務必使用查詢工具取得知識庫的資料後，給出包含「具體金額」與「條件」的繁體中文純文字答案。

使用者問題：${newChatData.content}

請遵循以下回覆格式與原則：
1. 先給出親切簡短的開頭（例如：以下是相關資訊：）
2. 接著請一律使用數字 (1. 2. 3.) 列點呈現重點。
3. 內容務必包含「具體金額（如：最高補助 10,000 元）」，嚴禁給出「視地區而定」或「請查詢官網」這種籠統且無實際幫助的話。
4. 絕對禁止使用任何 Markdown 語法（例如不要用星號產生粗體），請全部輸出純文字。` },
				],
			};
			try {
				const resp = await http.post('/ai/chat/twai', payload);
				console.log('Subsidy API response:', resp.data);
				const botContent = resp?.data?.data?.content || resp?.data?.content || '抱歉，我暫時無法查詢，請稍後再試。';
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: botContent });
				saveChatLog(newChatData.content, botContent);

				// --- 根據關鍵字觸發第二則推薦圖表訊息 ---
				const contentStr = newChatData.content || "";
				if (/電動機車|電動車|充電|機車|車/i.test(contentStr)) {
					const recommendEV = "💡 延伸推薦：若你對電動車發展有興趣，可以參考「永續環境」主題中的【電動車充電站分布】與【新領牌車輛】圖表，一起了解電動車的普及與配套現況！";
					setTimeout(() => {
						chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: recommendEV });
						saveChatLog(newChatData.content, recommendEV);
					}, 500); // 稍微延遲 0.5 秒發送，感覺更自然
				} else if (/太陽能|太陽光電|太陽/i.test(contentStr)) {
					const recommendSolar = "💡 延伸推薦：想進一步了解太陽光電的發展趨勢？可以參考「永續環境」主題中的【再生能源裝置容量】圖表！";
					setTimeout(() => {
						chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: recommendSolar });
						saveChatLog(newChatData.content, recommendSolar);
					}, 500);
				}

			} catch (err) {
				console.error('AI energy subsidy error:', err);
				const reply = '抱歉，查詢服務暫時有問題，請稍後再試。';
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: reply });
				saveChatLog(newChatData.content, reply);
			}
			return;
		}

		if (newChatData.content === '能源補助顧問') {
			chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });
			const welcome = `⚡ 能源補助顧問已啟動！

請直接問我補助相關問題，例如：有哪些補助可以申請、申請資格、流程、補助額度等。只要話題還在補助上，我就會一直留在這個模式。`;
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: welcome });
			saveChatLog(newChatData.content, welcome);
			awaitingEnergySubsidyInput.value = true;
			return;
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

	return { chatData, addChatData, addQueryData, saveChatLog }
})
