function verifyDocument() {
    // Get the selected file
    const fileInput = document.getElementById('document');
    const file = fileInput.files[0];

    showLoadingAnimation();

    // Create a FileReader to read the file content
    const reader = new FileReader();

    reader.onloadend = function () {
        // Get the base64-encoded content
        const base64Image = reader.result.split(',')[1];

        // Create a JSON object with the base64-encoded image
        const requestData = {
            image: base64Image
        };

        // Send a POST request to the Flask backend with the JSON object
        fetch('/verify_aadhar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            hideLoadingAnimation();
            // Update the result on the page
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = `<p>Status: ${data.status}</p>`;
            if (data.detects) {
                resultDiv.innerHTML += `<p>Detects: ${data.detects.join(', ')}</p>`;
            }
            if (data.extracted_text) {
                resultDiv.innerHTML += `<p>Extracted Text: ${data.extracted_text}</p>`;
            }
            if (data.qr_data) {
                resultDiv.innerHTML += `<p>QR Data: ${data.qr_data}</p>`;
            }
            if (data.fields_from_text) {
                resultDiv.innerHTML += `<p>Fields from text: ${data.fields_from_text.join(', ')}</p>`;
            }
        })
        .catch(error => console.error('Error:', error));
    };

    // Read the file as a data URL (base64-encoded)
    reader.readAsDataURL(file);
}

function showLoadingAnimation() {
    // Display a loading spinner or other animation
    const loadingDiv = document.getElementById('loading');
    loadingDiv.style.display = 'block';
}

function hideLoadingAnimation() {
    // Hide the loading spinner or other animation
    const loadingDiv = document.getElementById('loading');
    loadingDiv.style.display = 'none';
}
