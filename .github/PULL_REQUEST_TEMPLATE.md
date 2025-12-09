# Pull Request

## Description

<!-- Describe the changes in this PR -->

## Framework-First Compliance Checklist

Before merging, verify:

- [ ] **SASE Templates in Framework First**
  - If adding SASE features, templates added to `SDLC-Enterprise-Framework/03-Templates-Tools/SASE-Artifacts/` first
  - Orchestrator reads from Framework submodule (NOT hard-coded)

- [ ] **SDLC Structure in Framework**
  - Structure rules defined in `SDLC-Enterprise-Framework/01-Overview/sdlc-structure-config.yml`
  - Validator reads from Framework config (NOT hard-coded)

- [ ] **AI Prompts in Framework**
  - Prompt templates in `SDLC-Enterprise-Framework/04-AI-Prompts/SE3.0-Agentic-Prompts/`
  - AI service reads from Framework (NOT hard-coded f-strings)

- [ ] **Submodule Pointer Updated**
  - If Framework changed, main repo submodule pointer updated
  - Commit message: "chore: Update Framework submodule - [description]"

- [ ] **ADR Created (if Orchestrator-specific)**
  - If feature is Orchestrator-specific (Option B), ADR created
  - ADR documents Framework compatibility

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## References

- [Framework-First Enforcement Guide](docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md)
- [Violation Examples](docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md#violation-examples)

## Related Issues

<!-- Link related issues here -->
