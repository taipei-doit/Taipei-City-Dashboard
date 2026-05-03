## How Dialogs Work
In short, each dialog is simply a Vue component whose existence in the user interface is controlled by the `dialogStore`. All dialog Vue components are stored in the folder `/src/components/dialogs`. Dialogs are also all assigned a name, which by convention is the camel case form of their Vue component file name.

### Dialog Store
The dialogStore stores the render status of all dialogs. All of the available dialogs in this project are listed below.

```js
dialogs: { // One of the states of the dialogStore
    // Admin Dialogs: /components/dialogs/admin
	adminComponentSettings: false,
	adminAddEditDashboards: false,
	adminEditIssue: false,
	adminAddComponent: false,
	adminDeleteDashboard: false,
	adminEditUser: false,
	adminAddEditContributor: false,
	adminDeleteContributor: false,
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
	contributorsList: false,
	contributorInfo: false,
	addPin: false,
	addViewPoint: false,
	findClosestPoint: false,
},
```

Dialog Vue components will conditionally render themselves based on their status which defaults to `false`.

### Anatomy of a Dialog Vue Component
The following is a breakdown of a typical dialog Vue component.


```html
&lt;template&gt;
    &lt;!-- a Vue feature that teleports the Vue componet to body --&gt;
    &lt;Teleport to=&quot;body&quot;&gt; 
        &lt;!-- a Vue feature that adds enter and leave transitons --&gt;
        &lt;Transition name=&quot;dialog&quot;&gt; 
            &lt;!-- conditionally render if dialog status is true --&gt;
            &lt;div class=&quot;dialogcontainer&quot; v-if=&quot;dialogStore.dialogs.mobileNavigation&quot;&gt; 
                &lt;!-- background overlay that closes the dialog on click --&gt;
                &lt;div class=&quot;dialogcontainer-background&quot; @click=&quot;dialogStore.hideAllDialogs&quot;&gt;&lt;/div&gt;
                &lt;div class=&quot;dialogcontainer-dialog&quot;&gt;
                    &lt;div class=&quot;mobilenavigation&quot;&gt;
                        &lt;!-- The content of the dialog --&gt;
                    &lt;/div&gt;
                &lt;/div&gt;
            &lt;/div&gt;
        &lt;/Transition&gt;
    &lt;/Teleport&gt;
&lt;/template&gt;
```

```html
&lt;style scoped lang=&quot;scss&quot;&gt;
    .dialogcontainer {
        /* take up the entire screen */
        /* position absolute, top layer */

        &amp;-background {
            /* blur the rest of the user interface */
        }
        
        &amp;-dialog {
            /* position, dimensions, border, background of the dialog */
        }
    }

    .mobilenavigation {
        /* styles for the main dialog */
    }

    .dialog-enter-from,
    .dialog-leave-to {
        /* dialog enter effects */
    }

    .dialog-enter-active,
    .dialog-leave-active {
        /* dialog leave effects */
    }
&lt;/style&gt;
```

>**t01**
>Learn more about Vue teleport [here](https://vuejs.org/guide/built-ins/teleport.html).
>Learn more about Vue transitions [here](https://vuejs.org/guide/built-ins/transition.html).

A wrapper Vue component, `DialogContainer`, is available for dialogs centered in the middle of the screen. This wrapper takes care of teleportation, transition, conditional rendering, and the overlay background. A breakdown of a dialog Vue component that uses this wrapper can be found below.

```html
&lt;template&gt;
    &lt;!-- dialog: pass in the dialog name --&gt;
    &lt;!-- @on-close: pass in a function that handles dialog closures --&gt;
    &lt;DialogContainer dialog=&quot;initialWarning&quot; @on-close=&quot;handleClose&quot;&gt;
        &lt;div class=&quot;initialwarning&quot;&gt;
            &lt;!-- The content of the dialog --&gt;
        &lt;/div&gt;
    &lt;/DialogContainer&gt;
&lt;/template&gt;
```

### Opening and Closing a Dialog
The typical flow for opening a dialog starts with a button or function calling the `showDialog` method of the `dialogStore`. This method takes the dialog name as a parameter and will toggle the dialog’s render status to `true`.

To close a dialog, call the `hideAllDialogs` method of the `dialogStore`. This method will toggle the status of all dialogs except for the `notificationBar` to `false`.

### Special Dialogs
There are three special dialogs in this project that work slightly differently from the others. This is due to the need to populate additional information in those dialogs.

The **`moreInfo`** dialog is opened by calling the `showMoreInfo` method of the `dialogStore`. This method takes the **component configuration** of the target component as a parameter and renders an info box that displays more detailed component information.

The **`reportIssue`** dialog is opened by calling the `showReportIssue` method of the `dialogStore`. This method takes the target component **name** and **id** as parameters and renders a form from which users could submit issue reports.

The **`notificationBar`** dialog is opened by calling the `showNotification` method of the `dialogStore`. This method takes two parameters: **status** (either “success” or “fail”) and the **message** to display. This will render a push notification at the top of the dashboard.

## Create a New Dialog
First, decide on a dialog name and create a Vue component following the anatomy of a dialog Vue component. Then, register the dialog in the `dialogStore` by adding the dialog name to the existing list of dialogs. Finally, add the dialog Vue component to the application. A good practice would be to add the dialog Vue component beside the element that triggers it, such as a button.

>**w01**
>Do not add the dialog Vue component to more than one place in the application. This will render more than one dialog when the dialog is activated.
