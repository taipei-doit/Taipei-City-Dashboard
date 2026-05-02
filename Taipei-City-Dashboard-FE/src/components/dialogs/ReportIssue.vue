<!-- Developed by Taipei Urban Intelligence Center 2023-2024 -->

<script setup>
import { ref } from "vue";
import http from "../../router/axios";
import { useDialogStore } from "../../store/dialogStore";
import { useAuthStore } from "../../store/authStore";
import { useContentStore } from "../../store/contentStore";
import { useBackendTranslation } from "../../composables/useBackendTranslation";
import DialogContainer from "./DialogContainer.vue";

const ISSUE_TYPE_IDS = [
	"incorrect_info",
	"incorrect_data",
	"system",
	"other",
];

/** 送後端／管理界面仍沿用繁中原句，利於對照 */
const CONTEXT_ZH_LABEL = {
	incorrect_info: "組件基本資訊有誤",
	incorrect_data: "組件資料有誤或未更新",
	system: "系統問題",
	other: "其他建議",
};

const dialogStore = useDialogStore();
const authStore = useAuthStore();
const contentStore = useContentStore();
const { t } = useBackendTranslation();

function blankInputs() {
	return {
		typeId: ISSUE_TYPE_IDS[0],
		description: "",
		title: "",
	};
}

const allInputs = ref(blankInputs());

async function handleSubmit() {
	const submitObject = {
		title: allInputs.value.title,
		description: allInputs.value.description,
		user_name: authStore.user.name,
		user_id: `${authStore.user.user_id}`,
		context: `類型：${
			CONTEXT_ZH_LABEL[allInputs.value.typeId] ?? ""
		} // 來源：${dialogStore.issue.id} - ${dialogStore.issue.index} - ${dialogStore.issue.name}`,
		status: "待處理",
	};
	await http.post(`/issue/`, submitObject);
	dialogStore.showNotification(
		"success",
		t("report.issue.success_notify") ||
			"回報問題成功，感謝您的建議"
	);
	contentStore.loading = false;
	handleClose();
}
function handleClose() {
	allInputs.value = blankInputs();
	dialogStore.dialogs.reportIssue = false;
}
</script>

<template>
  <DialogContainer
    dialog="reportIssue"
    @on-close="handleClose"
  >
    <div class="reportissue">
      <h2>{{ t('report.issue.dialog_title') }}</h2>
      <h3>
        {{ t('report.issue.field_title_hint') }} ({{ allInputs.title.length }}/20)
      </h3>
      <input
        v-model="allInputs.title"
        class="reportissue-input"
        type="text"
        :minLength="1"
        :maxLength="20"
        required
      >
      <h3>{{ t('report.issue.field_type') }}</h3>
      <div
        v-for="tid in ISSUE_TYPE_IDS"
        :key="tid"
      >
        <input
          :id="'report-type-' + tid"
          v-model="allInputs.typeId"
          class="reportissue-radio"
          type="radio"
          :value="tid"
        >
        <label :for="'report-type-' + tid">
          <div />
          {{ t('report.issue.type.' + tid) }}
        </label>
      </div>
      <h3>
        {{ t('report.issue.field_description_hint') }}
        ({{ allInputs.description.length }}/200)
      </h3>
      <textarea
        v-model="allInputs.description"
        :minLength="1"
        :maxLength="200"
        required
      />
      <div class="reportissue-control">
        <button
          class="reportissue-control-cancel"
          @click="handleClose"
        >
          {{ t('report.issue.cancel') }}
        </button>
        <button
          v-if="allInputs.description && allInputs.title"
          class="reportissue-control-confirm"
          @click="handleSubmit"
        >
          {{ t('report.issue.submit') }}
        </button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.reportissue {
	width: 300px;
	display: flex;
	flex-direction: column;

	h3 {
		margin: 0.5rem 0;
		font-size: var(--font-s);
		font-weight: 400;
	}

	&-radio {
		display: none;

		&:checked + label {
			color: white;

			div {
				background-color: var(--color-highlight);
			}
		}

		&:hover + label {
			color: var(--color-highlight);

			div {
				border-color: var(--color-highlight);
			}
		}
	}

	label {
		position: relative;
		display: flex;
		align-items: center;
		font-size: var(--font-s);
		color: var(--color-complement-text);
		transition: color 0.2s;
		cursor: pointer;

		div {
			width: calc(var(--font-s) / 2);
			height: calc(var(--font-s) / 2);
			margin-right: 4px;
			padding: calc(var(--font-s) / 4);
			border-radius: 50%;
			border: 1px solid var(--color-border);
			transition: background-color 0.2s, border-color 0.2s;
		}
	}

	&-control {
		display: flex;
		justify-content: flex-end;
		margin-top: var(--font-ms);

		&-cancel {
			margin: 0 2px;
			padding: 4px 6px;
			border-radius: 5px;
			transition: color 0.2s;

			&:hover {
				color: var(--color-highlight);
			}
		}

		&-confirm {
			margin: 0 2px;
			padding: 4px 10px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}
		}
	}
}
</style>
