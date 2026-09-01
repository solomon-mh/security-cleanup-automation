# DEPLOYMENT GUIDE - Security Cleanup

## 🚀 Quick Start (5 Minutes)

### Step 1: Enable Batch Cleanup Script
```bash
# Make the batch script executable
chmod +x batch-cleanup.sh

# Run in DRY RUN mode first for an explicit repo list
./batch-cleanup.sh --repos traceOn,auth

# Or preview the full built-in batch list
./batch-cleanup.sh --all

# Review the scan_YYYYMMDD_HHMMSS.log file
cat cleanup_*.log
```

### Step 2: Review Findings
- Check how many repos have infected files
- Review what will be removed
- Verify no legitimate code will be deleted

### Step 3: Apply Cleanup (Real Deployment)
```bash
# Apply cleanup by pushing review branches for the selected repos
GH_TOKEN=YOUR_PAT ./batch-cleanup.sh --repos traceOn,auth --no-dry-run

# Monitor progress in the log file
tail -f cleanup_*.log
```

> **Important:** For private repositories or GitHub Actions runs, use a personal access token with access to the target repositories. In this repository's workflow, store it as `CLEANUP_REPO_TOKEN`.

---

## 📋 VERIFICATION CHECKLIST

After cleanup completes, verify each repository:

### For Each Repo (Quick 2-min check):

```bash
cd /path/to/repo

# 1. Check eslint.config.js is clean
cat eslint.config.js
# ✅ Should end with: export default tseslint.config(...);
# ❌ Should NOT contain: _0x, global.i, spawn(

# 2. Verify .gitignore is clean
grep -E "_0x|global|spawn" .gitignore
# ✅ Should return NOTHING
# If it returns lines, cleanup failed

# 3. Check for suspicious patterns in all files
grep -r "_0x[a-f0-9]" --include="*.js" --include="*.ts" --include="*.json" .
# ✅ Should return NOTHING
# ❌ If found, run cleanup.py again

# 4. Verify no Ethereum address
grep -r "0xa322E5f3" .
# ✅ Should return NOTHING

# 5. Check public folder
ls -lah public/ | grep -E "\.woff2|\.woff|\.ttf"
# ✅ Should only show legitimate fonts (<2MB each)
# ❌ If any >5MB fonts, delete manually

# 6. Run tests
npm test  # or yarn test

# 7. Lint check
npm run lint  # should pass

# 8. Build check
npm run build  # should succeed
```

### Automated Verification Script

```bash
#!/bin/bash
# verify-cleanup.sh - Automated verification

verify_repo() {
    local repo=$1
    echo "Verifying $repo..."
    
    cd "$repo"
    
    # Check for malicious patterns
    if grep -r "_0x[a-f0-9]" . --include="*.js" --include="*.ts" 2>/dev/null | grep -v node_modules; then
        echo "❌ FAILED: Found obfuscated code"
        return 1
    fi
    
    if grep -r "0xa322E5f3" . 2>/dev/null; then
        echo "❌ FAILED: Found Ethereum wallet address"
        return 1
    fi
    
    if grep -r "spawn.*node.*-e" . --include="*.js" --include="*.ts" 2>/dev/null; then
        echo "❌ FAILED: Found spawn patterns"
        return 1
    fi
    
    # Check eslint.config.js
    if [ -f eslint.config.js ]; then
        if ! tail -c 5 eslint.config.js | grep -q ");"; then
            echo "❌ FAILED: eslint.config.js doesn't end with );"
            return 1
        fi
    fi
    
    echo "✅ PASSED: $repo is clean"
    cd ..
    return 0
}

# Verify all repos
for repo in "${REPOS[@]}"; do
    verify_repo "$repo" || echo "VERIFICATION FAILED: $repo"
done
```

---

## 🔐 SECURITY HARDENING (After Cleanup)

