## Global Services

### Cobra

Cobra commands are stored in `/cmd/root.go`. By default, the application will run the `TaipeiCityDashboardBE` command if no prefixes are specified when starting the application. Other commands such are `migrateDB` to migrate the database schemas are also available.

### Logs

Logging configurations are stored in `/logs/logs.go`, providing a global logger for the application.

### Global Variables

Global variables are stored in `/global/consts.go` and `/global/vars.go`. The former contains all the constants used in the application, while the latter reads and stores the project's environment variables.

## App

The main application is stored in `/app/app.go`. It contains a `StartApplication` function that initializes the application and starts the server. In `/app`, there are six additional folders that contain the application's router, middlewares, controllers, database handlers, cache handler, and utility functions.

### Router

The router is stored in `/app/router/router.go`. It contains all the routes for the application. More information will be provided on the available routes in this application in [the section after next](/back-end/authentication-apis).

### Middlewares

Middlewares are stored in `/app/middlewares`. These middlewares control rate limiting, authentication, permissions management, and adding common headers to responses.

### Controllers

Controllers are stored in `/app/controllers`. These controllers handle authentication and the business logic of the application. More information will be provided on the available controllers in this application in [the section after next](/back-end/authentication-apis).

### Database

The main logic behind connecting to the PostgreSQL database is stored in `/app/models/database.go`. The database connections are made available globally through the `DBDashboard` (referring to the `dashboard` database) and the `DBManager` (referring to the `dashboardmanager` database) variables.

The models and handlers for the database are stored in `/app/models` where the file names correspond with the controller files that uses them. For example, the `/models/dashboard.go` file contains the `Dashboard` model that is used by the controllers in `/controllers/dashboard.go`.

### Cache

The main logic behind connecting to the Redis cache is stored in `/app/cache/redis.go`. The connection is made available globally through the `Redis` variable.

### Utilities

Utility functions are stored in `/app/utils`. These functions are used across the application in middlewares, controllers, and database handlers.

> **i01**
> When creating a new function, place it in the appropriate folder within the `/app` directory.
>
> For functions that handle requests and passes them to the controllers, place them in the `/app/middlewares` folder; for functions that handle requests and responds to the client, place them in the `/app/controllers` folder; for functions that interact with the database, place them in the `/app/models` folder; for functions that don't fall into the above categories, place them in the `/app/utils` folder.
