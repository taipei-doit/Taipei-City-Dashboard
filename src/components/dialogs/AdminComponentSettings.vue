<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useAdminStore } from "../../store/adminStore";
import { storeToRefs } from "pinia";

import DialogContainer from "./DialogContainer.vue";
import ComponentContainer from "../components/ComponentContainer.vue";
import InputTags from "../utilities/InputTags.vue";

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const { currentComponent } = storeToRefs(adminStore);
const allSettings = {
	all: "整體",
	chart: "圖表",
	history: "歷史軸",
	map: "地圖",
};
const currentSettings = ref("all");
const tempInputStorage = ref({
	link: "",
	contributor: "",
});

function handleClose() {
	dialogStore.hideAllDialogs();
	adminStore.currentComponent = null;
}
</script>

<template>
	<DialogContainer :dialog="`admincomponentsettings`" @on-close="handleClose">
		<div class="admincomponentsettings">
			<h2>組件設定</h2>
			<div class="admincomponentsettings-tabs">
				<button
					v-for="(setting, key) in allSettings"
					:key="key"
					:class="{ active: currentSettings === key }"
					@click="currentSettings = key"
				>
					{{ setting }}
				</button>
			</div>
			<div class="admincomponentsettings-content">
				<div class="admincomponentsettings-settings">
					<div
						v-if="currentSettings === 'all'"
						class="admincomponentsettings-settings-items"
					>
						<label
							>組件名稱* ({{
								currentComponent.name.length
							}}/20)</label
						>
						<input
							type="text"
							v-model="currentComponent.name"
							:minlength="1"
							:maxlength="20"
						/>
						<label>資料來源*</label>
						<input
							type="text"
							v-model="currentComponent.source"
							:minlength="1"
							:maxlength="12"
						/>
						<label>更新頻率* (0 = 不定期更新)</label>
						<div class="two-block">
							<input
								type="number"
								v-model="currentComponent.update_freq"
								:min="0"
								:max="31"
							/>
							<select v-model="currentComponent.update_freq_unit">
								<option value="day">天</option>
								<option value="week">週</option>
								<option value="month">月</option>
								<option value="year">年</option>
							</select>
						</div>
						<label
							>組件簡述* ({{
								currentComponent.short_desc.length
							}}/50)</label
						>
						<textarea
							v-model="currentComponent.short_desc"
							:minlength="1"
							:maxlength="50"
						></textarea>
						<label
							>組件詳述* ({{
								currentComponent.long_desc.length
							}}/100)</label
						>
						<textarea
							v-model="currentComponent.long_desc"
							:minlength="1"
							:maxlength="100"
						></textarea>
						<label
							>範例情境* ({{
								currentComponent.use_case.length
							}}/100)</label
						>
						<textarea
							v-model="currentComponent.use_case"
							:minlength="1"
							:maxlength="100"
						></textarea>
						<label>資料連結</label>
						<InputTags
							:tags="currentComponent.links"
							@deletetag="
								(index) => {
									currentComponent.links.splice(index, 1);
								}
							"
							@updatetagorder="
								(updatedTags) => {
									currentComponent.links = updatedTags;
								}
							"
						/>
						<input
							type="text"
							:minlength="1"
							v-model="tempInputStorage.link"
							@keypress.enter="
								() => {
									if (tempInputStorage.link.length > 0) {
										currentComponent.links.push(
											tempInputStorage.link
										);
										tempInputStorage.link = '';
									}
								}
							"
						/>
						<label>貢獻者</label>
						<InputTags
							:tags="currentComponent.contributors"
							@deletetag="
								(index) => {
									currentComponent.contributors.splice(
										index,
										1
									);
								}
							"
							@updatetagorder="
								(updatedTags) => {
									currentComponent.contributors = updatedTags;
								}
							"
						/>
						<input
							type="text"
							v-model="tempInputStorage.contributor"
							@keypress.enter="
								() => {
									if (
										tempInputStorage.contributor.length > 0
									) {
										currentComponent.contributors.push(
											tempInputStorage.contributor
										);
										tempInputStorage.contributor = '';
									}
								}
							"
						/>
					</div>
				</div>
				<div class="admincomponentsettings-preview">
					<ComponentContainer
						v-if="
							currentSettings === 'all' ||
							currentSettings === 'chart'
						"
						:notMoreInfo="false"
						:content="currentComponent"
						:style="{ width: '100%', height: 'calc(100% - 35px)' }"
					/>
				</div>
			</div>
		</div>
	</DialogContainer>
</template>

<style scoped lang="scss">
.admincomponentsettings {
	width: 750px;
	height: 500px;

	@media (max-width: 770px) {
		display: none;
	}
	@media (max-height: 520px) {
		display: none;
	}

	&-content {
		height: calc(100% - 70px);
		display: grid;
		grid-template-columns: 1fr 350px;
	}

	&-tabs {
		height: 30px;
		display: flex;
		align-items: center;
		margin-top: var(--font-s);

		button {
			width: 70px;
			height: 30px;
			border-radius: 5px 5px 0px 0px;
			background-color: var(--color-border);
			font-size: var(--font-m);
			color: var(--color-text);
			cursor: pointer;
			transition: background-color 0.2s;

			&:hover {
				background-color: var(--color-complement-text);
			}
		}
		.active {
			background-color: var(--color-complement-text);
		}
	}

	&-settings {
		padding: 0 0.5rem 0.5rem 0.5rem;
		margin-right: 1rem;
		border-radius: 0px 5px 5px 5px;
		border: solid 1px var(--color-border);
		overflow-y: scroll;

		label {
			margin: 8px 0 4px;
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}
		.two-block {
			display: grid;
			grid-template-columns: 1fr 1fr;
			column-gap: 0.5rem;
		}

		&-items {
			display: flex;
			flex-direction: column;
		}

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			background-color: rgba(136, 135, 135, 0.5);
			border-radius: 4px;
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
	}

	&-preview {
		border-radius: 5px;
		border: solid 1px var(--color-border);
	}
}
</style>
