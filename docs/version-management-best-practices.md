# BMAD Version Management Best Practices

## Overview

This document outlines best practices for managing dependency versions in the BMAD project to ensure stability, security, and maintainability while staying current with the latest features and improvements.

## Core Principles

### 1. **Security First**
- Always prioritize security updates
- Apply security patches immediately
- Regularly scan for vulnerabilities
- Never ignore high-severity security alerts

### 2. **Stability Over Latest**
- Prefer stable, well-tested versions over bleeding edge
- Allow time for community feedback on new releases
- Test thoroughly before adopting major version changes
- Use LTS (Long Term Support) versions when available

### 3. **Automated When Safe**
- Automate patch and minor updates for stable packages
- Require manual review for major version changes
- Use dependency bots for monitoring and alerts
- Implement automated testing for update validation

### 4. **Documentation and Communication**
- Document all dependency changes
- Communicate breaking changes to the team
- Maintain changelog for dependency updates
- Keep migration guides up to date

## Version Management Strategy

### Semantic Versioning (SemVer) Approach

Following the `MAJOR.MINOR.PATCH` format:

#### **PATCH Updates (x.x.Z)** - ✅ **Auto-update**
- **What**: Bug fixes, security patches
- **Risk**: Very low
- **Timeline**: Apply immediately
- **Testing**: Automated tests only
- **Examples**: `1.10.3` → `1.10.4`

```bash
# Safe to auto-update
npm update package-name
pip install package-name --upgrade
```

#### **MINOR Updates (x.Y.z)** - ⚠️ **Scheduled review**
- **What**: New features, backwards-compatible changes
- **Risk**: Low to medium
- **Timeline**: Weekly review and update
- **Testing**: Automated + smoke testing
- **Examples**: `1.10.4` → `1.11.0`

```bash
# Review changelog first, then update
npm update package-name
pip install package-name==1.11.0
```

#### **MAJOR Updates (X.y.z)** - 🔍 **Manual review required**
- **What**: Breaking changes, API changes
- **Risk**: High
- **Timeline**: Quarterly planning
- **Testing**: Full regression testing
- **Examples**: `1.11.0` → `2.0.0`

```bash
# Requires migration planning and testing
# See specific migration guides
```

## Dependency Categories

### Critical Dependencies (Zero-Downtime Updates)

These require immediate attention for security but careful handling for features:

#### **Frontend Critical**
- **CopilotKit** (`@copilotkit/*`)
  - Security: Immediate
  - Features: Weekly review
  - Breaking: Quarterly planning

- **Next.js** (`next`)
  - Security: Immediate
  - Features: Bi-weekly review
  - Breaking: Major version planning

- **React** (`react`, `react-dom`)
  - Security: Immediate
  - Features: Monthly review
  - Breaking: Major version planning (rare)

#### **Backend Critical**
- **Google ADK** (`google-adk`)
  - Security: Immediate
  - Features: Weekly review
  - Breaking: Quarterly planning

- **FastAPI** (`fastapi`)
  - Security: Immediate
  - Features: Bi-weekly review
  - Breaking: Rare, plan carefully

- **SQLAlchemy** (`sqlalchemy`)
  - Security: Immediate
  - Features: Monthly review
  - Breaking: Major planning required

### Development Dependencies (Flexible Updates)

These can be updated more aggressively:

#### **Frontend Development**
- **TypeScript** (`typescript`)
- **Testing libraries** (`@testing-library/*`, `vitest`)
- **Linting tools** (`eslint`, `prettier`)
- **Build tools** (`@vitejs/*`)

#### **Backend Development**
- **Testing tools** (`pytest`, `httpx`)
- **Development servers** (`uvicorn`)
- **Code quality** (`mypy`, `black`)

### UI/Design Dependencies (Coordinated Updates)

These require design system coordination:

#### **UI Components**
- **Radix UI** (`@radix-ui/*`)
  - Update in groups to maintain consistency
  - Test visual regression
  - Coordinate with design team

- **Tailwind CSS** (`tailwindcss`)
  - Major versions require design system review
  - Test responsive behavior
  - Update design tokens

- **Icons** (`lucide-react`)
  - Check for icon changes
  - Update icon usage guide

## Update Procedures

### Daily Monitoring

1. **Security Alerts**
   ```bash
   # Check for security alerts
   npm audit --audit-level high
   safety check  # for Python
   ```

2. **Dependabot PRs**
   - Review auto-generated PRs
   - Merge patch updates quickly
   - Schedule minor updates for review

### Weekly Update Cycle

**Monday: Planning**
- Review Dependabot PRs from the weekend
- Plan updates for the week
- Check for critical security updates

**Tuesday-Wednesday: Tier 1 Updates**
```bash
# Run safe updates
./scripts/update-dependencies.sh 1 false
```

**Thursday: Tier 2 Updates**
```bash
# Run planned updates
./scripts/update-dependencies.sh 2 false
```

**Friday: Testing and Documentation**
- Run full integration tests
- Update documentation
- Prepare for next week

