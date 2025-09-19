# Create Implementation Plan Task

## Overview
This task creates a comprehensive implementation plan for the agent's specific phase in the SDLC workflow. This is the **mandatory first task** that each agent must complete before proceeding with any other work in their phase.

## Purpose
- Establish clear planning and approach before execution
- Define success criteria and deliverables
- Identify risks and mitigation strategies
- Create timeline and milestones
- Prepare for handoff to next phase

## Task Instructions

### Step 1: Determine Agent Type and Phase
- Identify your agent type (analyst, architect, coder, tester, deployer)
- Confirm the SDLC phase you're responsible for
- Load the appropriate implementation plan template

### Step 2: Load Implementation Plan Template
Based on your agent type, load the corresponding template:
- **Analyst**: Use `analyst-implementation-plan-tmpl.yaml`
- **Architect**: Use `architect-implementation-plan-tmpl.yaml`
- **Coder**: Use `coder-implementation-plan-tmpl.yaml`
- **Tester**: Use `tester-implementation-plan-tmpl.yaml`
- **Deployer**: Use `deployer-implementation-plan-tmpl.yaml`

### Step 3: Gather Context Information
Before filling out the template, gather:
- Project requirements and objectives
- Previous phase deliverables (if applicable)
- Stakeholder expectations
- Technical constraints
- Timeline requirements
- Budget considerations

### Step 4: Complete Implementation Plan
Work through each section of the template systematically:

1. **Phase Overview**: Define the phase objective and success criteria
2. **Approach/Strategy**: Define your methodology and approach
3. **Technical Details**: Specify technical requirements and decisions
4. **Timeline & Milestones**: Create realistic timeline with key milestones
5. **Risk Assessment**: Identify risks and mitigation strategies
6. **Quality Assurance**: Define quality measures and standards
7. **Handoff Preparation**: Plan for transition to next phase

### Step 5: Validate Implementation Plan
Review the completed plan to ensure:
- All required sections are completed
- Success criteria are measurable
- Timeline is realistic
- Risks are adequately addressed
- Handoff requirements are clear

### Step 6: Seek Approval
Present the implementation plan for approval before proceeding with execution:
- Share with project stakeholders
- Request feedback and approval
- Make necessary adjustments
- Get formal sign-off

## Critical Requirements

### Mandatory First Task
- This task MUST be completed before any other work in the phase
- No execution activities should begin until the implementation plan is approved
- The plan serves as the roadmap for all subsequent work

### HITL Integration
- Implementation plan creation requires human approval
- Plan must be reviewed and approved before execution begins
- Any changes to the plan during execution require additional approval

### Quality Standards
- Plan must be comprehensive and detailed
- All sections must be completed (no placeholders)
- Success criteria must be specific and measurable
- Timeline must include realistic estimates

## Deliverables
- Completed Implementation Plan document
- Risk assessment with mitigation strategies
- Timeline with key milestones
- Handoff preparation checklist

## Success Criteria
- Implementation plan is complete and approved
- All stakeholders understand the approach
- Risks are identified and mitigation strategies defined
- Timeline is realistic and achievable
- Quality standards are established
- Handoff requirements are clear

## Next Steps
After implementation plan approval:
1. Begin execution according to the plan
2. Monitor progress against milestones
3. Update stakeholders on progress
4. Adjust plan if necessary (with approval)
5. Prepare for handoff to next phase

## Template Usage
Use the `create-doc` task with the appropriate implementation plan template:
```
*create-doc {agent-type}-implementation-plan-tmpl.yaml
```

## Notes
- This task ensures proper planning before execution
- Helps prevent scope creep and timeline issues
- Provides clear success criteria for the phase
- Facilitates smooth handoffs between phases
- Supports HITL approval workflow requirements