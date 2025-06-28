#!/usr/bin/env python3
"""
Suna Mac Deployment Test Suite
This script tests the Mac deployment of Suna to ensure everything is working correctly.
"""

import os
import sys
import time
import platform
import subprocess
import json
import urllib.request
import urllib.error
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

def print_test_header(test_name):
    """Print a test header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}🧪 {test_name}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")

class MacDeploymentTester:
    """Test suite for Mac deployment of Suna."""
    
    def __init__(self):
        self.is_apple_silicon = self.detect_apple_silicon()
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def detect_apple_silicon(self):
        """Detect if running on Apple Silicon."""
        try:
            result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
            return result.stdout.strip() == 'arm64'
        except:
            return False
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results."""
        self.total_tests += 1
        print_test_header(test_name)
        
        try:
            result = test_func()
            if result:
                print_success(f"{test_name} PASSED")
                self.passed_tests += 1
                self.test_results[test_name] = "PASSED"
            else:
                print_error(f"{test_name} FAILED")
                self.failed_tests += 1
                self.test_results[test_name] = "FAILED"
            return result
        except Exception as e:
            print_error(f"{test_name} FAILED with exception: {e}")
            self.failed_tests += 1
            self.test_results[test_name] = f"FAILED: {e}"
            return False
    
    def test_macos_compatibility(self):
        """Test macOS compatibility."""
        if platform.system() != "Darwin":
            print_error("Not running on macOS")
            return False
        
        # Get macOS version
        try:
            result = subprocess.run(['sw_vers', '-productVersion'], capture_output=True, text=True)
            macos_version = result.stdout.strip()
            print_info(f"macOS Version: {macos_version}")
            
            # Check if version is supported (12.0+)
            version_parts = macos_version.split('.')
            major_version = int(version_parts[0])
            
            if major_version >= 12:
                print_success("macOS version is supported")
                return True
            else:
                print_warning("macOS 12.0+ recommended for best performance")
                return True  # Still pass, but with warning
                
        except Exception as e:
            print_error(f"Could not determine macOS version: {e}")
            return False
    
    def test_architecture_detection(self):
        """Test architecture detection."""
        arch_info = "Apple Silicon (ARM64)" if self.is_apple_silicon else "Intel (x86_64)"
        print_info(f"Detected Architecture: {arch_info}")
        
        # Verify with system command
        try:
            result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
            system_arch = result.stdout.strip()
            
            if (self.is_apple_silicon and system_arch == 'arm64') or \
               (not self.is_apple_silicon and system_arch == 'x86_64'):
                print_success("Architecture detection is correct")
                return True
            else:
                print_error(f"Architecture mismatch: detected {arch_info}, system reports {system_arch}")
                return False
        except Exception as e:
            print_error(f"Could not verify architecture: {e}")
            return False
    
    def test_dependencies(self):
        """Test required dependencies."""
        dependencies = {
            'git': 'git --version',
            'python3': 'python3 --version',
            'node': 'node --version',
            'npm': 'npm --version',
            'docker': 'docker --version',
        }
        
        optional_dependencies = {
            'supabase': 'supabase --version',
            'uv': 'uv --version',
        }
        
        all_good = True
        
        # Test required dependencies
        for dep, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True, check=True)
                version = result.stdout.strip().split('\n')[0]
                print_success(f"{dep}: {version}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print_error(f"{dep} is not installed or not working")
                all_good = False
        
        # Test optional dependencies
        for dep, cmd in optional_dependencies.items():
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True, check=True)
                version = result.stdout.strip().split('\n')[0]
                print_success(f"{dep}: {version}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print_warning(f"{dep} is not installed (optional)")
        
        return all_good
    
    def test_docker_status(self):
        """Test Docker Desktop status."""
        try:
            # Check if Docker is running
            subprocess.run(['docker', 'info'], capture_output=True, check=True)
            print_success("Docker Desktop is running")
            
            # Get Docker system info
            result = subprocess.run(['docker', 'system', 'info', '--format', 'json'], 
                                  capture_output=True, text=True, check=True)
            docker_info = json.loads(result.stdout)
            
            # Check memory allocation
            total_memory = docker_info.get('MemTotal', 0)
            if total_memory > 0:
                memory_gb = total_memory / (1024**3)
                print_info(f"Docker Memory: {memory_gb:.1f} GB")
                
                if memory_gb >= 4:
                    print_success("Docker has adequate memory allocation")
                else:
                    print_warning("Docker memory allocation is low (< 4GB)")
            
            # Check CPU allocation
            cpus = docker_info.get('NCPU', 0)
            if cpus > 0:
                print_info(f"Docker CPUs: {cpus} cores")
                print_success("Docker CPU allocation looks good")
            
            return True
            
        except subprocess.CalledProcessError:
            print_error("Docker Desktop is not running")
            return False
        except json.JSONDecodeError:
            print_error("Could not parse Docker system info")
            return False
    
    def test_environment_files(self):
        """Test environment file configuration."""
        files_to_check = [
            'backend/.env',
            'frontend/.env.local'
        ]
        
        all_good = True
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                print_success(f"{file_path} exists")
                
                # Check if file has content
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        print_info(f"{file_path} has configuration")
                    else:
                        print_warning(f"{file_path} is empty")
                        all_good = False
            else:
                print_error(f"{file_path} does not exist")
                all_good = False
        
        return all_good
    
    def test_docker_compose_files(self):
        """Test Docker Compose configuration."""
        compose_files = [
            'docker-compose.yaml',
            'docker-compose.mac.yaml'
        ]
        
        has_compose = False
        
        for file_path in compose_files:
            if os.path.exists(file_path):
                print_success(f"{file_path} exists")
                has_compose = True
                
                # Try to validate the compose file
                try:
                    subprocess.run(['docker', 'compose', '-f', file_path, 'config'], 
                                 capture_output=True, check=True)
                    print_success(f"{file_path} is valid")
                except subprocess.CalledProcessError:
                    print_warning(f"{file_path} has configuration issues")
            else:
                print_info(f"{file_path} does not exist")
        
        return has_compose
    
    def test_service_connectivity(self):
        """Test if services are accessible."""
        services = {
            "Frontend": "http://localhost:3000",
            "Backend Health": "http://localhost:8000/health",
            "Backend API": "http://localhost:8000/api",
        }
        
        accessible_services = 0
        
        for service, url in services.items():
            try:
                response = urllib.request.urlopen(url, timeout=5)
                if response.getcode() == 200:
                    print_success(f"{service} is accessible ({url})")
                    accessible_services += 1
                else:
                    print_warning(f"{service} returned status {response.getcode()}")
            except urllib.error.URLError:
                print_warning(f"{service} is not accessible ({url})")
            except Exception as e:
                print_warning(f"{service} test failed: {e}")
        
        # Consider test passed if at least one service is accessible
        return accessible_services > 0
    
    def test_system_resources(self):
        """Test system resource availability."""
        all_good = True
        
        # Check memory
        try:
            result = subprocess.run(['sysctl', 'hw.memsize'], capture_output=True, text=True)
            memory_bytes = int(result.stdout.split(':')[1].strip())
            memory_gb = memory_bytes / (1024**3)
            
            print_info(f"System Memory: {memory_gb:.1f} GB")
            
            if memory_gb >= 8:
                print_success("System has adequate memory")
            elif memory_gb >= 4:
                print_warning("System memory is low but usable")
            else:
                print_error("System memory is insufficient (< 4GB)")
                all_good = False
                
        except Exception as e:
            print_warning(f"Could not check system memory: {e}")
        
        # Check disk space
        try:
            result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                available = parts[3]
                print_info(f"Available Disk Space: {available}")
                
                # Extract numeric value (assuming format like "50Gi" or "50G")
                import re
                match = re.search(r'(\d+)', available)
                if match:
                    space_num = int(match.group(1))
                    if space_num >= 20:
                        print_success("Adequate disk space available")
                    else:
                        print_warning("Disk space is low")
                        
        except Exception as e:
            print_warning(f"Could not check disk space: {e}")
        
        return all_good
    
    def test_homebrew_setup(self):
        """Test Homebrew installation and setup."""
        try:
            # Check if Homebrew is installed
            result = subprocess.run(['brew', '--version'], capture_output=True, text=True, check=True)
            version = result.stdout.strip().split('\n')[0]
            print_success(f"Homebrew: {version}")
            
            # Check Homebrew prefix
            result = subprocess.run(['brew', '--prefix'], capture_output=True, text=True, check=True)
            prefix = result.stdout.strip()
            
            expected_prefix = "/opt/homebrew" if self.is_apple_silicon else "/usr/local"
            
            if prefix == expected_prefix:
                print_success(f"Homebrew prefix is correct: {prefix}")
                return True
            else:
                print_warning(f"Homebrew prefix unexpected: {prefix} (expected {expected_prefix})")
                return True  # Still functional
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("Homebrew is not installed")
            return False
    
    def test_mac_scripts(self):
        """Test Mac-specific scripts."""
        scripts = [
            'install_dependencies_mac.sh',
            'setup_mac.py',
            'start_mac.py',
            'test_mac_deployment.py'
        ]
        
        all_good = True
        
        for script in scripts:
            if os.path.exists(script):
                print_success(f"{script} exists")
                
                # Check if script is executable
                if os.access(script, os.X_OK):
                    print_success(f"{script} is executable")
                else:
                    print_warning(f"{script} is not executable")
            else:
                print_error(f"{script} does not exist")
                all_good = False
        
        return all_good
    
    def run_all_tests(self):
        """Run all tests."""
        print(f"""
{Colors.BLUE}{Colors.BOLD}
   ███████╗██╗   ██╗███╗   ██╗ █████╗ 
   ██╔════╝██║   ██║████╗  ██║██╔══██╗
   ███████╗██║   ██║██╔██╗ ██║███████║
   ╚════██║██║   ██║██║╚██╗██║██╔══██║
   ███████║╚██████╔╝██║ ╚████║██║  ██║
   ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
                                      
   🧪 Mac Deployment Test Suite
{Colors.ENDC}
""")
        
        arch_info = "Apple Silicon (ARM64)" if self.is_apple_silicon else "Intel (x86_64)"
        print_info(f"Testing on: {arch_info}")
        print()
        
        # Run all tests
        tests = [
            ("macOS Compatibility", self.test_macos_compatibility),
            ("Architecture Detection", self.test_architecture_detection),
            ("Dependencies", self.test_dependencies),
            ("Docker Status", self.test_docker_status),
            ("Environment Files", self.test_environment_files),
            ("Docker Compose Files", self.test_docker_compose_files),
            ("System Resources", self.test_system_resources),
            ("Homebrew Setup", self.test_homebrew_setup),
            ("Mac Scripts", self.test_mac_scripts),
            ("Service Connectivity", self.test_service_connectivity),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print_info("TEST SUMMARY")
        print("="*60)
        
        for test_name, result in self.test_results.items():
            if result == "PASSED":
                print_success(f"{test_name}: {result}")
            elif result == "FAILED":
                print_error(f"{test_name}: {result}")
            else:
                print_error(f"{test_name}: {result}")
        
        print("\n" + "-"*60)
        print_info(f"Total Tests: {self.total_tests}")
        print_success(f"Passed: {self.passed_tests}")
        print_error(f"Failed: {self.failed_tests}")
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        print_info(f"Success Rate: {success_rate:.1f}%")
        
        print("\n" + "="*60)
        
        if self.failed_tests == 0:
            print_success("🎉 All tests passed! Your Mac deployment looks great!")
        elif self.failed_tests <= 2:
            print_warning("⚠️  Some tests failed, but deployment should still work")
            print_info("Check the failed tests above and fix any critical issues")
        else:
            print_error("❌ Multiple tests failed. Please review your deployment")
            print_info("Run setup_mac.py to fix configuration issues")
        
        print("\n" + "="*60)
        
        # Recommendations
        print_info("RECOMMENDATIONS:")
        
        if "Dependencies" in self.test_results and self.test_results["Dependencies"] != "PASSED":
            print("• Run: ./install_dependencies_mac.sh")
        
        if "Environment Files" in self.test_results and self.test_results["Environment Files"] != "PASSED":
            print("• Run: python setup_mac.py")
        
        if "Docker Status" in self.test_results and self.test_results["Docker Status"] != "PASSED":
            print("• Start Docker Desktop from Applications folder")
        
        if "Service Connectivity" in self.test_results and self.test_results["Service Connectivity"] != "PASSED":
            print("• Run: python start_mac.py")
        
        print("• Check docs/MAC-DEPLOYMENT.md for detailed troubleshooting")
        print("• Join Discord for help: https://discord.gg/Py6pCBUUPw")
        
        print("\n" + "="*60)

def main():
    """Main entry point."""
    # Check if running on macOS
    if platform.system() != "Darwin":
        print_error("This test suite is designed for macOS only.")
        sys.exit(1)
    
    tester = MacDeploymentTester()
    tester.run_all_tests()
    
    # Exit with appropriate code
    if tester.failed_tests == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
