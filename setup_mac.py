#!/usr/bin/env python3
"""
Suna Mac-Optimized Setup Wizard
This script provides a Mac-specific setup experience for Suna with optimizations
for both Intel and Apple Silicon Macs.
"""

import os
import sys
import time
import platform
import subprocess
import re
import json
import secrets
import base64
import shutil
from pathlib import Path

# Import the base setup functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from setup import (
    Colors, print_banner, print_step, print_info, print_success, 
    print_warning, print_error, parse_env_file, load_existing_env_vars,
    generate_encryption_key, mask_sensitive_value, validate_url,
    validate_api_key, SetupWizard
)

class MacSunaSetup(SetupWizard):
    """Mac-optimized version of the Suna setup wizard."""
    
    def __init__(self):
        super().__init__()
        self.is_apple_silicon = self.detect_apple_silicon()
        self.homebrew_prefix = self.get_homebrew_prefix()
        self.docker_platform = "linux/arm64" if self.is_apple_silicon else "linux/amd64"
        
    def detect_apple_silicon(self):
        """Detect if running on Apple Silicon."""
        try:
            result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
            return result.stdout.strip() == 'arm64'
        except:
            return False
    
    def get_homebrew_prefix(self):
        """Get the Homebrew prefix based on architecture."""
        if self.is_apple_silicon:
            return "/opt/homebrew"
        else:
            return "/usr/local"
    
    def print_mac_banner(self):
        """Print Mac-specific banner."""
        arch_info = "Apple Silicon (ARM64)" if self.is_apple_silicon else "Intel (x86_64)"
        macos_version = self.get_macos_version()
        
        print_banner()
        print(f"{Colors.CYAN}🍎 Mac-Optimized Setup for Suna{Colors.ENDC}")
        print(f"{Colors.CYAN}Architecture: {arch_info}{Colors.ENDC}")
        print(f"{Colors.CYAN}macOS Version: {macos_version}{Colors.ENDC}")
        print(f"{Colors.CYAN}Homebrew Prefix: {self.homebrew_prefix}{Colors.ENDC}")
        print(f"{Colors.CYAN}Docker Platform: {self.docker_platform}{Colors.ENDC}")
        print()
    
    def get_macos_version(self):
        """Get macOS version."""
        try:
            result = subprocess.run(['sw_vers', '-productVersion'], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "Unknown"
    
    def check_mac_prerequisites(self):
        """Check Mac-specific prerequisites."""
        print_step(1, self.total_steps, "Checking Mac Prerequisites")
        
        # Check macOS version
        macos_version = self.get_macos_version()
        print_info(f"macOS Version: {macos_version}")
        
        # Check if running on supported macOS version
        try:
            version_parts = macos_version.split('.')
            major_version = int(version_parts[0])
            if major_version < 12:
                print_warning("macOS 12.0 (Monterey) or later is recommended for best performance")
        except:
            pass
        
        # Check available memory
        self.check_system_memory()
        
        # Check available disk space
        self.check_disk_space()
        
        # Check dependencies
        missing_deps = self.check_dependencies()
        
        if missing_deps:
            print_warning(f"Missing dependencies: {', '.join(missing_deps)}")
            print_info("Run './install_dependencies_mac.sh' to install missing dependencies")
            
            install_deps = input("Would you like to install missing dependencies now? (Y/n): ").lower().strip()
            if install_deps != 'n':
                self.install_missing_dependencies()
        else:
            print_success("All dependencies are installed")
    
    def check_system_memory(self):
        """Check available system memory."""
        try:
            result = subprocess.run(['sysctl', 'hw.memsize'], capture_output=True, text=True)
            memory_bytes = int(result.stdout.split(':')[1].strip())
            memory_gb = memory_bytes / (1024**3)
            
            print_info(f"Available Memory: {memory_gb:.1f} GB")
            
            if memory_gb < 8:
                print_warning("8GB+ RAM recommended for optimal performance")
            elif memory_gb >= 16:
                print_success("Excellent memory configuration for Suna")
        except:
            print_warning("Could not determine system memory")
    
    def check_disk_space(self):
        """Check available disk space."""
        try:
            result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                available = parts[3]
                print_info(f"Available Disk Space: {available}")
        except:
            print_warning("Could not determine available disk space")
    
    def check_dependencies(self):
        """Check for required dependencies."""
        dependencies = {
            'git': 'git --version',
            'python3.11': 'python3.11 --version',
            'node': 'node --version',
            'npm': 'npm --version',
            'docker': 'docker --version',
            'supabase': 'supabase --version',
            'uv': 'uv --version'
        }
        
        missing = []
        for dep, cmd in dependencies.items():
            try:
                subprocess.run(cmd.split(), capture_output=True, check=True)
                print_success(f"{dep} is installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print_error(f"{dep} is not installed")
                missing.append(dep)
        
        return missing
    
    def install_missing_dependencies(self):
        """Install missing dependencies using the Mac installer script."""
        print_info("Installing missing dependencies...")
        try:
            script_path = os.path.join(os.getcwd(), 'install_dependencies_mac.sh')
            if os.path.exists(script_path):
                subprocess.run(['bash', script_path], check=True)
                print_success("Dependencies installed successfully")
            else:
                print_error("install_dependencies_mac.sh not found")
        except subprocess.CalledProcessError:
            print_error("Failed to install dependencies")
    
    def check_docker_status(self):
        """Check Docker Desktop status and configuration."""
        print_step(2, self.total_steps, "Checking Docker Configuration")
        
        # Check if Docker is running
        try:
            subprocess.run(['docker', 'info'], capture_output=True, check=True)
            print_success("Docker Desktop is running")
        except subprocess.CalledProcessError:
            print_warning("Docker Desktop is not running")
            print_info("Starting Docker Desktop...")
            try:
                subprocess.run(['open', '/Applications/Docker.app'], check=True)
                print_info("Waiting for Docker Desktop to start...")
                
                # Wait for Docker to be ready
                for i in range(30):
                    try:
                        subprocess.run(['docker', 'info'], capture_output=True, check=True)
                        print_success("Docker Desktop is now running")
                        break
                    except subprocess.CalledProcessError:
                        time.sleep(2)
                        print(".", end="", flush=True)
                else:
                    print_error("Docker Desktop failed to start")
                    return False
            except subprocess.CalledProcessError:
                print_error("Failed to start Docker Desktop")
                return False
        
        # Check Docker configuration
        self.check_docker_resources()
        return True
    
    def check_docker_resources(self):
        """Check Docker resource allocation."""
        try:
            # Get Docker system info
            result = subprocess.run(['docker', 'system', 'info', '--format', 'json'], 
                                  capture_output=True, text=True, check=True)
            docker_info = json.loads(result.stdout)
            
            # Check memory allocation
            total_memory = docker_info.get('MemTotal', 0)
            if total_memory > 0:
                memory_gb = total_memory / (1024**3)
                print_info(f"Docker Memory Allocation: {memory_gb:.1f} GB")
                
                if memory_gb < 4:
                    print_warning("Consider increasing Docker memory allocation to 8GB+")
                elif memory_gb >= 8:
                    print_success("Good Docker memory allocation")
            
            # Check CPU allocation
            cpus = docker_info.get('NCPU', 0)
            if cpus > 0:
                print_info(f"Docker CPU Allocation: {cpus} cores")
                
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            print_warning("Could not retrieve Docker resource information")
    
    def configure_mac_env_files(self):
        """Configure Mac-specific environment files."""
        print_step(11, self.total_steps, "Configuring Mac Environment Files")
        
        # Determine setup method
        is_docker = self.env_vars["setup_method"] == "docker"
        
        # Mac-specific host configuration
        if is_docker:
            redis_host = "redis"
            rabbitmq_host = "rabbitmq"
        else:
            redis_host = "localhost"
            rabbitmq_host = "localhost"
        
        # Backend .env with Mac optimizations
        backend_env = {
            "ENV_MODE": "local",
            **self.env_vars["supabase"],
            "REDIS_HOST": redis_host,
            "REDIS_PORT": "6379",
            "RABBITMQ_HOST": rabbitmq_host,
            "RABBITMQ_PORT": "5672",
            **self.env_vars["llm"],
            **self.env_vars["search"],
            **self.env_vars["rapidapi"],
            **self.env_vars["smithery"],
            **self.env_vars["qstash"],
            **self.env_vars["mcp"],
            **self.env_vars["daytona"],
            "NEXT_PUBLIC_URL": "http://localhost:3000",
            # Mac-specific optimizations
            "DOCKER_PLATFORM": self.docker_platform,
            "HOMEBREW_PREFIX": self.homebrew_prefix,
            "MAC_ARCHITECTURE": "arm64" if self.is_apple_silicon else "x86_64",
        }
        
        # Add Apple Silicon specific settings
        if self.is_apple_silicon:
            backend_env["DOCKER_BUILDKIT"] = "1"
            backend_env["DOCKER_DEFAULT_PLATFORM"] = "linux/arm64"
        
        backend_env_content = f"# Generated by Suna Mac setup script\n"
        backend_env_content += f"# Architecture: {'Apple Silicon' if self.is_apple_silicon else 'Intel'}\n"
        backend_env_content += f"# Setup Method: {self.env_vars['setup_method']}\n\n"
        
        for key, value in backend_env.items():
            backend_env_content += f"{key}={value or ''}\n"
        
        with open(os.path.join("backend", ".env"), "w") as f:
            f.write(backend_env_content)
        print_success("Created backend/.env file with Mac optimizations")
        
        # Frontend .env.local
        frontend_env = {
            "NEXT_PUBLIC_SUPABASE_URL": self.env_vars["supabase"]["SUPABASE_URL"],
            "NEXT_PUBLIC_SUPABASE_ANON_KEY": self.env_vars["supabase"]["SUPABASE_ANON_KEY"],
            "NEXT_PUBLIC_BACKEND_URL": "http://localhost:8000/api",
            "NEXT_PUBLIC_URL": "http://localhost:3000",
            "NEXT_PUBLIC_ENV_MODE": "LOCAL",
            # Mac-specific frontend settings
            "NEXT_PUBLIC_MAC_ARCHITECTURE": "arm64" if self.is_apple_silicon else "x86_64",
        }
        
        frontend_env_content = f"# Generated by Suna Mac setup script\n"
        frontend_env_content += f"# Architecture: {'Apple Silicon' if self.is_apple_silicon else 'Intel'}\n\n"
        
        for key, value in frontend_env.items():
            frontend_env_content += f"{key}={value or ''}\n"
        
        with open(os.path.join("frontend", ".env.local"), "w") as f:
            f.write(frontend_env_content)
        print_success("Created frontend/.env.local file with Mac optimizations")
    
    def create_mac_docker_compose(self):
        """Create Mac-optimized Docker Compose file."""
        print_info("Creating Mac-optimized Docker Compose configuration...")
        
        # Read the original docker-compose.yaml
        with open("docker-compose.yaml", "r") as f:
            original_content = f.read()
        
        # Create Mac-specific modifications
        mac_compose_content = f"""# Mac-optimized Docker Compose for Suna
# Architecture: {'Apple Silicon (ARM64)' if self.is_apple_silicon else 'Intel (x86_64)'}
# Generated by Suna Mac setup script

{original_content}

# Mac-specific service overrides
x-mac-common: &mac-common
  platform: {self.docker_platform}
  
services:
  backend:
    <<: *mac-common
    environment:
      - DOCKER_PLATFORM={self.docker_platform}
      - MAC_ARCHITECTURE={'arm64' if self.is_apple_silicon else 'x86_64'}
    deploy:
      resources:
        limits:
          memory: {'8G' if self.is_apple_silicon else '6G'}
        reservations:
          memory: {'4G' if self.is_apple_silicon else '3G'}
  
  frontend:
    <<: *mac-common
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
  
  redis:
    <<: *mac-common
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
  
  rabbitmq:
    <<: *mac-common
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
"""
        
        with open("docker-compose.mac.yaml", "w") as f:
            f.write(mac_compose_content)
        
        print_success("Created docker-compose.mac.yaml with Mac optimizations")
    
    def install_mac_dependencies(self):
        """Install Mac-specific dependencies."""
        print_step(13, self.total_steps, "Installing Mac Dependencies")
        
        # Backend dependencies
        print_info("Installing backend dependencies with UV...")
        try:
            subprocess.run(["uv", "sync"], cwd="backend", check=True, capture_output=True)
            print_success("Backend dependencies installed")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install backend dependencies: {e}")
            return False
        
        # Frontend dependencies
        print_info("Installing frontend dependencies with npm...")
        try:
            subprocess.run(["npm", "install"], cwd="frontend", check=True, capture_output=True)
            print_success("Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install frontend dependencies: {e}")
            return False
        
        return True
    
    def start_mac_services(self):
        """Start services with Mac optimizations."""
        print_step(14, self.total_steps, "Starting Suna Services")
        
        setup_method = self.env_vars.get("setup_method", "docker")
        
        if setup_method == "docker":
            print_info("Starting services with Docker Compose (Mac optimized)...")
            try:
                subprocess.run([
                    "docker", "compose", "-f", "docker-compose.mac.yaml", "up", "-d"
                ], check=True)
                print_success("Services started successfully")
                
                # Wait for services to be ready
                print_info("Waiting for services to be ready...")
                time.sleep(10)
                
                # Check service health
                self.check_service_health()
                
            except subprocess.CalledProcessError as e:
                print_error(f"Failed to start services: {e}")
                return False
        else:
            print_info("Starting services manually...")
            print_info("Please start the services manually:")
            print("  1. Start infrastructure: docker compose up redis rabbitmq -d")
            print("  2. Start backend: cd backend && uv run api.py")
            print("  3. Start worker: cd backend && uv run dramatiq run_agent_background")
            print("  4. Start frontend: cd frontend && npm run dev")
        
        return True
    
    def check_service_health(self):
        """Check if services are healthy."""
        services = {
            "Frontend": "http://localhost:3000",
            "Backend": "http://localhost:8000/health",
        }
        
        for service, url in services.items():
            try:
                import urllib.request
                urllib.request.urlopen(url, timeout=5)
                print_success(f"{service} is healthy")
            except:
                print_warning(f"{service} is not responding yet")
    
    def run_mac_setup(self):
        """Run the complete Mac setup process."""
        self.print_mac_banner()
        
        # Load existing progress
        self.load_progress()
        
        try:
            # Mac-specific steps
            if self.current_step <= 1:
                self.check_mac_prerequisites()
                self.save_progress(1)
            
            if self.current_step <= 2:
                if not self.check_docker_status():
                    print_error("Docker setup failed. Please fix Docker issues and try again.")
                    return False
                self.save_progress(2)
            
            # Run standard setup steps (3-10)
            if self.current_step <= 3:
                self.collect_setup_method()
                self.save_progress(3)
            
            if self.current_step <= 4:
                self.collect_supabase_keys()
                self.save_progress(4)
            
            if self.current_step <= 5:
                self.collect_daytona_keys()
                self.save_progress(5)
            
            if self.current_step <= 6:
                self.collect_llm_keys()
                self.save_progress(6)
            
            if self.current_step <= 7:
                self.collect_search_keys()
                self.save_progress(7)
            
            if self.current_step <= 8:
                self.collect_rapidapi_keys()
                self.save_progress(8)
            
            if self.current_step <= 9:
                self.collect_smithery_keys()
                self.save_progress(9)
            
            if self.current_step <= 10:
                self.collect_qstash_keys()
                self.save_progress(10)
            
            if self.current_step <= 11:
                self.collect_mcp_keys()
                self.save_progress(11)
            
            # Mac-specific configuration
            if self.current_step <= 12:
                self.configure_mac_env_files()
                self.create_mac_docker_compose()
                self.save_progress(12)
            
            if self.current_step <= 13:
                self.setup_supabase_database()
                self.save_progress(13)
            
            if self.current_step <= 14:
                if not self.install_mac_dependencies():
                    print_error("Dependency installation failed")
                    return False
                self.save_progress(14)
            
            if self.current_step <= 15:
                if not self.start_mac_services():
                    print_error("Service startup failed")
                    return False
                self.save_progress(15)
            
            # Setup complete
            self.print_completion_message()
            self.cleanup_progress()
            return True
            
        except KeyboardInterrupt:
            print("\n\nSetup interrupted. Progress has been saved.")
            print("Run 'python setup_mac.py' again to continue from where you left off.")
            return False
        except Exception as e:
            print_error(f"Setup failed: {e}")
            return False
    
    def print_completion_message(self):
        """Print Mac-specific completion message."""
        print("\n" + "="*60)
        print_success("🎉 Suna Mac Setup Complete!")
        print("="*60)
        
        arch_info = "Apple Silicon" if self.is_apple_silicon else "Intel"
        print(f"\n{Colors.CYAN}Mac Configuration:{Colors.ENDC}")
        print(f"  Architecture: {arch_info}")
        print(f"  Docker Platform: {self.docker_platform}")
        print(f"  Homebrew Prefix: {self.homebrew_prefix}")
        
        print(f"\n{Colors.GREEN}🌐 Access your Suna instance:{Colors.ENDC}")
        print(f"  Frontend: http://localhost:3000")
        print(f"  Backend API: http://localhost:8000")
        
        print(f"\n{Colors.BLUE}📋 Next steps:{Colors.ENDC}")
        print("  1. Open http://localhost:3000 in your browser")
        print("  2. Create your first account using Supabase authentication")
        print("  3. Start building with Suna!")
        
        print(f"\n{Colors.YELLOW}🔧 Management commands:{Colors.ENDC}")
        print("  Start services: python start_mac.py")
        print("  Stop services: docker compose -f docker-compose.mac.yaml down")
        print("  View logs: docker compose -f docker-compose.mac.yaml logs -f")
        print("  Health check: python test_mac_deployment.py")
        
        print(f"\n{Colors.CYAN}💡 Mac-specific tips:{Colors.ENDC}")
        if self.is_apple_silicon:
            print("  • You're running on Apple Silicon - enjoy the performance!")
            print("  • Some Docker images may use Rosetta 2 for x86 compatibility")
        else:
            print("  • You're running on Intel - ensure adequate cooling for intensive tasks")
        print("  • Monitor Docker resource usage in Activity Monitor")
        print("  • Use 'docker system prune' periodically to clean up unused resources")
        
        print(f"\n{Colors.GREEN}🆘 Need help?{Colors.ENDC}")
        print("  • Documentation: docs/MAC-DEPLOYMENT.md")
        print("  • Discord: https://discord.gg/Py6pCBUUPw")
        print("  • GitHub: https://github.com/kortix-ai/suna")
        
        print("\n" + "="*60)


def main():
    """Main entry point for Mac setup."""
    # Check if running on macOS
    if platform.system() != "Darwin":
        print_error("This script is designed for macOS only.")
        print_info("For other platforms, use: python setup.py")
        sys.exit(1)
    
    # Initialize and run Mac setup
    setup = MacSunaSetup()
    setup.total_steps = 15  # Mac setup has 15 steps
    
    success = setup.run_mac_setup()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
