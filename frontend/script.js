document.addEventListener('DOMContentLoaded', () => {

    // Helper function to convert a file to a base64 string
    const fileToBase64 = (file) => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = error => reject(error);
    });

    // --- LOGIC for PROMOTIONAL POSTER FORM ---
    const promotionalForm = document.getElementById('promotional-form');
    if (promotionalForm) {
        promotionalForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const generateButton = document.getElementById('generate-button');
            const downloadButton = document.getElementById('download-button');
            const loadingMessage = document.getElementById('loading-message');
            const posterImage = document.getElementById('poster-image');

            generateButton.disabled = true;
            generateButton.textContent = 'Generating...';
            loadingMessage.style.display = 'block';
            posterImage.style.display = 'none';
            if(downloadButton) downloadButton.disabled = true;


            try {
                const logoFile = document.getElementById('logo-upload').files[0];
                const logoBase64 = logoFile ? await fileToBase64(logoFile) : null;

                const formData = {
                    business_type: document.getElementById('business-type').value,
                    business_name: document.getElementById('business-name').value,
                    location: document.getElementById('location').value,
                    headline: document.getElementById('headline').value,
                    style: document.getElementById('style').value,
                    color_palette: document.getElementById('color-palette').value,
                    logo_base64: logoBase64,
                    use_logo_colors: document.getElementById('use-logo-colors').checked,
                };

                const response = await fetch('/api/generate_poster', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Something went wrong on the server.');
                }

                const data = await response.json();
                posterImage.src = data.image_url;
                posterImage.style.display = 'block';
                if(downloadButton) {
                    downloadButton.disabled = false;
                    downloadButton.dataset.imageUrl = data.image_url;
                }

            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate poster: ' + error.message);
            } finally {
                generateButton.disabled = false;
                generateButton.textContent = 'Generate Poster';
                loadingMessage.style.display = 'none';
            }
        });
    }

    // --- LOGIC for FESTIVAL POSTER FORM ---
    const festivalForm = document.getElementById('festival-form');
    if (festivalForm) {
        festivalForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const generateButton = document.getElementById('generate-button');
            const downloadButton = document.getElementById('download-button');
            const loadingMessage = document.getElementById('loading-message');
            const posterImage = document.getElementById('poster-image');

            generateButton.disabled = true;
            generateButton.textContent = 'Generating...';
            loadingMessage.style.display = 'block';
            posterImage.style.display = 'none';
            if(downloadButton) downloadButton.disabled = true;

            try {
                const logoFile = document.getElementById('logo-upload').files[0];
                const logoBase64 = logoFile ? await fileToBase64(logoFile) : null;

                const formData = {
                    business_name: document.getElementById('business-name').value,
                    location: document.getElementById('location').value,
                    festival: document.getElementById('festival').value,
                    greeting: document.getElementById('greeting').value,
                    style: document.getElementById('style').value,
                    color_palette: document.getElementById('color-palette').value,
                    logo_base64: logoBase64,
                    use_logo_colors: document.getElementById('use-logo-colors').checked,
                };

                const response = await fetch('/api/generate_festival_poster', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Something went wrong on the server.');
                }

                const data = await response.json();
                posterImage.src = data.image_url;
                posterImage.style.display = 'block';
                 if(downloadButton) {
                    downloadButton.disabled = false;
                    downloadButton.dataset.imageUrl = data.image_url;
                }

            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate poster: ' + error.message);
            } finally {
                generateButton.disabled = false;
                generateButton.textContent = 'Generate Poster';
                loadingMessage.style.display = 'none';
            }
        });
    }

    // --- LOGIC for MENU CREATOR FORM ---
    const menuForm = document.getElementById('menu-form');
    if (menuForm) {
        const menuItemsContainer = document.getElementById('menu-items-container');
        const addItemButton = document.getElementById('add-item-button');

        const addMenuItem = () => {
            const menuItemDiv = document.createElement('div');
            menuItemDiv.classList.add('menu-item');
            menuItemDiv.innerHTML = `
                <input type="text" placeholder="Item Name" class="menu-item-name" required>
                <input type="text" placeholder="Price" class="menu-item-price" required>
                <button type="button" class="remove-item-button">&times;</button>
            `;
            menuItemsContainer.appendChild(menuItemDiv);
            menuItemDiv.querySelector('.remove-item-button').addEventListener('click', () => {
                menuItemDiv.remove();
            });
        };

        addItemButton.addEventListener('click', addMenuItem);
        addMenuItem(); // Start with one item

        menuForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const generateButton = document.getElementById('generate-button');
            const downloadButton = document.getElementById('download-button');
            const loadingMessage = document.getElementById('loading-message');
            const posterImage = document.getElementById('poster-image');

            generateButton.disabled = true;
            generateButton.textContent = 'Generating...';
            loadingMessage.style.display = 'block';
            posterImage.style.display = 'none';
            if(downloadButton) downloadButton.disabled = true;

            try {
                const logoFile = document.getElementById('logo-upload').files[0];
                if (!logoFile) {
                    throw new Error("A logo is required to generate a menu.");
                }
                const logoBase64 = await fileToBase64(logoFile);

                const menuItems = [];
                document.querySelectorAll('.menu-item').forEach(item => {
                    const name = item.querySelector('.menu-item-name').value;
                    const price = item.querySelector('.menu-item-price').value;
                    if (name && price) {
                        menuItems.push({ name, price });
                    }
                });

                if (menuItems.length === 0) {
                    throw new Error("Please add at least one menu item.");
                }
                
                const formData = {
                    business_name: document.getElementById('business-name').value,
                    contact_info: document.getElementById('contact-info').value,
                    logo_base64: logoBase64,
                    menu_items: menuItems,
                };

                const response = await fetch('/api/generate_menu', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData),
                });
                
                if (!response.ok) {
                    let errorText;
                    try {
                        const errorData = await response.json();
                        errorText = errorData.error;
                    } catch(e) {
                        errorText = await response.text();
                    }
                    throw new Error(errorText || 'Something went wrong on the server.');
                }

                const data = await response.json();
                posterImage.src = data.image_url;
                posterImage.style.display = 'block';
                 if(downloadButton) {
                    downloadButton.disabled = false;
                    downloadButton.dataset.imageUrl = data.image_url;
                }
                
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate menu: ' + error.message);
            } finally {
                generateButton.disabled = false;
                generateButton.textContent = 'Generate Menu';
                loadingMessage.style.display = 'none';
            }
        });
    }
    
    // Universal Download Button Logic
    const downloadButton = document.getElementById('download-button');
    if (downloadButton) {
        downloadButton.addEventListener('click', () => {
            const imageUrl = downloadButton.dataset.imageUrl;
            if (imageUrl) {
                const a = document.createElement('a');
                a.href = imageUrl;
                a.download = imageUrl.split('/').pop();
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
        });
    }
});