### 1. GitHub Account Security
```
Priority 1 (DO IMMEDIATELY):
☐ Change GitHub password: https://github.com/settings/password
☐ Enable 2FA: https://github.com/settings/security
☐ Review Security Log: https://github.com/settings/security-log
☐ Check for suspicious SSH keys: https://github.com/settings/ssh
☐ Revoke all Personal Access Tokens: https://github.com/settings/tokens
☐ Check for unrecognized devices/sessions

Priority 2 (Within 1 hour):
☐ Review all collaborators on each repo
☐ Remove any suspicious collaborators
☐ Check for new webhooks: /admin/hooks
☐ Check for new deploy keys: /settings/keys
```

### 2. Repository Protection

For EACH repository:

```bash
# Via GitHub Web UI:
# 1. Go to Settings > Branches
# 2. Create branch protection rule for "main"
# 3. Enable:
☐ Require pull request reviews before merging
☐ Require status checks to pass before merging
☐ Require branches to be up to date before merging
☐ Include administrators
☐ Dismiss stale pull request approvals
☐ Require code owners review
☐ Restrict who can push to matching branches
```

### 3. Enable Security Scanning

For EACH repository:

```bash
# Via GitHub Web UI:
# 1. Go to Settings > Code security and analysis
# 2. Enable:
☐ Dependabot alerts
☐ Dependabot security updates
☐ Secret scanning
☐ Private vulnerability reporting
☐ Code scanning with CodeQL
```

### 4. Ethereum Wallet Security

```bash
Priority 1 (URGENT):
☐ Check wallet transaction history
  https://etherscan.io/address/0xa322E5f3
☐ If ANY suspicious transactions:
  → IMMEDIATELY move funds to NEW wallet
  → Do NOT use old wallet
☐ If wallet is CLEAN:
  → Still consider it compromised
  → Move funds to new wallet as precaution
  → Rotate all credentials
```

---

## 📊 CLEANUP VALIDATION REPORT

Generate validation report after cleanup:

```bash
#!/bin/bash
# generate-validation-report.sh

echo "# Security Cleanup Validation Report" > validation_report.md
echo "Generated: $(date)" >> validation_report.md
echo "" >> validation_report.md

PASS=0
FAIL=0

for repo in "${REPOS[@]}"; do
    if [ ! -d "$repo" ]; then
        git clone "https://github.com/solomon-mh/$repo.git"
    fi
    
    cd "$repo"
    git pull
    
    if grep -r "_0x[a-f0-9]" . --include="*.js" --include="*.ts" 2>/dev/null | grep -v node_modules; then
        echo "❌ $repo - FAILED (obfuscated code found)" >> ../validation_report.md
        ((FAIL++))
    elif grep -r "0xa322E5f3" . 2>/dev/null; then
        echo "❌ $repo - FAILED (wallet address found)" >> ../validation_report.md
        ((FAIL++))
    else
        echo "✅ $repo - PASSED" >> ../validation_report.md
        ((PASS++))
    fi
    
    cd ..
done

echo "" >> validation_report.md
echo "## Summary" >> validation_report.md
echo "- Passed: $PASS" >> validation_report.md
echo "- Failed: $FAIL" >> validation_report.md
echo "- Total: $((PASS + FAIL))" >> validation_report.md

echo "Report saved to validation_report.md"
```

---

## 🚨 EMERGENCY PROCEDURES

### If Cleanup Fails on a Repository

```bash
# Option 1: Manual cleanup
cd /path/to/repo
python3 cleanup.py .
git diff  # Review changes
git add -A
git commit -m "security: manual cleanup"
git push

# Option 2: Reset and retry
git reset --hard HEAD~1
git clean -fd
./cleanup.py .
git add -A
git commit -m "security: cleanup after reset"
git push
```

### If Malicious Code Reappears

