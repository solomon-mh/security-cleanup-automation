# QUICK START GUIDE - Security Cleanup

## ⚡ 5-Minute Setup

### Step 1: Download Tools (1 min)
```bash
# Clone the cleanup automation repo
git clone https://github.com/solomon-mh/security-cleanup-automation.git
cd security-cleanup-automation

# Make batch script executable
chmod +x batch-cleanup.sh
```

### Step 2: Dry Run (2 min)
```bash
# Run cleanup in DRY RUN mode for an explicit repo list
./batch-cleanup.sh --repos traceOn,auth

# Or preview the full built-in batch list
./batch-cleanup.sh --all

# This will:
# ✅ Clone only the repos you selected
# ✅ Scan for malicious patterns
# ✅ Show what WOULD be removed
# ✅ Create detailed log file
```

### Step 3: Review Findings (2 min)
```bash
# Check the log file
cat cleanup_*.log

# Look for:
# - [INFECTED] - Files with malicious code
# - [CLEANED] - Files that would be cleaned
# - [+] Found X infected files
```

---

## 🚀 DEPLOY CLEANUP (When Ready)

```bash
# Apply cleanup by pushing review branches
GH_TOKEN=YOUR_PAT ./batch-cleanup.sh --repos traceOn,auth --no-dry-run

# Monitor progress:
tail -f cleanup_*.log
```

### What It Does:
✅ Clones each repo  
✅ Scans for 12+ malicious patterns  
✅ Removes obfuscated code  
✅ Cleans .gitignore  
✅ Removes suspicious fonts  
✅ Pushes review branches instead of direct-to-main changes  
✅ Generates detailed reports  

---

## ✅ VERIFY CLEANUP WORKED

### Quick Check (30 seconds per repo)
```bash
cd /path/to/repo

# Check 1: No obfuscated code
grep -r "_0x[a-f0-9]" . --include="*.js" --include="*.ts" 2>/dev/null | grep -v node_modules
# Should return NOTHING ✅

# Check 2: No Ethereum address
grep -r "0xa322E5f3" .
# Should return NOTHING ✅

# Check 3: No spawn patterns
grep -r "spawn.*node" . --include="*.js" --include="*.ts" 2>/dev/null
# Should return NOTHING ✅

# Check 4: Tests still pass
npm test
# Should PASS ✅
```

### Full Verification Script
```bash
#!/bin/bash
# verify-all.sh - Check all repos

REPOS=("traceOn" "traceon-loadrunner" "fetanfews-server" "Afalagi" ...)

for repo in "${REPOS[@]}"; do
    echo "Checking $repo..."
    if grep -r "_0x[a-f0-9]" "$repo" 2>/dev/null | grep -v node_modules; then
        echo "❌ FAILED"
    else
        echo "✅ PASSED"
    fi
done
```

---

## 🔐 IMMEDIATE SECURITY ACTIONS

### DO THESE NOW (Takes 5 minutes):

```bash
# 1. Change GitHub password
# https://github.com/settings/password

# 2. Enable 2FA
# https://github.com/settings/security

# 3. Check GitHub Security Log
# https://github.com/settings/security-log
# Look for any unauthorized access

# 4. Revoke SSH keys
# https://github.com/settings/ssh
# Delete ALL current keys, then regenerate

# 5. Revoke Personal Access Tokens
# https://github.com/settings/tokens
# Delete all tokens

# 6. Check Ethereum Wallet
# https://etherscan.io/address/0xa322E5f3
# If ANY suspicious transactions: MOVE FUNDS TO NEW WALLET NOW!
```

---

## 🛡️ BRANCH PROTECTION (Per Repository)

For EACH repo:

1. Go to: `https://github.com/solomon-mh/REPO_NAME/settings/branches`
2. Click "Add rule"
3. Pattern: `main` (or `master`)
4. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass
   - ✅ Include administrators

---

## 📊 CLEANUP AUTOMATION REPOSITORY

**URL**: https://github.com/solomon-mh/security-cleanup-automation (Private)

**Files**:
- `cleanup.py` - Detection & removal script
- `deep-cleanup-workflow.yml` - GitHub Actions automation
- `batch-cleanup.sh` - Batch processing script
- `README.md` - Full documentation
- `DEPLOYMENT.md` - Step-by-step guide
- `INCIDENT.md` - Incident report
- `QUICKSTART.md` - This file

---

## 🚨 MALICIOUS CODE SIGNATURES

### What We're Removing:

```javascript
// Pattern 1: Ethereum wallet code
global.i="A10-*4650"
_0x[random characters]
0xa322E5f3...  // Target wallet

// Pattern 2: Obfuscated functions
const _0x499797=_0x1574;
function _0x1574() { ... }

// Pattern 3: RPC manipulation
withRpcEndpoints|rpcCall|rpcBatch
eth_getTra|eth_blockN|eth_getBlo

// Pattern 4: Command execution
spawn('node', ['-e', ...])
global['r'] = require

// Pattern 5: Hex encoding
\\x[0-9a-f]{2}  // Hidden strings
```

