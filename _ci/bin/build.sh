#!/bin/sh

################################################################################
# This script is for creating a Docker image for running test and lint jobs    #
################################################################################

# Easy name by which to refer the Docker image being created
IMAGE_TAG="duo_log_sync"

# Path to get to the Dockerfile this script is using to build a Docker image
DOCKERFILE_PATH="_ci/docker/Dockerfile"

# Directory containing source code for DuoLogSync
SOURCE_DIR="duologsync"

# If we're building in Gitlab, the registry image prefix is predefined
if [ -n "${CI_REGISTRY_IMAGE}" ]; then
    IMAGE_TAG="${CI_REGISTRY_IMAGE}/${IMAGE_TAG}"
fi

# If we're building in Gitlab, the project root is predefined
if ! SRC=$(git rev-parse --show-toplevel) 2>/dev/null; then
    SRC="${CI_PROJECT_DIR}"
fi

# Our Dockerfile uses experimental buildkit syntax
export DOCKER_BUILDKIT=1

# Create a Docker Image with the name IMAGE_TAG using the Dockerfile located 
# by the file path passed to the 'f' flag and build the Dockerfile in the 
# SRC directory
docker build --tag "${IMAGE_TAG}" -f "${SRC}"/"${DOCKERFILE_PATH}" "${SRC}"
