#!/bin/bash
# batch-cleanup.sh - Automated cleanup script for multiple repositories

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

DEFAULT_REPOS=(
    "traceOn"
    "traceon-loadrunner"
    "fetanfews-server"
    "Afalagi"
    "aladia-QA"
    "auth"
    "bahirdar_hotels_room_reservation_backend_api"
    "bahirdar_hotels_room_reservation_frontend"
    "adrp-discuss"
    "ai-website-ui-clone"
    "brainwave"
    "car-insta-firebase"
    "carbuff-nextjs"
    "cellvortex"
    "clean-architecture-nestJS"
    "customEd"
    "headline-news-page"
    "mealer"
    "mikander"
    "mymoment"
    "nextjs-commerce"
    "nextjs-dashboard"
    "OAuth-boilerplate"
    "receipt-ocr"
    "regalcanvas"
    "solomon-muhye"
    "vanlife"
)

GITHUB_USER="${GITHUB_USER:-solomon-mh}"
REPO_BASE_URL=""
CLEANUP_SCRIPT_URL="${CLEANUP_SCRIPT_URL:-https://raw.githubusercontent.com/solomon-mh/security-cleanup-automation/main/cleanup.py}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-/tmp/security-cleanup-${TIMESTAMP}}"
LOG_FILE="${LOG_FILE:-cleanup_${TIMESTAMP}.log}"
DRY_RUN=true
USE_ALL=false
PUSH_BRANCH_PREFIX="${PUSH_BRANCH_PREFIX:-security-cleanup}"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

REPOS=()
DIRTY_REPOS=0
PUSHED_REPOS=0
FAILED_REPOS=0
SKIPPED_REPOS=0
FAILED_REPO_NAMES=()

