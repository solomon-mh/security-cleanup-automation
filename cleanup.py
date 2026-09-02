#!/usr/bin/env python3
"""
Security Cleanup Script for GitHub Repositories
Detects and removes malicious code injected by supply chain attack
Targets: eslint.config.js, .gitignore, build configs, public folder malware
"""

import os
import json
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

# MALICIOUS PATTERNS TO DETECT
MALICIOUS_PATTERNS = [
    # Obfuscated Ethereum wallet code
    r'global\.i\s*=\s*["\']A10-\*4650["\']',
    r'_0x[a-f0-9]{6}.*function',
    r'const\s+_0x[a-f0-9]+\s*=',
    r'eth_getTra|eth_blockN|eth_getBlo',
    r'0xa322E5f3',  # Target Ethereum address
    r'createInfl|createGunz|createBrot',  # Compression function obfuscation
    r'spawn.*node.*-e',  # Command execution pattern
    r'withRpcEndpoints|rpcCall|rpcBatch',  # RPC manipulation
    r'global\[.{0,20}r.\]\s*=\s*require',  # Global require injection
    r'global\[.{0,20}_V.\]\s*=',  # Wallet variable injection
    r'global\[.{0,20}_H.\]\s*=',  # Hash injection
    # Obfuscated patterns common in minified malware
    r'\\x[0-9a-f]{2}.*\\x[0-9a-f]{2}',  # Hex encoding
    r'_0x\w+\[0x\w+\]',  # Obfuscated array access
    # Font file injection (malware disguised as fonts)
    r'\.woff2.*exec|\.ttf.*require|\.woff.*eval',
]

# Helper files the attack plants and then hides via .gitignore
MALICIOUS_GITIGNORE_ENTRIES = [
    r'temp_auto_push\.bat',
    r'temp_interactive_push\.bat',
    r'branch_structure\.json',
]

# Files that commonly get infected
TARGET_FILES = [
    'eslint.config.js',
    'eslint.config.mjs',
    '.eslintrc.js',
    '.gitignore',
    'webpack.config.js',
    'next.config.js',
    'next.config.mjs',
    'vite.config.ts',
    'vite.config.js',
    'build.mjs',
    'build.js',
    'rollup.config.js',
    'tsconfig.json',
    'package.json',
]

# Suspicious directories
SUSPICIOUS_DIRS = [
    'public',
    'static',
    'assets',
    '.next',
    'dist',
]

