#!/usr/bin/env python3
"""
Suna Mac Startup Script
This script provides Mac-optimized startup and management for Suna services.
"""

import os
import sys
import time
import platform
import subprocess
import json
import signal
from pathlib import Path

# Colors for output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

def print_info(message):
    """Print an informational message."""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.ENDC}")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✅  {message}{Colors.ENDC}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}❌  {message}{Colors.ENDC}")

class MacSunaManager:
    """Mac-optimized Suna service manager."""
    
    def __init__(self):
        self.is_apple_silicon = self.detect_apple_silicon()
        self.docker_platform = "linux/arm64" if self.is_apple_silicon else "linux/amd64"
        self.compose_file = "docker-compose.mac.yaml"
        self.running_processes = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def detect_apple_silicon(self):
        """Detect if running on Apple Silicon."""
        try:
            result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
            return result.stdout.strip() == 'arm64'
        except:
            return False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n\nReceived shutdown signal. Stopping services...")
        self.stop_services()
        sys.exit(0)
    
    def print_banner(self):
        """Print startup banner."""
        arch_info = "Apple Silicon (ARM64)" if self.is_apple_silicon else "Intel (x86_64)"
        
        print(f"""
{Colors.BLUE}{Colors.BOLD}
   ███████╗██╗   ██╗███╗   ██╗ █████╗ 
   ██╔════╝██║   ██║████╗  ██║██╔══██╗
   ███████╗██║   ██║██╔██╗ ██║███████║
   ╚════██║██║   ██║██║╚██╗██║██╔══██║
   ███████║╚██████╔╝██║ ╚████║██║  ██║
   ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
                                      
   🍎 Mac Service Manager
   Architecture: {arch_info}
{Colors.ENDC}
""")
    
    def check_prerequisites(self):
        """Check if prerequisites are met."""
        print_info("Checking prerequisites...")
        
        # Check if Docker is running
        try:
            subprocess.run(['docker', 'info'], capture_output=True, check=True)
            print_success("Docker Desktop is running")
        except subprocess.CalledProcessError:
            print_error("Docker Desktop is not running")
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
        
        # Check if compose file exists
        if not os.path.exists(self.compose_file):
            print_warning(f"{self.compose_file} not found, using docker-compose.yaml")
            self.compose_file = "docker-compose.yaml"
        
        # Check if environment files exist
        if not os.path.exists("backend/.env"):
            print_error("backend/.env not found. Run setup_mac.py first.")
            return False
        
        if not os.path.exists("frontend/.env.local"):
            print_error("frontend/.env.local not found. Run setup_mac.py first.")
            return False
        
        return True
    
    def get_service_status(self):
        """Get the status of all services."""
        try:
            result = subprocess.run([
                'docker', 'compose', '-f', self.compose_file, 'ps', '--format', 'json'
            ], capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                services = json.loads(result.stdout)
                if not isinstance(services, list):
                    services = [services]
                return services
            return []
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
    
    def start_services(self):
        """Start Suna services using Docker Compose."""
        print_info("Starting Suna services...")
        
        try:
            # Pull latest images if needed
            print_info("Pulling latest images...")
            subprocess.run([
                'docker', 'compose', '-f', self.compose_file, 'pull'
            ], check=True, capture_output=True)
            
            # Start services
            print_info("Starting containers...")
            subprocess.run([
                'docker', 'compose', '-f', self.compose_file, 'up', '-d'
            ], check=True)
            
            print_success("Services started successfully")
            
            # Wait for services to be ready
            print_info("Waiting for services to be ready...")
            time.sleep(10)
            
            # Check service health
            self.check_service_health()
            
            return True
            
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to start services: {e}")
            return False
    
    def stop_services(self):
        """Stop Suna services."""
        print_info("Stopping Suna services...")
        
        try:
            subprocess.run([
                'docker', 'compose', '-f', self.compose_file, 'down'
            ], check=True)
            print_success("Services stopped successfully")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to stop services: {e}")
            return False
    
    def restart_services(self):
        """Restart Suna services."""
        print_info("Restarting Suna services...")
        
        if self.stop_services():
            time.sleep(2)
            return self.start_services()
        return False
    
    def check_service_health(self):
        """Check if services are healthy."""
        services = {
            "Frontend": "http://localhost:3000",
            "Backend": "http://localhost:8000/health",
        }
        
        print_info("Checking service health...")
        
        for service, url in services.items():
            try:
                import urllib.request
                urllib.request.urlopen(url, timeout=10)
                print_success(f"{service} is healthy")
            except Exception as e:
                print_warning(f"{service} is not responding: {e}")
    
    def show_status(self):
        """Show detailed status of all services."""
        print_info("Service Status:")
        print("-" * 50)
        
        services = self.get_service_status()
        
        if not services:
            print_warning("No services are running")
            return
        
        for service in services:
            name = service.get('Name', 'Unknown')
            state = service.get('State', 'Unknown')
            status = service.get('Status', 'Unknown')
            
            if state == 'running':
                print_success(f"{name}: {state} ({status})")
            else:
                print_warning(f"{name}: {state} ({status})")
        
        print("-" * 50)
        
        # Check service health
        self.check_service_health()
    
    def show_logs(self, service=None, follow=False):
        """Show logs for services."""
        cmd = ['docker', 'compose', '-f', self.compose_file, 'logs']
        
        if follow:
            cmd.append('-f')
        
        if service:
            cmd.append(service)
        
        try:
            if follow:
                print_info(f"Following logs for {service or 'all services'}. Press Ctrl+C to stop.")
                subprocess.run(cmd)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to get logs: {e}")
        except KeyboardInterrupt:
            print("\nStopped following logs.")
    
    def open_browser(self):
        """Open Suna in the default browser."""
        try:
            subprocess.run(['open', 'http://localhost:3000'], check=True)
            print_success("Opened Suna in browser")
        except subprocess.CalledProcessError:
            print_error("Failed to open browser")
    
    def show_system_info(self):
        """Show Mac system information relevant to Suna."""
        print_info("Mac System Information:")
        print("-" * 50)
        
        # macOS version
        try:
            result = subprocess.run(['sw_vers', '-productVersion'], capture_output=True, text=True)
            print(f"macOS Version: {result.stdout.strip()}")
        except:
            print("macOS Version: Unknown")
        
        # Architecture
        arch_info = "Apple Silicon (ARM64)" if self.is_apple_silicon else "Intel (x86_64)"
        print(f"Architecture: {arch_info}")
        
        # Memory
        try:
            result = subprocess.run(['sysctl', 'hw.memsize'], capture_output=True, text=True)
            memory_bytes = int(result.stdout.split(':')[1].strip())
            memory_gb = memory_bytes / (1024**3)
            print(f"Total Memory: {memory_gb:.1f} GB")
        except:
            print("Total Memory: Unknown")
        
        # Docker info
        try:
            result = subprocess.run(['docker', 'system', 'info', '--format', 'json'], 
                                  capture_output=True, text=True, check=True)
            docker_info = json.loads(result.stdout)
            
            total_memory = docker_info.get('MemTotal', 0)
            if total_memory > 0:
                memory_gb = total_memory / (1024**3)
                print(f"Docker Memory: {memory_gb:.1f} GB")
            
            cpus = docker_info.get('NCPU', 0)
            if cpus > 0:
                print(f"Docker CPUs: {cpus} cores")
                
        except:
            print("Docker Info: Not available")
        
        print("-" * 50)
    
    def cleanup_docker(self):
        """Clean up Docker resources."""
        print_info("Cleaning up Docker resources...")
        
        try:
            # Remove unused containers, networks, images
            subprocess.run(['docker', 'system', 'prune', '-f'], check=True)
            print_success("Docker cleanup completed")
        except subprocess.CalledProcessError as e:
            print_error(f"Docker cleanup failed: {e}")
    
    def show_help(self):
        """Show help information."""
        print(f"""
{Colors.BOLD}Suna Mac Service Manager{Colors.ENDC}

{Colors.CYAN}Usage:{Colors.ENDC}
  python start_mac.py [command]

{Colors.CYAN}Commands:{Colors.ENDC}
  start     Start all Suna services (default)
  stop      Stop all Suna services
  restart   Restart all Suna services
  status    Show service status
  logs      Show service logs
  follow    Follow service logs in real-time
  open      Open Suna in browser
  info      Show system information
  cleanup   Clean up Docker resources
  help      Show this help message

{Colors.CYAN}Examples:{Colors.ENDC}
  python start_mac.py              # Start services
  python start_mac.py status       # Check status
  python start_mac.py logs backend # Show backend logs
  python start_mac.py follow       # Follow all logs
  python start_mac.py cleanup      # Clean up Docker

{Colors.CYAN}Mac-Specific Features:{Colors.ENDC}
  • Automatic Docker Desktop startup
  • Architecture detection (Intel/Apple Silicon)
  • Optimized resource allocation
  • Mac-specific health checks

{Colors.CYAN}Troubleshooting:{Colors.ENDC}
  • If services fail to start, check Docker Desktop
  • Use 'python start_mac.py cleanup' to free up space
  • Check logs with 'python start_mac.py logs'
  • Restart Docker Desktop if needed

{Colors.CYAN}Documentation:{Colors.ENDC}
  • Mac Guide: docs/MAC-DEPLOYMENT.md
  • General Guide: docs/SELF-HOSTING.md
  • Discord: https://discord.gg/Py6pCBUUPw
""")

def main():
    """Main entry point."""
    # Check if running on macOS
    if platform.system() != "Darwin":
        print_error("This script is designed for macOS only.")
        print_info("For other platforms, use: python start.py")
        sys.exit(1)
    
    manager = MacSunaManager()
    
    # Parse command line arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    if command == "help":
        manager.show_help()
        return
    
    manager.print_banner()
    
    # Check prerequisites for most commands
    if command not in ["help", "info"]:
        if not manager.check_prerequisites():
            print_error("Prerequisites not met. Please fix the issues above.")
            sys.exit(1)
    
    # Execute command
    if command == "start":
        if manager.start_services():
            print_success("\n🎉 Suna is now running!")
            print_info("Frontend: http://localhost:3000")
            print_info("Backend: http://localhost:8000")
            print_info("Use 'python start_mac.py stop' to stop services")
        else:
            sys.exit(1)
    
    elif command == "stop":
        if manager.stop_services():
            print_success("Suna services stopped")
        else:
            sys.exit(1)
    
    elif command == "restart":
        if manager.restart_services():
            print_success("Suna services restarted")
        else:
            sys.exit(1)
    
    elif command == "status":
        manager.show_status()
    
    elif command == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        manager.show_logs(service)
    
    elif command == "follow":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        manager.show_logs(service, follow=True)
    
    elif command == "open":
        manager.open_browser()
    
    elif command == "info":
        manager.show_system_info()
    
    elif command == "cleanup":
        manager.cleanup_docker()
    
    else:
        print_error(f"Unknown command: {command}")
        print_info("Use 'python start_mac.py help' for available commands")
        sys.exit(1)

if __name__ == "__main__":
    main()