```bash
# 1. Investigate immediately
git log --oneline | head -20
# Check if someone committed new malicious code

# 2. Check account security
# Go to https://github.com/settings/security-log

# 3. Force-push clean version
git push --force-with-lease origin main

# 4. Enable branch protection to prevent future pushes
# Settings > Branches > Add rule for "main"
```

### If Tests Fail After Cleanup

```bash
# Option 1: Cleanup was too aggressive
git diff HEAD~1
# Review what was removed

# Option 2: Restore and re-run with verbose
git reset --hard HEAD~1
python3 cleanup.py . --verbose
# Be more selective about what to remove

# Option 3: Manual fix
# Edit files manually to remove only malicious code
# Keep legitimate code intact
```

---

## 📈 MONITORING & MAINTENANCE

### Weekly Tasks
```bash
# Check for new suspicious commits
git log --oneline --since="1 week ago"

# Run security scan
npm audit
npm run lint

# Check for new dependencies
git diff package-lock.json
```

### Monthly Tasks
```bash
# Update dependencies safely
npm update
npm audit fix

# Review recent commits
git log --oneline --since="1 month ago" | head -20

# Check GitHub security alerts
# https://github.com/settings/security-log
```

### Quarterly Tasks
```bash
# Full security audit
npm audit --audit-level=moderate

# Review all collaborators
# Review all deploy keys and SSH keys
# Review all webhooks

# Run deep scan for malicious patterns
for repo in "${REPOS[@]}"; do
    python3 cleanup.py "$repo" --scan-only
done
```

---

## ✅ FINAL DEPLOYMENT CHECKLIST

Before considering cleanup complete:

**Phase 1: Cleanup Execution**
- [ ] Ran cleanup in dry-run mode
- [ ] Reviewed all findings in log file
- [ ] Ran cleanup with --no-dry-run
- [ ] All repositories processed successfully
- [ ] No errors in cleanup logs

**Phase 2: Verification**
- [ ] Ran verification script on all repos
- [ ] No obfuscated patterns found
- [ ] No Ethereum wallet addresses found
- [ ] No spawn patterns found
- [ ] All tests pass
- [ ] All linting passes
- [ ] All builds succeed

**Phase 3: Security Hardening**
- [ ] Changed GitHub password
- [ ] Enabled 2FA
- [ ] Reviewed security log for suspicious activity
- [ ] Revoked SSH keys and tokens
- [ ] Removed suspicious collaborators
- [ ] Enabled branch protection on all repos
- [ ] Enabled GitHub security scanning

**Phase 4: Ethereum Security**
- [ ] Checked wallet transaction history
- [ ] Moved funds to new wallet (if compromised)
- [ ] Rotated credentials

**Phase 5: Documentation**
- [ ] Generated cleanup report
- [ ] Generated validation report
- [ ] Documented incident details
- [ ] Notified team members

---

## 📞 SUPPORT

### Common Issues & Solutions

**Q: Cleanup says "No infected files" but I see suspicious code**
A: The repo may have already been cleaned. Check git log to verify.

**Q: Tests fail after cleanup**
A: Some legitimate code might have been removed. Review cleanup.py output and restore if needed.

**Q: How do I verify cleanup worked?**
A: Run the verification checklist above. No output from grep means clean.

**Q: Can I undo the cleanup?**
A: Yes - `git reset --hard HEAD~1` but make sure cleanup was actually needed.

**Q: What if my wallet was compromised?**
A: Immediately move all funds to a NEW wallet. Do not try to recover the old one.

---

## 🎯 SUCCESS CRITERIA

Cleanup is complete when:

✅ All 40+ repos scanned  
✅ All infected files identified  
✅ All malicious code removed  
✅ All tests pass  
✅ All verification checks pass  
✅ GitHub account security hardened  
✅ Ethereum wallet secured  
✅ Branch protection enabled  
✅ Security scanning enabled  
✅ Team notified  

---

**Status**: Ready for deployment  
**Next Step**: Run `./batch-cleanup.sh` to begin