class SecurityCleanup:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.infected_files = []
        self.removed_code = {}
        self.report = {
            'repo': str(self.repo_path),
            'infected_files': [],
            'patterns_found': {},
            'actions_taken': [],
            'timestamp': str(__import__('datetime').datetime.now()),
        }

    def scan_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Scan a file for malicious patterns"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            found_patterns = []
            
            for pattern in MALICIOUS_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    found_patterns.append(pattern)
            
            return len(found_patterns) > 0, found_patterns
        except Exception as e:
            print(f"[!] Error scanning {file_path}: {e}")
            return False, []

    def clean_eslint_config(self, file_path: Path) -> bool:
        """Remove malicious code from eslint.config.js"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original_length = len(content)
            
            # Pattern: remove everything after the closing eslint config
            # eslint.config.js should end with );
            if ');' in content:
                # Find the last legitimate closing
                match = re.search(r'(export\s+default\s+tseslint\.config\([^)]*\);)', content, re.DOTALL)
                if match:
                    content = match.group(1)
                else:
                    # Fallback: find any config ending and cut there
                    last_semi = content.rfind(');')
                    if last_semi != -1:
                        content = content[:last_semi + 2]
            
            # Remove any global variable injections
            content = re.sub(r'global\.i\s*=.*?;', '', content)
            content = re.sub(r'global\.r\s*=.*?;', '', content)
            content = re.sub(r'global\.m\s*=.*?;', '', content)
            content = re.sub(r'const\s+_0x\w+.*?;', '', content, flags=re.DOTALL)
            
            # Remove function declarations starting with _0x
            content = re.sub(r'function\s+_0x\w+\([^)]*\)\s*\{[^}]*\}', '', content, flags=re.DOTALL)
            
            # Clean up extra whitespace
            content = re.sub(r'\n\s*\n+', '\n', content)
            
            if original_length > len(content):
                self.removed_code[str(file_path)] = f"Removed {original_length - len(content)} bytes of malicious code"
                file_path.write_text(content, encoding='utf-8')
                return True
            
            return False
        except Exception as e:
            print(f"[!] Error cleaning eslint config {file_path}: {e}")
            return False

    def clean_gitignore(self, file_path: Path) -> bool:
        """Clean .gitignore of malicious entries"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original_length = len(content)
            
            # Remove obfuscated patterns
            content = re.sub(r'_0x\w+.*', '', content)
            content = re.sub(r'global\[.*', '', content)
            content = re.sub(r'const\s+_0x.*', '', content)

            # Remove entries that hide the attack's helper files
            for entry in MALICIOUS_GITIGNORE_ENTRIES:
                content = re.sub(r'(?m)^.*' + entry + r'.*$\n?', '', content)

            # Keep only legitimate gitignore patterns
            malicious_entry = re.compile('|'.join(MALICIOUS_GITIGNORE_ENTRIES), re.IGNORECASE)
            lines = [line for line in content.split('\n')
                    if line.strip()
                    and not re.search(MALICIOUS_PATTERNS[0], line)
                    and not malicious_entry.search(line)]
            
            content = '\n'.join(lines)
            
            if original_length > len(content):
                self.removed_code[str(file_path)] = f"Removed {original_length - len(content)} bytes"
                file_path.write_text(content, encoding='utf-8')
                return True
            
            return False
        except Exception as e:
            print(f"[!] Error cleaning .gitignore {file_path}: {e}")
            return False

    def clean_config_files(self, file_path: Path) -> bool:
        """Clean webpack/vite/next config files"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original_length = len(content)
            
            # Remove injected global variables
            content = re.sub(r'global\s*\[.*?\]\s*=.*?;', '', content, flags=re.DOTALL)
            
            # Remove obfuscated function calls
            content = re.sub(r'const\s+_0x\w+.*?;', '', content, flags=re.DOTALL)
            content = re.sub(r'function\s+_0x\w+.*?\n', '', content)
            
            # Remove spawn/exec patterns
            content = re.sub(r'spawn\(["\']node["\'].*?\)', '', content, flags=re.DOTALL)
            
            if original_length > len(content):
                self.removed_code[str(file_path)] = f"Removed {original_length - len(content)} bytes"
                file_path.write_text(content, encoding='utf-8')
                return True
            
            return False
        except Exception as e:
            print(f"[!] Error cleaning config {file_path}: {e}")
            return False

    def scan_directory(self):
        """Scan all files in the repository"""
        print(f"\n[*] Scanning repository: {self.repo_path}")
        
        # Scan target files
        for target_file in TARGET_FILES:
            file_path = self.repo_path / target_file
            if file_path.exists():
                is_infected, patterns = self.scan_file(file_path)
                if is_infected:
                    print(f"[!] INFECTED: {target_file} - {len(patterns)} patterns found")
                    self.infected_files.append({
                        'file': target_file,
                        'patterns': patterns,
                        'path': file_path
                    })
                    self.report['infected_files'].append(target_file)
                    self.report['patterns_found'][target_file] = patterns[:3]  # First 3 patterns
        
        # Scan public folder for suspicious files
        public_dirs = [d for d in [self.repo_path / suspicious for suspicious in SUSPICIOUS_DIRS] 
                      if d.exists() and d.is_dir()]
        
        for public_dir in public_dirs:
            for file_path in public_dir.rglob('*'):
                if file_path.is_file():
                    is_infected, patterns = self.scan_file(file_path)
                    if is_infected:
                        print(f"[!] INFECTED: {file_path.relative_to(self.repo_path)}")
                        self.infected_files.append({
                            'file': str(file_path.relative_to(self.repo_path)),
                            'patterns': patterns,
                            'path': file_path
                        })

    def cleanup(self):
        """Clean all infected files"""
        print(f"\n[*] Starting cleanup of {len(self.infected_files)} infected files...")
        
        for infected in self.infected_files:
            file_path = infected['path']
            file_name = infected['file']
            
            print(f"[*] Cleaning: {file_name}")
            
            if 'eslint' in file_name.lower():
                if self.clean_eslint_config(file_path):
                    self.report['actions_taken'].append(f"Cleaned {file_name}")
            elif '.gitignore' in file_name:
                if self.clean_gitignore(file_path):
                    self.report['actions_taken'].append(f"Cleaned {file_name}")
            elif any(config in file_name.lower() for config in ['webpack', 'vite', 'next', 'build', 'rollup']):
                if self.clean_config_files(file_path):
                    self.report['actions_taken'].append(f"Cleaned {file_name}")
            else:
                # For unknown files, just remove them if highly suspicious
                file_path.unlink()
                self.report['actions_taken'].append(f"Removed {file_name} (suspicious file)")
        
        print(f"\n[+] Cleanup complete! {len(self.report['actions_taken'])} files cleaned")

    def generate_report(self, output_file: str = 'cleanup_report.json'):
        """Generate cleanup report"""
        with open(output_file, 'w') as f:
            json.dump(self.report, f, indent=2)
        print(f"[+] Report saved to {output_file}")
        return self.report

    def run(self):
        """Run full cleanup"""
        self.scan_directory()
        if self.infected_files:
            self.cleanup()
        report = self.generate_report()
        return report

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    scan_only = '--scan' in sys.argv or '--scan-only' in sys.argv

    if not args:
        print("Usage: python3 cleanup.py [--scan] <repo_path>")
        print("  --scan  detect and report only; make no changes "
              "(exit 1 if anything is infected)")
        sys.exit(1)

    repo_path = args[0]
    cleanup = SecurityCleanup(repo_path)

    if scan_only:
        cleanup.scan_directory()
        report = cleanup.generate_report()
        print("\n" + "="*60)
        print("SCAN REPORT (no changes made)")
        print("="*60)
        print(json.dumps(report, indent=2))
        sys.exit(1 if cleanup.infected_files else 0)

    report = cleanup.run()

    print("\n" + "="*60)
    print("CLEANUP REPORT")
    print("="*60)
    print(json.dumps(report, indent=2))
