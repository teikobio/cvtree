# Flow Cytometry Cell Population and CV Calculator
Streamlit application for flow cytometry experiment planning and analysis. Calculate expected cell yields through processing steps, visualize hierarchical populations, and assess measurement reliability with CV metrics. Design better panels, estimate required sample volumes, and identify potentially low coefficient of variation population measurements *before* running your experiment. Designed for drug developers who want to minimize sample waste and get reliable measurements of populations.

## Build and Run Locally

```bash
make build
make run
```

## Deploy to AWS ECR

```bash
make publish
make redeploy-ecs
```

## .env requirements

```bash
ECR_REPOSISTORY_URL=
ECR_REPOSISTORY_NAME=cv-tree-teiko-bio
ECS_CLUSTER_NAME=cv-tree-teiko-bio
ECS_SERVICE_NAME=cv-tree-teiko-bio
```
