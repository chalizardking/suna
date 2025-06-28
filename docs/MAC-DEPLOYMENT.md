# Suna Mac Deployment Guide

This guide provides detailed instructions for setting up and deploying Suna on macOS systems, with optimizations for both Intel and Apple Silicon Macs.

## Table of Contents

- [Overview](#overview)
- [Mac-Specific Prerequisites](#mac-specific-prerequisites)
- [Quick Start for Mac](#quick-start-for-mac)
- [Manual Installation](#manual-installation)
- [Mac-Specific Configuration](#mac-specific-configuration)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting Mac Issues](#troubleshooting-mac-issues)
- [Apple Silicon vs Intel Considerations](#apple-silicon-vs-intel-considerations)

## Overview

Suna runs excellently on macOS with proper configuration. This guide covers Mac-specific optimizations, dependency management using Homebrew, and performance tuning for different Mac hardware configurations.

### Supported macOS Versions

- macOS Monterey (12.0+)
- macOS Ventura (13.0+)
- macOS Sonoma (14.0+)
- macOS Sequoia (15.0+)

### Supported Hardware

- Intel-based Macs (x86_64)
- Apple Silicon Macs (M1, M2, M3, M4 series)

## Mac-Specific Prerequisites

### 1. Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Required Dependencies

Run our automated dependency installer:

```bash
chmod +x install_dependencies_mac.sh
./install_dependencies_mac.sh
```

Or install manually:

```bash
# Core dependencies
brew install git python@3.11 node docker
brew install --cask docker

# Supabase CLI
brew install supabase/tap/supabase

# UV for Python package management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Start Docker Desktop
open /Applications/Docker.app
```

### 3. Configure Docker for Mac

For optimal performance on Mac:

1. **Docker Desktop Settings**:
   - Memory: 8GB minimum (16GB recommended for Apple Silicon)
   - CPUs: Use 75% of available cores
   - Disk: 100GB minimum
   - Enable "Use Rosetta for x86/amd64 emulation on Apple Silicon" (Apple Silicon only)

2. **File Sharing**: Ensure your project directory is in Docker's file sharing list

## Quick Start for Mac

### 1. Clone and Setup

```bash
git clone https://github.com/kortix-ai/suna.git
cd suna
```

### 2. Run Mac-Optimized Setup

```bash
python setup_mac.py
```

This Mac-specific setup wizard will:
- Detect your Mac hardware (Intel vs Apple Silicon)
- Install missing dependencies via Homebrew
- Configure optimal Docker settings
- Set up environment files with Mac-specific optimizations
- Configure Supabase with proper permissions
- Start services with Mac performance tuning

### 3. Start Suna

```bash
python start_mac.py
```

## Manual Installation

If you prefer manual setup or need custom configuration:

### 1. Environment Setup

Copy Mac-specific environment templates:

```bash
cp backend/.env.mac.template backend/.env
cp frontend/.env.mac.template frontend/.env.local
```

Edit the files with your API keys and configuration.

### 2. Database Setup

```bash
# Login to Supabase
supabase login

# Link project (replace with your project reference)
supabase link --project-ref your-project-ref

# Push migrations
supabase db push
```

### 3. Install Dependencies

```bash
# Backend dependencies
cd backend
uv sync
cd ..

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 4. Start Services

Using Docker Compose (recommended):

```bash
docker compose -f docker-compose.mac.yaml up -d
```

Or manually:

```bash
# Start infrastructure
docker compose up redis rabbitmq -d

# Start backend (in one terminal)
cd backend && uv run api.py

# Start worker (in another terminal)
cd backend && uv run dramatiq run_agent_background

# Start frontend (in another terminal)
cd frontend && npm run dev
```

## Mac-Specific Configuration

### Docker Compose for Mac

The `docker-compose.mac.yaml` includes Mac-specific optimizations:

- Optimized memory allocation
- Proper volume mounting for macOS
- Network configuration for Docker Desktop
- Apple Silicon compatibility settings

### Environment Variables

Mac-specific environment variables in `.env.mac.template`:

```bash
# Mac-specific Docker settings
DOCKER_PLATFORM=linux/amd64  # For Intel Macs
# DOCKER_PLATFORM=linux/arm64  # For Apple Silicon Macs

# Mac-optimized paths
REDIS_HOST=localhost
RABBITMQ_HOST=localhost

# Performance settings
WORKER_CONCURRENCY=4  # Adjust based on your Mac's CPU cores
```

## Performance Optimization

### For Apple Silicon Macs

1. **Use Native ARM Images**: When available, use ARM64 Docker images
2. **Memory Allocation**: Allocate more memory to Docker (16GB recommended)
3. **Rosetta 2**: Enable for x86 compatibility when needed

```bash
# Check if running on Apple Silicon
uname -m  # Should return "arm64"

# Use Apple Silicon optimized settings
export DOCKER_DEFAULT_PLATFORM=linux/arm64
```

### For Intel Macs

1. **CPU Allocation**: Use 75% of available CPU cores
2. **Memory Management**: Monitor memory usage and adjust Docker limits
3. **Disk Performance**: Use SSD for Docker storage

```bash
# Intel Mac optimizations
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```

### General Mac Optimizations

1. **Close Unnecessary Applications**: Free up system resources
2. **Monitor Activity**: Use Activity Monitor to track resource usage
3. **SSD Storage**: Ensure Docker is using SSD storage
4. **Network**: Use wired connection for better stability

## Troubleshooting Mac Issues

### Common Mac-Specific Issues

#### 1. Docker Desktop Not Starting

```bash
# Reset Docker Desktop
rm -rf ~/Library/Group\ Containers/group.com.docker
rm -rf ~/Library/Containers/com.docker.docker
open /Applications/Docker.app
```

#### 2. Permission Issues

```bash
# Fix Docker permissions
sudo chown -R $(whoami) ~/.docker
```

#### 3. Port Conflicts

```bash
# Check for port conflicts
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :6379  # Redis
lsof -i :5672  # RabbitMQ

# Kill conflicting processes
sudo kill -9 <PID>
```

#### 4. Homebrew Issues

```bash
# Update Homebrew
brew update && brew upgrade

# Fix Homebrew permissions
sudo chown -R $(whoami) $(brew --prefix)/*
```

#### 5. Python Version Conflicts

```bash
# Use specific Python version
brew unlink python@3.12 && brew link python@3.11

# Verify Python version
python3 --version  # Should be 3.11.x
```

### Apple Silicon Specific Issues

#### 1. Rosetta 2 Required

```bash
# Install Rosetta 2 if needed
softwareupdate --install-rosetta
```

#### 2. Architecture Mismatch

```bash
# Force x86 emulation when needed
arch -x86_64 docker compose up
```

### Intel Mac Specific Issues

#### 1. Memory Pressure

- Increase Docker memory allocation
- Close unnecessary applications
- Monitor memory usage in Activity Monitor

#### 2. CPU Throttling

- Ensure proper cooling
- Monitor CPU temperature
- Reduce Docker CPU allocation if overheating

## Apple Silicon vs Intel Considerations

### Apple Silicon Advantages

- **Better Performance**: Native ARM64 execution
- **Energy Efficiency**: Lower power consumption
- **Memory**: Unified memory architecture

### Intel Mac Advantages

- **Compatibility**: Better x86 Docker image support
- **Mature Ecosystem**: More tested configurations

### Choosing the Right Configuration

#### For Apple Silicon Macs:

```yaml
# docker-compose.mac.yaml
services:
  backend:
    platform: linux/arm64
    environment:
      - DOCKER_PLATFORM=linux/arm64
```

#### For Intel Macs:

```yaml
# docker-compose.mac.yaml
services:
  backend:
    platform: linux/amd64
    environment:
      - DOCKER_PLATFORM=linux/amd64
```

## Health Checks

Run Mac-specific health checks:

```bash
python test_mac_deployment.py
```

This will verify:
- Docker Desktop status
- Service connectivity
- Performance metrics
- Mac-specific configurations

## Getting Help

If you encounter issues:

1. Check the [main troubleshooting guide](./SELF-HOSTING.md#troubleshooting)
2. Run the Mac health check script
3. Join the [Suna Discord Community](https://discord.gg/Py6pCBUUPw)
4. Create an issue on [GitHub](https://github.com/kortix-ai/suna/issues) with Mac-specific details

## Performance Monitoring

Monitor your Mac deployment:

```bash
# System resources
top -o cpu

# Docker stats
docker stats

# Service health
curl http://localhost:8000/health
curl http://localhost:3000
```

---

For additional help and community support, visit our [Discord](https://discord.gg/Py6pCBUUPw) or [GitHub repository](https://github.com/kortix-ai/suna).
