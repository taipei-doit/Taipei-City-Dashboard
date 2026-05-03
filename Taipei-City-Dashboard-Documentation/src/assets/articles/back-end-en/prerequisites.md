## Development Environment

For the most optimal development experience, we recommend using a device with Windows or macOS as the operating system. We also recommend configuring your development environment to the below specifications.

### Development Tools

If you wish to follow our [project setup guide](/back-end/project-setup), please ensure the following development tools are installed on your computer: [Go](https://golang.org/), [Git](https://git-scm.com/) (and optionally GitHub Desktop), Docker (via installing [Docker Desktop](https://www.docker.com/products/docker-desktop/)), [Postman](https://www.postman.com/). If you will also be working with our front-end, please also install [Node.js LTS](https://nodejs.org/en).

### Text Editor

[VScode](https://code.visualstudio.com/) is our preferred text editor. We recommend installing the following extensions: Go, Docker. If you will also be working with our front-end, we also recommend installing the Prettier, ESLint, Vue Language Features (Volar) extensions. If you go with an alternative text editor, please ensure that it supports the above extensions.

## Tech Stack

### Go

Go is this project's primary programming language. It is a compiled, statically typed language with a focus on concurrency and simplicity. Go's documentation and installation guide can be found [here](https://golang.org/doc/).

### PostgreSQL

This project uses PostgreSQL as its database. PostgreSQL's documentation can be found [here](https://www.postgresql.org/docs/).

### Redis

This project uses Redis as a caching tool to store frequently requested info. Redis's documentation can be found [here](https://redis.io/docs/).

## Core Go Libraries and Packages

### Cobra

Cobra is a library used to create CLI applications in Go. This project utilizes Cobra to perform neccessary tasks without interferring with the main backend service. Cobra's documentation can be found [here](https://cobra.dev/)

### Gin

Gin is a web framework for Go. Gin's documentation can be found [here](https://gin-gonic.com/docs/).

### GORM

GORM is an ORM library for Go used to connect to databases such as PostgreSQL. GORM's documentation can be found [here](https://gorm.io/docs/).

### Redis

Redis is a library used to connect to Redis. Redis's documentation can be found [here](https://pkg.go.dev/github.com/go-redis/redis/v8).
