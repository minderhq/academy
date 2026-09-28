---
Document ID: CHEAT-SHEET-003
Title: "CHEAT SHEET: Git & Version Control"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# CHEAT SHEET: Git & Version Control

**Essential Git commands for AI/ML development**

---

## 📝 Basic Commands

### Initialize & Clone
```bash
# Initialize new repository
git init

# Clone existing repository
git clone https://github.com/user/repo.git

# Clone with specific branch
git clone -b branch-name https://github.com/user/repo.git

# Clone with depth (shallow clone for large repos)
git clone --depth 1 https://github.com/user/repo.git
```

### Check Status
```bash
# Check repository status
git status

# Check current branch
git branch

# Check all branches
git branch -a

# Check remote URL
git remote -v
```

---

## 💾 Staging & Committing

### Stage Changes
```bash
# Stage specific file
git add file.py

# Stage all changes
git add .

# Stage all changes in directory
git add directory/

# Interactive staging
git add -i

# Stage with patch (select specific lines)
git add -p file.py
```

### Commit Changes
```bash
# Commit with message
git commit -m "Add feature X"

# Stage and commit in one command
git commit -am "Fix bug Y"

# Commit with template
git commit -t commit_template.txt

# Amend last commit
git commit --amend

# Amend last commit without changing message
git commit --amend --no-edit
```

### Best Practices
```bash
# Good commit messages
git commit -m "feat: add user authentication"
git commit -m "fix: resolve memory leak in model loader"
git commit -m "docs: update API documentation"
git commit -m "refactor: optimize data pipeline"

# Format: ${TYPE}(${SCOPE}): ${SUBJECT}
# Types: feat, fix, docs, style, refactor, test, chore
```

---

## 🌳 Branching & Merging

### Create & Switch Branches
```bash
# Create new branch
git branch feature-branch

# Switch to branch
git checkout feature-branch

# Create and switch in one command
git checkout -b feature-branch

# Switch to previous branch
git checkout -

# Rename branch
git branch -m old-name new-name

# Delete branch (local)
git branch -d feature-branch

# Delete branch (force)
git branch -D feature-branch

# Delete branch (remote)
git push origin --delete feature-branch
```

### Merge Branches
```bash
# Merge branch into current
git merge feature-branch

# Merge with commit (always create merge commit)
git merge --no-ff feature-branch

# Squash merge (combine commits)
git merge --squash feature-branch

# Abort merge
git merge --abort
```

### Resolve Conflicts
```bash
# Check conflicted files
git status

# Edit conflicted file
# Look for <<<<<<<, =======, >>>>>>> markers

# Mark as resolved
git add resolved-file.py

# Continue merge
git commit
```

---

## 🔄 Remote Operations

### Push & Pull
```bash
# Push to remote
git push

# Push to specific branch
git push origin feature-branch

# Push with upstream tracking
git push -u origin feature-branch

# Push all branches
git push --all

# Pull with rebase (linear history)
git pull --rebase

# Fetch without merging
git fetch

# Fetch specific branch
git fetch origin feature-branch
```

### Remote Management
```bash
# Add remote
git remote add origin https://github.com/user/repo.git

# Change remote URL
git remote set-url origin https://github.com/user/new-repo.git

# Remove remote
git remote remove origin

# Show remote info
git remote show origin
```

---

## 📜 History & Logs

### View History
```bash
# Show commit history
git log

# Show compact history
git log --oneline

# Show graph (branch visualization)
git log --graph --oneline --all

# Show last N commits
git log -n 5

# Show commits since date
git log --since="2024-01-01"

# Show commits by author
git log --author="John Doe"

# Show file history
git log --follow file.py
```

### View Changes
```bash
# Show changes in commit
git show HEAD

# Show file at specific commit
git show HEAD~2:file.py

# Show diff between commits
git diff HEAD~2 HEAD

# Show diff between branches
git diff main feature-branch

# Show staged changes
git diff --staged
```

---

## ↩️ Undo Changes

### Unstage & Discard
```bash
# Unstage file
git restore --staged file.py

# Discard local changes
git restore file.py

# Discard all local changes
git restore .

# Unstage all
git reset HEAD

# Reset to commit (keep changes)
git reset --soft HEAD~1

# Reset to commit (discard changes)
git reset --hard HEAD~1

# ⚠️ DANGER: Reset to remote
git reset --hard origin/main
```

### Revert Changes
```bash
# Revert commit (create new commit)
git revert HEAD

# Revert specific commit
git revert ${COMMIT_HASH}

# Revert merge
git revert -m 1 ${MERGE_COMMIT_HASH}
```

---

## 🏷️ Tagging

### Create Tags
```bash
# Create lightweight tag
git tag v1.0.0

# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Tag specific commit
git tag v0.9.0 ${COMMIT_HASH}

# Show tag info
git show v1.0.0

# Delete tag
git tag -d v1.0.0
```

