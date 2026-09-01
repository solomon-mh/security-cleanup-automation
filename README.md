# Security Cleanup Automation - Complete Guide

## 🚨 Overview

This repository contains automated tools to detect and remove malicious code injected into your 40+ GitHub repositories via a supply chain attack that occurred between Aug 27-31, 2026.

### Attack Summary
- **Type**: Supply chain attack via compromised dependency
- **Vector**: Malicious code injected into config files and .gitignore
- **Affected Repos**: 40+ repositories in solomon-mh account
- **Timeline**: Aug 27-31, 2026
- **Payload**: Obfuscated Ethereum wallet exploitation code
- **Status**: ✅ Removal tools created and ready to deploy

---

## 📋 What Was Infected

### Primary Infection Points
1. **eslint.config.js** - Obfuscated malicious JavaScript appended
2. **.gitignore** - Injected global variable definitions
3. **Build configs** (vite.config.ts, next.config.js, webpack.config.js)
4. **public/fonts** - Suspicious font files (potential malware)
5. **src/index.ts** and other entry points

### Malicious Code Pattern
```javascript
// Example of removed malicious code:
global.i="A10-*4650";const _0x499797=_0x1574;
(function(_0x50cf58,_0x4b5935){
  // Obfuscated RPC endpoint probing
  // Ethereum wallet targeting (0xa322E5f3...)
  // Command execution via spawn()
})
```

---

## 🛠️ Tools Provided

### 1. **cleanup.py** - Standalone Detection & Removal Script
Comprehensive Python script that:
- Scans all files recursively for 12+ malicious patterns
- Removes obfuscated code from config files
- Cleans .gitignore entries
- Removes suspicious font files
- Generates detailed cleanup reports

**Usage:**
```bash
python3 cleanup.py /path/to/repo
```

### 2. **deep-cleanup-workflow.yml** - GitHub Actions Automation
Automated workflow that:
- Processes 26 major repositories in parallel
- Runs 5-phase deep cleanup
- Creates PRs for review
- Generates detailed reports
- Supports dry-run mode

**How to use:**
1. Copy `deep-cleanup-workflow.yml` to `.github/workflows/` in each repo
2. Go to Actions tab
3. Trigger "Deep Security Cleanup" workflow
4. Set `dry_run=true` first to preview changes
5. Set `dry_run=false` to apply changes

---

## 🔍 Detection Patterns

The cleanup tools detect:

### Ethereum Exploitation Code
```
global\.i\s*=\s*["\']A10-\*4650
0xa322E5f3  # Target wallet address
eth_getTra|eth_blockN|eth_getBlo  # RPC calls
withRpcEndpoints|rpcCall|rpcBatch
```

### Obfuscation Patterns
```
_0x[a-f0-9]{6}  # Obfuscated function/variable names
const\s+_0x\w+.*?=.*?function  # Obfuscated function definitions
_0x\w+\[0x\w+\]  # Obfuscated array access
\\x[0-9a-f]{2}  # Hex-encoded strings
```

### Command Execution
```
spawn\(["\']node["\'].*?-e  # Process spawning
global\[["\']r["\']\]\s*=\s*require  # Global require injection
```

---

## 📊 Cleanup Phases

### Phase 1: Deep Recursive Scan
- Walks entire repository structure
- Skips safe directories (.git, node_modules, .next)
- Tests 12+ patterns against every file
- Identifies all infected files

### Phase 2: Deep Cleaning
- Removes obfuscated patterns
- Cleans RPC manipulation code
- Removes spawn/exec patterns
- For eslint.config.js: extracts only legitimate config
- Removes hex-encoded strings
- Cleans whitespace

### Phase 3: Font File Scanning
- Identifies unusually large font files (>5MB)
- Removes suspicious fonts from public/static/assets
- These likely contain hidden payloads

### Phase 4: .gitignore Cleanup
- Removes all obfuscated entries
- Keeps legitimate gitignore patterns
- Validates syntax

### Phase 5: Public Folder Scan
- Deep scan of public/, static/, assets/ directories
- Removes all suspicious font files
- Verifies integrity of remaining assets

---

## 🚀 How to Deploy

### Option 1: Manual Cleanup (Per Repository)

```bash
# Clone the repo
git clone https://github.com/solomon-mh/REPO_NAME.git
cd REPO_NAME

# Download cleanup script
wget https://raw.githubusercontent.com/solomon-mh/security-cleanup-automation/main/cleanup.py

# Run cleanup (review first!)
python3 cleanup.py .

# Review changes
git diff

# Commit and push
git add -A
git commit -m "security: remove malicious code from supply chain attack"
git push origin main
```

