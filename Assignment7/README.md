# Web Page Indexer with FAISS and Ollama Embeddings

This project creates a semantic search system for web pages using FAISS (Facebook AI Similarity Search) vectors along with a Chrome extension that allows you to search and navigate to specific content on indexed web pages. The system leverages Ollama for local embedding generation.

## Project Structure

- `/faiss_index/`: Contains the Python backend for the FAISS indexing system
  - `web_indexer.py`: Core indexing functionality using Ollama embeddings
  - `server.py`: Flask API server
  - `requirements.txt`: Python dependencies
  - `README.md`: Detailed backend documentation

- `/chrome_extension/`: Contains the Chrome extension
  - `manifest.json`: Extension configuration
  - `popup.html/css/js`: Extension popup interface
  - `contentScript.js`: Page interaction and highlighting
  - `background.js`: Extension background service
  - `highlight.css`: Styling for highlighted content
  - `images/`: Directory for extension icons

## How It Works

1. The Chrome extension captures web pages you visit
2. Web page content is processed and embedded using Ollama's embedding models
3. Embeddings are stored in a FAISS vector index
4. When you search, the query is embedded and similar content is found
5. Results link back to the original web pages with relevant content highlighted

## Setup

### Ollama Setup

1. Install Ollama following the instructions at [ollama.ai](https://ollama.ai)
2. Pull the embedding model:
   ```bash
   ollama pull nomic-embed-text
   ```
3. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

### Backend Setup

1. Navigate to the `faiss_index` directory
2. Install dependencies: `pip install -r requirements.txt`
3. Start the server: `python server.py`

### Chrome Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `chrome_extension` folder
4. Create icon files in the `images` directory (16x16, 48x48, 128x128)

## Usage

1. Browse the web normally
2. Click the extension icon and choose "Index Current Page" to add pages to your index
3. To search: open the extension popup, enter your query, and click "Search"
4. Click on a result to navigate to that page with the content highlighted

## Requirements

- Python 3.8+
- Google Chrome browser
- Ollama installed and running locally
- Flask server running locally