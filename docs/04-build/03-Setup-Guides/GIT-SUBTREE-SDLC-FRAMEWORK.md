# Git Subtree Setup: SDLC-Enterprise-Framework

**Version**: 1.0.0  
**Date**: December 5, 2025  
**Status**: ACTIVE

## Overview

`SDLC-Enterprise-Framework` is included in the main repository as a **Git Subtree**, allowing it to:
- ✅ Be part of the main repo (no submodule init needed)
- ✅ Sync independently with its remote repo
- ✅ Maintain separate version history

## Remote Repository

- **URL**: https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework
- **Remote Name**: `sdlc-framework`
- **Branch**: `main`

## Common Operations

### Pull Latest Changes from Remote

```bash
# Pull latest changes from SDLC-Enterprise-Framework remote
git subtree pull --prefix=SDLC-Enterprise-Framework sdlc-framework main --squash
```

### Push Changes to Remote

```bash
# Push local changes to SDLC-Enterprise-Framework remote
git subtree push --prefix=SDLC-Enterprise-Framework sdlc-framework main
```

### View Subtree History

```bash
# View commits related to SDLC-Enterprise-Framework
git log --oneline --all -- SDLC-Enterprise-Framework/
```

### Add Remote (if not exists)

```bash
# Add remote for SDLC-Enterprise-Framework
git remote add sdlc-framework https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework.git

# Fetch from remote
git fetch sdlc-framework
```

## Workflow

### Updating SDLC-Enterprise-Framework

1. **Pull latest from remote:**
   ```bash
   git subtree pull --prefix=SDLC-Enterprise-Framework sdlc-framework main --squash
   ```

2. **Make changes locally** (if needed)

3. **Commit changes:**
   ```bash
   git add SDLC-Enterprise-Framework/
   git commit -m "Update SDLC-Enterprise-Framework"
   ```

4. **Push to main repo:**
   ```bash
   git push origin main
   ```

5. **Push to SDLC-Enterprise-Framework remote** (if changes are framework-specific):
   ```bash
   git subtree push --prefix=SDLC-Enterprise-Framework sdlc-framework main
   ```

## Benefits of Subtree vs Submodule

| Feature | Subtree | Submodule |
|---------|---------|-----------|
| Included in main repo | ✅ Yes | ❌ No (reference only) |
| Clone works immediately | ✅ Yes | ❌ Requires `git submodule init` |
| Can push to remote | ✅ Yes | ❌ No (read-only) |
| History in main repo | ✅ Yes | ❌ No (separate) |
| File size | ⚠️ Larger | ✅ Smaller |

## Troubleshooting

### Subtree Already Exists Error

If you see `fatal: prefix 'SDLC-Enterprise-Framework' already exists`:

```bash
# Remove from git cache
git rm -r --cached SDLC-Enterprise-Framework

# Re-add as subtree
git subtree add --prefix=SDLC-Enterprise-Framework sdlc-framework main --squash
```

### Merge Conflicts

If conflicts occur during pull:

```bash
# Resolve conflicts manually
git status

# After resolving, continue
git add SDLC-Enterprise-Framework/
git commit -m "Merge SDLC-Enterprise-Framework updates"
```

## References

- [Git Subtree Documentation](https://www.atlassian.com/git/tutorials/git-subtree)
- [SDLC-Enterprise-Framework Repo](https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework)

