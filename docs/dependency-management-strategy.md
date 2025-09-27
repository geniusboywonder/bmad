# BMAD Dependency Management Strategy

## Executive Summary

This document outlines a comprehensive strategy for managing dependencies in the BMAD project, ensuring we stay current with the latest versions of CopilotKit, shadcn/ui, Google ADK, and other critical dependencies while avoiding breaking changes.

## Current State Analysis

### Frontend Dependencies (package.json)

**Critical Dependencies:**
- **CopilotKit**: `^1.10.3` → Latest: `1.10.4` ✅ Minor update
- **Next.js**: `^15.5.2` → Latest: `15.5.4` ✅ Patch update
- **React**: `^19` → Latest: `19` ✅ Up to date
- **shadcn/ui (Radix UI)**: Multiple components with significant updates available
- **Tailwind CSS**: `^3.4.17` → Latest: `4.1.13` ⚠️ Major version update

**Major Updates Identified:**
- **Radix UI Components**: Most components have major version updates (1.x → 1.3.x)
- **Tailwind CSS**: v3 → v4 (significant changes)
- **Zod**: `3.25.67` → `4.1.11` (major version)
- **React Window**: `1.8.11` → `2.1.2` (major version)

### Backend Dependencies (requirements.txt)

**Critical Dependencies:**
- **Google ADK**: `1.14.1` → Latest: `1.15.1` ✅ Minor update
- **FastAPI**: `0.115.0` → Latest: `0.117.1` ✅ Minor update
- **Google Cloud AI Platform**: `1.113.0` → Latest: `1.117.0` ✅ Minor update
- **Pydantic**: `2.10.0` → Current: `2.33.2` → Latest: `2.39.0` ✅ Patch updates

**Significant Updates:**
- **Celery**: `5.3.4` → `5.5.3` (minor version)
- **Redis**: `5.0.1` → `6.4.0` (major version)
- **Structlog**: `23.2.0` → `25.4.0` (major version)

## Breaking Changes Analysis

### CopilotKit 1.10.4 Updates

**✅ Safe to Upgrade:**
- **No Breaking Changes**: Version 1.10.4 is a patch release with bug fixes and improvements
- **Key Improvements**:
  - Enhanced error handling with custom error rendering
  - Fixed chat state management issues
  - Improved HITL (Human-in-the-Loop) functionality
  - Updated AG-UI LangGraph packages

**Migration Steps:**
```bash
npm update @copilotkit/react-core @copilotkit/react-textarea @copilotkit/react-ui @copilotkit/runtime
```

### Google ADK 1.15.1 Updates

**✅ Safe to Upgrade:**
- **No Breaking Changes**: Version 1.15.1 is a minor release
- **Previous Major Changes (1.0.0)** already implemented:
  - Asynchronous operations
  - MCP Toolbox integration
  - Evaluation schema improvements

**Migration Steps:**
```bash
pip install google-adk==1.15.1
```

### shadcn/ui and Radix UI Updates

**⚠️ Mixed Safety:**
- **shadcn/ui CLI 3.0**: ✅ No breaking changes for existing components
- **Radix UI Components**: ⚠️ Many major version updates available
- **Tailwind v4**: ⚠️ Major version change (optional)

**Current Project Status:**
- Using individual Radix UI packages (recommended approach)
- Tailwind v3 stable (can migrate to v4 later)
- All existing components will continue to work

## Dependency Management Strategy

### 1. Tier-Based Update Approach

#### **Tier 1: Safe Updates (Immediate)**
Apply immediately as they contain only bug fixes and security patches:

**Frontend:**
```bash
# CopilotKit updates
npm update @copilotkit/react-core @copilotkit/react-textarea @copilotkit/react-ui @copilotkit/runtime

# Next.js patch update
npm update next

# Minor Radix UI updates (careful selection)
npm update @radix-ui/react-toast @radix-ui/react-tooltip @radix-ui/react-progress
```

