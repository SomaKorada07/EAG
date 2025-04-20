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
      
      // Add click event to navigate to the result URL and highlight content
      resultElement.querySelector('.result-title').addEventListener('click', () => {
        // Store data in localStorage to use after navigation
        localStorage.setItem('faiss_highlight_query', query);
        localStorage.setItem('faiss_highlight_position', JSON.stringify(result.position || {}));
        localStorage.setItem('faiss_highlight_text', result.text);
        
        // Open in new tab
        openAndHighlight(result.url, query, result.text, result.position);
      });
      
      searchResults.appendChild(resultElement);
    });
  }
  
  function openAndHighlight(url, query, text, position) {
    console.log("Opening URL and preparing to highlight:", url);
    console.log("Text to highlight:", text.substring(0, 100) + "...");
    
    // Create a new tab with the URL
    chrome.tabs.create({ url: url }, newTab => {
      console.log("Created new tab with ID:", newTab.id);
      
      // Create a listener for tab updates that injects our content script and highlights content
      function tabUpdateListener(tabId, changeInfo, tab) {
        console.log("Tab update:", tabId, changeInfo.status);
        
        if (tabId === newTab.id && changeInfo.status === 'complete') {
          console.log("Tab fully loaded, preparing to inject scripts");
          // Remove the listener once it's triggered
          chrome.tabs.onUpdated.removeListener(tabUpdateListener);
          
          // Ensure the content script is injected
          chrome.scripting.executeScript({
            target: { tabId: newTab.id },
            files: ['contentScript.js']
          }, () => {
            console.log("Content script injected");
            
            // Also inject the CSS
            chrome.scripting.insertCSS({
              target: { tabId: newTab.id },
              files: ['highlight.css']
            }, () => {
              console.log("CSS injected");
              
              // Ping the content script to make sure it's ready
              chrome.tabs.sendMessage(newTab.id, { action: 'ping' }, (pingResponse) => {
                if (pingResponse && pingResponse.status === 'ok') {
                  console.log("Content script is responsive, proceeding with highlight");
                  
                  // Wait for the page to fully render
                  setTimeout(() => {
                    console.log("Sending highlight message");
                    // Send the highlight message
                    chrome.tabs.sendMessage(newTab.id, {
                      action: 'highlight',
                      query: query,
                      text: text,
                      position: position
                    }, response => {
                      console.log('Highlight response:', response);
                    });
                  }, 2000); // Longer delay to ensure page is fully loaded
                } else {
                  console.error("Content script not responding after injection, retrying once");
                  // If we didn't get a response, try once more after a delay
                  setTimeout(() => {
                    chrome.tabs.sendMessage(newTab.id, {
                      action: 'highlight',
                      query: query,
                      text: text,
                      position: position
                    }, response => {
                      console.log('Highlight retry response:', response);
                    });
                  }, 5000); // Longer retry delay
                }
              });
            });
          });
        }
      }
      
      // Register the listener before navigating
      chrome.tabs.onUpdated.addListener(tabUpdateListener);
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
    // More semantic highlighting for result previews
    const queryLower = query.toLowerCase();
    const textLower = text.toLowerCase();
    
    // If the exact query exists in the text, highlight it
    if (textLower.includes(queryLower)) {
      const startIndex = textLower.indexOf(queryLower);
      const endIndex = startIndex + queryLower.length;
      
      return text.substring(0, startIndex) + 
             `<span class="highlight-text">${text.substring(startIndex, endIndex)}</span>` + 
             text.substring(endIndex);
    }
    
    // Otherwise, try to highlight key phrases or concepts
    const words = query.split(' ').filter(word => word.length > 3);
    let highlightedText = text;
    
    // First find important phrases (2+ words together)
    for (let i = 0; i < words.length - 1; i++) {
      const phrase = words[i] + ' ' + words[i+1];
      const phraseRegex = new RegExp(escapeRegExp(phrase), 'gi');
      highlightedText = highlightedText.replace(phraseRegex, match => 
        `<span class="highlight-text">${match}</span>`
      );
    }
    
    // Then highlight individual important words
    words.forEach(word => {
      // Only highlight important words (longer than 3 chars)
      if (word.length > 3) {
        const wordRegex = new RegExp(`\\b${escapeRegExp(word)}\\b`, 'gi');
        highlightedText = highlightedText.replace(wordRegex, match => 
          `<span class="highlight-text">${match}</span>`
        );
      }
    });
    
    return highlightedText;
  }
  
  // Helper function to escape special regex characters
  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
});