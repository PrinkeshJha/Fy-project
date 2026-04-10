import re
import socket
import ssl
import requests
from urllib.parse import urlparse
from datetime import datetime

SHORTENERS = ["bit.ly", "tinyurl.com", "goo.gl", "t.co"]

def extract_features(url, phishing_label):
    parsed = urlparse(url)
    params = parsed.query

    features = {}

    # Character-based features
    features["qty_equal_params"] = params.count("=")
    features["qty_at_params"] = url.count("@")
    features["qty_and_params"] = url.count("&")
    features["qty_exclamation_params"] = url.count("!")
    features["qty_space_params"] = url.count(" ")
    features["qty_tilde_params"] = url.count("~")
    features["qty_comma_params"] = url.count(",")
    features["qty_plus_params"] = url.count("+")
    features["qty_asterisk_params"] = url.count("*")
    features["qty_hashtag_params"] = url.count("#")
    features["qty_dollar_params"] = url.count("$")
    features["qty_percent_params"] = url.count("%")

    # Parameter statistics
    features["params_length"] = len(params)
    features["qty_params"] = params.count("=")

    # TLD present
    features["tld_present_params"] = 1 if parsed.netloc.split(".")[-1] else 0

    # Email in URL
    features["email_in_url"] = 1 if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+", url) else 0

    # URL shortened
    features["url_shortened"] = 1 if any(s in parsed.netloc for s in SHORTENERS) else 0

    # Network-based features (safe defaults)
    try:
        start = datetime.now()
        requests.get(url, timeout=3)
        features["time_response"] = (datetime.now() - start).total_seconds()
    except:
        features["time_response"] = -1

    try:
        ip = socket.gethostbyname(parsed.netloc)
        features["qty_ip_resolved"] = 1
        features["asn_ip"] = 1
    except:
        features["qty_ip_resolved"] = 0
        features["asn_ip"] = 0

    # SSL Certificate check
    try:
        context = ssl.create_default_context()
        with context.wrap_socket(socket.socket(), server_hostname=parsed.netloc) as s:
            s.connect((parsed.netloc, 443))
            features["tls_ssl_certificate"] = 1
    except:
        features["tls_ssl_certificate"] = 0

    # Placeholder values (can be extended later)
    features["domain_spf"] = 0
    features["time_domain_activation"] = 0
    features["time_domain_expiration"] = 0
    features["qty_nameservers"] = 0
    features["qty_mx_servers"] = 0
    features["ttl_hostname"] = 0
    features["qty_redirects"] = 0
    features["url_google_index"] = 1
    features["domain_google_index"] = 1

    # Label
    features["phishing"] = phishing_label

    return features

url = "https://www.amazon.in"
features = extract_features(url, phishing_label=0)

for k, v in features.items():
    print(k, ":", v)