---

## ⚠️ IF SOMETHING GOES WRONG

### Issue: Cleanup fails on a repo
```bash
# Manual fix:
cd /path/to/repo
wget https://raw.githubusercontent.com/solomon-mh/security-cleanup-automation/main/cleanup.py
python3 cleanup.py .
git diff  # Review
git add -A
git commit -m "security: manual cleanup"
git push
```

### Issue: Tests fail after cleanup
```bash
# Check what was removed:
git diff HEAD~1

# If too much was removed:
git reset --hard HEAD~1
# And manually edit the file
```

### Issue: Can't push changes
```bash
# Check branch protection settings:
# https://github.com/solomon-mh/REPO_NAME/settings/branches

# Ensure your user has permission to bypass protection
# Or temporarily disable protection, push, then re-enable
```

---

## 📈 MONITOR PROGRESS

### Dry Run Phase
```
[*] Scanning repository...
[!] INFECTED: eslint.config.js - 2 patterns found
[!] INFECTED: .gitignore - 1 pattern found
[+] Found 24 infected files

DRY RUN MODE - No changes committed
```

### Real Cleanup Phase
```
[*] Processing: traceOn
[*] Scanning traceOn...
[+] Changes detected in traceOn
[+] Committing changes for traceOn
[+] Successfully pushed changes for traceOn
[✓] Completed: traceOn

[+] Total bytes removed: 2,847,392
[✅] Cleanup complete!
```

---

## 📝 CLEANUP REPORT FORMAT

After cleanup, you'll get:

**cleanup_YYYYMMDD_HHMMSS.log**
```
[*] Processing: traceOn
[!] INFECTED: eslint.config.js
[!] INFECTED: .gitignore
[+] CLEANED: eslint.config.js (removed 1,247 bytes)
[+] CLEANED: .gitignore (removed 342 bytes)
[+] Completed: traceOn

Summary:
- Total repositories: 27
- Successfully cleaned: 24
- Failed: 0
- Skipped (no changes): 3
```

---

## 🔄 NEXT STEPS AFTER CLEANUP

### Immediate (Same day)
1. ✅ Run verification on all repos
2. ✅ Enable branch protection
3. ✅ Harden GitHub account

### Short Term (This week)
1. Enable GitHub security scanning
2. Update all dependencies
3. Monitor for suspicious activity

### Medium Term (This month)
1. Team security training
2. Code review audit
3. Dependency audit

### Long Term (Ongoing)
1. Monthly security checks
2. Quarterly credential rotation
3. Regular dependency updates

---

## 💡 KEY POINTS

✅ **Cleanup is safe** - It only removes malicious code  
✅ **Dry run first** - Always test before applying  
✅ **Review changes** - Check git diff before committing  
✅ **Tests must pass** - Run npm test after cleanup  
✅ **Security is priority** - Take time to verify everything  

❌ **Don't ignore warnings** - Address every finding  
❌ **Don't skip security hardening** - Essential for protection  
❌ **Don't use old wallet** - If compromised, funds may be stolen  
❌ **Don't trust external code** - Always audit before using  

---

## 📞 HELP & SUPPORT

**Documentation**:
- `README.md` - Overview and detection patterns
- `DEPLOYMENT.md` - Detailed step-by-step guide
- `INCIDENT.md` - Complete incident report

**Tools**:
- `cleanup.py` - Python detection and removal script
- `batch-cleanup.sh` - Bash batch processing
- `deep-cleanup-workflow.yml` - GitHub Actions automation

**Repository**:
- https://github.com/solomon-mh/security-cleanup-automation

---

## 🎯 SUCCESS CHECKLIST

After completing cleanup:

- [ ] Ran cleanup in dry-run mode
- [ ] Reviewed all findings
- [ ] Ran cleanup with --no-dry-run
- [ ] All repos processed successfully
- [ ] Verified no malicious code remains
- [ ] All tests pass
- [ ] Changed GitHub password
- [ ] Enabled 2FA
- [ ] Revoked SSH keys and PATs
- [ ] Checked Ethereum wallet
- [ ] Enabled branch protection (all repos)
- [ ] Enabled GitHub security scanning
- [ ] Team notified
- [ ] Incident documented

---

## ✨ COMPLETION

When all checkboxes are complete:

🎉 **Your repositories are clean and secure!**

**Status**: ✅ Ready for production  
**Risk Level**: ⬇️ CRITICAL → LOW  
**Next Review**: 1 week (monitor for anomalies)

---

**Questions?** Read the full docs in the security-cleanup-automation repository.  
**Ready to start?** Run: `./batch-cleanup.sh`
