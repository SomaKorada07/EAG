// Background service worker for FAISS Web Indexer extension

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('FAISS Web Indexer extension installed');
});

// Ensure the content script is properly injected when needed
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && /^http/.test(tab.url)) {
    // Check if the content script is already injected
    chrome.tabs.sendMessage(tabId, { action: 'ping' }, response => {
      if (chrome.runtime.lastError) {
        // Content script not loaded, inject it
        chrome.scripting.executeScript({
          target: { tabId: tabId },
          files: ['contentScript.js']
        }, () => {
          // Inject the CSS as well
          chrome.scripting.insertCSS({
            target: { tabId: tabId },
            files: ['highlight.css']
          }, () => {
            // Check if there's a pending highlight operation for this tab
            const query = localStorage.getItem('faiss_highlight_query');
            const position = localStorage.getItem('faiss_highlight_position');
            const text = localStorage.getItem('faiss_highlight_text');
            
            if (query) {
              // Wait a moment for the page to fully render
              setTimeout(() => {
                // Send the highlight message
                chrome.tabs.sendMessage(tabId, {
                  action: 'highlight',
                  query: query,
                  text: text,
                  position: position ? JSON.parse(position) : undefined
                });
                
                // Clear the stored data
                localStorage.removeItem('faiss_highlight_query');
                localStorage.removeItem('faiss_highlight_position');
                localStorage.removeItem('faiss_highlight_text');
              }, 1500);
            }
          });
        });
      }
    });
  }
});

// Handle messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'injectContentScript' && message.tabId) {
    // Inject content script into the specified tab
    chrome.scripting.executeScript({
      target: { tabId: message.tabId },
      files: ['contentScript.js']
    }, () => {
      // Also inject the CSS
      chrome.scripting.insertCSS({
        target: { tabId: message.tabId },
        files: ['highlight.css']
      }, () => {
        sendResponse({ status: 'injected' });
      });
    });
    return true; // Keep the message channel open for the async response
  }
  
  if (message.action === 'openUrl') {
    chrome.tabs.create({ url: message.url }, tab => {
      if (message.highlight) {
        // Store highlight info for when the page loads
        localStorage.setItem('faiss_highlight_query', message.query);
        localStorage.setItem('faiss_highlight_text', message.text || '');
        if (message.position) {
          localStorage.setItem('faiss_highlight_position', JSON.stringify(message.position));
        }
      }
      sendResponse({ status: 'opened', tabId: tab.id });
    });
    return true; // Keep the message channel open for the async response
  }
});