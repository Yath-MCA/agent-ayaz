#!/bin/bash

# ============================================================================
# AyazDy - Docker Hub Push Script
# Builds and pushes images to Docker Hub
# ============================================================================

set -e

DOCKER_REGISTRY="yasardevops"
IMAGE_TAG="latest"
COMPOSE_FILE="docker-compose-production.yml"

echo ""
echo "============================================================================"
echo "🐳 AyazDy - Docker Hub Push"
echo "============================================================================"
echo ""
echo "Registry: $DOCKER_REGISTRY"
echo "Tag: $IMAGE_TAG"
echo ""

# Step 1: Check Docker
echo "[1/5] Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    echo "Download: https://www.docker.com/products/docker-desktop"
    exit 1
fi
docker_version=$(docker --version)
echo "✓ Docker found: $docker_version"

# Step 2: Check login
echo ""
echo "[2/5] Checking Docker Hub login..."
if ! docker info | grep -q "Username"; then
    echo "⚠️  Not logged in to Docker Hub"
    echo "Logging in..."
    docker login -u "$DOCKER_REGISTRY"
fi
echo "✓ Docker Hub authenticated"

# Step 3: Build images
echo ""
echo "[3/5] Building Docker images..."
echo "Setting environment variables..."

export DOCKER_REGISTRY="$DOCKER_REGISTRY"
export IMAGE_TAG="$IMAGE_TAG"

docker-compose -f "$COMPOSE_FILE" build

echo "✓ Images built successfully"

# Step 4: Tag images
echo ""
echo "[4/5] Tagging images..."

for service in queue-api dashboard queue-processor; do
    echo "   Tagging ayazdy-$service..."
    docker tag ayazdy-$service:latest "$DOCKER_REGISTRY/ayazdy-$service:$IMAGE_TAG"
done

echo "✓ All images tagged"

# Step 5: Push images
echo ""
echo "[5/5] Pushing images to Docker Hub..."
echo ""

FAILED=0

for service in queue-api dashboard queue-processor; do
    echo "Pushing $DOCKER_REGISTRY/ayazdy-$service:$IMAGE_TAG..."
    if docker push "$DOCKER_REGISTRY/ayazdy-$service:$IMAGE_TAG"; then
        echo "✓ Pushed ayazdy-$service"
    else
        echo "❌ Failed to push ayazdy-$service"
        FAILED=1
    fi
done

echo ""
echo "============================================================================"

if [ $FAILED -eq 0 ]; then
    echo "✅ All images pushed successfully!"
    echo ""
    echo "Access on Docker Hub:"
    echo "   https://hub.docker.com/r/$DOCKER_REGISTRY/ayazdy-queue-api"
    echo "   https://hub.docker.com/r/$DOCKER_REGISTRY/ayazdy-dashboard"
    echo "   https://hub.docker.com/r/$DOCKER_REGISTRY/ayazdy-queue-processor"
    echo ""
else
    echo "❌ Some images failed to push. Check errors above."
    exit 1
fi

echo "============================================================================"
echo ""
