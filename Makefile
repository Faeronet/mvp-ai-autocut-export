.PHONY: tidy test build web docker-up docker-down fmt

tidy:
	go mod tidy

test:
	go test ./...

build:
	go build -o bin/api ./cmd/api
	go build -o bin/worker ./cmd/worker
	go build -o bin/mcp ./cmd/mcp

web:
	cd apps/web && npm install && npm run build

docker-up:
	docker compose -f deploy/docker-compose.yml up --build -d

docker-down:
	docker compose -f deploy/docker-compose.yml down

fmt:
	gofmt -w $$(find . -name '*.go' -not -path './apps/*')
