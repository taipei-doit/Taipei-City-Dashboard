## Running the Project Locally

**_looks_one_** Fork [the project repository](https://github.com/taipei-doit/Taipei-City-Dashboard) then clone the project to your computer. Open the repository with VSCode or your preferred code editor.

**_looks_two_** Start the Docker engine via opening Docker Desktop or the command line. Then, open the repository terminal and change the directory to `/docker` (`cd docker`).

**_looks_3_** In the docker directory, there is an `.env.template` file. Copy that file and rename it to `.env`. Most of the variables have already been pre-filled and some are labeled `[External Dev Don't Need to Fill]`. Please do not change the values of those variables. However, you will need to fill in the following 9 variables yourself:

```bash
## Docker image tag
...

## Frontend ENV Configs
...
VITE_MAPBOXTOKEN= # See Info 1
VITE_MAPBOXTILE=mapbox:// # See Info 2
VITE_PERSONAL_BOARD_UPDATE= #  See Info 3. This variable can be configured according to your needs
...

## Server ENV Configs
...
DASHBOARD_DEFAULT_USERNAME= # Creates a default admin account. Fill in any username.
DASHBOARD_DEFAULT_Email= # Creates a default admin account. Fill in any email.
DASHBOARD_DEFAULT_PASSWORD= # Fill in any password for the admin account.

## DB Configs
# Dashboard data DB
...
DB_DASHBOARD_PASSWORD= # Fill in a password of your choice for the dashboard database.
...

# Dashboard Manager DB
...
DB_MANAGER_PASSWORD= # Fill in a password of your choice for the manager database.
...

# Redis Configs
...

# Qdrant Configs
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY= # Qdrant password (required). You must enter your Qdrant access password here, otherwise the connection will fail.
QDRANT_COLLECTION_NAME=query_charts

# pgadmin
PGADMIN_DEFAULT_EMAIL= # Creates a default pgadmin account. Fill in any email.
PGADMIN_DEFAULT_PASSWORD= # Fill in any password for the pgadmin account.
...
```

> **i01**
> Fill in the variable `VITE_MAPBOXTOKEN` with a Mapbox access token which will allow the maps in this project to be rendered. Create your own Mapbox token by creating a Mapbox account and following [this guide](https://docs.mapbox.com/help/getting-started/access-tokens/). If you aren't using the default public token of your Mapbox account, remember to add https://localhost:8080 to the list of urls supported by your token.

> **i02**
> This variable adds a 3D building layer to the base map. This step is optional and you may leave the variable blank if you choose.
>
> First, download the model file (`geojson`) [here](https://drive.google.com/file/d/1cMBrq1gmSNAioogFZNqA5IyAmhXoeLVs/view?usp=drive_link). Then, open Mapbox Studio and navigate to ["Tilesets"](https://studio.mapbox.com/tilesets/). Click on "New Tileset" and upload the downloaded file. After the upload has been completed, open the tileset and click on "share & use". Copy the "Tileset ID" and append it to the variable `VITE_MAPBOXTILE` in the `.env` file (paste it after "mapbox://").
>
> Navigate back to the tileset on MapBox. On the left of the screen, you will see a sidebar titled "Vector Layers". Copy the name of the polygon layer (it should start with "tp_building_height") below the title. Then, return to project repository and navigate to `/src/assets/configs/mapbox/mapConfig.js`. Find a object called "TaipeiBuilding" and replace the parameter "source-layer" with the polygon layer name you copied.

> **i03**
> This variable is newly added in version 3.0, used to control the automatic update frequency of personal dashboards. You can leave this variable empty and configure your personal dashboard update frequency later as needed.
>
> Parameter format definition: personal dashboard index:update frequency(seconds),personal dashboard index:update frequency(seconds), using commas to separate multiple dashboard settings.
> 
> Configuration example:
>  
> `VITE_PERSONAL_BOARD_UPDATE`=71528009ae4b:600,415dc056e6df:600,278b42f7d039:600,f7a3542955f1:600
>
> The above example shows four different dashboards (identified by index), each set to automatically refresh once every 600 seconds (10 minutes).
> 

**_looks_4_** In the terminal, execute the following commands one by one to create a docker network and start the containers.

> **t01**
> If you encounter any issues, please check the docker logs. Common mistakes include not filling in the `.env` file correctly, not having the Docker engine running, not having the correct network settings, or not removing the volumes `docker compose -f docker-compose-db.yaml down -v` before running the setup.

Create a Docker network named `br_dashboard` with a specified subnet.

```bash
docker network create --driver=bridge --subnet=192.168.128.0/24 --gateway=192.168.128.1  br_dashboard
```

Run DB and Qdrant related containers. After executing this command, check if all containers are running. Please also wait until the database is fully initialized (check docker logs and see the message, `database system is ready to accept connections`, is present) before running the next command. Note: The Qdrant container must be enabled locally to use the Chatbot function.

```bash
docker-compose -f docker-compose-db.yaml up -d
```

Initialize the frontend and backend environments. The containers created via this command are temporary. Please wait until the containers stop running before running the next command.

```bash
docker-compose -f docker-compose-init.yaml up -d
```

> **i04**
> Within the docker-compose-init.yaml file, three containers are tasked with the following responsibilities:
>
> `dashboard-fe-init`: Execute npm install; `dashboard-be-init-manager`: Initialize the manager DB; `dashboard-be-init-dashboard`: Initialize the dashboard DB.

Run the frontend and backend services:

> **w01**
> The following command will also run a nginx service. If you don't require `https`, comment out lines 11-15 in `/docker/nginx/conf.d/default.conf`; If you do, generate a ssl certificate (`citydashboard-fullchain1.pem`) and private key (`citydashboard-privkey.pem`) and store it in `/docker/nginx/ssl`.

```bash
docker-compose up -d
```

> **t02**
> The frontend supports hot-reloading, so you can make changes to the code and see the changes reflected in the browser (for Windows users, add `watch: {usePolling: true}` to the `server` property in `vite.config.js`).
>
> The backend does not support hot-reloading. If you make changes to the backend code, you will need to restart the `dashboard-be` container.

> **i05**
> From now on, if you would like to reinitiate the databases, please follow the steps below:
>
> Firstly, ensure that all relevant containers are closed or deleted. Next, delete the volumes `docker compose -f docker-compose-db.yaml down -v` directory. Finally, execute the above three `docker-compose` commands.

**_looks_5_** The project should now be running locally. Open your browser and navigate to [https://localhost:8080](https://localhost:8080). You should see the dashboard homepage. To login by email, open the login dialog then hold down `shift` and click the DOIT logo. If you encounter any issues, please check the docker logs or the console in the browser.

## Further Development Setup

### PGAdmin

To register the 2 Postgres databases in pgAdmin, follow the steps below:

**_looks_one_** Open pgAdmin (https://localhost:8889/login) and log in with the credentials you filled in the `.env` file. Then, right-click on "Servers" in the top left corner and select "Register" > "Server...". In the "General" tab, fill in "Name" with `dashboard`. Then, in the "Connection" tab, fill in "Host name/address" with `postgres-data`, "Username" with `postgres`, and "Password" with the password you filled in the `.env` file (`DB_DASHBOARD_PASSWORD`). Click "Save" and then "Connect".

**_looks_two_** Repeat the first step but in the "General" tab, fill in "Name" instead with `dashboardmanager`. And in the "Connection" tab, fill in "Host name/address" instead with `postgres-manager`, and "Password" with the password you filled in the `.env` file (`DB_MANAGER_PASSWORD`). Click "Save" and then "Connect".

### Postman

To better test the APIs of this product, we recommend using Postman. The collection file for the APIs can be found <a href="/documentation/data/dashboard_postman.json" download>here</a>. After downloading the file, open Postman and click on "Import" > "Choose Files" and select the downloaded file. The collection will then be added to your Postman workspace. Also import the environment file <a href="/documentation/data/dashboard_postman_env.json" download>here</a> and select the environment in the top right corner of Postman.

### Qdrant Vector Database & Data Ingestion

This step is used to convert data from the PostgreSQL database into vector embeddings and upload them to the Qdrant vector database for search functionality.

**_looks_one_** Ensure the Qdrant service is running. When you run `docker-compose -f docker-compose-db.yaml up -d`, the Qdrant service (`qdrant`) should start automatically.

**_looks_two_** Run the data ingestion tool. This tool converts data from PostgreSQL into vectors and writes them to Qdrant. Execute the following in the `docker` directory:

```bash
docker compose --profile tools up vector-db-upgrade
```

> **i06**
> The first run will automatically download the AI model (approx. 500MB), so please be patient. To view detailed execution logs, remove the `-d` parameter. If you encounter out-of-memory errors, please refer to `docker/qdrant-upgrade/README.md` for adjustment instructions.
