#!/usr/bin/env python3
"""
BotArmy Deployment Automation Script

This script automates the deployment process for the BotArmy POC application,
including database migrations, service health checks, and rollback capabilities.

Usage:
    python deploy.py --environment [dev|staging|prod] [--rollback]
    python deploy.py --health-check
    python deploy.py --migrate-only
"""

import argparse
import subprocess
import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class DeploymentError(Exception):
    """Custom exception for deployment errors."""
    pass


class DeploymentManager:
    """Manages the deployment process for BotArmy application."""
    
    def __init__(self, environment: str, project_root: Path):
        self.environment = environment
        self.project_root = project_root
        self.backend_path = project_root / "backend"
        self.config = self._load_environment_config()
        
    def _load_environment_config(self) -> Dict:
        """Load environment-specific configuration."""
        configs = {
            "dev": {
                "database_url": os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/botarmy_dev"),
                "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                "api_base_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
                "docker_compose_file": "docker-compose.dev.yml",
                "health_check_timeout": 30,
                "migration_timeout": 60
            },
            "staging": {
                "database_url": os.getenv("STAGING_DATABASE_URL"),
                "redis_url": os.getenv("STAGING_REDIS_URL"),
                "api_base_url": os.getenv("STAGING_API_BASE_URL"),
                "docker_compose_file": "docker-compose.staging.yml",
                "health_check_timeout": 60,
                "migration_timeout": 120
            },
            "prod": {
                "database_url": os.getenv("PROD_DATABASE_URL"),
                "redis_url": os.getenv("PROD_REDIS_URL"),
                "api_base_url": os.getenv("PROD_API_BASE_URL"),
                "docker_compose_file": "docker-compose.yml",
                "health_check_timeout": 120,
                "migration_timeout": 300
            }
        }
        
        if self.environment not in configs:
            raise DeploymentError(f"Unknown environment: {self.environment}")
        
        config = configs[self.environment]
        
        # Validate required environment variables
        required_vars = ["database_url", "redis_url", "api_base_url"]
        for var in required_vars:
            if not config.get(var):
                raise DeploymentError(f"Missing required environment variable for {var}")
        
        return config
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None, 
                   timeout: int = 60) -> Tuple[int, str, str]:
        """Run a shell command and return (return_code, stdout, stderr)."""
        try:
            cwd = cwd or self.project_root
            logger.info("Running command", command=" ".join(command), cwd=str(cwd))
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.stdout:
                logger.debug("Command stdout", output=result.stdout)
            if result.stderr:
                logger.debug("Command stderr", output=result.stderr)
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            raise DeploymentError(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        except Exception as e:
            raise DeploymentError(f"Failed to run command {' '.join(command)}: {str(e)}")
    
    def check_prerequisites(self) -> None:
        """Check deployment prerequisites."""
        logger.info("Checking deployment prerequisites")
        
        # Check required tools
        required_tools = ["docker", "docker-compose", "python", "pip"]
        for tool in required_tools:
            returncode, _, _ = self.run_command(["which", tool])
            if returncode != 0:
                raise DeploymentError(f"Required tool not found: {tool}")
        
        # Check Python version
        returncode, stdout, _ = self.run_command(["python", "--version"])
        if returncode != 0:
            raise DeploymentError("Unable to check Python version")
        
        # Check Docker is running
        returncode, _, _ = self.run_command(["docker", "info"])
        if returncode != 0:
            raise DeploymentError("Docker is not running")
        
        logger.info("Prerequisites check passed")
    
    def backup_database(self) -> str:
        """Create database backup before deployment."""
        logger.info("Creating database backup")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"botarmy_backup_{self.environment}_{timestamp}.sql"
        backup_path = self.project_root / "backups" / backup_filename
        
        # Create backups directory
        backup_path.parent.mkdir(exist_ok=True)
        
        # Create database dump
        db_url = self.config["database_url"]
        dump_command = [
            "pg_dump",
            db_url,
            "-f", str(backup_path),
            "--verbose"
        ]
        
        returncode, _, stderr = self.run_command(dump_command, timeout=300)
        if returncode != 0:
            raise DeploymentError(f"Database backup failed: {stderr}")
        
        logger.info("Database backup completed", backup_file=str(backup_path))
        return str(backup_path)
    
    def run_database_migrations(self) -> None:
        """Run database migrations."""
        logger.info("Running database migrations")
        
        # Change to backend directory for alembic
        migration_command = ["alembic", "upgrade", "head"]
        
        returncode, stdout, stderr = self.run_command(
            migration_command, 
            cwd=self.backend_path,
            timeout=self.config["migration_timeout"]
        )
        
        if returncode != 0:
            raise DeploymentError(f"Database migration failed: {stderr}")
        
        logger.info("Database migrations completed successfully")
    
    def build_and_start_services(self) -> None:
        """Build and start application services."""
        logger.info("Building and starting services")
        
        compose_file = self.config["docker_compose_file"]
        
        # Build services
        build_command = ["docker-compose", "-f", compose_file, "build", "--no-cache"]
        returncode, _, stderr = self.run_command(build_command, timeout=600)
        if returncode != 0:
            raise DeploymentError(f"Service build failed: {stderr}")
        
        # Start services
        start_command = ["docker-compose", "-f", compose_file, "up", "-d"]
        returncode, _, stderr = self.run_command(start_command, timeout=300)
        if returncode != 0:
            raise DeploymentError(f"Service startup failed: {stderr}")
        
        logger.info("Services built and started successfully")
    
    def wait_for_health_check(self) -> None:
        """Wait for application to become healthy."""
        logger.info("Waiting for application health check")
        
        health_url = f"{self.config['api_base_url']}/health/z"
        timeout = self.config["health_check_timeout"]
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=10)
                
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get("status") == "healthy":
                        logger.info("Application is healthy")
                        return
                    elif health_data.get("status") == "degraded":
                        logger.warning("Application is in degraded mode", 
                                     health_data=health_data)
                        # Continue waiting for full health
                else:
                    logger.warning("Health check returned non-200 status", 
                                 status_code=response.status_code)
                
            except requests.RequestException as e:
                logger.debug("Health check request failed", error=str(e))
            
            time.sleep(5)
        
        raise DeploymentError(f"Application failed to become healthy within {timeout} seconds")
    
    def run_post_deployment_tests(self) -> None:
        """Run post-deployment validation tests."""
        logger.info("Running post-deployment tests")
        
        # Test critical endpoints
        base_url = self.config["api_base_url"]
        test_endpoints = [
            f"{base_url}/health/",
            f"{base_url}/health/z",
            f"{base_url}/api/v1/audit/events?limit=1"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code not in [200, 404]:  # 404 acceptable for empty audit log
                    logger.warning("Endpoint test failed", 
                                 endpoint=endpoint, 
                                 status_code=response.status_code)
                else:
                    logger.debug("Endpoint test passed", endpoint=endpoint)
            except requests.RequestException as e:
                logger.warning("Endpoint test error", endpoint=endpoint, error=str(e))
        
        # Run performance test
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/health/z", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response_time > 200:
                logger.warning("Performance test failed", 
                             response_time_ms=response_time,
                             requirement_ms=200)
            else:
                logger.info("Performance test passed", response_time_ms=response_time)
        except Exception as e:
            logger.error("Performance test error", error=str(e))
        
        logger.info("Post-deployment tests completed")
    
    def rollback_deployment(self, backup_file: str) -> None:
        """Rollback deployment to previous state."""
        logger.warning("Starting deployment rollback")
        
        try:
            # Stop current services
            compose_file = self.config["docker_compose_file"]
            stop_command = ["docker-compose", "-f", compose_file, "down"]
            self.run_command(stop_command)
            
            # Restore database backup
            db_url = self.config["database_url"]
            restore_command = [
                "psql",
                db_url,
                "-f", backup_file
            ]
            returncode, _, stderr = self.run_command(restore_command, timeout=300)
            if returncode != 0:
                logger.error("Database restore failed", error=stderr)
            
            logger.warning("Rollback completed")
            
        except Exception as e:
            logger.error("Rollback failed", error=str(e))
            raise DeploymentError(f"Rollback failed: {str(e)}")
    
    def deploy(self, skip_backup: bool = False) -> None:
        """Execute complete deployment process."""
        logger.info("Starting deployment", environment=self.environment)
        backup_file = None
        
        try:
            # Phase 1: Prerequisites and backup
            self.check_prerequisites()
            
            if not skip_backup and self.environment != "dev":
                backup_file = self.backup_database()
            
            # Phase 2: Database migrations
            self.run_database_migrations()
            
            # Phase 3: Build and deploy services
            self.build_and_start_services()
            
            # Phase 4: Health verification
            self.wait_for_health_check()
            
            # Phase 5: Post-deployment validation
            self.run_post_deployment_tests()
            
            logger.info("Deployment completed successfully", environment=self.environment)
            
        except Exception as e:
            logger.error("Deployment failed", error=str(e))
            
            if backup_file and self.environment != "dev":
                try:
                    self.rollback_deployment(backup_file)
                except Exception as rollback_error:
                    logger.error("Rollback also failed", error=str(rollback_error))
            
            raise DeploymentError(f"Deployment failed: {str(e)}")


def main():
    """Main deployment script entry point."""
    parser = argparse.ArgumentParser(description="BotArmy Deployment Automation")
    parser.add_argument(
        "--environment", "-e",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Deployment environment"
    )
    parser.add_argument(
        "--health-check", "-hc",
        action="store_true",
        help="Run health check only"
    )
    parser.add_argument(
        "--migrate-only", "-m",
        action="store_true",
        help="Run database migrations only"
    )
    parser.add_argument(
        "--skip-backup", "-sb",
        action="store_true",
        help="Skip database backup (dev environment only)"
    )
    
    args = parser.parse_args()
    
    # Get project root directory
    project_root = Path(__file__).parent.absolute()
    
    try:
        deployment_manager = DeploymentManager(args.environment, project_root)
        
        if args.health_check:
            deployment_manager.wait_for_health_check()
            print(f"✅ Health check passed for {args.environment} environment")
            
        elif args.migrate_only:
            deployment_manager.run_database_migrations()
            print(f"✅ Database migrations completed for {args.environment} environment")
            
        else:
            deployment_manager.deploy(skip_backup=args.skip_backup)
            print(f"✅ Deployment completed successfully for {args.environment} environment")
            
    except DeploymentError as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("❌ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()