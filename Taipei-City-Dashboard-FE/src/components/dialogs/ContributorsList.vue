<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { computed, ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";

import DialogContainer from "./DialogContainer.vue";
import ContributorInfo from "./ContributorInfo.vue";

const dialogStore = useDialogStore();
const contentStore = useContentStore();

const currentContributor = ref(null);

const parsedContributors = computed(() => {
	return Object.values(contentStore.contributors)
		.filter((contributor) => contributor.include)
		.sort((a, b) => a.id - b.id);
});

function handleSelectContributor(contributor) {
	currentContributor.value = contributor;
	dialogStore.showDialog("contributorInfo");
}

function handleClose() {
	currentContributor.value = null;
	dialogStore.dialogs.contributorsList = false;
}
</script>

<template>
  <DialogContainer
    :dialog="`contributorsList`"
    @on-close="handleClose"
  >
    <div class="contributorslist">
      <h2>專案貢獻者清單</h2>
      <label> 點擊貢獻者頭貼以了解更多 </label>
      <div class="contributorslist-list">
        <button
          v-for="contributor in parsedContributors"
          :key="`contributor-${contributor.user_id}`"
          @click="handleSelectContributor(contributor)"
        >
          <img
            :src="
              contributor.image.includes('http')
                ? contributor.image
                : `/images/contributors/${contributor.image}`
            "
            :alt="`協作者-${contributor.user_name}`"
          >
        </button>
      </div>
      <ContributorInfo :contributor="currentContributor" />
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.contributorslist {
	width: 304px;

	display: flex;
	flex-direction: column;

	label {
		margin: 8px 0 12px;
		font-size: var(--font-s);
		color: var(--color-complement-text);
	}

	&-list {
		max-height: 250px;
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		flex-basis: content;
		align-items: baseline;
		gap: 8px;

		overflow-y: scroll;

		button {
			position: relative;
			overflow: visible;
		}

		img {
			width: 36px;
			height: 36px;
			border-radius: 50%;
			cursor: pointer;
		}

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			border-radius: 4px;
			background-color: rgba(136, 135, 135, 0.5);
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
	}
}
</style>
