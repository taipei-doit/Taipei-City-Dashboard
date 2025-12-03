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
        	'您好，我是【臺北城市儀表板】小幫手，很高興為您服務 ! 您可以直接點擊左側儀表板主題或輸入您感興趣的主題描述，讓我為您推薦組件。',
    	},
  	];

  	// const defaultRes = [
	//     {
	//         "id": 60,
	//         "index": "youbike_availability",
	//         "name": "YouBike使用情況",
	//         "city": "metrotaipei",
	//         "score": 0.8453
	//     },
	//     {
	//         "id": 60,
	//         "index": "youbike_availability",
	//         "name": "YouBike使用情況",
	//         "city": "taipei",
	//         "score": 0.8445
	//     },
	//     {
	//         "id": 219,
	//         "index": "bike_map",
	//         "name": "自行車道路網圖資",
	//         "city": "taipei",
	//         "score": 0.8181
	//     },
	//     {
	//         "id": 114,
	//         "index": "public_parking_lots",
	//         "name": "公共停車場",
	//         "city": "taipei",
	//         "score": 0.8164
	//     },
	//     {
	//         "id": 284,
	//         "index": "test_componets",
	//         "name": "示範組件",
	//         "city": "taipei",
	//         "score": 0.8163
	//     },
	//     {
	//         "id": 213,
	//         "index": "bike_network",
	//         "name": "自行車道路統計資料",
	//         "city": "metrotaipei",
	//         "score": 0.8163
	//     },
	//     {
	//         "id": 219,
	//         "index": "bike_map",
	//         "name": "自行車道路網圖資",
	//         "city": "metrotaipei",
	//         "score": 0.8163
	//     },
	//     {
	//         "id": 213,
	//         "index": "bike_network",
	//         "name": "自行車道路統計資料",
	//         "city": "taipei",
	//         "score": 0.8158
	//     },
	//     {
	//         "id": 146,
	//         "index": "youbike_grid",
	//         "name": "YouBike設站狀態",
	//         "city": "taipei",
	//         "score": 0.8156
	//     },
	//     {
	//         "id": 212,
	//         "index": "ebus_percent",
	//         "name": "電動巴士比例",
	//         "city": "metrotaipei",
	//         "score": 0.8142
	//     }
	// ];

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

  	const addQueryData = async (newChatData) => {

    	chatData.value.push({ id: chatData.value.length + 1, isDefault: false, ...newChatData });
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
			if (response.data.data.length > 0) {
				recommendComponents.value = response.data.data;
			} else {
				chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: `很抱歉，您提供的描述未有相關組件 !` });
			}
		} catch (error) { 
			console.error("VectorAnalysisError :", error);
		}

		if (recommendComponents.value.length > 0) {
			topK = recommendComponents.value.sort((a, b) => b.score - a.score);
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, button: [{ id:1, text:'建立儀表板' }], content: `您好 😊 \n 以下是根據您的問題，自動為您推薦的「組件清單」。您可以將這些組件整批加入「個人儀表板」，方便日後快速查看與使用。\n`, relations: topK });
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: `若您有任何新的查詢或想深入探索的內容，都可以隨時在對話框告訴我～\n 我很樂意再協助您 💬✨` });
		} else {
			chatData.value.push({ id: chatData.value.length + 1, role: 'bot', isDefault: false, content: `很抱歉，您提供的描述未有相關組件 !` });
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
