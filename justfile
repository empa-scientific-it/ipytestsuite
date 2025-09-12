# IPyTestSuite - Task Automation

# Default recipe
default:
    @just --list

# Development setup
dev:
    uv sync --dev

# Build the package
build:
    uv build

# Run tests
test:
    pytest

# Test core functionality (without AI dependencies)
test-core:
    mkdir -p test-core
    uv sync --directory test-core
    uv run --directory test-core pytest
    rm -rf test-core

# Test with AI features
test-ai:
    mkdir -p test-ai
    uv sync --extra ai --directory test-ai
    uv run --directory test-ai pytest
    rm -rf test-ai

# Test both core and AI functionality
test-all: test-core test-ai

# Clean up test environments
clean-test:
    rm -rf test-core test-ai

# Install package in development mode
install:
    uv pip install -e .

# Format code (if you add formatting tools later)
fmt:
    @echo "No formatter configured yet"

# Lint code (if you add linting tools later)  
lint:
    @echo "No linter configured yet"