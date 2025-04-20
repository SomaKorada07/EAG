document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('search-input');
  const searchButton = document.getElementById('search-button');
  const searchResults = document.getElementById('search-results');
  const indexPageButton = document.getElementById('index-page-button');
  const spinner = document.getElementById('spinner');
  const totalUrlsElement = document.getElementById('total-urls');
  const totalChunksElement = document.getElementById('total-chunks');
  
  const API_URL = 'http://127.0.0.1:5000';
  
  // Load status on popup open
  fetchStatus();
  
  // Search functionality
  searchButton.addEventListener('click', performSearch);
  searchInput.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
      performSearch();
    }
  });
  
  // Index current page
  indexPageButton.addEventListener('click', indexCurrentPage);
  
  function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return;
    
    // Show loading state
    searchResults.innerHTML = '<p>Searching...</p>';
    
    // Fetch search results
    fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`)
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          searchResults.innerHTML = `<p>Error: ${data.error}</p>`;
          return;
        }
        
        displaySearchResults(data.results, query);
      })
      .catch(error => {
        searchResults.innerHTML = `<p>Error connecting to server: ${error.message}. Make sure the Flask server is running at ${API_URL}</p>`;
        console.error('Search error:', error);
      });
  }
  
  function displaySearchResults(results, query) {
    if (!results || results.length === 0) {
      searchResults.innerHTML = '<p>No results found. Try indexing more pages.</p>';
      return;
    }
    
    searchResults.innerHTML = '';
    
    results.forEach(result => {
      const resultElement = document.createElement('div');
      resultElement.className = 'result-item';
      
      const title = result.title || new URL(result.url).hostname;
      
      resultElement.innerHTML = `
        <div class="result-title">${escapeHtml(title)}</div>
        <div class="result-url">${escapeHtml(result.url)}</div>
        <div class="result-text">${highlightText(escapeHtml(result.text), query)}</div>
      `;
      
      // Add click event to navigate to the result URL
      resultElement.querySelector('.result-title').addEventListener('click', () => {
        // Send message to highlight this specific result on the page
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
          const activeTab = tabs[0];
          if (activeTab) {
            // Navigate to the URL if we're not already there
            if (activeTab.url !== result.url) {
              chrome.tabs.update(activeTab.id, {url: result.url}, function() {
                // Wait for page load and then send highlight message
                chrome.tabs.onUpdated.addListener(function listener(tabId, changeInfo) {
                  if (tabId === activeTab.id && changeInfo.status === 'complete') {
                    chrome.tabs.onUpdated.removeListener(listener);
                    
                    // Give the page a moment to fully render
                    setTimeout(() => {
                      sendHighlightMessage(activeTab.id, query, result.position);
                    }, 1000);
                  }
                });
              });
            } else {
              // Already on the correct page, just send highlight message
              sendHighlightMessage(activeTab.id, query, result.position);
            }
          }
        });
      });
      
      searchResults.appendChild(resultElement);
    });
  }
  
  function sendHighlightMessage(tabId, query, position) {
    // Try to send message to the content script
    chrome.tabs.sendMessage(tabId, {
      action: 'highlight',
      query: query,
      position: position
    }, response => {
      // If the content script isn't loaded, inject it and try again
      if (chrome.runtime.lastError) {
        console.log("Content script not loaded, injecting it now");
        
        // Ask the background script to inject the content script
        chrome.runtime.sendMessage({
          action: 'injectContentScript',
          tabId: tabId
        }, () => {
          // Wait a moment for the script to load
          setTimeout(() => {
            chrome.tabs.sendMessage(tabId, {
              action: 'highlight',
              query: query,
              position: position
            });
          }, 500);
        });
      }
    });
  }
  
  function indexCurrentPage() {
    // Show loading state
    spinner.style.display = 'block';
    indexPageButton.disabled = true;
    
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      const activeTab = tabs[0];
      if (!activeTab) {
        showIndexingResult(false, 'No active tab found');
        return;
      }
      
      // Check if content script is loaded and get page content
      sendMessageWithFallback(
        activeTab.id,
        {action: 'getPageContent'},
        function(response) {
          if (!response || !response.content) {
            showIndexingResult(false, 'Failed to get page content');
            return;
          }
          
          // Send to server for indexing
          fetch(`${API_URL}/index`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
              url: activeTab.url,
              title: activeTab.title,
              content: response.content
            })
          })
            .then(response => response.json())
            .then(data => {
              if (data.error) {
                showIndexingResult(false, data.error);
              } else {
                showIndexingResult(true, data.message);
                fetchStatus();  // Update counts
              }
            })
            .catch(error => {
              showIndexingResult(false, `Server error: ${error.message}. Make sure the Flask server is running at ${API_URL}`);
            });
        }
      );
    });
  }
  
  function sendMessageWithFallback(tabId, message, callback) {
    // Try to send message to the content script
    chrome.tabs.sendMessage(tabId, message, response => {
      // If the content script isn't loaded, inject it and try again
      if (chrome.runtime.lastError) {
        console.log("Content script not loaded, injecting it now");
        
        // Use executeScript to inject the content script directly
        chrome.scripting.executeScript({
          target: { tabId: tabId },
          files: ['contentScript.js']
        }, () => {
          // Also inject the CSS
          chrome.scripting.insertCSS({
            target: { tabId: tabId },
            files: ['highlight.css']
          }, () => {
            // Wait a moment for the script to load
            setTimeout(() => {
              // Try sending the message again
              chrome.tabs.sendMessage(tabId, message, callback);
            }, 500);
          });
        });
      } else {
        // Content script responded, call the callback
        callback(response);
      }
    });
  }
  
  function showIndexingResult(success, message) {
    spinner.style.display = 'none';
    indexPageButton.disabled = false;
    
    // Create notification element
    const notification = document.createElement('div');
    notification.style.position = 'fixed';
    notification.style.bottom = '16px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.padding = '8px 16px';
    notification.style.borderRadius = '4px';
    notification.style.color = 'white';
    notification.style.fontSize = '14px';
    notification.style.zIndex = '1000';
    
    if (success) {
      notification.style.backgroundColor = '#34a853';
      notification.textContent = message || 'Page indexed successfully!';
    } else {
      notification.style.backgroundColor = '#ea4335';
      notification.textContent = `Error: ${message || 'Failed to index page'}`;
    }
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 3000);
  }
  
  function fetchStatus() {
    fetch(`${API_URL}/status`)
      .then(response => response.json())
      .then(data => {
        totalUrlsElement.textContent = data.total_urls || 0;
        totalChunksElement.textContent = data.total_chunks || 0;
      })
      .catch(error => {
        console.error('Status fetch error:', error);
        totalUrlsElement.textContent = '?';
        totalChunksElement.textContent = '?';
      });
  }
  
  // Helper functions
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  function highlightText(text, query) {
    // Simple highlighting - can be improved with better matching
    const words = query.split(' ').filter(word => word.length > 2);
    let highlightedText = text;
    
    words.forEach(word => {
      const regex = new RegExp(word, 'gi');
      highlightedText = highlightedText.replace(regex, match => 
        `<span class="highlight-text">${match}</span>`
      );
    });
    
    return highlightedText;
  }
});