**Backend:**
```bash
# Google ADK update
pip install google-adk==1.15.1

# FastAPI and Google Cloud updates
pip install fastapi>=0.117.1 google-cloud-aiplatform>=1.117.0

# Security updates
pip install uvicorn>=0.37.0 structlog>=25.4.0
```

#### **Tier 2: Planned Updates (Next Sprint)**
Schedule for controlled testing and migration:

**Frontend:**
- **React Testing Library**: `^16.3.0` → Latest
- **TypeScript**: Ensure latest `^5.x`
- **Lucide React**: `0.454.0` → `0.544.0`

**Backend:**
- **Celery**: `5.3.4` → `5.5.3`
- **Pytest**: `7.4.3` → `8.4.2`
- **Python-dotenv**: `1.0.0` → `1.1.1`

#### **Tier 3: Major Updates (Future Planning)**
Require careful planning and testing:

**Frontend:**
- **Tailwind CSS**: v3 → v4 (when ready)
- **Zod**: v3 → v4 (breaking changes)
- **React Window**: v1 → v2 (breaking changes)

**Backend:**
- **Redis**: v5 → v6 (major version)
- **Alembic**: `1.13.1` → `1.16.5` (database migrations)

### 2. Update Schedule

#### **Weekly (Patch Updates)**
- Security patches
- Bug fixes
- Patch version updates (x.x.Z)

#### **Bi-weekly (Minor Updates)**
- Feature additions
- Minor version updates (x.Y.z)
- Non-breaking improvements

#### **Monthly (Major Updates)**
- Breaking changes
- Major version updates (X.y.z)
- Architectural changes

### 3. Testing Strategy

#### **Pre-Update Testing**
```bash
# Frontend testing
npm run test
npm run lint
npm run build

# Backend testing
pytest backend/tests/
python -m mypy backend/
```

#### **Post-Update Validation**
```bash
# Full integration testing
npm run test:integration
python -m pytest backend/tests/integration/

# Visual regression testing
npm run test:visual

# Performance benchmarking
npm run test:performance
```

### 4. Rollback Strategy

#### **Frontend Rollback**
```bash
# Lock to known good versions
npm install @copilotkit/react-core@1.10.3 --save-exact
npm install next@15.5.2 --save-exact
```

#### **Backend Rollback**
```bash
# Revert to requirements.txt versions
pip install -r requirements.txt --force-reinstall
```

### 5. Automated Dependency Monitoring

#### **Setup Dependabot (GitHub)**
Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  # Frontend dependencies
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    assignees:
      - "bmad-team"
    reviewers:
      - "bmad-team"
    open-pull-requests-limit: 5

  # Backend dependencies
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    assignees:
      - "bmad-team"
    reviewers:
      - "bmad-team"
    open-pull-requests-limit: 5
```

#### **NPM Audit and Security**
```bash
# Weekly security audit
npm audit --audit-level moderate
npm audit fix

# Update security-critical packages
npm update --save
```

#### **Python Security Scanning**
```bash
# Install safety for vulnerability scanning
pip install safety

# Weekly security scan
safety check
safety check --db latest
```

### 6. Version Pinning Strategy

#### **Frontend (package.json)**
```json
{
  "dependencies": {
    // Pin critical dependencies to avoid unexpected breaks
    "@copilotkit/react-core": "1.10.4",
    "next": "15.5.4",
    "react": "19",

    // Allow patch updates for stable packages
    "lucide-react": "^0.544.0",
    "tailwind-merge": "^2.6.0",

    // Pin major versions for complex packages
    "zod": "3.25.67",
    "@radix-ui/react-dialog": "1.1.4"
  }
}
```

#### **Backend (requirements.txt)**
```txt
# Pin critical framework versions
fastapi==0.117.1
google-adk==1.15.1
google-cloud-aiplatform==1.117.0

# Allow minor updates for stable packages
uvicorn>=0.37.0,<1.0.0
pydantic>=2.39.0,<3.0.0

