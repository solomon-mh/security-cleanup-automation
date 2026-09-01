#!/bin/bash
# batch-cleanup.sh - Automated cleanup script for all infected repositories
# This script clones each repo, runs the cleanup, and commits the changes

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GITHUB_USER="solomon-mh"
CLEANUP_SCRIPT_URL="https://raw.githubusercontent.com/solomon-mh/security-cleanup-automation/main/cleanup.py"
LOG_FILE="cleanup_$(date +%Y%m%d_%H%M%S).log"
DRY_RUN=true

# List of repositories to clean
REPOS=(
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

# Statistics
TOTAL_REPOS=${#REPOS[@]}
CLEANED_REPOS=0
FAILED_REPOS=0
SKIPPED_REPOS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Security Cleanup - Batch Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Total repositories: $TOTAL_REPOS"
echo "  Dry run mode: $DRY_RUN"
echo "  Log file: $LOG_FILE"
echo ""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-dry-run)
            DRY_RUN=false
            shift
            ;;
        --repo)
            REPOS=("$2")
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-dry-run] [--repo REPO_NAME]"
            exit 1
            ;;
    esac
done

# Create cleanup directory
CLEANUP_DIR="./security-cleanup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CLEANUP_DIR"
cd "$CLEANUP_DIR"

log() {
    echo -e "$1" | tee -a "../$LOG_FILE"
}

cleanup_repo() {
    local repo_name=$1
    local repo_url="https://github.com/${GITHUB_USER}/${repo_name}.git"
    
    log "${BLUE}[*]${NC} Processing: ${repo_name}"
    
    # Clone the repository
    if ! git clone "$repo_url" "$repo_name" 2>/dev/null; then
        log "${RED}[!]${NC} Failed to clone ${repo_name}"
        ((FAILED_REPOS++))
        return 1
    fi
    
    cd "$repo_name"
    
    # Download cleanup script
    if ! wget -q "$CLEANUP_SCRIPT_URL" -O cleanup.py 2>/dev/null; then
        log "${RED}[!]${NC} Failed to download cleanup script for ${repo_name}"
        cd ..
        ((FAILED_REPOS++))
        return 1
    fi
    
    # Run cleanup
    log "${YELLOW}[*]${NC} Scanning ${repo_name}..."
    if python3 cleanup.py . > cleanup_output.log 2>&1; then
        # Check if there are changes
        if ! git diff --quiet; then
            log "${GREEN}[+]${NC} Changes detected in ${repo_name}"
            
            if [ "$DRY_RUN" = true ]; then
                log "${YELLOW}[*]${NC} DRY RUN - Changes not committed"
                git diff --stat >> "../$LOG_FILE"
            else
                log "${GREEN}[+]${NC} Committing changes for ${repo_name}"
                git config user.name "Security Cleanup Bot"
                git config user.email "security@automated.local"
                git add -A
                git commit -m "security: deep cleanup - remove malicious code from supply chain attack

- Remove obfuscated Ethereum wallet exploitation code
- Clean eslint.config.js from injected payloads
- Remove malicious entries from .gitignore
- Clean build configuration files
- Remove suspicious fonts from public/
- Full recursive deep scan completed

This is part of automated security remediation for supply chain attack (Aug 27-31, 2026)."
                
                # Push changes
                if git push origin main 2>/dev/null; then
                    log "${GREEN}[+]${NC} Successfully pushed changes for ${repo_name}"
                    ((CLEANED_REPOS++))
                else
                    log "${RED}[!]${NC} Failed to push changes for ${repo_name}"
                    ((FAILED_REPOS++))
                    cd ..
                    return 1
                fi
            fi
        else
            log "${YELLOW}[*]${NC} No malicious code found in ${repo_name}"
            ((SKIPPED_REPOS++))
        fi
    else
        log "${RED}[!]${NC} Cleanup script failed for ${repo_name}"
        cat cleanup_output.log >> "../$LOG_FILE"
        ((FAILED_REPOS++))
        cd ..
        return 1
    fi
    
    cd ..
    log "${GREEN}[✓]${NC} Completed: ${repo_name}"
    echo ""
}

# Process all repositories
for repo in "${REPOS[@]}"; do
    cleanup_repo "$repo"
done

# Generate summary
echo ""
log "${BLUE}========================================${NC}"
log "${BLUE}Cleanup Summary${NC}"
log "${BLUE}========================================${NC}"
log "Total repositories: $TOTAL_REPOS"
log "Successfully cleaned: $CLEANED_REPOS"
log "Failed: $FAILED_REPOS"
log "Skipped (no changes): $SKIPPED_REPOS"
log "Log file: $LOG_FILE"
log ""

if [ "$DRY_RUN" = true ]; then
    log "${YELLOW}⚠️  DRY RUN MODE - No changes were committed${NC}"
    log "${YELLOW}To apply changes, run: $0 --no-dry-run${NC}"
else
    log "${GREEN}✅ Cleanup complete!${NC}"
fi

cd ..
