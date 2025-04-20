// Content script initialization message
console.log('FAISS Web Indexer content script loaded');

// Listen for messages from the popup or background script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  // Respond to ping to confirm the content script is loaded
  if (request.action === 'ping') {
    sendResponse({status: 'ok'});
    return true;
  }
  
  if (request.action === 'getPageContent') {
    // Get the entire HTML content of the page
    const pageContent = document.documentElement.outerHTML;
    sendResponse({content: pageContent});
    return true;
  }
  
  if (request.action === 'highlight') {
    highlightContent(request.query, request.position);
    sendResponse({status: 'highlighted'});
    return true;
  }
  
  // Default response for unhandled requests
  sendResponse({error: 'Unhandled request'});
  return true;
});

// Function to highlight text on the page
function highlightContent(query, position) {
  // Remove any existing highlights
  removeHighlights();
  
  // Create tooltip element for instructions
  const tooltip = document.createElement('div');
  tooltip.className = 'faiss-tooltip';
  tooltip.textContent = 'Content found! Scroll to see highlighted text.';
  tooltip.style.top = '10px';
  tooltip.style.right = '10px';
  document.body.appendChild(tooltip);
  
  // Remove tooltip after 3 seconds
  setTimeout(() => {
    if (document.body.contains(tooltip)) {
      document.body.removeChild(tooltip);
    }
  }, 3000);
  
  // If we have position information, try to highlight that specific position
  if (position && position.start !== undefined && position.end !== undefined) {
    highlightByPosition(position);
    return;
  }
  
  // Otherwise, highlight by search query
  highlightByQuery(query);
}

function highlightByPosition(position) {
  // Get all text nodes in the document
  const textNodes = [];
  
  function getTextNodes(node) {
    if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
      textNodes.push(node);
    } else {
      for (let i = 0; i < node.childNodes.length; i++) {
        getTextNodes(node.childNodes[i]);
      }
    }
  }
  
  getTextNodes(document.body);
  
  // Approximate position by word count
  let wordCount = 0;
  let foundNode = null;
  let foundIndex = 0;
  
  for (const node of textNodes) {
    const words = node.textContent.split(/\s+/);
    
    if (wordCount + words.length > position.start) {
      // Found the node containing our starting position
      const offset = position.start - wordCount;
      foundNode = node;
      foundIndex = offset;
      break;
    }
    
    wordCount += words.length;
  }
  
  if (foundNode) {
    try {
      // Highlight the text
      const range = document.createRange();
      const words = foundNode.textContent.split(/\s+/);
      
      // Find start position within the text node
      let startPos = 0;
      for (let i = 0; i < foundIndex; i++) {
        if (i < words.length) {
          startPos += words[i].length + 1; // +1 for space
        }
      }
      
      // Set the range
      range.setStart(foundNode, startPos);
      range.setEnd(foundNode, foundNode.textContent.length);
      
      // Create highlight
      const span = document.createElement('span');
      span.className = 'faiss-active-highlight';
      range.surroundContents(span);
      
      // Scroll to the highlight
      span.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    } catch (error) {
      console.error("Error highlighting by position:", error);
      // Fall back to query-based highlighting
      highlightByQuery(position.text || "");
    }
  }
}

function highlightByQuery(query) {
  if (!query) return;
  
  const words = query.split(' ')
    .filter(word => word.length > 2)
    .map(word => word.toLowerCase());
  
  if (words.length === 0) return;
  
  // Find instance of the query in the page
  const textNodes = [];
  
  function getTextNodes(node) {
    if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
      textNodes.push(node);
    } else {
      for (let i = 0; i < node.childNodes.length; i++) {
        getTextNodes(node.childNodes[i]);
      }
    }
  }
  
  getTextNodes(document.body);
  
  // Sort nodes by relevance score
  const scoredNodes = textNodes.map(node => {
    const text = node.textContent.toLowerCase();
    let score = 0;
    
    words.forEach(word => {
      if (text.includes(word)) {
        score += 1;
      }
    });
    
    return { node, score };
  });
  
  // Sort by score, descending
  scoredNodes.sort((a, b) => b.score - a.score);
  
  // Highlight the top matches
  let highlightCount = 0;
  const maxHighlights = 10;
  
  for (const { node, score } of scoredNodes) {
    if (score === 0 || highlightCount >= maxHighlights) break;
    
    try {
      const text = node.textContent;
      const parent = node.parentNode;
      
      // Create a temporary container
      const temp = document.createElement('div');
      
      // Replace the search terms with highlighted versions
      let highlightedText = text;
      words.forEach(word => {
        if (word.length < 3) return; // Skip short words
        
        const regex = new RegExp(`(${escapeRegExp(word)})`, 'gi');
        highlightedText = highlightedText.replace(regex, '<span class="faiss-highlight">$1</span>');
      });
      
      // Set the HTML
      temp.innerHTML = highlightedText;
      
      // Only proceed if we made changes
      if (temp.querySelectorAll('.faiss-highlight').length > 0) {
        // Replace the text node with our highlighted version
        const fragment = document.createDocumentFragment();
        while (temp.firstChild) {
          fragment.appendChild(temp.firstChild);
        }
        
        parent.replaceChild(fragment, node);
        highlightCount++;
        
        // If this is the first match, scroll to it
        if (highlightCount === 1) {
          const firstHighlight = document.querySelector('.faiss-highlight');
          if (firstHighlight) {
            firstHighlight.className = 'faiss-active-highlight';
            firstHighlight.scrollIntoView({
              behavior: 'smooth',
              block: 'center'
            });
          }
        }
      }
    } catch (error) {
      console.error("Error highlighting by query:", error);
      continue;
    }
  }
}

function removeHighlights() {
  // Remove all highlight spans
  const highlights = document.querySelectorAll('.faiss-highlight, .faiss-active-highlight');
  
  highlights.forEach(highlight => {
    try {
      const parent = highlight.parentNode;
      
      // Replace the highlight span with its text content
      const textNode = document.createTextNode(highlight.textContent);
      parent.replaceChild(textNode, highlight);
      
      // Normalize the parent to merge adjacent text nodes
      parent.normalize();
    } catch (error) {
      console.error("Error removing highlight:", error);
    }
  });
  
  // Remove any tooltips
  const tooltips = document.querySelectorAll('.faiss-tooltip');
  tooltips.forEach(tooltip => {
    if (document.body.contains(tooltip)) {
      document.body.removeChild(tooltip);
    }
  });
}

// Helper function to escape special regex characters
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}