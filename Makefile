include .env

build:
	docker build -t flow-cytometry-calculator .

run:
	docker run -p 8501:8501 flow-cytometry-calculator

publish:
	aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin $(ECR_REPOSISTORY_URL)
	
	docker buildx build \
		--platform linux/amd64 \
		-t $(ECR_REPOSISTORY_URL)/$(ECR_REPOSISTORY_NAME):latest \
		-t $(ECR_REPOSISTORY_URL)/$(ECR_REPOSISTORY_NAME):$(shell git rev-parse --short HEAD) \
		--push \
		. 

redeploy-ecs:
	aws ecs update-service \
		--cluster $(ECS_CLUSTER_NAME) \
		--service $(ECS_SERVICE_NAME) \
		--force-new-deployment
