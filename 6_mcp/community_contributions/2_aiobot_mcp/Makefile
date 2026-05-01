# Makefile for aiobot-mcp

IMAGE_NAME = aiobot-mcp
VERSION = latest
CONTAINER_NAME = aiobot-mcp-container
PORT = 7860

.PHONY: build run dev stop logs clean restart

build: ## Build Docker image with nginx
	docker build --no-cache -t $(IMAGE_NAME):$(VERSION) .

run: ## Run with hot reloading
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		-v $(PWD):/app \
		--env-file .env \
		$(IMAGE_NAME):$(VERSION) \
		sh -c "pip install watchfiles && watchfiles 'uv run app.py' /app"
	@echo "🚀 Run this app at http://localhost:$(PORT)"

dev:  ## Run and build the docker container
	make build && make run


stop: ## Stop the container
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

logs: ## View container logs
	docker logs -f $(CONTAINER_NAME)

clean: stop
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME):$(VERSION) || true

restart: clean dev ## Restart Docker container (clean + run)
