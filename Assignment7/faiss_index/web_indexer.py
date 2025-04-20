import os
import json
import faiss
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
import time
import datetime
import requests

load_dotenv()

# Configuration
INDEX_DIR = Path("faiss_index")
METADATA_FILE = INDEX_DIR / "metadata.json"
INDEX_FILE = INDEX_DIR / "index.bin"
CACHE_FILE = INDEX_DIR / "url_cache.json"
CHUNK_SIZE = 200
CHUNK_OVERLAP = 50
MAX_RETRIES = 3
RETRY_DELAY = 2
OLLAMA_API_BASE = "http://localhost:11434/api"
EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_DIMENSION = 768  # Default embedding dimension for nomic-embed-text

# Ensure index directory exists
os.makedirs(INDEX_DIR, exist_ok=True)

class WebPageIndexer:
    def __init__(self):
        self.metadata = []
        self.index = None
        self.dimension = DEFAULT_DIMENSION
        self.load_or_create_index()
        self.url_cache = self.load_cache()
    
    def load_cache(self) -> Dict[str, int]:
        """Load URL processing cache"""
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        """Save URL processing cache"""
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.url_cache, f)
    
    def load_or_create_index(self):
        """Load existing index or create a new one"""
        if METADATA_FILE.exists() and INDEX_FILE.exists():
            # Load existing metadata
            with open(METADATA_FILE, 'r') as f:
                self.metadata = json.load(f)
            
            # Load existing index
            self.index = faiss.read_index(str(INDEX_FILE))
            self.dimension = self.index.d
            print(f"Loaded existing index with {len(self.metadata)} chunks")
        else:
            # Create new index
            self.index = faiss.IndexFlatL2(self.dimension)
            print("Created new FAISS index")
    
    def chunk_text(self, text: str, url: str) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        words = text.split()
        chunks_data = []
        
        for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk_words = words[i:i + CHUNK_SIZE]
            if not chunk_words:
                continue
                
            chunk_text = " ".join(chunk_words)
            start_pos = i
            end_pos = i + len(chunk_words) - 1
            
            chunks_data.append({
                "text": chunk_text,
                "url": url,
                "position": {
                    "start": start_pos,
                    "end": end_pos
                },
                "timestamp": datetime.datetime.now().isoformat(),
                "chunk_id": f"{url.replace('://', '_').replace('/', '_').replace('.', '_')}_{start_pos}"
            })
            
        return chunks_data
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using Ollama's API"""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    f"{OLLAMA_API_BASE}/embeddings",
                    json={
                        "model": EMBEDDING_MODEL,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                embedding = response.json().get("embedding")
                
                if not embedding:
                    raise ValueError("No embedding returned from Ollama API")
                    
                return np.array(embedding, dtype=np.float32)
                
            except Exception as e:
                print(f"Embedding error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                else:
                    raise
    
    def index_webpage(self, url: str, content: str, title: str = ""):
        """Index a webpage's content"""
        # Check if URL was already processed
        content_hash = hash(content)
        
        if url in self.url_cache and self.url_cache[url] == content_hash:
            print(f"URL {url} already indexed and unchanged. Skipping.")
            return
            
        # Process the webpage content
        chunks_data = self.chunk_text(content, url)
        new_embeddings = []
        new_metadata = []
        
        print(f"Processing {len(chunks_data)} chunks from {url}")
        
        for i, chunk_data in enumerate(chunks_data):
            try:
                # Get embedding for chunk
                embedding = self.get_embedding(chunk_data["text"])
                
                # If this is the first embedding, set dimension
                if not self.metadata and self.index.ntotal == 0:
                    self.dimension = len(embedding)
                    self.index = faiss.IndexFlatL2(self.dimension)
                
                # Append to new data
                new_embeddings.append(embedding)
                
                # Add title to metadata
                chunk_data["title"] = title
                new_metadata.append(chunk_data)
                
                # Sleep to avoid rate limiting
                if i < len(chunks_data) - 1:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error processing chunk {i} from {url}: {e}")
        
        if new_embeddings:
            # Add to index
            embeddings_array = np.stack(new_embeddings)
            self.index.add(embeddings_array)
            
            # Update metadata
            self.metadata.extend(new_metadata)
            
            # Update cache
            self.url_cache[url] = content_hash
            
            # Save everything
            self.save()
            self.save_cache()
            
            print(f"✅ Added {len(new_embeddings)} chunks from {url} to index")
        else:
            print(f"⚠️ No chunks were successfully processed from {url}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for relevant content"""
        if not self.metadata or self.index.ntotal == 0:
            return []
            
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            query_embedding = query_embedding.reshape(1, -1)
            
            # Search index
            distances, indices = self.index.search(query_embedding, k=min(k, len(self.metadata)))
            
            # Prepare results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= len(self.metadata) or idx < 0:  # Guard against out-of-bounds
                    continue
                    
                result = self.metadata[idx].copy()
                result["score"] = float(distances[0][i])
                results.append(result)
                
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def save(self):
        """Save index and metadata"""
        # Save metadata
        with open(METADATA_FILE, 'w') as f:
            json.dump(self.metadata, f)
            
        # Save index
        faiss.write_index(self.index, str(INDEX_FILE))
        
        print(f"Saved index with {len(self.metadata)} chunks")
    
    def get_highlights(self, query: str, text: str, window_size: int = 100) -> List[Dict[str, Any]]:
        """Get highlighted sections of text based on query"""
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Split text into windows
        words = text.split()
        windows = []
        
        for i in range(0, len(words), window_size // 2):
            window_words = words[i:i + window_size]
            if not window_words:
                continue
                
            window_text = " ".join(window_words)
            windows.append({
                "text": window_text,
                "position": {
                    "start": i,
                    "end": i + len(window_words) - 1
                }
            })
        
        # Get embeddings for windows
        window_embeddings = []
        for window in windows:
            try:
                window_embedding = self.get_embedding(window["text"])
                window_embeddings.append(window_embedding)
            except Exception:
                # If embedding fails, skip this window
                window_embeddings.append(None)
        
        # Calculate similarity scores
        highlights = []
        for i, (window, embedding) in enumerate(zip(windows, window_embeddings)):
            if embedding is None:
                continue
                
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity > 0.5:  # Threshold for relevance
                highlight = window.copy()
                highlight["score"] = float(similarity)
                highlights.append(highlight)
        
        # Sort by similarity score
        highlights.sort(key=lambda x: x["score"], reverse=True)
        
        return highlights[:5]  # Return top 5 highlights


# Create an instance that can be imported by other modules
indexer = WebPageIndexer()

# Example usage
if __name__ == "__main__":
    print("Web Page Indexer initialized")
    
    # Example search
    if indexer.metadata:
        results = indexer.search("example query", k=3)
        print("\nSearch Results:")
        for i, result in enumerate(results):
            print(f"\n#{i+1}: {result['url']} - Score: {result['score']}")
            print(f"→ {result['text'][:150]}...")