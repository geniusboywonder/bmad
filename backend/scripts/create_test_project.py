#!/usr/bin/env python3
"""
Create a test project for policy enforcement testing.

This script creates a project with a specific SDLC phase to test
that policy enforcement blocks/allows agents appropriately.
"""

import sys
import os
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.connection import get_session
from app.database.models import ProjectDB
from app.services.orchestrator.project_manager import ProjectManager

# Use the same project ID from the frontend demo
TEST_PROJECT_ID = "018f9fa8-b639-4858-812d-57f592324a35"


def create_test_project(phase: str = "design"):
    """Create or update test project with specific SDLC phase.

    Args:
        phase: SDLC phase (discover, plan, design, build, validate, launch)
    """
    db: Session = next(get_session())

    try:
        # Use ProjectManager to properly handle phase management
        project_manager = ProjectManager(db)

        # Check if project exists
        project = db.query(ProjectDB).filter(
            ProjectDB.id == UUID(TEST_PROJECT_ID)
        ).first()

        if project:
            # Update existing project
            project_manager.set_current_phase(UUID(TEST_PROJECT_ID), phase)
            print(f"✅ Updated existing project '{project.name}' to phase: {phase}")
        else:
            # Create new project - ProjectManager handles phase initialization
            print(f"✅ Creating new test project...")
            project = ProjectDB(
                id=UUID(TEST_PROJECT_ID),
                name="Policy Enforcement Test Project",
                description="Test project for verifying phase-based policy enforcement",
                status="active"
            )
            db.add(project)
            db.commit()
            db.refresh(project)

            # Set the desired phase
            project_manager.set_current_phase(UUID(TEST_PROJECT_ID), phase)
            print(f"✅ Created new test project in phase: {phase}")

        # Display project info
        current_phase = project_manager.get_current_phase(UUID(TEST_PROJECT_ID))
        print(f"\nProject Details:")
        print(f"  ID: {project.id}")
        print(f"  Name: {project.name}")
        print(f"  Phase: {current_phase}")
        print(f"  Status: {project.status}")

        # Show allowed agents for this phase
        from app.services.orchestrator.phase_policy_service import PhasePolicyService

        policy_service = PhasePolicyService(db)
        decision = policy_service.evaluate(str(project.id), "analyst")

        print(f"\nPolicy for '{current_phase}' phase:")
        print(f"  Allowed agents: {', '.join(decision.allowed_agents)}")
        print(f"  Analyst allowed: {decision.status == 'allowed'}")

        print(f"\n✨ Test project ready for policy enforcement testing!")
        print(f"   Frontend will use project ID: {TEST_PROJECT_ID}")
        print(f"\n💡 To test policy enforcement:")
        print(f"   1. Start backend: uvicorn app.main:app --reload")
        print(f"   2. Open frontend: http://localhost:3000/copilot-demo")
        print(f"   3. Try to use 'analyst' agent - should be blocked in '{current_phase}' phase")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Default to 'design' phase where only architect and orchestrator are allowed
    # This will block analyst, coder, tester, deployer
    phase = sys.argv[1] if len(sys.argv) > 1 else "design"

    valid_phases = ["analyze", "design", "build", "validate", "launch"]
    if phase not in valid_phases:
        print(f"❌ Invalid phase: {phase}")
        print(f"   Valid phases: {', '.join(valid_phases)}")
        sys.exit(1)

    create_test_project(phase)
