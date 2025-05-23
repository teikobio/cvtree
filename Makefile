define get-ecr-info
	$(eval ECR_ACCOUNT_ID := $(shell aws sts get-caller-identity --query "Account" --output text --profile=default))
	$(eval AWS_REGION := $(shell aws configure get region --profile=default))
	$(eval ECR_REPOSITORY_URL := $(ECR_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com)
endef

# Login to ECR
define ecr-login
	aws ecr get-login-password --region $(AWS_REGION) --profile=default | docker login --username AWS --password-stdin $(ECR_REPOSITORY_URL)
endef

build:
	docker build -t flow-cytometry-calculator .

run:
	docker run -p 8501:8501 flow-cytometry-calculator

publish-to-ecr:
	$(call get-ecr-info)
	$(call ecr-login)

	docker buildx build \
		--platform linux/amd64 \
		-t $(ECR_REPOSITORY_URL)/cv-tree-teiko-bio:latest \
		-t $(ECR_REPOSITORY_URL)/cv-tree-teiko-bio:$(shell git rev-parse --short HEAD) \
		--push \
		. 

redeploy-ecs:
	aws ecs update-service \
		--cluster cv-tree-teiko-bio \
		--service cv-tree-teiko-bio \
		--force-new-deployment \
		--output table > /dev/null

publish-app:
	aws sso login
	make publish-to-ecr
	make redeploy-ecs