### Option 2: GitHub Actions Workflow (Automated)

1. **In each repo**, create `.github/workflows/cleanup.yml`:
```bash
mkdir -p .github/workflows
cp deep-cleanup-workflow.yml .github/workflows/cleanup.yml
git add .github/workflows/cleanup.yml
git commit -m "ci: add security cleanup workflow"
git push
```

2. **Trigger the workflow**:
   - Go to Actions tab
   - Select "Deep Security Cleanup"
   - Click "Run workflow"
   - Set `dry_run=true` first
   - Review the scan results
   - Re-run with `dry_run=false` to apply

### Option 3: Batch Cleanup Script

```bash
#!/bin/bash
# cleanup-all.sh - Cleanup all repositories

REPOS=(
  "traceOn"
  "traceon-loadrunner"
  "fetanfews-server"
  "Afalagi"
  "auth"
)

for repo in "${REPOS[@]}"; do
  echo "[*] Cleaning $repo..."
  git clone https://github.com/solomon-mh/$repo.git
  cd $repo
  wget https://raw.githubusercontent.com/solomon-mh/security-cleanup-automation/main/cleanup.py
  python3 cleanup.py .
  git add -A
  git commit -m "security: remove malicious code" || echo "No changes"
  git push
  cd ..
done
```

---

## ✅ Verification Checklist

After cleanup, verify:

- [ ] `eslint.config.js` ends with `);` (no trailing obfuscated code)
- [ ] `.gitignore` contains only legitimate patterns
- [ ] No files contain `_0x` pattern matches
- [ ] No files contain `0xa322E5f3` (target wallet)
- [ ] No spawn/require injections in globals
- [ ] `public/` folder has no suspicious font files
- [ ] Build files are clean and functional
- [ ] All tests still pass: `npm test`
- [ ] Linting works: `npm run lint`

---

## 🔐 Post-Cleanup Security Steps

### 1. GitHub Account Security
```
✅ Change password immediately
✅ Enable 2FA (if not enabled)
✅ Revoke all SSH keys
✅ Revoke all Personal Access Tokens
✅ Review Security Log for unauthorized access
✅ Remove compromised collaborators
```

### 2. Ethereum Wallet Security
```
✅ Check transaction history
✅ If any suspicious txs: move funds to NEW wallet
✅ If clean: rotate all credentials
✅ Monitor for future suspicious activity
```

### 3. Account Monitoring
```
✅ Set up GitHub notifications for all repos
✅ Enable branch protection on main/master
✅ Require PR reviews before merge
✅ Enable status checks requirement
✅ Disable force pushes
```

### 4. Audit Other Systems
```
✅ Check TRU-Living repo (friend's account)
✅ Audit npm packages for similar patterns
✅ Review VSCode extensions for suspicious updates
✅ Check git config for unauthorized remotes
```

---

## 📋 Affected Repositories (26 in first batch)

Priority 1 (Most Critical):
- [ ] traceOn
- [ ] traceon-loadrunner
- [ ] fetanfews-server
- [ ] Afalagi
- [ ] aladia-QA
- [ ] auth

Priority 2 (High):
- [ ] bahirdar_hotels_room_reservation_backend_api
- [ ] bahirdar_hotels_room_reservation_frontend
- [ ] adrp-discuss
- [ ] ai-website-ui-clone
- [ ] brainwave
- [ ] car-insta-firebase

Priority 3 (Medium):
- [ ] carbuff-nextjs
- [ ] cellvortex
- [ ] clean-architecture-nestJS
- [ ] customEd
- [ ] headline-news-page
- [ ] mealer
- [ ] mikander
- [ ] mymoment
- [ ] nextjs-commerce
- [ ] nextjs-dashboard
- [ ] OAuth-boilerplate
- [ ] receipt-ocr
- [ ] regalcanvas
- [ ] solomon-muhye
- [ ] vanlife

---

## 📊 Expected Results

After running cleanup across all 40+ repos:

```
✅ Estimated malicious code removed: ~2-5MB
✅ Files cleaned: 80-120 files
✅ Patterns detected: 200-400 instances
✅ Execution time: 2-4 hours (automated)
✅ Manual review time: 1-2 hours
```

---

## 🔄 Continuous Security

After cleanup, maintain security with:

1. **Enable branch protection** on all repos
2. **Enable GitHub security scanning** (Dependabot, Secret Scanning)
3. **Regular audits** of dependencies and code
4. **Monitoring** of git activity and deployments

---

**Last Updated**: September 1, 2026  
**Status**: ✅ Ready for deployment
