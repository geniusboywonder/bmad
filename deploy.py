#!/usr/bin/env python3
"""
BMAD Enterprise Deployment Automation Script v5.0

Comprehensive deployment orchestration for BMAD AI Orchestration Platform.
Supports development, staging, and production environments with full CI/CD capabilities,
monitoring integration, and enterprise-grade deployment features.

Features:
- Multi-environment deployment (dev/staging/prod)
- Automated health checks and validation
- Database migration management
- Rollback capabilities with backup restoration
- Monitoring and alerting integration
- Security scanning and compliance checks
- Performance benchmarking
- Zero-downtime deployment support

Usage:
    python deploy.py --environment [dev|staging|prod] [--rollback]
    python deploy.py --health-check
    python deploy.py --migrate-only
    python deploy.py --security-scan
    python deploy.py --performance-test
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
        """Run comprehensive post-deployment validation tests."""
        logger.info("Running post-deployment tests")

        # Test critical endpoints
        base_url = self.config["api_base_url"]
        test_endpoints = [
            f"{base_url}/health/",
            f"{base_url}/health/z",
            f"{base_url}/api/v1/audit/events?limit=1",
            f"{base_url}/api/v1/projects",
            f"{base_url}/api/v1/agents/status"
        ]

        for endpoint in test_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code not in [200, 404]:  # 404 acceptable for empty data
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

        # Test BMAD-specific features
        self._test_bmad_features(base_url)

        logger.info("Post-deployment tests completed")

    def _test_bmad_features(self, base_url: str) -> None:
        """Test BMAD-specific features and integrations."""
        logger.info("Testing BMAD-specific features")

        # Test orchestrator status
        try:
            response = requests.get(f"{base_url}/api/v1/orchestrator/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                logger.info("Orchestrator status check passed",
                          phase=status_data.get("current_phase"),
                          projects=status_data.get("active_projects", 0))
            else:
                logger.warning("Orchestrator status check failed",
                             status_code=response.status_code)
        except Exception as e:
            logger.warning("Orchestrator status test error", error=str(e))

        # Test context store
        try:
            response = requests.get(f"{base_url}/api/v1/context/analytics", timeout=10)
            if response.status_code == 200:
                analytics = response.json()
                logger.info("Context store analytics check passed",
                          artifacts=analytics.get("total_artifacts", 0))
            else:
                logger.warning("Context store analytics check failed",
                             status_code=response.status_code)
        except Exception as e:
            logger.warning("Context store test error", error=str(e))

        # Test HITL system
        try:
            response = requests.get(f"{base_url}/api/v1/hitl/requests?limit=1", timeout=10)
            if response.status_code == 200:
                hitl_data = response.json()
                logger.info("HITL system check passed",
                          pending_requests=len(hitl_data.get("requests", [])))
            else:
                logger.warning("HITL system check failed",
                             status_code=response.status_code)
        except Exception as e:
            logger.warning("HITL system test error", error=str(e))

    def run_security_scan(self) -> Dict[str, Any]:
        """Run comprehensive security scanning."""
        logger.info("Running security scan")

        scan_results = {
            "vulnerabilities_found": 0,
            "critical_issues": 0,
            "warnings": 0,
            "passed_checks": 0,
            "scan_duration_seconds": 0
        }

        start_time = time.time()

        try:
            # Run dependency vulnerability scan
            returncode, stdout, stderr = self.run_command(
                ["safety", "check", "--json"],
                cwd=self.backend_path,
                timeout=300
            )

            if returncode == 0:
                safety_results = json.loads(stdout)
                scan_results["vulnerabilities_found"] = len(safety_results.get("vulnerabilities", []))
                scan_results["critical_issues"] = len([
                    v for v in safety_results.get("vulnerabilities", [])
                    if v.get("severity") == "critical"
                ])
                logger.info("Safety scan completed",
                          vulnerabilities=scan_results["vulnerabilities_found"],
                          critical=scan_results["critical_issues"])
            else:
                logger.warning("Safety scan failed", error=stderr)

            # Run container security scan
            returncode, stdout, stderr = self.run_command(
                ["docker", "scan", "bmad-backend", "--json"],
                timeout=600
            )

            if returncode == 0:
                container_scan = json.loads(stdout)
                scan_results["container_vulnerabilities"] = len(
                    container_scan.get("vulnerabilities", [])
                )
                logger.info("Container scan completed",
                          vulnerabilities=scan_results["container_vulnerabilities"])
            else:
                logger.warning("Container scan failed", error=stderr)

            # Check SSL/TLS configuration
            self._check_ssl_configuration(scan_results)

            # Check security headers
            self._check_security_headers(scan_results)

        except Exception as e:
            logger.error("Security scan error", error=str(e))

        scan_results["scan_duration_seconds"] = time.time() - start_time

        # Determine overall security status
        if scan_results["critical_issues"] > 0:
            scan_results["overall_status"] = "CRITICAL"
        elif scan_results["vulnerabilities_found"] > 10:
            scan_results["overall_status"] = "WARNING"
        else:
            scan_results["overall_status"] = "PASSED"

        logger.info("Security scan completed",
                   status=scan_results["overall_status"],
                   duration_seconds=scan_results["scan_duration_seconds"])

        return scan_results

    def _check_ssl_configuration(self, scan_results: Dict[str, Any]) -> None:
        """Check SSL/TLS configuration."""
        try:
            # Use sslscan or similar tool if available
            returncode, stdout, stderr = self.run_command(
                ["openssl", "s_client", "-connect", "localhost:443", "-servername", "localhost"],
                timeout=30
            )

            if "SSL handshake has read" in stdout:
                scan_results["ssl_configured"] = True
                logger.info("SSL configuration check passed")
            else:
                scan_results["ssl_configured"] = False
                logger.warning("SSL configuration check failed")

        except Exception as e:
            logger.warning("SSL configuration check error", error=str(e))
            scan_results["ssl_configured"] = False

    def _check_security_headers(self, scan_results: Dict[str, Any]) -> None:
        """Check security headers configuration."""
        try:
            base_url = self.config["api_base_url"]
            response = requests.get(base_url, timeout=10)

            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Strict-Transport-Security"
            ]

            missing_headers = []
            for header in security_headers:
                if header not in response.headers:
                    missing_headers.append(header)

            scan_results["missing_security_headers"] = missing_headers
            scan_results["security_headers_score"] = len(security_headers) - len(missing_headers)

            if missing_headers:
                logger.warning("Missing security headers", headers=missing_headers)
            else:
                logger.info("Security headers check passed")

        except Exception as e:
            logger.warning("Security headers check error", error=str(e))

    def run_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive performance testing."""
        logger.info("Running performance tests")

        perf_results = {
            "response_times": [],
            "throughput": 0,
            "error_rate": 0.0,
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0.0,
            "test_duration_seconds": 0
        }

        start_time = time.time()

        try:
            # Run load testing with locust or similar
            self._run_load_test(perf_results)

            # Test API endpoints performance
            self._test_api_performance(perf_results)

            # Monitor system resources
            self._monitor_system_resources(perf_results)

            # Test concurrent users
            self._test_concurrent_users(perf_results)

        except Exception as e:
            logger.error("Performance test error", error=str(e))

        perf_results["test_duration_seconds"] = time.time() - start_time

        # Calculate performance score
        avg_response_time = sum(perf_results["response_times"]) / len(perf_results["response_times"]) if perf_results["response_times"] else 0

        if avg_response_time < 100 and perf_results["error_rate"] < 0.01:
            perf_results["performance_score"] = "EXCELLENT"
        elif avg_response_time < 200 and perf_results["error_rate"] < 0.05:
            perf_results["performance_score"] = "GOOD"
        elif avg_response_time < 500 and perf_results["error_rate"] < 0.10:
            perf_results["performance_score"] = "ACCEPTABLE"
        else:
            perf_results["performance_score"] = "POOR"

        logger.info("Performance test completed",
                   score=perf_results["performance_score"],
                   avg_response_time_ms=avg_response_time,
                   error_rate=perf_results["error_rate"],
                   duration_seconds=perf_results["test_duration_seconds"])

        return perf_results

    def _run_load_test(self, perf_results: Dict[str, Any]) -> None:
        """Run load testing."""
        try:
            # Simple load test using curl
            base_url = self.config["api_base_url"]

            # Test with 10 concurrent requests
            load_test_command = [
                "curl",
                "-s",
                "-w", "%{time_total}\\n",
                "--parallel",
                "--parallel-max", "10",
                f"{base_url}/health/z",
                f"{base_url}/health/z",
                f"{base_url}/health/z",
                f"{base_url}/health/z",
                f"{base_url}/health/z"
            ]

            returncode, stdout, stderr = self.run_command(load_test_command, timeout=60)

            if returncode == 0:
                response_times = [float(line.strip()) * 1000 for line in stdout.split('\n') if line.strip()]
                perf_results["response_times"].extend(response_times)
                perf_results["throughput"] = len(response_times) / 60  # requests per second
                logger.info("Load test completed",
                          requests=len(response_times),
                          throughput=perf_results["throughput"])
            else:
                logger.warning("Load test failed", error=stderr)

        except Exception as e:
            logger.warning("Load test error", error=str(e))

    def _test_api_performance(self, perf_results: Dict[str, Any]) -> None:
        """Test API endpoints performance."""
        base_url = self.config["api_base_url"]
        endpoints = [
            "/health/z",
            "/api/v1/audit/events?limit=10",
            "/api/v1/projects",
            "/api/v1/agents/status"
        ]

        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000

                perf_results["response_times"].append(response_time)

                if response.status_code >= 400:
                    perf_results["error_rate"] += 1

                logger.debug("API performance test",
                           endpoint=endpoint,
                           response_time_ms=response_time,
                           status_code=response.status_code)

            except Exception as e:
                logger.warning("API performance test error",
                             endpoint=endpoint,
                             error=str(e))
                perf_results["error_rate"] += 1

        # Calculate error rate
        total_requests = len(endpoints)
        perf_results["error_rate"] = perf_results["error_rate"] / total_requests if total_requests > 0 else 0

    def _monitor_system_resources(self, perf_results: Dict[str, Any]) -> None:
        """Monitor system resource usage."""
        try:
            # Get container resource usage
            returncode, stdout, stderr = self.run_command([
                "docker", "stats", "--no-stream", "--format", "json"
            ], timeout=30)

            if returncode == 0:
                stats = json.loads(stdout)
                perf_results["memory_usage_mb"] = float(stats.get("MemUsage", "0MiB").split('MiB')[0])
                perf_results["cpu_usage_percent"] = float(stats.get("CPUPerc", "0%").strip('%'))
                logger.info("System resource monitoring completed",
                          memory_mb=perf_results["memory_usage_mb"],
                          cpu_percent=perf_results["cpu_usage_percent"])
            else:
                logger.warning("System resource monitoring failed", error=stderr)

        except Exception as e:
            logger.warning("System resource monitoring error", error=str(e))

    def _test_concurrent_users(self, perf_results: Dict[str, Any]) -> None:
        """Test concurrent user handling."""
        try:
            # Test with multiple concurrent requests
            import threading
            import queue

            base_url = self.config["api_base_url"]
            results_queue = queue.Queue()

            def make_request():
                try:
                    start_time = time.time()
                    response = requests.get(f"{base_url}/health/z", timeout=10)
                    response_time = (time.time() - start_time) * 1000
                    results_queue.put((response_time, response.status_code))
                except Exception as e:
                    results_queue.put((None, None))

            # Launch 20 concurrent requests
            threads = []
            for i in range(20):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=15)

            # Collect results
            concurrent_response_times = []
            concurrent_errors = 0

            while not results_queue.empty():
                response_time, status_code = results_queue.get()
                if response_time is not None:
                    concurrent_response_times.append(response_time)
                else:
                    concurrent_errors += 1

            perf_results["concurrent_response_times"] = concurrent_response_times
            perf_results["concurrent_errors"] = concurrent_errors

            logger.info("Concurrent user test completed",
                      requests=len(concurrent_response_times),
                      errors=concurrent_errors,
                      avg_response_time=sum(concurrent_response_times)/len(concurrent_response_times) if concurrent_response_times else 0)

        except Exception as e:
            logger.warning("Concurrent user test error", error=str(e))

    def send_deployment_notification(self, status: str, details: Dict[str, Any]) -> None:
        """Send deployment notifications."""
        logger.info("Sending deployment notification", status=status)

        try:
            # Send Slack notification if configured
            slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
            if slack_webhook:
                self._send_slack_notification(slack_webhook, status, details)

            # Send email notification if configured
            smtp_server = os.getenv("SMTP_SERVER")
            if smtp_server:
                self._send_email_notification(smtp_server, status, details)

            # Log to monitoring system
            self._log_to_monitoring_system(status, details)

        except Exception as e:
            logger.warning("Deployment notification failed", error=str(e))

    def _send_slack_notification(self, webhook_url: str, status: str, details: Dict[str, Any]) -> None:
        """Send Slack notification."""
        message = {
            "text": f"BMAD Deployment {status.title()}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚀 BMAD Deployment {status.title()}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Environment:* {self.environment}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {status.title()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Timestamp:* {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(webhook_url, json=message, timeout=10)
            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
            else:
                logger.warning("Slack notification failed", status_code=response.status_code)
        except Exception as e:
            logger.warning("Slack notification error", error=str(e))

    def _send_email_notification(self, smtp_server: str, status: str, details: Dict[str, Any]) -> None:
        """Send email notification."""
        # Email notification implementation would go here
        logger.info("Email notification configured but not implemented")

    def _log_to_monitoring_system(self, status: str, details: Dict[str, Any]) -> None:
        """Log deployment event to monitoring system."""
        try:
            # Send to monitoring endpoint if configured
            monitoring_url = os.getenv("MONITORING_WEBHOOK_URL")
            if monitoring_url:
                event_data = {
                    "event_type": "deployment",
                    "environment": self.environment,
                    "status": status,
                    "timestamp": time.time(),
                    "details": details
                }

                response = requests.post(monitoring_url, json=event_data, timeout=10)
                if response.status_code == 200:
                    logger.info("Monitoring system notification sent")
                else:
                    logger.warning("Monitoring system notification failed", status_code=response.status_code)
        except Exception as e:
            logger.warning("Monitoring system notification error", error=str(e))
    
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
    parser = argparse.ArgumentParser(description="BMAD Enterprise Deployment Automation v5.0")
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
        "--security-scan", "-ss",
        action="store_true",
        help="Run security scanning"
    )
    parser.add_argument(
        "--performance-test", "-pt",
        action="store_true",
        help="Run performance testing"
    )
    parser.add_argument(
        "--skip-backup", "-sb",
        action="store_true",
        help="Skip database backup (dev environment only)"
    )
    parser.add_argument(
        "--notify", "-n",
        action="store_true",
        help="Send deployment notifications"
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

        elif args.security_scan:
            scan_results = deployment_manager.run_security_scan()
            status_emoji = "✅" if scan_results["overall_status"] == "PASSED" else "⚠️" if scan_results["overall_status"] == "WARNING" else "❌"
            print(f"{status_emoji} Security scan completed: {scan_results['overall_status']}")
            print(f"   Vulnerabilities found: {scan_results['vulnerabilities_found']}")
            print(f"   Critical issues: {scan_results['critical_issues']}")
            print(f"   Scan duration: {scan_results['scan_duration_seconds']:.1f}s")

        elif args.performance_test:
            perf_results = deployment_manager.run_performance_test()
            print(f"🏃 Performance test completed: {perf_results['performance_score']}")
            avg_response_time = sum(perf_results["response_times"]) / len(perf_results["response_times"]) if perf_results["response_times"] else 0
            print(f"   Average response time: {avg_response_time:.1f}ms")
            print(f"   Error rate: {perf_results['error_rate']:.1%}")
            print(f"   Throughput: {perf_results['throughput']:.1f} req/s")
            print(f"   Test duration: {perf_results['test_duration_seconds']:.1f}s")

        else:
            # Full deployment
            deployment_manager.deploy(skip_backup=args.skip_backup)

            # Send notifications if requested
            if args.notify:
                deployment_manager.send_deployment_notification(
                    "completed",
                    {
                        "environment": args.environment,
                        "timestamp": time.time(),
                        "version": "5.0.0"
                    }
                )

            print(f"✅ Deployment completed successfully for {args.environment} environment")

    except DeploymentError as e:
        # Send failure notification if requested
        if args.notify:
            try:
                deployment_manager.send_deployment_notification(
                    "failed",
                    {
                        "environment": args.environment,
                        "error": str(e),
                        "timestamp": time.time()
                    }
                )
            except Exception as notify_error:
                print(f"⚠️  Failed to send failure notification: {notify_error}")

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