### Monthly Major Review

**First Monday of Month:**
1. Review all major version updates available
2. Plan migration timeline for breaking changes
3. Update dependency strategy if needed
4. Review and update pinned versions

## Testing Strategy for Updates

### Pre-Update Testing
```bash
# Run full test suite before updates
npm run test
npm run test:integration
npm run build

pytest backend/tests/
python -m mypy backend/
```

### Post-Update Validation
```bash
# Automated validation
./scripts/check-dependencies.sh

# Manual testing checklist
# 1. Application starts without errors
# 2. Key features work as expected
# 3. Performance hasn't degraded
# 4. No new console errors
# 5. Database migrations work (if applicable)
```

### Integration Testing
```bash
# End-to-end testing
npm run test:e2e
python -m pytest backend/tests/integration/

# Performance testing
npm run test:performance
```

## Rollback Procedures

### Immediate Rollback (Production Issues)

1. **Frontend Rollback**
   ```bash
   # Restore from backup
   cp .backup/TIMESTAMP/package.json .
   cp .backup/TIMESTAMP/package-lock.json .
   npm ci
   ```

2. **Backend Rollback**
   ```bash
   # Restore from backup
   cp .backup/TIMESTAMP/requirements.txt .
   pip install -r requirements.txt --force-reinstall
   ```

3. **Database Rollback** (if needed)
   ```bash
   # Alembic downgrade
   alembic downgrade -1
   ```

### Git-Based Rollback
```bash
# Create emergency fix branch
git checkout -b emergency/rollback-dependencies

# Revert dependency updates
git revert COMMIT_HASH

# Deploy fix
git push origin emergency/rollback-dependencies
```

## Security Management

### Vulnerability Scanning

**Daily Automated Scans:**
```bash
# Frontend security audit
npm audit --audit-level moderate

# Backend security scan
safety check --db latest
```

**Weekly Deep Scans:**
```bash
# Full dependency audit
npm audit --audit-level low
safety check --full-report

# License compliance check
npm ls --depth=0
pip-licenses
```

### Security Response Protocol

1. **High-Severity Vulnerabilities** (CVSS 7.0+)
   - **Timeline**: Fix within 24 hours
   - **Process**: Emergency update → Test → Deploy
   - **Communication**: Immediate team notification

2. **Medium-Severity Vulnerabilities** (CVSS 4.0-6.9)
   - **Timeline**: Fix within 1 week
   - **Process**: Include in next update cycle
   - **Communication**: Include in weekly update summary

3. **Low-Severity Vulnerabilities** (CVSS < 4.0)
   - **Timeline**: Fix within 1 month
   - **Process**: Include in monthly review
   - **Communication**: Include in monthly report

### Security Update Exceptions

Sometimes security updates may break functionality:

1. **Assess Impact**
   - Is the vulnerability exploitable in our environment?
   - What's the attack vector?
   - What data is at risk?

2. **Risk vs. Functionality**
   - Can we mitigate the risk temporarily?
   - Is there a workaround for the breaking change?
   - What's the timeline for a proper fix?

3. **Communication**
   - Document the decision
   - Set timeline for resolution
   - Monitor for exploits

## Version Pinning Strategy

### When to Pin Versions

**Always Pin:**
- **Production-critical packages** where stability is paramount
- **Packages with frequent breaking changes**
- **Database and infrastructure packages**

**Allow Range Updates:**
- **Development and testing tools**
- **Well-maintained packages with good SemVer compliance**
- **Security and performance libraries**

### Pinning Formats

#### **Frontend (package.json)**
```json
{
  "dependencies": {
    // Exact pinning for critical packages
    "next": "15.5.4",
    "react": "19.0.0",

    // Patch updates allowed
    "@copilotkit/react-core": "~1.10.4",

    // Minor updates allowed
    "lucide-react": "^0.544.0",

    // Range for dev tools
    "typescript": "^5.0.0"
  }
}
```

#### **Backend (requirements.txt)**
```txt
# Exact versions for critical packages
fastapi==0.117.1
google-adk==1.15.1
sqlalchemy==2.0.43

# Compatible versions for stable packages
uvicorn>=0.37.0,<1.0.0
pydantic>=2.39.0,<3.0.0

# Flexible versions for dev tools
pytest>=8.4.2
```

## Tool-Specific Best Practices

### CopilotKit Management

**Update Strategy:**
- Monitor releases weekly
- Test HITL functionality after updates
- Verify integration with backend APIs
- Check for breaking changes in chat interfaces

**Critical Areas to Test:**
- Chat message handling
- Agent integration
- WebSocket connections
- Error handling

**Migration Checklist:**
- [ ] Read release notes
- [ ] Update all CopilotKit packages together
- [ ] Test chat functionality
- [ ] Verify WebSocket connections
- [ ] Test HITL workflows
- [ ] Check error handling

### Google ADK Management

