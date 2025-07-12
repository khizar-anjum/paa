# Git Push Protocol

This document outlines the standard protocol for pushing changes to the git repository.

## Step-by-Step Protocol

### 1. Pull Latest Changes
Always start by pulling the latest changes from the remote repository:
```bash
git pull origin main
```

### 2. Handle Conflicts
If there are merge conflicts:
- Review each conflict carefully
- Attempt to resolve conflicts by preserving both changes where appropriate
- If uncertain about any conflict resolution, **stop and ask the user for guidance**
- Never make assumptions about which changes should take precedence

### 3. Stage Changes
After resolving conflicts (if any), add all relevant files:
```bash
git add <relevant-files>
```
Or if adding all changes:
```bash
git add .
```

### 4. Commit Changes
Create a commit with a short, concise one-line message:
```bash
git commit -m "Add feature X" 
```

**Commit Message Guidelines:**
- Keep it under 50 characters
- Use imperative mood ("Add" not "Added")
- Be specific about what changed
- **NO mention of Claude, AI tools, or automated generation**
- Examples:
  - ✅ "Add underwater channel simulation module"
  - ✅ "Fix decoder chunk scaling bug"
  - ✅ "Update README with installation instructions"
  - ❌ "Update files as requested by user"
  - ❌ "AI-generated improvements to codebase"

### 5. Push to GitHub
Finally, push the changes to the remote repository:
```bash
git push origin main
```

## Important Notes

- Never force push unless explicitly instructed
- Always ensure tests pass before pushing (if applicable)
- Keep commits atomic - one logical change per commit
- If working on a feature branch, replace `main` with the appropriate branch name

## Quick Reference
```bash
git pull origin main
# Resolve any conflicts if needed
git add .
git commit -m "Descriptive message here"
git push origin main
```