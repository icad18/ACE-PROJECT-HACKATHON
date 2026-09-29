document.addEventListener('DOMContentLoaded', () => {
    const menuData = [
        {
            id: 'nasi-goreng',
            name: 'Nasi Goreng Spesial',
            price: 'Rp 25.000',
            description: 'Nasi goreng dengan bumbu rahasia, telur, ayam suwir, dan kerupuk.',
            type: 'food'
        },
        {
            id: 'mie-ayam',
            name: 'Mie Ayam Bakso',
            price: 'Rp 22.000',
            description: 'Mie ayam dengan topping ayam cincang gurih dan bakso kenyal.',
            type: 'food'
        },
        {
            id: 'roti-bakar',
            name: 'Roti Bakar Coklat Keju',
            price: 'Rp 18.000',
            description: 'Roti bakar hangat dengan lelehan coklat dan parutan keju melimpah.',
            type: 'food'
        },
        {
            id: 'indomie-rebus',
            name: 'Indomie Rebus Telur',
            price: 'Rp 15.000',
            description: 'Indomie rebus klasik dengan tambahan telur dan sayuran.',
            type: 'food'
        },
        {
            id: 'kopi-susu',
            name: 'Kopi Susu Gula Aren',
            price: 'Rp 18.000',
            description: 'Perpaduan kopi pilihan dengan susu segar dan manisnya gula aren.',
            type: 'drink'
        },
        {
            id: 'es-teh',
            name: 'Es Teh Manis',
            price: 'Rp 8.000',
            description: 'Es teh segar yang manis, cocok untuk melepas dahaga.',
            type: 'drink'
        },
        {
            id: 'lemon-tea',
            name: 'Lemon Tea Hangat/Dingin',
            price: 'Rp 15.000',
            description: 'Teh dengan perasan lemon asli, bisa disajikan hangat atau dingin.',
            type: 'drink'
        },
        {
            id: 'matcha-latte',
            name: 'Matcha Latte',
            price: 'Rp 20.000',
            description: 'Minuman matcha premium dengan susu creamy, disajikan dingin.',
            type: 'drink'
        }
    ];

    const foodMenuContainer = document.getElementById('food-menu');
    const drinkMenuContainer = document.getElementById('drink-menu');
    const itemModal = document.getElementById('item-modal');
    const closeModalButton = document.querySelector('.close-button');
    const modalItemName = document.getElementById('modal-item-name');
    const modalItemDescription = document.getElementById('modal-item-description');
    const modalItemPrice = document.getElementById('modal-item-price');

    // Function to render menu items
    function renderMenuItems() {
        foodMenuContainer.innerHTML = ''; // Clear existing items
        drinkMenuContainer.innerHTML = ''; // Clear existing items

        menuData.forEach(item => {
            const menuItemCard = document.createElement('div');
            menuItemCard.classList.add('menu-item-card');
            menuItemCard.dataset.itemId = item.id; // Store item ID for easy retrieval

            menuItemCard.innerHTML = `
                <h4>${item.name}</h4>
                <p>${item.description.substring(0, 50)}...</p>
                <p class="price">${item.price}</p>
                <button class="view-details-button">Lihat Detail</button>
            `;

            // Append to the correct category
            if (item.type === 'food') {
                foodMenuContainer.appendChild(menuItemCard);
            } else if (item.type === 'drink') {
                drinkMenuContainer.appendChild(menuItemCard);
            }
        });

        // Attach event listeners to all "View Details" buttons
        document.querySelectorAll('.view-details-button').forEach(button => {
            button.addEventListener('click', (event) => {
                const itemId = event.target.closest('.menu-item-card').dataset.itemId;
                displayItemDetails(itemId);
            });
        });
    }

    // Function to display item details in the modal
    function displayItemDetails(itemId) {
        const item = menuData.find(i => i.id === itemId);
        if (item) {
            modalItemName.textContent = item.name;
            modalItemDescription.textContent = item.description;
            modalItemPrice.textContent = item.price;
            itemModal.style.display = 'flex'; // Show the modal
        }
    }

    // Function to close the modal
    function closeItemModal() {
        itemModal.style.display = 'none';
    }

    // Event listener for the close button
    closeModalButton.addEventListener('click', closeItemModal);

    // Event listener to close modal when clicking outside the content
    window.addEventListener('click', (event) => {
        if (event.target === itemModal) {
            closeItemModal();
        }
    });

    // Initial render of menu items
    renderMenuItems();
});
