def get_human_readable_template(feature: str, value: float) -> str:
    """
    Returns a human-readable explanation template for a given feature and its raw value.
    """
    if feature == "domain_age":
        if value < 180:
            return f"Domain was registered very recently (only {int(value)} days ago)"
        return f"Domain age is {int(value)} days"
    
    if feature == "url_length":
        if value > 75:
            return f"URL is unusually long ({int(value)} characters)"
        return f"URL length is {int(value)} characters"
        
    if feature == "hostname_length":
        if value > 25:
            return f"Hostname is unusually long ({int(value)} characters)"
        return f"Hostname length is {int(value)} characters"
        
    if feature == "num_dots":
        if value > 3:
            return f"URL contains an unusually high number of dots ({int(value)})"
        return f"URL contains {int(value)} dot(s)"
        
    if feature == "num_hyphens":
        if value > 2:
            return f"URL contains an unusually high number of hyphens ({int(value)})"
        return f"URL contains {int(value)} hyphen(s)"
        
    if feature == "num_subdomains":
        if value > 2:
            return f"URL uses multiple subdomains ({int(value)})"
        return f"URL uses {int(value)} subdomain(s)"
        
    if feature == "has_ip_address":
        if value == 1:
            return "URL is a raw IP address rather than a domain name"
        return "URL uses a standard domain name (no IP address)"
        
    if feature == "has_at_symbol":
        if value == 1:
            return "URL contains an '@' symbol, which is often used to obscure the true domain"
        return "URL does not contain an '@' symbol"
        
    if feature == "is_https":
        if value == 0:
            return "Website does not use secure HTTPS"
        return "Website uses secure HTTPS"
        
    if feature == "domain_entropy":
        if value > 4.0:
            return f"Domain name appears randomly generated (high entropy: {value:.2f})"
        return f"Domain name entropy is typical ({value:.2f})"
        
    if feature == "num_suspicious_keywords":
        if value > 0:
            return f"URL contains {int(value)} suspicious security/login keyword(s)"
        return "URL does not contain suspicious keywords"
        
    if feature == "path_length":
        if value > 40:
            return f"URL path is unusually long ({int(value)} characters)"
        return f"URL path length is {int(value)} characters"
        
    if feature == "num_query_params":
        if value > 3:
            return f"URL contains many query parameters ({int(value)})"
        return f"URL contains {int(value)} query parameter(s)"

    # Fallback
    return f"{feature} (value: {value}) contributed to this prediction"

def format_shap_explanation(shap_result: dict) -> list[str]:
    """
    Takes the top_features from shap_service and returns a list of formatted human-readable strings.
    """
    top_reasons = []
    
    if not shap_result or "top_features" not in shap_result:
        return top_reasons
        
    for item in shap_result["top_features"]:
        feature = item["feature"]
        value = item["value"]
        
        # We only want to highlight features that strongly contributed to the phishing/legit prediction
        # The template itself handles wording based on raw value.
        reason = get_human_readable_template(feature, value)
        top_reasons.append(reason)
        
    return top_reasons
