from flask import Flask, request, jsonify
from flask_cors import CORS
from Feature import extract_features

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the Chrome extension

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400
    
    url = data['url']
    
    try:
        # Extract features
        features = extract_features(url, phishing_label=0) # Label is a dummy for inference
        
        # Here we would normally pass `features` to a trained ML model
        # For now, we will use a simple heuristic based on the extracted features
        
        confidence = 0
        verdict = 'safe'
        tags = []
        
        # Simple heuristic (will be replaced by actual ML model later)
        suspicious_score = 0
        
        if features.get('qty_at_url', 0) > 0:
            suspicious_score += 20
            tags.append({'type': 'danger', 'label': '@ Symbol in URL'})
            
        if features.get('qty_hyphen_domain', 0) > 1:
            suspicious_score += 15
            tags.append({'type': 'warning', 'label': 'Multiple Hyphens in Domain'})
            
        if features.get('length_url', len(url)) > 75:
            suspicious_score += 10
            tags.append({'type': 'warning', 'label': 'Long URL'})
            
        if features.get('time_response', 0) > 3 or features.get('time_response', 0) == -1:
             suspicious_score += 10
             tags.append({'type': 'warning', 'label': 'Slow/No Response'})

        if suspicious_score >= 40:
            verdict = 'danger'
            confidence = min(99, 50 + suspicious_score)
        elif suspicious_score >= 15:
            verdict = 'warning'
            confidence = min(99, 40 + suspicious_score)
        else:
            verdict = 'safe'
            confidence = max(50, 100 - suspicious_score)
            tags.append({'type': 'safe', 'label': 'No major risks detected'})

        return jsonify({
            'url': url,
            'verdict': verdict,
            'confidence': confidence,
            'tags': tags,
            'features': features
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
