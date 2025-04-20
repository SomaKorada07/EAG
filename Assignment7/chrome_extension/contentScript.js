// Content script initialization message
console.log('FAISS Web Indexer content script loaded');

// Listen for messages from the popup or background script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  // Respond to ping to confirm the content script is loaded
  if (request.action === 'ping') {
    console.log("Ping received");
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
    // Log the received data for debugging
    console.log("[FAISS] Received highlight request:", request);
    
    // Delay to ensure page is loaded
    setTimeout(() => {
      try {
        // Simple highlighting approach
        const result = simpleHighlight(request.text);
        console.log("[FAISS] Highlight result:", result);
      } catch (e) {
        console.error("[FAISS] Error highlighting:", e);
      }
    }, 1000);
    
    sendResponse({status: 'highlight request received'});
    return true;
  }
  
  // Default response for unhandled requests
  sendResponse({error: 'Unhandled request'});
  return true;
});

// Simple direct text search highlighting
function simpleHighlight(text) {
  // Clean up any existing highlights
  removeHighlights();
  
  // Show a notification
  showTooltip("Searching for content...");
  
  if (!text || text.length < 10) {
    console.log("[FAISS] Text too short to highlight");
    return false;
  }
  
  // Clean and normalize the text
  const cleanText = text.replace(/\s+/g, ' ').trim();
  console.log("[FAISS] Clean text:", cleanText.substring(0, 50) + "...");
  
  // Extract a shorter segment that's likely to be unique
  const textSegments = [];
  
  // Try several sentences if available
  const sentences = cleanText.split(/[.!?]/).filter(s => s.trim().length > 15);
  if (sentences.length > 0) {
    sentences.slice(0, Math.min(3, sentences.length)).forEach(s => {
      textSegments.push(s.trim());
    });
  } else {
    // Or just use the first chunk
    textSegments.push(cleanText.substring(0, Math.min(100, cleanText.length)));
  }
  
  console.log("[FAISS] Text segments to try:", textSegments);
  
  // Highlight the main elements in the page
  const mainTextElements = getMainTextElements();
  
  // Log what we found for debugging
  console.log("[FAISS] Found", mainTextElements.length, "main text elements");
  
  // ENHANCED TEXT MATCHING APPROACH
  // First try to search for direct text matches
  for (const segment of textSegments) {
    // Skip segments that are too short
    if (segment.length < 15) continue;
    
    // Try exact matching first
    for (const element of mainTextElements) {
      const elementText = element.innerText || element.textContent;
      
      // If the element contains the segment exactly
      if (elementText.includes(segment)) {
        console.log("[FAISS] Found exact matching element:", element.tagName, elementText.substring(0, 50) + "...");
        
        // Highlight the specific text inside the element
        highlightExactText(element, segment);
        
        // Show a tooltip about the find
        showTooltip("Found exact matching content! Scroll to see highlighted text.");
        
        return true;
      }
    }
  }
  
  // If no exact matches, try normalized text matching (ignoring case and extra spaces)
  for (const segment of textSegments) {
    if (segment.length < 15) continue;
    
    const normalizedSegment = segment.toLowerCase().replace(/\s+/g, ' ').trim();
    
    for (const element of mainTextElements) {
      const elementText = (element.innerText || element.textContent).toLowerCase().replace(/\s+/g, ' ').trim();
      
      if (elementText.includes(normalizedSegment)) {
        console.log("[FAISS] Found case-insensitive match:", element.tagName);
        highlightElement(element);
        showTooltip("Found matching content! Scroll to see highlighted text.");
        return true;
      }
    }
  }
  
  // If still no matches, try fuzzy matching on paragraphs
  const paragraphs = document.querySelectorAll('p');
  const firstSegment = textSegments[0]; // Use the first segment for fuzzy matching
  
  // Score each paragraph by word overlap
  const scoredParagraphs = [];
  
  for (const para of paragraphs) {
    const paraText = para.innerText || para.textContent;
    if (paraText.length < 20) continue; // Skip short paragraphs
    
    const score = calculateWordOverlap(firstSegment, paraText);
    if (score > 0.5) { // At least 50% word overlap
      scoredParagraphs.push({ element: para, score });
    }
  }
  
  // Sort by score
  scoredParagraphs.sort((a, b) => b.score - a.score);
  
  // Highlight the top match if we found any
  if (scoredParagraphs.length > 0) {
    console.log("[FAISS] Found fuzzy match with score:", scoredParagraphs[0].score);
    highlightElement(scoredParagraphs[0].element);
    showTooltip("Found similar content! Scroll to see highlighted text.");
    return true;
  }
  
  // Last resort: highlight any paragraph containing query words
  const words = firstSegment.split(/\s+/).filter(w => w.length > 4);
  console.log("[FAISS] Looking for key words:", words);
  
  if (words.length > 0) {
    for (const para of paragraphs) {
      const paraText = para.innerText || para.textContent;
      for (const word of words) {
        if (paraText.toLowerCase().includes(word.toLowerCase())) {
          console.log("[FAISS] Found paragraph with key word:", word);
          highlightElement(para);
          showTooltip("Found related content! Scroll to see highlighted text.");
          return true;
        }
      }
    }
  }
  
  // If we still haven't found anything, highlight the main content area
  const mainContent = findMainContentElement();
  if (mainContent) {
    console.log("[FAISS] Highlighting main content as fallback");
    highlightElement(mainContent);
    showTooltip("Highlighted main content. The exact text may have changed.");
    return true;
  }
  
  console.log("[FAISS] Could not find any matching content");
  return false;
}

