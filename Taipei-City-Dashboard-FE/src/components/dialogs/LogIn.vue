<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { computed, ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useAuthStore } from "../../store/authStore";

import DialogContainer from "./DialogContainer.vue";

const {
	VITE_APP_TITLE,
	PROD,
	VITE_TAIPEIPASS_URL,
	VITE_TAIPEIPASS_CLIENT_ID,
	VITE_TAIPEIPASS_SCOPE,
} = import.meta.env;

const dialogStore = useDialogStore();
const authStore = useAuthStore();

const loginMode = ref("tp");
const email = ref("");
const password = ref("");

const taipeiPassUrl = computed(() => {
	return `${VITE_TAIPEIPASS_URL}/oauth2/authorize?response_type=code&client_id=${VITE_TAIPEIPASS_CLIENT_ID}&scope=${VITE_TAIPEIPASS_SCOPE}`;
});

function handleSwitchMode() {
	if (PROD) {
		return;
	} else {
		loginMode.value = loginMode.value === "tp" ? "email" : "tp";
		email.value = "";
		password.value = "";
	}
}
function handleTaipeiPassLogin() {
	window.open(taipeiPassUrl.value, "_self");
}
async function handleEmailLogin() {
	const loggedIn = await authStore.loginByEmail(email.value, password.value);
	if (loggedIn) {
		handleClose();
	}
}
function handleClose() {
	loginMode.value = "tp";
	dialogStore.hideAllDialogs();
}
</script>

<template>
  <DialogContainer
    dialog="login"
    @on-close="handleClose"
  >
    <div class="login">
      <div class="login-logo">
        <div class="login-logo-image">
          <img
            src="../../assets/images/TUIC.svg"
            alt="tuic logo"
            @click.shift="handleSwitchMode"
          >
        </div>
        <div>
          <h1>{{ VITE_APP_TITLE }}</h1>
          <h2>Taipei City Dashboard</h2>
        </div>
      </div>
      <div
        v-if="loginMode === 'tp'"
        class="login-form"
      >
        <button @click="handleTaipeiPassLogin">
          <img src="../../assets/images/taipeipass.png">台北通登入
        </button>
      </div>
      <div
        v-if="loginMode === 'email'"
        class="login-form"
      >
        <label>電子郵件</label>
        <input
          v-model="email"
          required
          type="email"
        >
        <label>密碼</label>
        <input
          v-model="password"
          required
          type="password"
        >
        <button @click="handleEmailLogin">
          登入
        </button>
      </div>
      <p>點擊「台北通登入」即表示您已閱讀並同意</p>
      <p>
        <a
          href="https://tuic.gov.taipei/zh/works/dashboard"
          target="_blank"
        >臺北城市儀表板</a>的<a
          href="https://tuic.gov.taipei/zh/privacy"
          target="_blank"
        >隱私權政策</a>
      </p>
      <p
        :style="{
          color: '#302C2E',
          cursor: 'default',
          userSelect: 'none',
        }"
      >
        TUIC Igor Ann Iima Chu Jack 2023-2024
      </p>
      <p>《讓城市儀表板成為您的儀表板》</p>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.login {
	width: 300px;

	p {
		text-align: center;
		color: var(--color-complement-text);
	}

	p:last-child {
		background: linear-gradient(
			75deg,
			var(--color-complement-text),
			var(--color-highlight) 70%,
			var(--color-complement-text)
		);
		background-clip: text;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		animation: title-gradient 10s linear none infinite;
	}

	a {
		color: var(--color-highlight);
	}

	button {
		width: 180px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 12px 0;
		padding: 6px;
		font-size: var(--font-m);
		background-color: #03b2c3;
		border-radius: 100px;

		img {
			width: 1.5rem;
			margin: 0 10px 0 0;
		}
	}

	label {
		margin-bottom: 4px;
		color: var(--color-complement-text);
		font-size: var(--font-s);
		align-self: flex-start;
	}

	input {
		margin-bottom: 8px;
		width: calc(100% - 14px);
	}

	&-logo {
		display: flex;
		justify-content: center;

		h1 {
			font-weight: 500;
		}

		h2 {
			font-size: var(--font-s);
			font-weight: 400;
		}

		&-image {
			width: 22.94px;
			height: 45px;
			margin: 0 10px 0 0;

			img {
				height: 45px;
				filter: invert(1);
			}
		}
	}

	&-form {
		width: 100%;
		height: 200px;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
	}
}

@keyframes title-gradient {
	0% {
		background-position: 0;
	}

	50% {
		background-position: 600px;
	}

	100% {
		background-position: 0;
	}
}
</style>
