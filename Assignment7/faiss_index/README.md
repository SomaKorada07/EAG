# FAISS Web Indexer with Ollama Embeddings

This project creates a system that indexes web pages you visit and builds a FAISS vector index for semantic search. It includes a Chrome extension that allows you to search your browsing history semantically and highlights relevant content on web pages. The system uses Ollama's embedding models for generating vector embeddings.

## Components

1. **FAISS Index System**:
   - Processes web page content
   - Creates embeddings using Ollama's embedding models
   - Builds and maintains a FAISS vector index
   - Provides search API

2. **Chrome Extension**:
   - Captures web page content as you browse
   - Sends content to the indexing system
   - Provides search interface
   - Highlights relevant content on web pages

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

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python server.py
   ```

### Chrome Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `chrome_extension` folder
4. Create icon files in the `images` directory (16x16, 48x48, 128x128)

## Usage

1. **Indexing Pages**:
   - Browse the web normally
   - Click the extension icon in your browser toolbar
   - Click "Index Current Page" to add the current page to your index

2. **Searching**:
   - Click the extension icon
   - Enter your search query in the search box
   - Click on a result to navigate to that page with the relevant content highlighted

## Technical Details

- Uses FAISS (Facebook AI Similarity Search) for efficient vector search
- Leverages Ollama's local embedding models for creating semantic embeddings
- Implements Flask backend for API endpoints
- Chrome extension uses content scripts for page interaction

## Limitations

- Ollama and the server need to be running locally for the extension to work
- Initial indexing may take some time depending on page size
- Highlighting might not be perfect for dynamically loaded content

## Future Improvements

- Support for PDF and other document types
- Improved text chunking strategies
- Better highlighting algorithm
- Support for authentication and multiple users
- Support for other embedding models