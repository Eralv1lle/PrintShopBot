let cart = [];
let products = [];
let scrollbarWidth = 0;

function initApp() {
    calculateScrollbarWidth();
    loadProducts();
    loadCartFromStorage();
    updateCartUI();
    
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    document.getElementById('checkoutForm').addEventListener('submit', handleCheckout);
    
    document.getElementById('phone').addEventListener('input', validatePhone);
    
    document.getElementById('username').addEventListener('input', validateUsername);
}

function calculateScrollbarWidth() {
    const outer = document.createElement('div');
    outer.style.visibility = 'hidden';
    outer.style.overflow = 'scroll';
    document.body.appendChild(outer);
    const inner = document.createElement('div');
    outer.appendChild(inner);
    scrollbarWidth = outer.offsetWidth - inner.offsetWidth;
    outer.remove();
    document.documentElement.style.setProperty('--scrollbar-width', `${scrollbarWidth}px`);
}

function lockScroll() {
    document.body.classList.add('modal-open');
}

function unlockScroll() {
    document.body.classList.remove('modal-open');
}

function validatePhone(e) {
    const oldValue = e.target.value;
    const newValue = oldValue.replace(/[^0-9+]/g, '');

    if (oldValue !== newValue) {
        showToast('⚠️ Телефон: только цифры и +');
    }

    e.target.value = newValue;
}

function validateUsername(e) {
    const oldValue = e.target.value;
    const newValue = oldValue.replace(/[^a-zA-Z0-9_]/g, '');

    if (oldValue !== newValue) {
        showToast('⚠️ Username: только латинские буквы, цифры и _');
    }

    e.target.value = newValue;
}

async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        const data = await response.json();
        if (data.success) {
            products = data.products;
            renderProducts(products);
        }
    } catch (error) {
        showToast('Ошибка загрузки товаров');
    }
}