if [[ "${LOG_FILE}" = /* ]]; then
    LOG_FILE_PATH="${LOG_FILE}"
else
    LOG_FILE_PATH="${PWD}/${LOG_FILE}"
fi

log() {
    printf '%b\n' "$1" | tee -a "$LOG_FILE_PATH"
}

usage() {
    cat <<EOF
Usage: $0 [options]

Options:
  --repo NAME               Clean a single repository (can be used multiple times)
  --repos NAME1,NAME2       Clean a comma-separated repository list
  --all                     Target the built-in repository list
  --no-dry-run              Commit changes and push review branches
  --github-user USER        GitHub owner/user for HTTPS clone URLs (default: ${GITHUB_USER})
  --repo-base-url URL       Base clone URL (default: https://github.com/<github-user>)
  --push-branch-prefix PFX  Prefix for review branches in apply mode (default: ${PUSH_BRANCH_PREFIX})
  --workspace PATH          Workspace for cloned repos (default: ${WORKSPACE_ROOT})
  --log-file PATH           Write the batch log to PATH (default: ${LOG_FILE})
  -h, --help                Show this help

Examples:
  $0 --repos traceOn,auth
  $0 --all
  GH_TOKEN=*** $0 --repo auth --no-dry-run
EOF
}

trim() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

add_repo() {
    local repo_name
    repo_name="$(trim "$1")"
    if [[ -n "$repo_name" ]]; then
        REPOS+=("$repo_name")
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-dry-run)
            DRY_RUN=false
            shift
            ;;
        --repo)
            add_repo "${2:-}"
            shift 2
            ;;
        --repos)
            IFS=',' read -r -a repo_values <<< "${2:-}"
            for repo_name in "${repo_values[@]}"; do
                add_repo "$repo_name"
            done
            shift 2
            ;;
        --all)
            USE_ALL=true
            shift
            ;;
        --github-user)
            GITHUB_USER="${2:-}"
            shift 2
            ;;
        --repo-base-url)
            REPO_BASE_URL="${2:-}"
            shift 2
            ;;
        --push-branch-prefix)
            PUSH_BRANCH_PREFIX="${2:-}"
            shift 2
            ;;
        --workspace)
            WORKSPACE_ROOT="${2:-}"
            shift 2
            ;;
        --log-file)
            LOG_FILE="${2:-}"
            if [[ "${LOG_FILE}" = /* ]]; then
                LOG_FILE_PATH="${LOG_FILE}"
            else
                LOG_FILE_PATH="${PWD}/${LOG_FILE}"
            fi
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ -z "$REPO_BASE_URL" ]]; then
    REPO_BASE_URL="https://github.com/${GITHUB_USER}"
fi

if [[ "$USE_ALL" = true ]] && [[ ${#REPOS[@]} -gt 0 ]]; then
    echo "Use either --all or --repo/--repos, not both." >&2
    exit 1
fi

if [[ "$USE_ALL" = true ]]; then
    REPOS=("${DEFAULT_REPOS[@]}")
elif [[ ${#REPOS[@]} -eq 0 ]]; then
    if [[ "$DRY_RUN" = true ]]; then
        REPOS=("${DEFAULT_REPOS[@]}")
    else
        echo "Apply mode requires an explicit target list via --repo/--repos or confirmation via --all." >&2
        exit 1
    fi
fi

TOTAL_REPOS=${#REPOS[@]}
mkdir -p "$WORKSPACE_ROOT"
mkdir -p "$(dirname "$LOG_FILE_PATH")"
: > "$LOG_FILE_PATH"

resolve_cleanup_script() {
    if [[ -f "${SCRIPT_DIR}/cleanup.py" ]]; then
        printf '%s' "${SCRIPT_DIR}/cleanup.py"
        return 0
    fi

    local downloaded_script="${WORKSPACE_ROOT}/cleanup.py"
    curl -fsSL "$CLEANUP_SCRIPT_URL" -o "$downloaded_script"
    chmod +x "$downloaded_script"
    printf '%s' "$downloaded_script"
}

CLEANUP_SCRIPT_PATH="$(resolve_cleanup_script)"

repo_clone_url() {
    local repo_name="$1"

    if [[ "$REPO_BASE_URL" == https://github.com/* && -n "$TOKEN" ]]; then
        printf '%s' "https://x-access-token:${TOKEN}@github.com/${GITHUB_USER}/${repo_name}.git"
    else
        printf '%s/%s.git' "${REPO_BASE_URL%/}" "$repo_name"
    fi
}

default_branch_for_repo() {
    local repo_dir="$1"
    local default_branch=""

    default_branch="$(git -C "$repo_dir" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')" || true
    if [[ -z "$default_branch" ]]; then
        default_branch="$(git -C "$repo_dir" remote show origin 2>/dev/null | sed -n '/HEAD branch/s/.*: //p')" || true
    fi
    if [[ -z "$default_branch" ]]; then
        default_branch="$(git -C "$repo_dir" branch --show-current 2>/dev/null)" || true
    fi
    if [[ -z "$default_branch" ]]; then
        default_branch="main"
    fi

    printf '%s' "$default_branch"
}

cleanup_repo() {
    local repo_name="$1"
    local repo_dir="${WORKSPACE_ROOT}/${repo_name}"
    local clone_url
    local default_branch
    local branch_safe_name
    local branch_name
    local repo_report

    clone_url="$(repo_clone_url "$repo_name")"
    repo_report="${WORKSPACE_ROOT}/${repo_name}-cleanup_report.json"

    log "${BLUE}[*]${NC} Processing: ${repo_name}"

    rm -rf "$repo_dir"
    if ! git clone "$clone_url" "$repo_dir" >/dev/null 2>&1; then
        log "${RED}[!]${NC} Failed to clone ${repo_name}. If this repo is private, set GH_TOKEN or GITHUB_TOKEN (PAT with access to target repos)."
        ((FAILED_REPOS++))
        FAILED_REPO_NAMES+=("$repo_name")
        return 1
    fi

    log "${YELLOW}[*]${NC} Scanning ${repo_name}..."
    rm -f "${WORKSPACE_ROOT}/cleanup_report.json" "$repo_report"
    if ! (
        cd "$WORKSPACE_ROOT"
        python3 "$CLEANUP_SCRIPT_PATH" "$repo_dir" > "${repo_dir}/cleanup_output.log" 2>&1
    ); then
        log "${RED}[!]${NC} Cleanup script failed for ${repo_name}"
        cat "${repo_dir}/cleanup_output.log" >> "$LOG_FILE_PATH"
        ((FAILED_REPOS++))
        FAILED_REPO_NAMES+=("$repo_name")
        return 1
    fi

    if [[ -f "${WORKSPACE_ROOT}/cleanup_report.json" ]]; then
        mv "${WORKSPACE_ROOT}/cleanup_report.json" "$repo_report"
    fi

    if git -C "$repo_dir" diff --quiet; then
        log "${YELLOW}[*]${NC} No malicious code found in ${repo_name}"
        ((SKIPPED_REPOS++))
        return 0
    fi

    ((DIRTY_REPOS++))
    log "${GREEN}[+]${NC} Changes detected in ${repo_name}"
    git -C "$repo_dir" diff --stat >> "$LOG_FILE_PATH"

    if [[ "$DRY_RUN" = true ]]; then
        log "${YELLOW}[*]${NC} DRY RUN - Review diff in ${repo_dir}"
        return 0
    fi

    default_branch="$(default_branch_for_repo "$repo_dir")"
    branch_safe_name="$(printf '%s' "$repo_name" | tr -c '[:alnum:]._-' '-')"
    branch_name="${PUSH_BRANCH_PREFIX}-${branch_safe_name}-$(date +%Y%m%d%H%M%S)"

    git -C "$repo_dir" config user.name "Security Cleanup Bot"
    git -C "$repo_dir" config user.email "security@automated.local"
    git -C "$repo_dir" add -A
    git -C "$repo_dir" commit -m "security: remove malicious code from supply chain attack" >/dev/null

    if git -C "$repo_dir" push origin "HEAD:${branch_name}" >/dev/null 2>&1; then
        log "${GREEN}[+]${NC} Pushed review branch ${branch_name} for ${repo_name} (base branch: ${default_branch})"
        ((PUSHED_REPOS++))
        return 0
    fi

    log "${RED}[!]${NC} Failed to push review branch for ${repo_name}"
    ((FAILED_REPOS++))
    FAILED_REPO_NAMES+=("$repo_name")
    return 1
}

log "${BLUE}========================================${NC}"
log "${BLUE}Security Cleanup - Batch Script${NC}"
log "${BLUE}========================================${NC}"
log ""
log "${YELLOW}Configuration:${NC}"
log "  Target repositories: $TOTAL_REPOS"
log "  Dry run mode: $DRY_RUN"
log "  Workspace: $WORKSPACE_ROOT"
log "  Log file: $LOG_FILE_PATH"
if [[ "$DRY_RUN" = false ]]; then
    log "  Push branch prefix: $PUSH_BRANCH_PREFIX"
fi
log ""

for repo_name in "${REPOS[@]}"; do
    cleanup_repo "$repo_name" || true
    log ""
done

log "${BLUE}========================================${NC}"
log "${BLUE}Cleanup Summary${NC}"
log "${BLUE}========================================${NC}"
log "Target repositories: $TOTAL_REPOS"
log "Repositories with detected changes: $DIRTY_REPOS"
log "Review branches pushed: $PUSHED_REPOS"
log "Failed: $FAILED_REPOS"
log "Skipped (no changes): $SKIPPED_REPOS"
if ((FAILED_REPOS > 0)); then
    failed_repos_display=""
    for failed_repo in "${FAILED_REPO_NAMES[@]}"; do
        if [[ -n "$failed_repos_display" ]]; then
            failed_repos_display+=", "
        fi
        failed_repos_display+="$failed_repo"
    done
    log "Failed repositories: $failed_repos_display"
fi
log "Log file: $LOG_FILE_PATH"
log ""

if [[ "$DRY_RUN" = true ]]; then
    log "${YELLOW}⚠️  DRY RUN MODE - No remote branches were pushed${NC}"
    log "${YELLOW}To apply changes safely, re-run with --no-dry-run and an explicit repo list or --all${NC}"
else
    log "${GREEN}✅ Batch cleanup completed${NC}"
fi

if ((FAILED_REPOS > 0)); then
    if [[ "$DRY_RUN" = true ]]; then
        log "${YELLOW}⚠️  Dry run completed with failures. Review failed repositories in the summary above.${NC}"
        exit 0
    fi
    exit 1
fi
