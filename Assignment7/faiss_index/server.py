from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from web_indexer import indexer
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/index', methods=['POST'])
def index_page():
    """Endpoint to receive and index page content from Chrome extension"""
    data = request.json
    if not data or 'url' not in data or 'content' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    url = data['url']
    content = data['content']
    title = data.get('title', '')
    
    # Clean HTML content with BeautifulSoup
    try:
        soup = BeautifulSoup(content, 'html.parser')
        # Extract text content
        text_content = soup.get_text(separator=' ', strip=True)
        # Index the cleaned content
        indexer.index_webpage(url, text_content, title)
        return jsonify({"success": True, "message": f"Indexed {url}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['GET'])
def search():
    """Endpoint to search the index"""
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    
    try:
        results = indexer.search(query, k=5)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/highlight', methods=['POST'])
def highlight():
    """Get text highlights for a specific URL based on query"""
    data = request.json
    if not data or 'url' not in data or 'query' not in data or 'content' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    url = data['url']
    query = data['query']
    content = data['content']
    
    try:
        # Clean HTML content
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        
        # Get highlights
        highlights = indexer.get_highlights(query, text_content)
        return jsonify({"highlights": highlights})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get indexer status"""
    return jsonify({
        "total_chunks": len(indexer.metadata),
        "total_urls": len(set(item["url"] for item in indexer.metadata)) if indexer.metadata else 0
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)