// Get the main text elements from the page
function getMainTextElements() {
  const elements = [];
  
  // Common text-containing elements
  const selectors = [
    'p', 'article', 'section', 'div > p', '.content', 
    'h1', 'h2', 'h3', 'li', 'blockquote', '.post',
    'article p', 'main p', '.content p', '.post p'
  ];
  
  selectors.forEach(selector => {
    const found = document.querySelectorAll(selector);
    found.forEach(el => {
      if ((el.innerText || el.textContent).trim().length > 20) {
        elements.push(el);
      }
    });
  });
  
  return elements;
}

// Highlight an element and scroll to it
function highlightElement(element) {
  // Clean up any existing highlights
  removeHighlights();
  
  // Add the highlight class
  element.classList.add('faiss-active-highlight');
  
  // Scroll to the element
  element.scrollIntoView({
    behavior: 'smooth',
    block: 'center'
  });
  
  return true;
}

// Highlight exact text within an element
function highlightExactText(element, text) {
  // Clean up existing highlights
  removeHighlights();
  
  const innerHTML = element.innerHTML;
  const index = element.innerText.indexOf(text);
  
  if (index === -1) {
    // Fallback to highlighting the whole element if text not found
    highlightElement(element);
    return false;
  }
  
  // Create a wrapper for the target text
  const wrapper = document.createElement('span');
  wrapper.className = 'faiss-active-highlight';
  
  // Find the text node containing our target text
  const textNodes = [];
  getTextNodesIn(element, textNodes);
  
  let currentIndex = 0;
  let foundNode = null;
  let nodeStartIndex = 0;
  
  // Find the text node containing our target text
  for (const node of textNodes) {
    const nodeTextLength = node.textContent.length;
    
    if (currentIndex <= index && index < currentIndex + nodeTextLength) {
      foundNode = node;
      nodeStartIndex = currentIndex;
      break;
    }
    
    currentIndex += nodeTextLength;
  }
  
  if (foundNode) {
    // Calculate where in the node our text starts
    const startOffset = index - nodeStartIndex;
    const endOffset = startOffset + text.length;
    
    // Use range to highlight the text
    const range = document.createRange();
    range.setStart(foundNode, startOffset);
    range.setEnd(foundNode, endOffset);
    
    // Replace with wrapped text
    const span = document.createElement('span');
    span.className = 'faiss-active-highlight';
    range.surroundContents(span);
    
    // Scroll the highlighted span into view
    span.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    });
    
    return true;
  } else {
    // Fallback to highlighting the whole element
    highlightElement(element);
    return false;
  }
}

// Helper function to get all text nodes in an element
function getTextNodesIn(node, textNodes) {
  if (node.nodeType === Node.TEXT_NODE) {
    textNodes.push(node);
  } else {
    const children = node.childNodes;
    for (let i = 0; i < children.length; i++) {
      getTextNodesIn(children[i], textNodes);
    }
  }
}

// Calculate word overlap between two texts
function calculateWordOverlap(text1, text2) {
  const words1 = new Set(text1.toLowerCase().split(/\s+/).filter(w => w.length > 3));
  const words2 = text2.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  
  if (words1.size === 0 || words2.length === 0) return 0;
  
  let matches = 0;
  for (const word of words2) {
    if (words1.has(word)) {
      matches++;
    }
  }
  
  return matches / Math.max(words1.size, words2.length);
}

// Find the main content element of the page
function findMainContentElement() {
  // Common main content selectors
  const mainSelectors = [
    'main',
    'article',
    '#content',
    '.content',
    '.main',
    '.main-content',
    '.post-content',
    '.entry-content',
    '#main'
  ];
  
  for (const selector of mainSelectors) {
    const element = document.querySelector(selector);
    if (element && (element.innerText || element.textContent).length > 100) {
      return element;
    }
  }
  
  // If no main content element found, try to find the element with the most text
  const elements = document.querySelectorAll('div, section, article');
  let bestElement = null;
  let maxLength = 0;
  
  for (const element of elements) {
    const text = element.innerText || element.textContent;
    if (text.length > maxLength) {
      maxLength = text.length;
      bestElement = element;
    }
  }
  
  return bestElement;
}

// Remove all highlights from the page
function removeHighlights() {
  // Remove highlighted elements
  const highlighted = document.querySelectorAll('.faiss-active-highlight, .faiss-highlight');
  highlighted.forEach(el => {
    el.classList.remove('faiss-active-highlight');
    el.classList.remove('faiss-highlight');
  });
  
  // Remove tooltips
  const tooltips = document.querySelectorAll('.faiss-tooltip');
  tooltips.forEach(tooltip => tooltip.remove());
}

// Show a tooltip with the given message
function showTooltip(message) {
  // Remove any existing tooltips
  const existingTooltips = document.querySelectorAll('.faiss-tooltip');
  existingTooltips.forEach(tooltip => tooltip.remove());
  
  // Create a new tooltip
  const tooltip = document.createElement('div');
  tooltip.className = 'faiss-tooltip';
  tooltip.textContent = message;
  tooltip.style.top = '10px';
  tooltip.style.right = '10px';
  
  // Add a close button
  const closeButton = document.createElement('span');
  closeButton.textContent = '×';
  closeButton.style.marginLeft = '10px';
  closeButton.style.cursor = 'pointer';
  closeButton.style.fontWeight = 'bold';
  closeButton.onclick = () => tooltip.remove();
  tooltip.appendChild(closeButton);
  
  // Add to the document
  document.body.appendChild(tooltip);
  
  // Remove after 10 seconds
  setTimeout(() => {
    if (document.body.contains(tooltip)) {
      tooltip.remove();
    }
  }, 10000);
}