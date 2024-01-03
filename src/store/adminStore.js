import axios from "axios";
import { defineStore } from "pinia";
import { useDialogStore } from "./dialogStore";
const { VITE_API_URL } = import.meta.env;

export const useAdminStore = defineStore("admin", {
	state: () => ({
		components: [],
		editingComponent: {},
	}),
	getters: {},
	actions: {
		getPublicComponents(params) {
			const dialogStore = useDialogStore();

			axios
				.get(`${VITE_API_URL}/component/`, {
					params,
				})
				.then((response) => {
					this.components = response.data.data;
				})
				.catch((err) => {
					console.error(err);
					dialogStore.showDialog("fail", "無法取得組件");
				});
		},
	},
});
