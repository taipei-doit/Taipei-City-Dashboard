# <img src='Taipei-City-Dashboard-FE/src/assets/images/TUIC.svg' height='28'> Taipei City Dashboard

## Important Notice

From now to late February 2024, Taipei City Dashboard FE will be undergoing a massive overhaul to officially connect the platform's backend. During this time, any outside issues or pull requests will not be accepted and be closed immediately.

## Introduction

Taipei City Dashboard is a data visualization platform developed by [Taipei Urban Intelligence Center (TUIC)](https://tuic.gov.taipei/en).

Our main goal is to create a comprehensive data visualization tool to assist in Taipei City policy decisions. This was achieved through the first version of the Taipei City Dashboard, which displayed a mix of internal and open data, seamlessly blending statistical and geographical data.

Fast forward to mid-2023, as Taipei City’s open data ecosystem matured and expanded, our vision gradually expanded as well. We aimed not only to aid policy decisions but also to keep citizens informed about the important statistics of their city. Given the effectiveness of this tool, we also hoped to publicize the codebase for this project so that any relevant organization could easily create a similar data visualization tool of their own.

Our dashboard, made yours.

Based on the above vision, we decided to begin development on Taipei City Dashboard 2.0. Unlike its predecessor, Taipei City Dashboard 2.0 will be a public platform instead of an internal tool. The codebase for Taipei City Dashboard will also be open-sourced, inviting all interested parties to participate in the development of this platform.

We have since completed the initial layouts and basic functionalities of Taipei City Dashboard 2.0 and feel the time is right to begin sharing the development process with the general public. From now on, you will be able to suggest features and changes to Taipei City Dashboard and develop the platform alongside us. We are excited for you to join Taipei City Dashboard’s journey!

Please refer to the docs for the [Chinese Version](https://tuic.gov.taipei/documentation/front-end/introduction) (and click on the "switch languages" icon in the top right corner).

[Demo](https://tuic.gov.taipei/dashboard-demo) | [License](https://github.com/tpe-doit/Taipei-City-Dashboard-FE/blob/main/LICENSE) | [Code of Conduct](https://github.com/tpe-doit/Taipei-City-Dashboard/blob/main/.github/CODE_OF_CONDUCT.md) | [Contribution Guide](https://tuic.gov.taipei/documentation/front-end/contribution-overview)

## Quick Start

### Docker-compose

1. Install [Docker](https://www.docker.com/products/docker-desktop/) on your computer and start running it.
2. Install [Docker-compose](https://docs.docker.com/compose/install/).
3. Fork this repository then clone the project to your computer. Execute `cd docker` in the repository terminal to change to the docker folder.
4. Execute the following command in the system terminal to start and check 1 Redis and 2 PostgreSQL database servers.
```bash
docker-compose -f docker-compose-db.yaml up -d
```
>**i01** Use `docker-compose -f [yaml_file] ps` to check the container status specified in the YAML file.

>**i02** Use `docker logs -f [container id or name]` to check container status

5. Execute the following command to initialize the dashboard frontend and backend.
```bash
docker-compose -f docker-compose-init.yaml up -d
```

6. Execute the following commands to start Nginx, the dashboard frontend, and backend.
```bash
docker-compose up -d
```

7. Refer to the [Docs](https://tuic.gov.taipei/documentation/back-end/project-setup) to complete further configurations.

## Documentation

Check out the complete documentation for Taipei City Dashboard [here](https://tuic.gov.taipei/documentation).

## Contributors

Many thanks to the contributors to this project!

<a href="https://github.com/tpe-doit/Taipei-City-Dashboard-FE/graphs/contributors">
<img src="https://contrib.rocks/image?repo=tpe-doit/Taipei-City-Dashboard-FE" />
</a>
