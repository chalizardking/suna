#!/bin/bash

# Suna Mac Dependencies Installer
# This script installs all required dependencies for running Suna on macOS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅  $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌  $1${NC}"
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script is designed for macOS only."
        exit 1
    fi
    log_success "Running on macOS"
}

# Detect Mac architecture
detect_architecture() {
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        log_info "Detected Apple Silicon Mac (ARM64)"
        export HOMEBREW_PREFIX="/opt/homebrew"
        export DOCKER_DEFAULT_PLATFORM="linux/arm64"
    else
        log_info "Detected Intel Mac (x86_64)"
        export HOMEBREW_PREFIX="/usr/local"
        export DOCKER_DEFAULT_PLATFORM="linux/amd64"
    fi
}

# Check if Homebrew is installed
check_homebrew() {
    if ! command -v brew &> /dev/null; then
        log_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH
        if [[ "$ARCH" == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        log_success "Homebrew installed successfully"
    else
        log_success "Homebrew is already installed"
        # Update Homebrew
        log_info "Updating Homebrew..."
        brew update
    fi
}

# Install Git
install_git() {
    if ! command -v git &> /dev/null; then
        log_info "Installing Git..."
        brew install git
        log_success "Git installed successfully"
    else
        log_success "Git is already installed"
    fi
}

# Install Python 3.11
install_python() {
    if ! command -v python3.11 &> /dev/null; then
        log_info "Installing Python 3.11..."
        brew install python@3.11
        
        # Link Python 3.11
        brew unlink python@3.12 2>/dev/null || true
        brew link python@3.11
        
        log_success "Python 3.11 installed successfully"
    else
        log_success "Python 3.11 is already installed"
    fi
    
    # Verify Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -o "3.11" || echo "")
    if [[ "$PYTHON_VERSION" != "3.11" ]]; then
        log_warning "Python 3.11 is installed but not the default. You may need to adjust your PATH."
    fi
}

# Install UV (Python package manager)
install_uv() {
    if ! command -v uv &> /dev/null; then
        log_info "Installing UV (Python package manager)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Add UV to PATH
        export PATH="$HOME/.cargo/bin:$PATH"
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zprofile
        
        log_success "UV installed successfully"
    else
        log_success "UV is already installed"
    fi
}

# Install Node.js and npm
install_node() {
    if ! command -v node &> /dev/null; then
        log_info "Installing Node.js..."
        brew install node
        log_success "Node.js installed successfully"
    else
        log_success "Node.js is already installed"
    fi
    
    # Verify Node.js version
    NODE_VERSION=$(node --version)
    log_info "Node.js version: $NODE_VERSION"
}

# Install Docker Desktop
install_docker() {
    if ! command -v docker &> /dev/null; then
        log_info "Installing Docker Desktop..."
        brew install --cask docker
        log_success "Docker Desktop installed successfully"
        log_warning "Please start Docker Desktop manually from Applications folder"
    else
        log_success "Docker is already installed"
    fi
    
    # Check if Docker Desktop is running
    if ! docker info &> /dev/null; then
        log_warning "Docker Desktop is not running. Starting Docker Desktop..."
        open /Applications/Docker.app
        log_info "Waiting for Docker Desktop to start..."
        
        # Wait for Docker to be ready
        for i in {1..30}; do
            if docker info &> /dev/null; then
                log_success "Docker Desktop is now running"
                break
            fi
            sleep 2
            echo -n "."
        done
        
        if ! docker info &> /dev/null; then
            log_error "Docker Desktop failed to start. Please start it manually."
        fi
    else
        log_success "Docker Desktop is running"
    fi
}

# Install Supabase CLI
install_supabase() {
    if ! command -v supabase &> /dev/null; then
        log_info "Installing Supabase CLI..."
        brew install supabase/tap/supabase
        log_success "Supabase CLI installed successfully"
    else
        log_success "Supabase CLI is already installed"
    fi
}

# Configure Docker for Mac
configure_docker() {
    log_info "Configuring Docker for optimal Mac performance..."
    
    # Create Docker daemon configuration
    DOCKER_CONFIG_DIR="$HOME/.docker"
    mkdir -p "$DOCKER_CONFIG_DIR"
    
    # Set Docker configuration based on architecture
    if [[ "$ARCH" == "arm64" ]]; then
        cat > "$DOCKER_CONFIG_DIR/daemon.json" << EOF
{
  "experimental": false,
  "features": {
    "buildkit": true
  },
  "builder": {
    "gc": {
      "enabled": true,
      "defaultKeepStorage": "20GB"
    }
  }
}
EOF
    else
        cat > "$DOCKER_CONFIG_DIR/daemon.json" << EOF
{
  "experimental": false,
  "features": {
    "buildkit": true
  },
  "builder": {
    "gc": {
      "enabled": true,
      "defaultKeepStorage": "20GB"
    }
  }
}
EOF
    fi
    
    log_success "Docker configuration updated"
}

# Set up environment variables
setup_environment() {
    log_info "Setting up environment variables..."
    
    # Create or update shell profile
    SHELL_PROFILE=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_PROFILE="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        SHELL_PROFILE="$HOME/.bash_profile"
    fi
    
    if [[ -n "$SHELL_PROFILE" ]]; then
        # Add environment variables
        echo "" >> "$SHELL_PROFILE"
        echo "# Suna Mac Environment Variables" >> "$SHELL_PROFILE"
        echo "export DOCKER_DEFAULT_PLATFORM=$DOCKER_DEFAULT_PLATFORM" >> "$SHELL_PROFILE"
        echo "export HOMEBREW_PREFIX=$HOMEBREW_PREFIX" >> "$SHELL_PROFILE"
        
        if [[ "$ARCH" == "arm64" ]]; then
            echo "export DOCKER_BUILDKIT=1" >> "$SHELL_PROFILE"
        fi
        
        log_success "Environment variables added to $SHELL_PROFILE"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    local errors=0
    
    # Check each dependency
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed"
        ((errors++))
    fi
    
    if ! command -v python3.11 &> /dev/null; then
        log_error "Python 3.11 is not installed"
        ((errors++))
    fi
    
    if ! command -v uv &> /dev/null; then
        log_error "UV is not installed"
        ((errors++))
    fi
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        ((errors++))
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        ((errors++))
    fi
    
    if ! command -v supabase &> /dev/null; then
        log_error "Supabase CLI is not installed"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "All dependencies are installed correctly!"
        return 0
    else
        log_error "$errors dependencies failed to install"
        return 1
    fi
}

# Print system information
print_system_info() {
    log_info "System Information:"
    echo "  macOS Version: $(sw_vers -productVersion)"
    echo "  Architecture: $ARCH"
    echo "  Homebrew Prefix: $HOMEBREW_PREFIX"
    echo "  Docker Platform: $DOCKER_DEFAULT_PLATFORM"
    echo ""
}

# Main installation function
main() {
    echo "🚀 Suna Mac Dependencies Installer"
    echo "=================================="
    echo ""
    
    check_macos
    detect_architecture
    print_system_info
    
    log_info "Starting dependency installation..."
    
    check_homebrew
    install_git
    install_python
    install_uv
    install_node
    install_docker
    install_supabase
    configure_docker
    setup_environment
    
    echo ""
    log_info "Installation completed!"
    
    if verify_installation; then
        echo ""
        log_success "🎉 All dependencies installed successfully!"
        echo ""
        log_info "Next steps:"
        echo "  1. Restart your terminal or run: source ~/.zshrc (or ~/.bash_profile)"
        echo "  2. Run: python setup_mac.py"
        echo ""
        log_info "If Docker Desktop is not running, please start it from Applications folder"
    else
        echo ""
        log_error "Some dependencies failed to install. Please check the errors above."
        exit 1
    fi
}

# Run main function
main "$@"
