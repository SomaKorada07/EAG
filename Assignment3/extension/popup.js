document.getElementById('sendButton').addEventListener('click', async () => {
    const email = document.getElementById('email').value;
    const statusDiv = document.getElementById('status');
    
    if (!email) {
        statusDiv.textContent = 'Please enter an email address';
        return;
    }

    statusDiv.textContent = 'Sending request...';
    
    try {
        const response = await fetch('http://localhost:8000/fetch-and-send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
        });

        const data = await response.json();
        
        if (response.ok) {
            statusDiv.textContent = 'Success! Check your email.';
            statusDiv.style.color = 'green';
        } else {
            throw new Error(data.detail || 'Failed to send request');
        }
    } catch (error) {
        statusDiv.textContent = `Error: ${error.message}`;
        statusDiv.style.color = 'red';
    }
}); 