# Pin database and infrastructure
sqlalchemy==2.0.43
alembic==1.13.1
redis==5.0.1
```

## Implementation Phases

### Phase 1: Immediate Safe Updates (Week 1)

**Day 1-2: Frontend Tier 1 Updates**
```bash
cd frontend
npm update @copilotkit/react-core @copilotkit/react-textarea @copilotkit/react-ui @copilotkit/runtime
npm update next @anthropic-ai/claude-code
npm test && npm run build
```

**Day 3-4: Backend Tier 1 Updates**
```bash
cd backend
pip install google-adk==1.15.1 fastapi==0.117.1 google-cloud-aiplatform==1.117.0
pytest && python -m mypy .
```

**Day 5: Integration Testing**
```bash
# Full system testing
npm run test:integration
python -m pytest backend/tests/integration/
```

### Phase 2: Planned Updates (Week 2-3)

**Week 2: Frontend Tier 2 Updates**
- Update testing libraries
- Update TypeScript and tooling
- Update icon libraries

**Week 3: Backend Tier 2 Updates**
- Update Celery and Redis client
- Update testing frameworks
- Update development tools

### Phase 3: Monitoring Setup (Week 4)

**Setup Automated Monitoring:**
- Configure Dependabot
- Setup security scanning
- Create update schedules
- Document rollback procedures

## Risk Mitigation

### 1. Breaking Change Detection

**Pre-Update Checks:**
```bash
# Check for breaking changes
npm-check-updates --doctor
pip-check-reqs --ignore-dunder

# Review changelogs
npm info @copilotkit/react-core versions --json
pip show google-adk
```

**Automated Testing:**
```bash
# Contract testing
npm run test:contracts
python -m pytest backend/tests/contracts/

# API compatibility testing
npm run test:api-compatibility
```

### 2. Staged Rollouts

**Development → Staging → Production**
1. Update development environment first
2. Run full test suite
3. Deploy to staging for integration testing
4. Monitor for 24-48 hours
5. Deploy to production with rollback ready

### 3. Backup and Recovery

**Before Major Updates:**
```bash
# Create backup branch
git checkout -b backup/pre-major-update-$(date +%Y%m%d)
git commit -am "Backup before major dependency updates"

# Tag current working version
git tag stable/pre-update-$(date +%Y%m%d)
```

## Monitoring and Alerting

### 1. Dependency Health Dashboard

**Key Metrics:**
- Number of outdated packages
- Security vulnerabilities
- Last update timestamp
- Test success rates post-update

### 2. Automated Alerts

**Setup Alerts For:**
- Critical security vulnerabilities
- Failed dependency updates
- Breaking changes in major dependencies
- Test failures after updates

### 3. Regular Reviews

**Monthly Dependency Review:**
- Review all outdated packages
- Assess security vulnerabilities
- Plan major version updates
- Update pinning strategy

## Documentation and Communication

### 1. Update Documentation

**After Each Update:**
- Update CHANGELOG.md
- Document breaking changes
- Update installation instructions
- Review API documentation

### 2. Team Communication

**Update Notifications:**
- Slack notifications for critical updates
- Email summaries for major updates
- Team meetings for breaking changes
- Documentation updates

## Conclusion

This dependency management strategy ensures BMAD stays current with the latest versions of critical dependencies while minimizing risks from breaking changes. By implementing a tier-based approach with automated monitoring and careful testing, we can maintain system stability while benefiting from the latest features and security improvements.

### Key Success Metrics

- **Update Frequency**: Weekly patch updates, bi-weekly minor updates
- **Security**: Zero high-severity vulnerabilities
- **Stability**: <5% update-related incidents
- **Automation**: 80% of updates automated
- **Documentation**: 100% of breaking changes documented

### Next Steps

1. ✅ **Immediate**: Apply Tier 1 safe updates
2. 📅 **Week 2**: Setup automated monitoring
3. 📅 **Week 3**: Plan Tier 2 updates
4. 📅 **Month 1**: Complete major update assessment
5. 📅 **Ongoing**: Monthly dependency review meetings