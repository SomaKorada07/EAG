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
        });
        
        // Inject the CSS as well
        chrome.scripting.insertCSS({
          target: { tabId: tabId },
          files: ['highlight.css']
        });
      }
    });
  }
});

// Handle messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'openUrl') {
    chrome.tabs.create({ url: message.url });
    return true;
  }
});