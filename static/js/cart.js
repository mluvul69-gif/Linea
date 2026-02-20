// ==================
// CART FUNCTIONALITY
// ==================

// Select all quantity buttons and remove icons
const increaseBtns = document.querySelectorAll('.increase');
const decreaseBtns = document.querySelectorAll('.decrease');
const removeBtns = document.querySelectorAll('.remove-item');
const totalPriceEl = document.querySelector('.total-price');

// Helper: recalculate total
function recalcTotal() {
    let total = 0;
    const cartItems = document.querySelectorAll('.cart-item');
    cartItems.forEach(item => {
        const priceText = item.querySelector('.item-price').innerText;
        let price = parseFloat(priceText.replace(/[^0-9.]/g, '')); // remove $ / R symbols
        const quantity = parseInt(item.querySelector('.quantity').innerText);
        total += price * quantity;
    });
    if (totalPriceEl) totalPriceEl.innerText = `$${total.toFixed(2)}`;
}

// ==================
// INCREASE / DECREASE
increaseBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const parent = btn.closest('.cart-item');
        const quantityEl = parent.querySelector('.quantity');
        let quantity = parseInt(quantityEl.innerText);
        quantity++;
        quantityEl.innerText = quantity;
        recalcTotal();
    });
});

decreaseBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const parent = btn.closest('.cart-item');
        const quantityEl = parent.querySelector('.quantity');
        let quantity = parseInt(quantityEl.innerText);
        if (quantity > 1) {
            quantity--;
            quantityEl.innerText = quantity;
            recalcTotal();
        }
    });
});

// ==================
// REMOVE ITEM
removeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const parent = btn.closest('.cart-item');
        parent.remove();
        recalcTotal();

        // Show empty cart message if no items left
        const cartItemsContainer = document.querySelector('.cart-items');
        if (cartItemsContainer && cartItemsContainer.children.length === 0) {
            document.querySelector('.cart-container').innerHTML = `
                <div class="empty-cart">
                    <h2>Your cart is empty</h2>
                    <a href="shop.html" class="shop-now-btn">Shop Now</a>
                </div>
            `;
        }
    });
});

// ==================
// INITIALIZE TOTAL
recalcTotal();