function renderProducts(productsToRender) {
    const grid = document.getElementById('productsGrid');
    const emptyState = document.getElementById('emptyState');
    
    if (productsToRender.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    grid.style.display = 'grid';
    emptyState.style.display = 'none';
    
    grid.innerHTML = productsToRender.map(product => {
        const imageContent = product.photo_path ? 
            `<img src="${product.photo_path}" alt="${product.name}">` : 
            '🖨️';
        return `
            <div class="product-card" onclick="openProductModal(${product.id})">
                <div class="product-image">${imageContent}</div>
                <div class="product-info">
                    <div class="product-name">${product.name}</div>
                    <div class="product-description">${product.description || ''}</div>
                    <div class="product-footer">
                        <div class="product-price">${formatPrice(product.price)}</div>
                        <button class="btn-add" onclick="event.stopPropagation(); quickAddToCart(${product.id})">В корзину</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function handleSearch(e) {
    const query = e.target.value.toLowerCase();
    const filtered = products.filter(p => 
        p.name.toLowerCase().includes(query) || 
        (p.description && p.description.toLowerCase().includes(query))
    );
    renderProducts(filtered);
}

function openProductModal(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;
    
    const imageContent = product.photo_path ? 
        `<img src="${product.photo_path}" alt="${product.name}">` : 
        '🖨️';
    
    document.getElementById('productModalContent').innerHTML = `
        <div class="product-modal-content">
            <div class="product-modal-image">${imageContent}</div>
            <div class="product-modal-title">${product.name}</div>
            <div class="product-modal-description">${product.description || ''}</div>
            <div class="product-modal-price">${formatPrice(product.price)}</div>
            <div class="quantity-selector">
                <label>Количество:</label>
                <div class="quantity-controls">
                    <button class="qty-btn" onclick="changeModalQty(-1)">−</button>
                    <span class="qty-value" id="modalQty">1</span>
                    <button class="qty-btn" onclick="changeModalQty(1)">+</button>
                </div>
            </div>
            <button class="btn-primary btn-full" onclick="addToCartFromModal(${product.id})">Добавить в корзину</button>
        </div>
    `;
    document.getElementById('productModal').classList.add('active');
    lockScroll();
}

function closeProductModal() {
    document.getElementById('productModal').classList.remove('active');
    unlockScroll();
}

function changeModalQty(delta) {
    const qtyEl = document.getElementById('modalQty');
    let qty = parseInt(qtyEl.textContent);
    qty = Math.max(1, qty + delta);
    qtyEl.textContent = qty;
}

function addToCartFromModal(productId) {
    const qty = parseInt(document.getElementById('modalQty').textContent);
    const product = products.find(p => p.id === productId);
    addToCart(product, qty);
    closeProductModal();
    showToast(`${product.name} добавлен в корзину`);
}

function quickAddToCart(productId) {
    const product = products.find(p => p.id === productId);
    addToCart(product, 1);
    showToast(`${product.name} добавлен в корзину`);
}

function addToCart(product, quantity) {
    const existingItem = cart.find(item => item.product.id === product.id);
    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({ product, quantity });
    }
    updateCartUI();
    saveCartToStorage();
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.product.id !== productId);
    updateCartUI();
    saveCartToStorage();
    renderCartItems();
}

function updateCartQuantity(productId, delta) {
    const item = cart.find(item => item.product.id === productId);
    if (!item) return;
    item.quantity += delta;
    if (item.quantity <= 0) {
        removeFromCart(productId);
        return;
    }
    updateCartUI();
    saveCartToStorage();
    renderCartItems();
}

function updateCartUI() {
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
    
    document.getElementById('cartBadge').textContent = totalItems;
    document.getElementById('headerCartBadge').textContent = totalItems;
    document.getElementById('cartTotal').textContent = formatPrice(totalPrice);
    
    document.getElementById('checkoutBtn').disabled = cart.length === 0;
}

function openCart() {
    renderCartItems();
    document.getElementById('cartSlideOver').classList.add('active');
    lockScroll();
}

function closeCart() {
    document.getElementById('cartSlideOver').classList.remove('active');
    unlockScroll();
}

function renderCartItems() {
    const container = document.getElementById('cartItems');
    const totalPrice = cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
    
    if (cart.length === 0) {
        container.innerHTML = `
            <div class="empty-cart">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="9" cy="21" r="1"></circle>
                    <circle cx="20" cy="21" r="1"></circle>
                    <path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"></path>
                </svg>
                <h3>Корзина пуста</h3>
                <p>Добавьте товары из каталога</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        ${cart.map(item => {
            const imageContent = item.product.photo_path ? 
                `<img src="${item.product.photo_path}" alt="${item.product.name}">` : 
                '🖨️';
            return `
                <div class="cart-item">
                    <div class="cart-item-top">
                        <div class="cart-item-image">${imageContent}</div>
                        <div class="cart-item-info">
                            <div class="cart-item-name">${item.product.name}</div>
                            <div class="cart-item-price">${formatPrice(item.product.price)} за шт.</div>
                        </div>
                    </div>
                    <div class="cart-item-bottom">
                        <div class="cart-item-controls">
                            <button class="qty-btn" onclick="updateCartQuantity(${item.product.id}, -1)">−</button>
                            <span class="qty-value">${item.quantity}</span>
                            <button class="qty-btn" onclick="updateCartQuantity(${item.product.id}, 1)">+</button>
                            <button class="qty-btn remove" onclick="removeFromCart(${item.product.id})">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M18 6L6 18M6 6L18 18"></path>
                                </svg>
                            </button>
                        </div>
                        <div class="cart-item-total">${formatPrice(item.product.price * item.quantity)}</div>
                    </div>
                </div>
            `;
        }).join('')}
        <div class="cart-summary">
            <div class="cart-summary-row">
                <span class="cart-summary-label">Итого:</span>
                <span class="cart-summary-value">${formatPrice(totalPrice)}</span>
            </div>
        </div>
    `;
}

function clearCart() {
    if (confirm('Очистить корзину?')) {
        cart = [];
        updateCartUI();
        saveCartToStorage();
        renderCartItems();
        showToast('Корзина очищена');
    }
}

function openCheckout() {
    const totalPrice = cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
    
    document.getElementById('checkoutTotalValue').textContent = formatPrice(totalPrice);
    
    closeCart();
    document.getElementById('checkoutModal').classList.add('active');
    lockScroll();
}

function closeCheckout() {
    document.getElementById('checkoutModal').classList.remove('active');
    unlockScroll();
}

async function handleCheckout(e) {
    e.preventDefault();
    const firstName = document.getElementById('firstName').value.trim();
    const lastName = document.getElementById('lastName').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const username = document.getElementById('username').value.trim();
    const comment = document.getElementById('comment').value.trim();
    
    if (!firstName || !lastName || !phone) {
        showToast('Заполните обязательные поля');
        return;
    }
    
    const orderData = {
        first_name: firstName,
        last_name: lastName,
        phone: phone,
        username: username,
        comment: comment,
        cart: cart.map(item => ({
            product_id: item.product.id,
            quantity: item.quantity
        }))
    };
    
    try {
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        const data = await response.json();
        if (data.success) {
            showToast('Заказ успешно оформлен!');
            cart = [];
            updateCartUI();
            saveCartToStorage();
            closeCheckout();
            document.getElementById('checkoutForm').reset();
        } else {
            showToast('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        showToast('Ошибка при оформлении заказа');
    }
}

function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
    }).format(price);
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function saveCartToStorage() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

function loadCartFromStorage() {
    const saved = localStorage.getItem('cart');
    if (saved) cart = JSON.parse(saved);
}

document.addEventListener('DOMContentLoaded', initApp);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeProductModal();
        closeCart();
        closeCheckout();
    }
});
