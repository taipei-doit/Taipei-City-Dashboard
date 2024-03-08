FROM golang:1.21.3-alpine3.18 as builder
WORKDIR /go/src/app
COPY . .
RUN go build 

FROM scratch
COPY --from=builder /go/src/app/TaipeiCityDashboardBE /app/
WORKDIR /app
EXPOSE 8080
CMD ["./TaipeiCityDashboardBE"]