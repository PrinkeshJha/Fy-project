import math
import socket
import ssl
import re
import datetime
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import tldextract
import whois
import sys
import os

# Add the backend root directory to the python path to import Feature.py
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from Feature import extract_features as extract_all_features

SUSPICIOUS_KEYWORDS = ["login", "verify", "bank", "secure", "account", "signin", "update", "confirm", "paypal", "amazon", "microsoft"]
SPECIAL_CHARS_PATTERN = re.compile(r'[@\?=\_%&]')
IP_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')

def _calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    entropy = 0.0
    for x in set(text):
        p_x = float(text.count(x)) / len(text)
        entropy -= p_x * math.log(p_x, 2)
    return entropy

def _get_domain_age(domain: str) -> int:
    try:
        # Wrap whois call with a timeout in production or rely on underlying socket timeout if possible.
        # python-whois doesn't have a direct timeout param on the high-level API,
        # but we can set a global socket timeout just in case it hangs on the network.
        socket.setdefaulttimeout(3.0)
        w = whois.whois(domain)
        creation_date = w.creation_date
        
        if not creation_date:
            return -1
            
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
            
        if isinstance(creation_date, str):
            # Try some basic parsing if it returned a string instead of datetime
            # Fallback to -1 if unparseable
            return -1
            
        age = (datetime.datetime.now() - creation_date).days
        return age if age >= 0 else -1
    except Exception:
        return -1
    finally:
        socket.setdefaulttimeout(None)

def _check_ssl(domain: str) -> int:
    try:
        context = ssl.create_default_context()
        # Set a short timeout
        with socket.create_connection((domain, 443), timeout=3.0) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                if cert:
                    return 1
    except Exception:
        return 0
    return 0

def extract_features(url: str) -> Tuple[Dict[str, float], List[str]]:
    """
    Extracts exactly 13 features for phishing detection.
    Returns: (feature_vector, reasons)
    """
    reasons = []
    
    if not url.startswith('http'):
        url = 'http://' + url

    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Extract domain parts
    ext = tldextract.extract(url)
    full_domain = ext.domain + "." + ext.suffix if ext.suffix else ext.domain
    subdomain = ext.subdomain

    # 1. url_length
    url_length = len(url)
    if url_length > 75:
        reasons.append("URL length is unusually long")
        
    # 2. dots (in domain)
    dots = domain.count('.')
    if dots > 3:
        reasons.append("Unusually high number of dots in domain")
        
    # 3. hyphens (in domain)
    hyphens = domain.count('-')
    if hyphens > 1:
        reasons.append("Multiple hyphens in domain, often used to spoof legitimate sites")
        
    # 4. digits (in domain)
    digits = sum(c.isdigit() for c in domain)
    if digits > 0:
        reasons.append("Domain contains numeric characters")
        
    # 5. special_chars
    special_chars = len(SPECIAL_CHARS_PATTERN.findall(url))
    if special_chars > 2:
        reasons.append("URL contains many special characters")
        
    # 6. contains_ip
    hostname = parsed.hostname or domain
    contains_ip = 1 if IP_PATTERN.match(hostname) else 0
    if contains_ip == 1:
        reasons.append("Domain is a raw IP address")
        
    # 7. contains_at
    contains_at = 1 if '@' in url else 0
    if contains_at == 1:
        reasons.append("URL contains '@', which can hide the true destination")
        
    # 8. https
    https = 1 if parsed.scheme == 'https' else 0
    if https == 0:
        reasons.append("URL does not use HTTPS")
        
    # 9. entropy
    entropy = _calculate_entropy(domain)
    if entropy > 4.0:
        reasons.append("Domain has high entropy (appears random/generated)")
        
    # 10. subdomains
    subdomains = len(subdomain.split('.')) if subdomain else 0
    if subdomains >= 2:
        reasons.append("Too many subdomains detected")
        
    # 11. domain_age
    domain_age = _get_domain_age(full_domain)
    if domain_age != -1 and domain_age < 180:
        reasons.append(f"Domain is recently created (age: {domain_age} days)")
    elif domain_age == -1:
        reasons.append("Could not determine domain age (WHOIS lookup failed)")
        
    # 12. ssl_valid
    ssl_valid = _check_ssl(domain)
    if ssl_valid == 0:
        reasons.append("No valid SSL certificate found")
        
    # 13. suspicious_keywords
    suspicious_keywords = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in url.lower())
    if suspicious_keywords > 0:
        reasons.append(f"URL contains {suspicious_keywords} suspicious keyword(s)")

    feature_vector = extract_all_features(url)
    
    return feature_vector, reasons
