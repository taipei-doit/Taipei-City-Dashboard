<script setup>
import { ref, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import SendIcon from '../icons/SendIcon.vue'
import BotLogo from '../icons/BotLogo.vue'
import UserLogo from '../icons/UserLogo.vue'

import { useChatStore } from '../../store/chat'
import { useContentStore } from "../../store/contentStore";
import { useAuthStore } from "../../store/authStore";

const chatStore = useChatStore()
const contentStore = useContentStore();
const authStore = useAuthStore();
const { addChatData, addQueryData } = chatStore
const { createDashboard } = contentStore;
const { chatData } = storeToRefs(chatStore)
const { editDashboard } = storeToRefs(contentStore);
const { user } = storeToRefs(authStore);

const userMessage = ref('')
const chatAreaRef = ref(null)

const qaBtnHandler = async(text,relations) => {
	if(text==='建立儀表板') {
		const components = Array.from(
  			new Set(relations.map(r => r.id))
		).map(id => ({ id }));

    	if (user.value.user_id ) {
			editDashboard.value = {
				index: "",
				name: "推薦儀表板",
				icon: "star",
				components: components
			}
			createDashboard();
		} else {
			addChatData({
    			role: 'bot',
    			content: '請先登入會員以使用此功能喔！',
  			})
		}
	}
}

const sendBtnHandler = (text) => {
	if (!text.trim()) return
	addQueryData({
		role: 'user',
		content: text,
	})
	userMessage.value = ''
}

watch(
	() => chatData.value.length,
	async () => {
		await nextTick()
		const chat = chatAreaRef.value
		if (!chat) return
		chat.scrollTop = chat.scrollHeight - chat.clientHeight
	},
	{ deep: true },
)
</script>

<template>
  <div class="chat-widget">
    <!-- 標題 -->
    <div class="header">
      <h3>臺北城市儀表板小幫手</h3>
    </div>

    <!-- 聊天區 -->
    <div
      ref="chatAreaRef"
      class="chat-area scrollbar-custom"
    >
      <div
        v-for="chat in chatData"
        :key="chat.id"
        class="message"
      >
        <!-- 機器人訊息 -->
        <div
          v-if="chat.role === 'bot'"
          class="bot"
        >
          <div class="avatar">
            <BotLogo />
          </div>
          <div class="content">
            <div
              v-if="chat.content"
              class="message--bubble"
            >
              <p>{{ chat.content }}</p>
              <!-- 表格區 -->
              <div
                v-if="chat.relations"
                class="relation-area"
              >
                <table class="relation-table">
                  <thead>
                    <tr>
                      <th>排名</th>
                      <th>城市名</th>
                      <th>組件名</th>
                      <th>關聯性</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(item, index) in chat.relations"
                      :key="index"
                    >
                      <td>{{ index + 1 }}</td>
                      <td>{{ item.city === 'taipei' ? '臺北' : '雙北' }}</td>
                      <td>{{ item.name }}</td>
                      <td>{{ item.score }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div
              v-if="chat.button"
              v-horizontal-wheel
              class="message--button scrollbar-x-hide"
            >
              <button
                v-for="(btn) in chat.button"
                :key="btn.id"
                @click="qaBtnHandler(btn.text,chat.relations)"
              >
                {{ btn.text }}
              </button>
            </div>
          </div>
        </div>
        <!-- 使用者訊息 -->
        <div
          v-else
          class="user"
        >
          <div class="avatar">
            <UserLogo />
          </div>
          <div
            v-if="chat.content"
            class="content"
          >
            <div class="message--bubble">
              <p>{{ chat.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 輸入區 -->
    <div class="input-area">
      <input
        v-model="userMessage"
        type="text"
        placeholder="輸入訊息..."
        @keyup.enter="sendBtnHandler(userMessage)"
      >
      <button @click="sendBtnHandler(userMessage)">
        <SendIcon />
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
/* === 變數設定 === */
$bg-dark: #090909;
$panel-bg: #494B4E;
$card-bg: #282A2C;
$border-color: #888787;
$input-bg: #D9D9D9;
$white: #ffffff;
$scroll-thumb-hover: #ababab;
$radius-10: 10px;
$radius-15: 15px;
$radius-20: 20px;

/* === Scrollbar === */
.scrollbar-x-hide {
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
}

.scrollbar-custom {
  &::-webkit-scrollbar {
    width: 2px;
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: $white;
    border-radius: 8px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: $scroll-thumb-hover;
  }
}

/* === 主要樣式 === */
.chat-widget {
  width: 400px;
  border-radius: $radius-20;
  overflow: hidden;
  background: $bg-dark;
  border: 1px solid $border-color;
  display: flex;
  flex-direction: column;

  .header {
    padding: 1rem;
    background: $panel-bg;
    border-bottom: 3px solid $border-color;

    h3 {
      font-size: 18px;
      font-weight: 700;
      color: $white;
      margin: 0;
    }
  }

  .chat-area {
    flex: 1;
    margin: 0.5rem;
    overflow-y: auto;
    background: $bg-dark;

    .message {
      padding: 0.75rem;

      .bot,
      .user {
        display: flex;
        gap: 0.5rem;
        align-items: flex-start;

        &.user {
          flex-direction: row-reverse;
        }

        .avatar {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;

          svg {
            width: 100%;
            height: auto;
          }
        }

        .content {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;

		  .relation-area {
			width: 100%;
			display: flex;
			justify-content: center;
			align-items: center;
			margin-top: 8px;
			margin-bottom: 16px;

			  .relation-table {
  				font-size: 13px;
		  	  }

		  	  .relation-table th,
		  	  .relation-table td {
  				border: 1px solid #ccc;
  				text-align: left;
				padding: 0px 8px;
				line-height: 1.1;
				vertical-align: middle;
		  	  }

			  .relation-table td {
  				height: 2.5rem;
		  	  }

		  	  .relation-table th {
  				font-weight: bold;
				text-align: center;
		  	  }
		    }

          .message--bubble {
            border: 1px solid $white;
            border-radius: $radius-10;
            background: $card-bg;

            p {
              color: $white;
              white-space: pre-line;
              margin: 0;
			  padding-top: 8px;
			  padding-bottom: 8px;
			  padding-left: 16px;
			  padding-right: 16px;
			  font-size: 16px;
            }
          }

          .message--button {
            display: flex;
            gap: 0.5rem;
            overflow-x: auto;

            button {
			  flex-shrink: 0;
              background: $panel-bg;
              color: $white;
			  font-size: 14px;
              padding: 0.5rem 1rem;
              border-radius: $radius-15;
              border: none;
              cursor: pointer;
              white-space: nowrap;

              &:hover {
                filter: brightness(0.5);
              }
            }
          }
        }
      }
    }
  }

  .input-area {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 1.5rem 1.125rem;
    background: $panel-bg;

    input[type='text'] {
      background: $white;
      height: 35px;
      width: 100%;
      border-radius: 20px;
      padding: 0 1rem;
      border: none;
      outline: none;
	  color: black;
    }

    button {
      height: 35px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      cursor: pointer;

      &:hover {
        filter: brightness(0.5);
      }
    }
  }
}
</style>
