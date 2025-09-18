#!/usr/bin/env python3
"""
Phase 1 Environment Setup Script

This script sets up the complete development environment for Phase 1 of the BotArmy implementation,
including database, Redis, LLM providers, and all necessary dependencies.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
import json
import shutil
from datetime import datetime

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class Phase1EnvironmentSetup:
    """Environment setup for Phase 1 components."""

    def __init__(self, verbose=False, dry_run=False):
        self.verbose = verbose
        self.dry_run = dry_run
        self.setup_log = []

    def log(self, message):
        """Log a message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.setup_log.append(log_message)
        print(log_message)

    def run_command(self, command, cwd=None, check=True):
        """Run a shell command."""
        if self.dry_run:
            self.log(f"[DRY RUN] Would run: {' '.join(command)}")
            return True

        if self.verbose:
            self.log(f"Running: {' '.join(command)}")
            if cwd:
                self.log(f"In directory: {cwd}")

        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=not self.verbose,
                text=True,
                check=check
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}")
            return False
        except Exception as e:
            self.log(f"Error running command: {e}")
            return False

    def setup_database(self):
        """Set up PostgreSQL database."""
        self.log("Setting up PostgreSQL database...")

        # Check if PostgreSQL is installed
        if not self.run_command(["which", "psql"], check=False):
            self.log("PostgreSQL not found. Installing...")
            if sys.platform == "darwin":  # macOS
                self.run_command(["brew", "install", "postgresql"])
                self.run_command(["brew", "services", "start", "postgresql"])
            elif sys.platform.startswith("linux"):
                self.run_command(["sudo", "apt-get", "update"])
                self.run_command(["sudo", "apt-get", "install", "-y", "postgresql", "postgresql-contrib"])
                self.run_command(["sudo", "service", "postgresql", "start"])
            else:
                self.log("Please install PostgreSQL manually for your platform")
                return False

        # Create database and user
        db_commands = [
            "CREATE DATABASE bmad_db;",
            "CREATE USER bmad_user WITH PASSWORD 'bmad_password';",
            "GRANT ALL PRIVILEGES ON DATABASE bmad_db TO bmad_user;",
            "ALTER USER bmad_user CREATEDB;"
        ]

        for cmd in db_commands:
            self.run_command([
                "psql", "-U", "postgres", "-c", cmd
            ], check=False)

        # Update .env file
        env_file = Path(".env")
        if not env_file.exists():
            env_file.touch()

        env_content = env_file.read_text() if env_file.exists() else ""
        env_lines = env_content.split('\n') if env_content else []

        # Add database configuration
        db_config = [
            f"DATABASE_URL=postgresql://{os.getenv('DB_USER', 'your_user')}:{os.getenv('DB_PASSWORD', 'your_password')}@localhost:5432/bmad_db",
            "DATABASE_POOL_SIZE=10",
            "DATABASE_MAX_OVERFLOW=20",
            "DATABASE_POOL_TIMEOUT=30"
        ]

        for config in db_config:
            if not any(line.startswith(config.split('=')[0]) for line in env_lines):
                env_lines.append(config)

        env_file.write_text('\n'.join(env_lines))

        self.log("Database setup complete.")
        return True

    def setup_redis(self):
        """Set up Redis for Celery."""
        self.log("Setting up Redis...")

        # Check if Redis is installed
        if not self.run_command(["which", "redis-server"], check=False):
            self.log("Redis not found. Installing...")
            if sys.platform == "darwin":  # macOS
                self.run_command(["brew", "install", "redis"])
                self.run_command(["brew", "services", "start", "redis"])
            elif sys.platform.startswith("linux"):
                self.run_command(["sudo", "apt-get", "install", "-y", "redis-server"])
                self.run_command(["sudo", "service", "redis-server", "start"])
            else:
                self.log("Please install Redis manually for your platform")
                return False

        # Test Redis connection
        if self.run_command(["redis-cli", "ping"], check=False):
            self.log("Redis is running and responding to ping")
        else:
            self.log("Redis connection test failed")
            return False

        # Update .env file with Redis configuration
        env_file = Path(".env")
        env_content = env_file.read_text() if env_file.exists() else ""
        env_lines = env_content.split('\n') if env_content else []

        redis_config = [
            "REDIS_URL=redis://localhost:6379/0",
            "CELERY_BROKER_URL=redis://localhost:6379/0",
            "CELERY_RESULT_BACKEND=redis://localhost:6379/0"
        ]

        for config in redis_config:
            if not any(line.startswith(config.split('=')[0]) for line in env_lines):
                env_lines.append(config)

        env_file.write_text('\n'.join(env_lines))

        self.log("Redis setup complete.")
        return True

    def setup_python_dependencies(self):
        """Install Python dependencies for Phase 1."""
        self.log("Installing Python dependencies...")

        # Core dependencies
        core_deps = [
            "fastapi==0.104.1",
            "sqlalchemy==2.0.43",
            "alembic==1.12.1",
            "psycopg2-binary==2.9.7",
            "redis==5.0.1",
            "celery==5.3.4",
            "pydantic==2.5.0",
            "uvicorn==0.24.0"
        ]

        # LLM provider dependencies
        llm_deps = [
            "openai==1.3.0",
            "anthropic==0.7.8",
            "google-cloud-aiplatform==1.36.4",
            "google-generativeai==0.3.2",
            "tiktoken==0.5.1"
        ]

        # AutoGen and template dependencies
        autogen_deps = [
            "autogen-agentchat==0.2.3",
            "jinja2==3.1.2",
            "pyyaml==6.0.1"
        ]

        # Test dependencies
        test_deps = [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "pytest-cov==4.1.0",
            "pytest-mock==3.12.0"
        ]

        all_deps = core_deps + llm_deps + autogen_deps + test_deps

        # Install dependencies
        for dep in all_deps:
            if not self.dry_run:
                self.run_command([sys.executable, "-m", "pip", "install", dep])
            else:
                self.log(f"[DRY RUN] Would install: {dep}")

        self.log("Python dependencies installation complete.")
        return True

    def setup_llm_providers(self):
        """Set up LLM provider configurations."""
        self.log("Setting up LLM provider configurations...")

        # Create .env entries for LLM providers
        env_file = Path(".env")
        env_content = env_file.read_text() if env_file.exists() else ""
        env_lines = env_content.split('\n') if env_content else []

        llm_config = [
            "# LLM Provider Configuration",
            "OPENAI_API_KEY=your_openai_api_key_here",
            "ANTHROPIC_API_KEY=your_anthropic_api_key_here",
            "GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json",
            "",
            "# Agent-to-LLM Mappings",
            "ANALYST_AGENT_PROVIDER=anthropic",
            "ANALYST_AGENT_MODEL=claude-3-5-sonnet-20241022",
            "ARCHITECT_AGENT_PROVIDER=openai",
            "ARCHITECT_AGENT_MODEL=gpt-4o",
            "CODER_AGENT_PROVIDER=openai",
            "CODER_AGENT_MODEL=gpt-4o",
            "TESTER_AGENT_PROVIDER=gemini",
            "TESTER_AGENT_MODEL=gemini-1.5-pro"
        ]

        for config in llm_config:
            if config and not any(line.strip() == config.strip() for line in env_lines):
                env_lines.append(config)

        env_file.write_text('\n'.join(env_lines))

        # Create Google service account template
        creds_template = {
            "type": "service_account",
            "project_id": "your-gcp-project-id",
            "private_key_id": "your-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key-here\n-----END PRIVATE KEY-----\n",
            "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
        }

        creds_file = Path("gcp-service-account-template.json")
        if not creds_file.exists():
            with open(creds_file, 'w') as f:
                json.dump(creds_template, f, indent=2)

            self.log("Created GCP service account template: gcp-service-account-template.json")
            self.log("Please update this file with your actual GCP credentials")

        self.log("LLM provider setup complete.")
        return True

    def setup_bmad_core(self):
        """Set up BMAD core directory structure."""
        self.log("Setting up BMAD core directory structure...")

        bmad_core_dir = Path("backend/app")
        if not bmad_core_dir.exists():
            bmad_core_dir.mkdir(parents=True)

        # Create subdirectories
        subdirs = [
            "templates",
            "workflows",
            "tasks",
            "data",
            "agents",
            "checklists"
        ]

        for subdir in subdirs:
            (bmad_core_dir / subdir).mkdir(exist_ok=True)

        # Create core configuration file
        core_config = {
            "markdownExploder": True,
            "qa": {
                "qaLocation": "docs/qa"
            },
            "prd": {
                "prdFile": "docs/prd/prd.md",
                "prdVersion": "v4",
                "prdSharded": True,
                "prdShardedLocation": "docs/prd"
            },
            "architecture": {
                "architectureFile": "docs/architecture/architecture.md",
                "architectureVersion": "v4",
                "architectureSharded": True,
                "architectureShardedLocation": "docs/architecture"
            },
            "devLoadAlwaysFiles": [
                "docs/CHANGELOG.md",
                "docs/SOLID.md",
                "docs/CODEPROTOCOL.md",
                "docs/architecture/architecture.md"
            ],
            "devDebugLog": ".ai/debug-log.md",
            "devStoryLocation": "docs/sprints",
            "slashPrefix": "BMad"
        }

        config_file = bmad_core_dir / "core-config.yaml"
        if not config_file.exists():
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(core_config, f, default_flow_style=False)

            self.log("Created BMAD core configuration file")

        # Create sample template
        sample_template = {
            "name": "Sample PRD Template",
            "version": "1.0",
            "sections": [
                {"name": "Overview", "required": True, "description": "High-level project overview"},
                {"name": "Requirements", "required": True, "description": "Functional requirements"},
                {"name": "Acceptance Criteria", "required": True, "description": "Definition of done"}
            ],
            "variables": {
                "project_name": "{{ project_name | default('Sample Project') }}",
                "author": "{{ author | default('Team') }}",
                "date": "{{ date | default('TBD') }}"
            }
        }

        template_file = bmad_core_dir / "templates" / "sample-prd-template.yaml"
        if not template_file.exists():
            import yaml
            with open(template_file, 'w') as f:
                yaml.dump(sample_template, f, default_flow_style=False)

            self.log("Created sample PRD template")

        self.log("BMAD core setup complete.")
        return True

    def setup_database_migrations(self):
        """Set up database migrations with Alembic."""
        self.log("Setting up database migrations...")

        # Initialize Alembic if not already done
        if not Path("backend/alembic").exists():
            self.run_command([
                sys.executable, "-m", "alembic", "init", "backend/alembic"
            ], cwd="backend")

        # Create initial migration
        self.run_command([
            sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "Initial migration"
        ], cwd="backend", check=False)

        # Update alembic.ini with database URL
        alembic_ini = Path("backend/alembic.ini")
        if alembic_ini.exists():
            content = alembic_ini.read_text()
            # Update sqlalchemy.url if it exists
            if "sqlalchemy.url" in content:
                # This would need to be updated with the actual database URL
                pass

        self.log("Database migrations setup complete.")
        return True

    def create_test_data(self):
        """Create test data for Phase 1 components."""
        self.log("Creating test data...")

        # Create test directories
        test_dirs = [
            "backend/test_reports",
            "backend/test_data",
            "docs/qa/gates",
            "docs/qa/assessments"
        ]

        for test_dir in test_dirs:
            Path(test_dir).mkdir(parents=True, exist_ok=True)

        # Create sample test data files
        sample_files = {
            "backend/test_data/sample_project.json": {
                "id": "test-project-123",
                "name": "Sample Project",
                "description": "A test project for Phase 1",
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            "backend/test_data/sample_story.yaml": {
                "title": "Sample User Story",
                "description": "As a user, I want to...",
                "acceptance_criteria": [
                    "Criteria 1",
                    "Criteria 2",
                    "Criteria 3"
                ],
                "status": "draft",
                "priority": "medium"
            }
        }

        import yaml
        for file_path, data in sample_files.items():
            with open(file_path, 'w') as f:
                if file_path.endswith('.json'):
                    json.dump(data, f, indent=2)
                elif file_path.endswith('.yaml'):
                    yaml.dump(data, f, default_flow_style=False)

        self.log("Test data creation complete.")
        return True

    def validate_setup(self):
        """Validate that the setup is complete and working."""
        self.log("Validating Phase 1 setup...")

        validation_checks = []

        # Check database connection
        try:
            import psycopg2
            conn = psycopg2.connect(
                dbname="bmad_db",
                user="bmad_user",
                password="bmad_password",
                host="localhost",
                port="5432"
            )
            conn.close()
            validation_checks.append(("Database connection", True))
        except Exception as e:
            self.log(f"Database connection failed: {e}")
            validation_checks.append(("Database connection", False))

        # Check Redis connection
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            validation_checks.append(("Redis connection", True))
        except Exception as e:
            self.log(f"Redis connection failed: {e}")
            validation_checks.append(("Redis connection", False))

        # Check Python imports
        python_imports = [
            "fastapi",
            "sqlalchemy",
            "celery",
            "openai",
            "anthropic",
            "google.generativeai",
            "autogen",
            "jinja2",
            "pyyaml"
        ]

        for module in python_imports:
            try:
                __import__(module)
                validation_checks.append((f"Import {module}", True))
            except ImportError:
                validation_checks.append((f"Import {module}", False))

        # Check file structure
        required_files = [
            ".env",
            "backend/app/config/core-config.yaml",
            "backend/alembic.ini"
        ]

        for file_path in required_files:
            exists = Path(file_path).exists()
            validation_checks.append((f"File {file_path}", exists))

        # Print validation results
        self.log("\nValidation Results:")
        all_passed = True
        for check, passed in validation_checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"  {status}: {check}")
            if not passed:
                all_passed = False

        return all_passed

    def generate_setup_report(self):
        """Generate a setup report."""
        report = {
            "setup_timestamp": datetime.now().isoformat(),
            "setup_log": self.setup_log,
            "environment_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": str(Path.cwd())
            }
        }

        report_file = f"backend/setup_reports/phase1_setup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.log(f"Setup report saved to: {report_file}")

    def run_full_setup(self):
        """Run the complete Phase 1 environment setup."""
        self.log("Starting Phase 1 environment setup...")

        setup_steps = [
            ("Database Setup", self.setup_database),
            ("Redis Setup", self.setup_redis),
            ("Python Dependencies", self.setup_python_dependencies),
            ("LLM Providers", self.setup_llm_providers),
            ("BMAD Core", self.setup_bmad_core),
            ("Database Migrations", self.setup_database_migrations),
            ("Test Data", self.create_test_data)
        ]

        success_count = 0
        for step_name, step_func in setup_steps:
            self.log(f"\n--- {step_name} ---")
            if step_func():
                success_count += 1
                self.log(f"✅ {step_name} completed successfully")
            else:
                self.log(f"❌ {step_name} failed")

        self.log(f"\nSetup Summary: {success_count}/{len(setup_steps)} steps completed")

        # Validate setup
        if self.validate_setup():
            self.log("✅ Phase 1 setup validation PASSED")
        else:
            self.log("❌ Phase 1 setup validation FAILED")

        # Generate report
        self.generate_setup_report()

        return success_count == len(setup_steps)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Set up Phase 1 environment")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    parser.add_argument(
        "--component",
        choices=["database", "redis", "deps", "llm", "bmad", "migrations", "testdata", "validate", "all"],
        default="all",
        help="Specific component to set up"
    )

    args = parser.parse_args()

    setup = Phase1EnvironmentSetup(verbose=args.verbose, dry_run=args.dry_run)

    if args.component == "all":
        success = setup.run_full_setup()
    else:
        # Run specific component
        component_map = {
            "database": setup.setup_database,
            "redis": setup.setup_redis,
            "deps": setup.setup_python_dependencies,
            "llm": setup.setup_llm_providers,
            "bmad": setup.setup_bmad_core,
            "migrations": setup.setup_database_migrations,
            "testdata": setup.create_test_data,
            "validate": setup.validate_setup
        }

        success = component_map[args.component]()

    if success:
        print("\n🎉 Phase 1 environment setup completed successfully!")
        print("You can now run the Phase 1 tests with: python backend/scripts/run_phase1_tests.py")
    else:
        print("\n❌ Phase 1 environment setup encountered issues.")
        print("Please check the logs above and resolve any failures before proceeding.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
