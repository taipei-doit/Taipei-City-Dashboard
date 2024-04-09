// Developed by Taipei Urban Intelligence Center 2023-2024

/* dialogStore */
/*
The dialogStore stores all states related to the popups and dialogs in the application.
To add a new dialog to the existing list, simply give the dialog a name and add it to "dialogs".
Then, in the component add a conditional statement to render the component only if it's value is switched to true.
Finally, remember to add the component to the application.
*/

import { defineStore } from "pinia";

export const useDialogStore = defineStore("dialog", {
	state: () => ({
		dialogs: {
			// Admin Dialogs: /components/dialogs/admin
			adminComponentSettings: false,
			adminAddEditDashboards: false,
			adminEditIssue: false,
			adminAddComponent: false,
			adminDeleteDashboard: false,
			adminEditUser: false,
			// Public Dialogs: /components/dialogs
			addComponent: false,
			addDashboard: false,
			dashboardSettings: false,
			addEditDashboards: false,
			initialWarning: false,
			login: false,
			mobileLayers: false,
			mobileNavigation: false,
			moreInfo: false,
			notificationBar: false,
			reportIssue: false,
			userSettings: false,
			embedComponent: false,
		},
		// Stores the content for notifications
		notification: {
			status: "",
			message: "",
		},
		// Stores the content for report issue dialogs
		issue: {
			id: null,
			index: null,
			name: "",
		},
		// Stores the content for more info dialogs
		moreInfoContent: null,
		// Stores Edit or Add mode for addeditdashboards dialog
		addEdit: "",
	}),
	getters: {},
	actions: {
		// Show the dialog passed into the function
		showDialog(dialog) {
			this.dialogs[dialog] = true;
		},
		// Will hide all dialogs currently active
		hideAllDialogs() {
			const keys = Object.keys(this.dialogs);
			for (let i = 0; i < keys.length; i++) {
				if (keys[i] === "notificationBar") {
					continue;
				}
				this.dialogs[keys[i]] = false;
			}
			this.moreInfoContent = null;
		},
		// Show the notification bar and update the notification message
		showNotification(status, message) {
			this.showDialog("notificationBar");
			this.notification = {
				status: status, // success, fail, info
				message: message,
			};
			setTimeout(() => {
				this.dialogs.notificationBar = false;
			}, 3000);
		},
		// Show the more info dialog and update the content
		showMoreInfo(content) {
			this.showDialog("moreInfo");
			this.moreInfoContent = content;
		},
		// Show the report issue dialog and enter the id and name of the component of origin
		showReportIssue(id, index, name) {
			this.showDialog("reportIssue");
			this.issue = {
				id: id,
				index: index,
				name: name,
			};
		},
	},
});
