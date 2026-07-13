import re
import socket
import ssl
import requests
from urllib.parse import urlparse
import time

SHORTENERS = [
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "is.gd", "cli.gs", "yfrog.com", 
    "migre.me", "ff.im", "twit.ac", "su.pr", "twurl.nl", "snipurl.com", "short.to", 
    "BudURL.com", "ping.fm", "post.ly", "Just.as", "bkite.com", "snipr.com", "fic.kr", 
    "loopt.us", "doiop.com", "short.ie", "kl.am", "wp.me", "rubyurl.com", "om.ly", 
    "to.ly", "bit.do", "lnkd.in", "db.tt", "qr.ae", "adf.ly", "bitly.com", "cur.lv", 
    "ow.ly", "ity.im", "q.gs", "po.st", "bc.vc", "twitthis.com", "u.to", "j.mp", 
    "buzurl.com", "cutt.us", "u.bb", "yourls.org", "x.co", "prettylinkpro.com", 
    "scrnch.me", "filoops.info", "vzturl.com", "qr.net", "1url.com", "tweez.me", "v.gd", 
    "tr.im", "link.zip.net"
]

def extract_features(url, phishing_label=None):
    features = {}
    
    if not url.startswith('http'):
        url = 'http://' + url
        
    parsed = urlparse(url)
    
    domain = parsed.netloc
    path = parsed.path
    query = parsed.query
    
    # Simple logic for directory and file
    if '/' in path:
        parts = path.split('/')
        if '.' in parts[-1]:
            file = parts[-1]
            directory = '/'.join(parts[:-1]) + '/'
        else:
            file = ""
            directory = path
    else:
        file = ""
        directory = path

    # Helper function to count chars
    def count_chars(text):
        if text is None: text = ""
        return {
            'qty_dot': text.count('.'),
            'qty_hyphen': text.count('-'),
            'qty_underline': text.count('_'),
            'qty_slash': text.count('/'),
            'qty_questionmark': text.count('?'),
            'qty_equal': text.count('='),
            'qty_at': text.count('@'),
            'qty_and': text.count('&'),
            'qty_exclamation': text.count('!'),
            'qty_space': text.count(' ') + text.count('%20'),
            'qty_tilde': text.count('~'),
            'qty_comma': text.count(','),
            'qty_plus': text.count('+'),
            'qty_asterisk': text.count('*'),
            'qty_hashtag': text.count('#'),
            'qty_dollar': text.count('$'),
            'qty_percent': text.count('%')
        }

    # URL specific
    url_chars = count_chars(url)
    for k, v in url_chars.items():
        features[k + "_url"] = v
        
    features['qty_tld_url'] = 1 if len(domain.split('.')) > 1 else 0
    features['length_url'] = len(url)

    # Domain specific
    domain_chars = count_chars(domain)
    for k, v in domain_chars.items():
        features[k + "_domain"] = v
        
    features['qty_vowels_domain'] = sum(1 for c in domain.lower() if c in 'aeiou')
    features['domain_length'] = len(domain)
    features['domain_in_ip'] = 1 if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain) else 0
    features['server_client_domain'] = 1 if 'server' in domain.lower() or 'client' in domain.lower() else 0

    # Directory specific
    dir_chars = count_chars(directory)
    for k, v in dir_chars.items():
        features[k + "_directory"] = v if directory else -1
    features['directory_length'] = len(directory) if directory else -1

    # File specific
    file_chars = count_chars(file)
    for k, v in file_chars.items():
        features[k + "_file"] = v if file else -1
    features['file_length'] = len(file) if file else -1

    # Params specific
    params_chars = count_chars(query)
    for k, v in params_chars.items():
        features[k + "_params"] = v if query else -1
    features['params_length'] = len(query) if query else -1
    features['tld_present_params'] = 1 if any(tld in query.lower() for tld in ['.com', '.org', '.net', '.info']) else (-1 if not query else 0)
    features['qty_params'] = query.count('=') if query else -1

    # General / Network
    features['email_in_url'] = 1 if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+", url) else 0

    try:
        start = time.time()
        requests.get(url, timeout=3)
        features["time_response"] = time.time() - start
    except:
        features["time_response"] = -1

    features['domain_spf'] = -1
    features['asn_ip'] = -1
    features['time_domain_activation'] = -1
    features['time_domain_expiration'] = -1

    try:
        ip = socket.gethostbyname(domain)
        features["qty_ip_resolved"] = 1
    except:
        features["qty_ip_resolved"] = -1

    features['qty_nameservers'] = 1
    features['qty_mx_servers'] = 1
    features['ttl_hostname'] = -1

    try:
        context = ssl.create_default_context()
        with context.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.connect((domain, 443))
            features["tls_ssl_certificate"] = 1
    except:
        features["tls_ssl_certificate"] = 0

    features['qty_redirects'] = -1
    features['url_google_index'] = 0
    features['domain_google_index'] = 0

    features['url_shortened'] = 1 if any(s in domain for s in SHORTENERS) else 0
    
    # Label
    if phishing_label is not None:
        features['phishing'] = phishing_label

    return features

if __name__ == "__main__":
    url = "https://www.amazon.in"
    f = extract_features(url, 0)
    for k, v in f.items():
        print(f"{k}: {v}")
