# History Purge — runbook

**What this does:** rewrites **every commit** in each infected repo to remove
the supply-chain-attack payload, then **force-pushes** the rewritten history.

**This is destructive and irreversible on the remote.** After a real run:

- every commit SHA in the repo changes;
- existing local clones can no longer `git pull` (they must re-clone);
- open pull requests break and usually auto-close;
- forks keep the old (infected) history until their owners re-sync;
- CI runs / deploys pinned to an old SHA will 404.

A recovery bundle of the *pre-rewrite* repo is saved as a build artifact
(`backup-<repo>`, 90-day retention) so nothing is truly lost.

---

## What gets removed

| Thing | How |
|---|---|
| `temp_auto_push.bat`, `temp_interactive_push.bat`, `branch_structure.json` | file deleted from all of history (`git filter-repo --invert-paths`) |
| Payload appended after legit code in `eslint.config.js` etc. | truncated back to the last real statement before the first indicator |
| `global.i="A10-…4650"`, injected `global.x=` / `global['_V']=` lines | line removed |
| `const/function _0x…` obfuscation, `withRpcEndpoints`/`rpcCall`/`rpcBatch` helpers | declaration removed |
| `0xa322E5f3…` wallet address | replaced with the zero address |
| `eth_getTra…`/`eth_blockN…`/`eth_getBlo…` probe strings | replaced with `""` |
| `spawn('node', ['-e', …])` | replaced with `null` |
| A file that is **entirely** payload | replaced with a one-line stub comment |

The logic lives in [`history_purge.py`](history_purge.py) — one file, used
both by the workflow and for local testing. It only rewrites a blob that
contains a **hard** indicator, so ordinary minified JS with `_0x…` names is
left untouched.

---

## Prerequisites (one time)

1. **`CLEANUP_TOKEN` secret** on this repo
   (Settings → Secrets and variables → Actions).
   A PAT that can push to all 26 repos: **Contents: Read/Write** and
   **Pull requests: Read/Write**. Fine-grained is fine — resource owner
   `solomon-mh`, all repos.

2. **Branch protection** — a force-push to a protected branch fails.
   For each infected repo, in Settings → Branches, temporarily enable
   **"Allow force pushes"** on the default branch (or delete the rule),
   run the purge, then restore it.

3. **Tell collaborators** to stop pushing until the rewrite is done, and to
   re-clone afterwards.

---

## Step 1 — test the scrubber locally (no repo touched)

```bash
python history_purge.py --self-check          # regexes healthy?
# try it on a real working copy:
git clone https://github.com/solomon-mh/<repo> /tmp/<repo>
python history_purge.py $(git -C /tmp/<repo> ls-files)
git -C /tmp/<repo> diff                        # review every change
```

## Step 2 — dry run (one repo)

GitHub → **Actions** → **Purge supply-chain malware from history** →
**Run workflow**:

- `repos`: `traceOn` (a single name)
- `dry_run`: `true`
- `confirm`: leave blank

Download the `backup-traceOn` artifact and read `report-before.md` and the
`git-filter-repo` analysis in the log. Nothing was pushed.

## Step 3 — real run (one repo)

Same, but:

- `dry_run`: `false`
- `confirm`: `REWRITE-HISTORY`  ← exact text, or the job refuses to run

The job re-scans the rewritten history and **aborts before pushing** if any
indicator survived. On success it force-pushes all branches and tags.

Verify:

```bash
git clone https://github.com/solomon-mh/traceOn /tmp/traceOn-check
cd /tmp/traceOn-check
git log --all -p -S 0xa322E5f3        # expect: nothing
python /path/to/cleanup.py --scan .   # expect: exit 0, no infected files
```

## Step 4 — fleet run

Once one repo checks out clean end-to-end:

- `repos`: `all`
- `dry_run`: `false`
- `confirm`: `REWRITE-HISTORY`

`max-parallel` is 2. Check the `_summary` artifact when it finishes.

## Step 5 — after

- Restore branch protection on every repo.
- Ask anyone with a clone or fork to delete it and re-clone.
- Rotate any secret that was ever committed to these repos (assume the
  attacker read everything in history).
- Keep the `backup-*` artifacts until you're satisfied.

---

## Recovery

```bash
# download the backup-<repo> artifact, then:
git clone backup-<repo>.bundle recovered
cd recovered
git remote set-url origin https://github.com/solomon-mh/<repo>.git
git push --force --all && git push --force --tags
```
