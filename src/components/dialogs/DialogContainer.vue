<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- This component is the template for most dialogs. It will show a dialog centered in the middle of the screen with the rest of the application blurred out -->
<!-- The "dialog" prop defines the target dialog to control whether it is shown, the "onClose" emit allows for a closing function to be passed in  -->

<script setup>
import { useDialogStore } from '../../store/dialogStore';

const dialogStore = useDialogStore();

defineProps({ dialog: String });
defineEmits(['onClose']);
</script>

<template>
	<Teleport to="body">
		<Transition name="dialog">
			<div class="dialogcontainer" v-if="dialogStore.dialogs[dialog]">
				<div class="dialogcontainer-background" @click="$emit('onClose')"></div>
				<div class="dialogcontainer-dialog">
					<slot></slot>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<style scoped lang="scss">
.dialogcontainer {
	width: 100vw;
	height: 100vh;
	height: calc(var(--vh) * 100);
	display: flex;
	align-items: center;
	justify-content: center;
	position: fixed;
	top: 0;
	left: 0;
	opacity: 1;
	z-index: 10;

	&-background {
		width: 100vw;
		height: 100vh;
		height: calc(var(--vh) * 100);
		position: absolute;
		top: 0;
		left: 0;
		background-color: rgba(0, 0, 0, 0.66);
	}

	&-dialog {
		width: fit-content;
		height: fit-content;
		position: relative;
		padding: var(--font-m);
		border: solid 1px var(--color-border);
		border-radius: 5px;
		background-color: var(--color-component-background);
		transform: translateY(0);
		z-index: 2;
	}
}

// Classes that are provided by vue transitions. Read the official docs for more instructions.
// https://vuejs.org/guide/built-ins/transition.html
.dialog-enter-from,
.dialog-leave-to {
	opacity: 0;

	.dialogcontainer-dialog {
		transform: translateY(-2.25rem);
	}
}

.dialog-enter-active,
.dialog-leave-active {
	transition: opacity 0.3s ease;

	.dialogcontainer-dialog {
		transition: transform 0.3s ease;
	}
}
</style>