**Update Strategy:**
- Follow Google's release cadence
- Test with real agent workflows
- Verify async operations work correctly
- Check MCP tool integrations

**Critical Areas to Test:**
- Agent creation and management
- Async service operations
- MCP toolbox functionality
- Evaluation pipelines

**Migration Checklist:**
- [ ] Read ADK changelog
- [ ] Test agent initialization
- [ ] Verify async patterns
- [ ] Test MCP tools
- [ ] Check evaluation schemas
- [ ] Validate service methods

### shadcn/ui and Radix UI Management

**Update Strategy:**
- Group related component updates
- Test visual consistency
- Verify accessibility compliance
- Check responsive behavior

**Critical Areas to Test:**
- Component rendering
- Theme compatibility
- Accessibility features
- Mobile responsiveness

**Migration Checklist:**
- [ ] Update components in groups
- [ ] Test visual regression
- [ ] Verify theme system
- [ ] Check accessibility
- [ ] Test responsive design
- [ ] Update component usage docs

## Documentation Requirements

### Change Documentation

**For Every Update:**
1. **CHANGELOG.md** entry with:
   - Package name and versions
   - Reason for update (security, feature, bug fix)
   - Breaking changes (if any)
   - Testing performed

2. **Git Commit Message** format:
   ```
   deps(frontend): update CopilotKit to 1.10.4

   - Fixes chat state management issues
   - Improves HITL functionality
   - No breaking changes

   Tested: ✅ Unit tests, ✅ Integration tests, ✅ Manual testing
   ```

3. **Team Communication:**
   - Slack notification for major updates
   - Email summary for weekly updates
   - Meeting discussion for breaking changes

### Migration Guides

**Create Migration Guide For:**
- Major version updates
- Breaking API changes
- Configuration changes
- Database schema changes

**Include in Migration Guide:**
- What changed and why
- Step-by-step update instructions
- Code examples (before/after)
- Testing checklist
- Rollback procedure

## Monitoring and Alerting

### Automated Monitoring

**Daily Checks:**
- Security vulnerabilities
- Failed dependency installations
- Broken package locks

**Weekly Reports:**
- Outdated packages summary
- Security scan results
- Update recommendations

**Monthly Analysis:**
- Dependency health overview
- License compliance report
- Update strategy effectiveness

### Alert Configuration

**Immediate Alerts:**
- High-severity security vulnerabilities
- Failed critical package updates
- Breaking dependency conflicts

**Daily Summary:**
- New Dependabot PRs
- Security scan results
- Package lock conflicts

**Weekly Report:**
- Outdated packages list
- Update recommendations
- Security posture summary

## Common Pitfalls and Solutions

### 1. **Dependency Conflicts**

**Problem:** Package A requires version 1.x, Package B requires version 2.x

**Solution:**
```bash
# Check for conflicts
npm ls
pip check

# Use resolutions (package.json)
"resolutions": {
  "package-name": "1.5.0"
}

# Use constraints (requirements.txt)
package-name==1.5.0  # in constraints.txt
```

### 2. **Breaking Changes Not Caught**

**Problem:** Update breaks functionality not covered by tests

**Solution:**
- Improve test coverage
- Add integration tests
- Manual testing checklist
- Staged rollout process

### 3. **Security vs. Stability Trade-offs**

**Problem:** Security update breaks critical functionality

**Solution:**
- Risk assessment framework
- Temporary mitigation strategies
- Expedited fix timeline
- Clear communication plan

### 4. **Version Lock-in**

**Problem:** Stuck on old versions due to breaking changes

**Solution:**
- Regular update schedule
- Incremental migration approach
- Dedicated update sprints
- Technical debt planning

## Team Responsibilities

### **Developer Responsibilities**
- Review Dependabot PRs promptly
- Test functionality after updates
- Report issues immediately
- Follow security protocols

### **Tech Lead Responsibilities**
- Approve major version updates
- Coordinate breaking change migrations
- Review security assessments
- Maintain update strategy

### **DevOps Responsibilities**
- Monitor automated updates
- Manage deployment pipelines
- Coordinate rollback procedures
- Maintain monitoring systems

## Tools and Resources

### **Monitoring Tools**
- **Dependabot**: Automated PR creation
- **npm audit**: Frontend security scanning
- **safety**: Backend security scanning
- **GitHub Security Advisories**: Vulnerability tracking

### **Update Tools**
- **npm-check-updates**: Check for outdated packages
- **pip-check-reqs**: Python dependency analysis
- **Custom scripts**: `./scripts/check-dependencies.sh`

### **Testing Tools**
- **Vitest**: Frontend testing
- **pytest**: Backend testing
- **GitHub Actions**: Automated testing
- **Docker**: Isolated testing environments

## Conclusion

Effective dependency management requires balancing security, stability, and innovation. By following these best practices, the BMAD project can maintain a secure, up-to-date, and stable dependency ecosystem while minimizing risks and disruptions.

The key is to automate what's safe, carefully plan what's risky, and always prioritize security and stability over having the latest features.