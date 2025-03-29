const GEMINI_API_KEY = 'AIzaSyD_fOXB_-Un6c4s77FOMrg2VUU5fecsYmI';
const API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('summarize').addEventListener('click', async () => {
    const summaryDiv = document.getElementById('summary');
    const errorDiv = document.getElementById('error');
    
    try {
      summaryDiv.textContent = 'Extracting page content...';
      errorDiv.style.display = 'none';

      // Get the current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Execute script to get page content
      const [{result}] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const content = document.body.innerText
            .replace(/\s+/g, ' ')
            .trim()
            .substring(0, 5000);
          return content;
        }
      });

      summaryDiv.textContent = 'Generating summary...';

      // Call Gemini API
      const response = await fetch(`${API_URL}?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: `Please provide a concise summary of the following text in 3-4 sentences: ${result}`
            }]
          }],
          generationConfig: {
            temperature: 0.7,
            topK: 40,
            topP: 0.95,
            maxOutputTokens: 1024,
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`API request failed: ${errorData.error?.message || 'Unknown error'}`);
      }

      const data = await response.json();
      summaryDiv.textContent = data.candidates[0].content.parts[0].text;

    } catch (error) {
      errorDiv.style.display = 'block';
      errorDiv.textContent = `Error: ${error.message}`;
      summaryDiv.textContent = '';
      console.error('Error:', error);
    }
  });
}); 