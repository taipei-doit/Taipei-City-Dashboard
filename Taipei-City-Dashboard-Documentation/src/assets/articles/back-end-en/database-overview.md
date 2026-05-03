## Introduction

This project uses two PostgreSQL databases to manage its data. The first one (`dashboard`) stores statistical, historical, and geographical data for the dashboard's components. The second one (`dashboardmanager`) is responsible for storing Taipei City Dashboard's management data, such as user information, roles, groups, dashboard configs, component configs, etc.

If you haven't already, please refer to [the project setup guide](/back-end/project-setup) to set up the databases and prepopulate them with data.

## dashboard

The `dashboard` database is connected to [Airflow](https://airflow.apache.org/), a workflow management platform which is responsible for updating the data in the database. The Postgis extension is also pre-installed in the database to support geographical data.

Data is extracted from the database via two primary methods. First via the dashboard's backend, which is responsible for querying statistical and historical data. Second via [Geoserver](https://geoserver.org/), which is responsible for querying and caching geographical data and transforming them into map tiles.

> **w01**
> We are still in the process of open-sourcing the configurations for Airflow. At the moment for external developers, data should be populated into the `dashboard` database manually or via an alternative service.

> **w02**
> We are still in the process of open-sourcing our configurations for Geoserver. At the moment for external developers, we advise using an alternative map server such as Mapbox or storing the data in geojson files directly in the frontend. Learn more [here](/front-end/map-data).

## dashboardmanager

The `dashboardmanager` database is connected to the dashboard's backend, which is responsible for querying and updating the data in the database. This documentation will go more in-depth into the database's structure and how to use it in the [following section](/back-end/users-roles-groups-db).
