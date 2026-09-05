#!/bin/bash
# ============================================
# AWS ECS Deployment Script
# ============================================
# Deploys the application to AWS ECS Fargate
# Prerequisites: AWS CLI configured, ECR repos created
#
# Usage: ./deploy-ecs.sh [environment]
#   environment: staging | production (default: production)

set -euo pipefail

ENV="${1:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
CLUSTER_NAME="text2img-${ENV}"
SERVICE_NAME="text2img-${ENV}"

echo "╔══════════════════════════════════════╗"
echo "║  AWS ECS Deploy — ${ENV}              ║"
echo "╚══════════════════════════════════════╝"

# ── Step 1: Login to ECR ──────────────────────
echo "[1/6] Logging in to ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
    docker login --username AWS --password-stdin "${ECR_REGISTRY}"

# ── Step 2: Build Images ──────────────────────
echo "[2/6] Building Docker images..."
docker compose build backend worker frontend

# ── Step 3: Tag & Push to ECR ─────────────────
echo "[3/6] Pushing images to ECR..."
for SERVICE in backend worker frontend; do
    IMAGE="${ECR_REGISTRY}/text2img-${SERVICE}:latest"
    IMAGE_TAG="${ECR_REGISTRY}/text2img-${SERVICE}:$(git rev-parse --short HEAD)"

    docker tag "text2img-${SERVICE}:latest" "${IMAGE}"
    docker tag "text2img-${SERVICE}:latest" "${IMAGE_TAG}"
    docker push "${IMAGE}"
    docker push "${IMAGE_TAG}"
    echo "  Pushed: ${IMAGE}"
done

# ── Step 4: Update Task Definition ────────────
echo "[4/6] Updating task definition..."
TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition "text2img-${ENV}" \
    --region "${AWS_REGION}" \
    --query 'taskDefinition' \
    --output json)

# Update image URIs in task definition
NEW_TASK_DEF=$(echo "${TASK_DEF}" | jq \
    --arg backend "${ECR_REGISTRY}/text2img-backend:latest" \
    --arg worker "${ECR_REGISTRY}/text2img-worker:latest" \
    --arg frontend "${ECR_REGISTRY}/text2img-frontend:latest" \
    '.containerDefinitions |= map(
        if .name == "backend" then .image = $backend
        elif .name == "worker" then .image = $worker
        elif .name == "frontend" then .image = $frontend
        else . end
    ) | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities)')

TASK_ARN=$(aws ecs register-task-definition \
    --region "${AWS_REGION}" \
    --cli-input-json "${NEW_TASK_DEF}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "  Task definition: ${TASK_ARN}"

# ── Step 5: Update Service ────────────────────
echo "[5/6] Updating ECS service..."
aws ecs update-service \
    --cluster "${CLUSTER_NAME}" \
    --service "${SERVICE_NAME}" \
    --task-definition "${TASK_ARN}" \
    --region "${AWS_REGION}" \
    --force-new-deployment > /dev/null

# ── Step 6: Wait for Stability ────────────────
echo "[6/6] Waiting for service to stabilize..."
aws ecs wait services-stable \
    --cluster "${CLUSTER_NAME}" \
    --services "${SERVICE_NAME}" \
    --region "${AWS_REGION}"

echo ""
echo "Deploy complete! Service is stable."
echo "  Cluster: ${CLUSTER_NAME}"
echo "  Service: ${SERVICE_NAME}"