### Push Tags
```bash
# Push specific tag
git push origin v1.0.0

# Push all tags
git push origin --tags

# Delete remote tag
git push origin --delete v1.0.0
```

---

## 🔍 Search & Find

### Search Code
```bash
# Search in files (current branch)
git grep "TODO"

# Search in all branches
git grep "TODO" $(git rev-list --all)

# Search by commit message
git log --grep="bug fix"

# Search by author
git log --author="John"

# Find commits touching file
git log --follow -- file.py
```

### Blame (Who Changed What)
```bash
# Show who changed each line
git blame file.py

# Show specific line range
git blame -L 10,20 file.py
```

---

## 📦 Stashing

### Stash Changes
```bash
# Stash current changes
git stash

# Stash with message
git stash save "Work in progress"

# Stash including untracked files
git stash -u

# Stash specific files
git stash push -m "message" file1.py file2.py
```

### Apply Stash
```bash
# Apply most recent stash
git stash pop

# Apply specific stash
git stash pop stash@{1}

# Apply stash without removing
git stash apply

# Drop stash
git stash drop

# Drop all stashes
git stash clear

# List stashes
git stash list
```

---

## 🔄 Rebase & Cherry-Pick

### Rebase
```bash
# Rebase onto main
git rebase main

# Interactive rebase (last 3 commits)
git rebase -i HEAD~3

# Continue rebase after conflict
git rebase --continue

# Skip commit during rebase
git rebase --skip

# Abort rebase
git rebase --abort
```

### Cherry-Pick
```bash
# Pick specific commit
git cherry-pick ${COMMIT_HASH}

# Pick multiple commits
git cherry-pick ${HASH1} ${HASH2}

# Pick without committing
git cherry-pick -n ${COMMIT_HASH}
```

---

## 🧹 Maintenance

### Cleanup
```bash
# Clean untracked files
git clean -f

# Clean untracked files and directories
git clean -fd

# Preview what would be cleaned
git clean -n

# Remove unreachable objects
git gc --prune=now

# Optimize repository
git gc --aggressive
```

### Check Integrity
```bash
# Check repository integrity
git fsck

# Verify objects
git verify-pack -v .git/objects/pack/*.idx
```

---

## 🐳 Git for Large Files (AI/ML)

### Git LFS (Large File Storage)
```bash
# Install Git LFS
git lfs install

# Track file types
git lfs track "*.pkl"
git lfs track "*.pt"
git lfs track "*.bin"
git lfs track "*.safetensors"

# Track models directory
git lfs track "models/"

# View tracked patterns
git lfs track

# Pull LFS files
git lfs pull

# Push LFS files
git lfs push
```

### Git Annex Alternative
```bash
# Initialize git-annex
git annex init

# Add large file
git annex add large_model.bin

# Get file content
git annex get large_model.bin

# Drop file content (keep metadata)
git annex drop large_model.bin
```

---

## 🤝 Collaboration

### Pull Requests
```bash
# Create pull request (GitHub CLI)
gh pr create --title "Add feature" --body "Description"

# View pull requests
gh pr list

# Checkout PR locally
gh pr checkout 123

# Merge PR
gh pr merge 123
```

### Code Review
```bash
# Request review
gh pr edit 123 --add-reviewer username

# View review comments
gh pr view 123 --comments

# Address review comments
# Edit code, commit, push
```

---

## 🎯 AI/ML Specific Workflows

### Model Versioning
```bash
# Tag model releases
git tag -a model-v1.0 -m "Release model v1.0"

# Track model files with LFS
git lfs track "models/*.safetensors"
git lfs track "checkpoints/*.pt"

# Ignore training data
echo "data/training/*.json" >> .gitignore
echo "data/cache/*" >> .gitignore
```

### Experiment Tracking
```bash
# Use branches for experiments
git checkout -b experiment/lr-0.001

# Commit experiment results
git add results/
git commit -m "exp: learning rate 0.001 results"

# Merge if successful
git checkout main
git merge experiment/lr-0.001

# Delete if not
git branch -D experiment/lr-0.001
```

### .gitignore for AI/ML
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# AI/ML specific
*.pkl
*.pt
*.pth
*.ckpt
*.safetensors
*.bin
!models/*.safetensors  # Track production models

# Data
data/raw/*
data/processed/*
!data/README.md

# Jupyter
.ipynb_checkpoints
*.ipynb

# Experiments
experiments/*/outputs/
experiments/*/checkpoints/
runs/
wandb/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## 🔗 Quick Links

- **[Tutorial 002: Docker Essentials](../tutorials/TUTORIAL-002-Docker-Essentials.md)** - Docker for AI/ML
- **[CHEAT-SHEET-001: Docker](CHEAT-SHEET-001-Docker.md)** - Docker commands
- **[CHEAT-SHEET-002: Python AI](CHEAT-SHEET-002-Python-AI.md)** - Python for AI

---

## Next Steps

- **[CHEAT SHEET: Linux Commands](CHEAT-SHEET-004-Linux.md)**
