#!/bin/bash

# Build and Push Docker Image Script for Jellyfin Telegram Notifier
# This script downloads the latest version of the repository, builds a Docker image,
# applies appropriate tags, and pushes it to a local registry
#
# Usage: ./build-and-push.sh [OPTIONS]
# Options:
#   --dry-run    Run without actually building or pushing images
#   --help       Display this help message

set -e  # Exit on any error

# Configuration
REPO_OWNER="paulredmond79"
REPO_NAME="jellyfin-telegram-notifier"
FULL_REPO="${REPO_OWNER}/${REPO_NAME}"
IMAGE_NAME="jellyfin-telegram-notifier"
LOCALHOST_REGISTRY="localhost:5000"  # Local Docker registry
WORK_DIR="/tmp/${REPO_NAME}-build"
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Build and Push Docker Image Script for Jellyfin Telegram Notifier"
            echo ""
            echo "Usage: ./build-and-push.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Run without actually building or pushing images"
            echo "  --help       Display this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required tools are installed
check_requirements() {
    log_info "Checking requirements..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if gh is authenticated
    if ! gh auth status &> /dev/null; then
        log_warning "GitHub CLI is not authenticated."
        log_warning "Please run 'gh auth login' or set GH_TOKEN environment variable."
        log_warning "For GitHub Actions, set: GH_TOKEN: \${{ github.token }}"
    fi
    
    log_success "All requirements met"
}

# Function to clean up previous build directory
cleanup_workspace() {
    log_info "Cleaning up workspace..."
    if [ -d "$WORK_DIR" ]; then
        rm -rf "$WORK_DIR"
        log_success "Previous workspace cleaned"
    fi
}

# Function to download the latest repository
download_repo() {
    log_info "Downloading latest version of ${FULL_REPO}..."
    
    # Try to clone using GitHub CLI first, fallback to git if that fails
    if gh auth status &> /dev/null; then
        if ! gh repo clone "$FULL_REPO" "$WORK_DIR" -- --depth 1 2>&1; then
            log_error "Failed to clone repository using GitHub CLI"
            exit 1
        fi
    else
        log_warning "GitHub CLI not authenticated, falling back to git clone"
        if ! git clone --depth 1 "https://github.com/${FULL_REPO}.git" "$WORK_DIR" 2>&1; then
            log_error "Failed to clone repository using git"
            exit 1
        fi
    fi
    
    log_success "Repository downloaded successfully"
}

# Function to get version information
get_version() {
    cd "$WORK_DIR"
    
    # Try to get the latest tag, if no tags exist, use "dev"
    VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "dev")
    
    # Get short commit hash
    COMMIT_HASH=$(git rev-parse --short HEAD)
    
    log_info "Version: ${VERSION}"
    log_info "Commit: ${COMMIT_HASH}"
    
    cd - > /dev/null
}

# Function to build Docker image
build_image() {
    log_info "Building Docker image..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN: Would build Docker image with tags:"
        log_warning "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:latest"
        log_warning "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${VERSION}"
        log_warning "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${COMMIT_HASH}"
        return 0
    fi
    
    cd "$WORK_DIR"
    
    # Build the image with multiple tags
    if ! docker build \
        -t "${LOCALHOST_REGISTRY}/${IMAGE_NAME}:latest" \
        -t "${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${VERSION}" \
        -t "${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${COMMIT_HASH}" \
        . ; then
        log_error "Docker build failed"
        exit 1
    fi
    
    cd - > /dev/null
    log_success "Docker image built successfully"
}

# Function to push image to local registry
push_image() {
    log_info "Pushing images to local registry at ${LOCALHOST_REGISTRY}..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN: Would push images to ${LOCALHOST_REGISTRY}"
        log_warning "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:latest"
        log_warning "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${VERSION}"
        log_warning "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${COMMIT_HASH}"
        return 0
    fi
    
    # Check if local registry is reachable
    if ! curl -s "http://${LOCALHOST_REGISTRY}/v2/" > /dev/null 2>&1; then
        log_warning "Local registry at ${LOCALHOST_REGISTRY} is not reachable"
        log_warning "Make sure the registry is running with: docker run -d -p 5000:5000 --name registry registry:2"
    fi
    
    # Push all tags
    log_info "Pushing tag: latest"
    if ! docker push "${LOCALHOST_REGISTRY}/${IMAGE_NAME}:latest"; then
        log_error "Failed to push latest tag to registry"
        exit 1
    fi
    
    log_info "Pushing tag: ${VERSION}"
    if ! docker push "${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${VERSION}"; then
        log_error "Failed to push ${VERSION} tag to registry"
        exit 1
    fi
    
    log_info "Pushing tag: ${COMMIT_HASH}"
    if ! docker push "${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${COMMIT_HASH}"; then
        log_error "Failed to push ${COMMIT_HASH} tag to registry"
        exit 1
    fi
    
    log_success "All images pushed successfully"
}

# Function to display summary
show_summary() {
    echo ""
    echo "======================================"
    log_success "BUILD AND PUSH COMPLETED"
    echo "======================================"
    echo ""
    echo "Images pushed to ${LOCALHOST_REGISTRY}:"
    echo "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:latest"
    echo "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${VERSION}"
    echo "  - ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:${COMMIT_HASH}"
    echo ""
    echo "To pull the image:"
    echo "  docker pull ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:latest"
    echo ""
    echo "To run the container:"
    echo "  docker run -d -p 5000:5000 --env-file .env ${LOCALHOST_REGISTRY}/${IMAGE_NAME}:latest"
    echo ""
}

# Main execution
main() {
    log_info "Starting build and push process for ${FULL_REPO}"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN MODE - No actual builds or pushes will be performed"
    fi
    
    check_requirements
    cleanup_workspace
    download_repo
    get_version
    build_image
    push_image
    show_summary
    
    # Cleanup
    log_info "Cleaning up workspace..."
    rm -rf "$WORK_DIR"
    
    log_success "Process completed successfully!"
}

# Run main function
main
