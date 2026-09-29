/**
 * Campus Canteen Management System — Main JavaScript
 * Handles responsive navigation, async cart management, menu search/filters,
 * real-time order tracking, star reviews, confirm dialogs, and Chart.js analytics.
 */

const App = {
    init() {
        this.initNavToggle();
        this.initFlashDismiss();
        this.initSidebar();
    },

    initNavToggle() {
        // Public navigation toggle
        const publicToggle = document.getElementById('publicNavToggle');
        const publicNavLinks = document.getElementById('publicNavLinks');
        if (publicToggle && publicNavLinks) {
            publicToggle.addEventListener('click', () => {
                publicNavLinks.classList.toggle('open');
            });
        }

        // Dashboard sidebar toggle button
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
                overlay?.classList.toggle('open');
            });
        }
    },

    initSidebar() {
        const overlay = document.getElementById('sidebarOverlay');
        const closeBtn = document.querySelector('.sidebar-close');
        const sidebar = document.getElementById('sidebar');

        const closeSidebar = () => {
            sidebar?.classList.remove('open');
            overlay?.classList.remove('open');
        };

        overlay?.addEventListener('click', closeSidebar);
        closeBtn?.addEventListener('click', closeSidebar);
    },

    initFlashDismiss() {
        document.querySelectorAll('[data-auto-dismiss]').forEach(el => {
            setTimeout(() => {
                el.style.opacity = '0';
                el.style.transform = 'translateX(100%)';
                setTimeout(() => el.remove(), 300);
            }, 5000);

            el.querySelector('.flash-close')?.addEventListener('click', () => {
                el.remove();
            });
        });
    },

    showToast(message, type = 'success') {
        let container = document.querySelector('.flash-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'flash-container';
            document.body.appendChild(container);
        }

        const flash = document.createElement('div');
        flash.className = `flash flash-${type}`;
        flash.innerHTML = `
            <span>${message}</span>
            <button class="flash-close" aria-label="Close">&times;</button>
        `;

        flash.querySelector('.flash-close').addEventListener('click', () => flash.remove());
        container.appendChild(flash);

        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(100%)';
            setTimeout(() => flash.remove(), 300);
        }, 4000);
    },

    updateCartBadges(count) {
        document.querySelectorAll('.cart-badge, .badge-count').forEach(el => {
            el.textContent = count;
            if (count > 0) {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        });
    },

    async fetchJSON(url, options = {}) {
        const res = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.error || 'Request failed. Please try again.');
        }
        return data;
    },
};

const MenuPage = {
    apiUrl: '',
    categoryId: '',
    searchTerm: '',

    init(apiUrl) {
        this.apiUrl = apiUrl;
        this.bindEvents();
        this.loadMenu();
    },

    bindEvents() {
        const searchInput = document.getElementById('menuSearch');
        let debounceTimer;
        searchInput?.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                this.searchTerm = e.target.value.trim();
                this.loadMenu();
            }, 300);
        });

        document.querySelectorAll('#categoryFilters .filter-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                document.querySelectorAll('#categoryFilters .filter-pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.categoryId = pill.dataset.category || '';
                this.loadMenu();
            });
        });
    },

    async loadMenu() {
        const grid = document.getElementById('menuGrid');
        const loading = document.getElementById('menuLoading');
        const empty = document.getElementById('menuEmpty');
        if (!grid) return;

        loading?.classList.remove('hidden');
        empty?.classList.add('hidden');

        try {
            const params = new URLSearchParams();
            if (this.categoryId) params.set('category_id', this.categoryId);
            if (this.searchTerm) params.set('search', this.searchTerm);

            const data = await App.fetchJSON(`${this.apiUrl}?${params.toString()}`);
            loading?.classList.add('hidden');

            if (!data.items || data.items.length === 0) {
                grid.innerHTML = '';
                empty?.classList.remove('hidden');
                return;
            }

            grid.innerHTML = data.items.map(item => `
                <article class="food-card">
                    <div class="food-card-image">
                        <img src="${item.image || '/static/images/food-placeholder.svg'}" alt="${item.name}" loading="lazy">
                        <span class="food-badge">${item.category || ''}</span>
                    </div>
                    <div class="food-card-body">
                        <h3 class="food-card-title">${item.name}</h3>
                        <p class="food-card-desc">${(item.description || '').substring(0, 70)}${(item.description && item.description.length > 70) ? '...' : ''}</p>
                        <div class="food-card-footer">
                            <span class="price">Rs. ${Math.round(item.price)}</span>
                            <div class="card-btn-group">
                                <a href="/student/menu/${item.id}" class="btn btn-xs btn-outline" title="View details">Details</a>
                                <button type="button" class="btn btn-xs btn-primary menu-add-cart" data-id="${item.id}" title="Quick add to cart">
                                    <i class="fas fa-plus"></i> Add
                                </button>
                            </div>
                        </div>
                    </div>
                </article>
            `).join('');

            // Bind Quick Add buttons
            grid.querySelectorAll('.menu-add-cart').forEach(btn => {
                btn.addEventListener('click', () => {
                    Cart.addItem(btn.dataset.id, 1);
                });
            });
        } catch (err) {
            loading?.classList.add('hidden');
            App.showToast(err.message, 'danger');
        }
    },
};

const Cart = {
    async addItem(itemId, quantity = 1) {
        try {
            const data = await App.fetchJSON('/student/api/cart/add', {
                method: 'POST',
                body: JSON.stringify({
                    menu_item_id: parseInt(itemId),
                    quantity: parseInt(quantity),
                }),
            });
            App.updateCartBadges(data.count);
            App.showToast('Added to your cart!', 'success');
        } catch (err) {
            App.showToast(err.message, 'danger');
        }
    },

    initAddToCart(itemId, maxStock) {
        const qtyInput = document.getElementById('quantity');
        document.querySelectorAll('.qty-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                let val = parseInt(qtyInput.value) || 1;
                if (btn.dataset.action === 'increase' && val < maxStock) {
                    val++;
                } else if (btn.dataset.action === 'decrease' && val > 1) {
                    val--;
                }
                qtyInput.value = val;
            });
        });

        const addBtn = document.getElementById('addToCartBtn');
        addBtn?.addEventListener('click', () => {
            const qty = parseInt(qtyInput?.value) || 1;
            this.addItem(itemId, qty);
        });
    },

    initCartPage() {
        document.querySelectorAll('.cart-update').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const row = btn.closest('.cart-item');
                const qtyEl = row.querySelector('.qty-value');
                let qty = parseInt(qtyEl.textContent) || 1;

                if (btn.dataset.action === 'increase') qty++;
                if (btn.dataset.action === 'decrease') qty--;

                try {
                    const data = await App.fetchJSON('/student/api/cart/update', {
                        method: 'PUT',
                        body: JSON.stringify({
                            menu_item_id: parseInt(id),
                            quantity: qty,
                        }),
                    });
                    App.updateCartBadges(data.count);
                    location.reload();
                } catch (err) {
                    App.showToast(err.message, 'danger');
                }
            });
        });

        document.querySelectorAll('.cart-remove').forEach(btn => {
            btn.addEventListener('click', async () => {
                try {
                    const data = await App.fetchJSON('/student/api/cart/remove', {
                        method: 'DELETE',
                        body: JSON.stringify({
                            menu_item_id: parseInt(btn.dataset.id),
                        }),
                    });
                    App.updateCartBadges(data.count);
                    App.showToast('Item removed from cart', 'info');
                    location.reload();
                } catch (err) {
                    App.showToast(err.message, 'danger');
                }
            });
        });
    },
};

const OrderTracker = {
    interval: null,
    orderId: null,

    init(orderId) {
        this.orderId = orderId;
        this.interval = setInterval(() => this.checkStatus(), 10000);
    },

    async checkStatus() {
        try {
            const data = await App.fetchJSON(`/api/orders/${this.orderId}`);
            const liveBadge = document.getElementById('liveStatusBadge');
            if (liveBadge && data.status) {
                liveBadge.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                liveBadge.className = `status-badge status-${data.status} status-badge-lg`;
            }

            if (data.status === 'completed' || data.status === 'cancelled') {
                clearInterval(this.interval);
                location.reload();
            }
        } catch (_) {
            // Silently retry on next poll
        }
    },
};

const Reviews = {
    init() {
        document.querySelectorAll('.review-form-item').forEach(form => {
            const starContainer = form.querySelector('.star-rating');
            const stars = form.querySelectorAll('.star-btn');
            const feedbackLabel = form.querySelector('.rating-label-feedback');
            let selectedRating = 0;

            const labels = ['', 'Poor ★', 'Fair ★★', 'Good ★★★', 'Very Good ★★★★', 'Excellent ★★★★★'];

            stars.forEach(star => {
                star.addEventListener('click', () => {
                    selectedRating = parseInt(star.dataset.value);
                    stars.forEach((s, i) => s.classList.toggle('active', i < selectedRating));
                    starContainer.dataset.rating = selectedRating;
                    if (feedbackLabel) feedbackLabel.textContent = labels[selectedRating] || '';
                });
            });

            form.querySelector('.submit-review')?.addEventListener('click', async () => {
                const r = parseInt(starContainer?.dataset.rating || selectedRating);
                if (!r || r < 1) {
                    return App.showToast('Please select a 1 to 5 star rating', 'warning');
                }

                const commentText = form.querySelector('.review-comment')?.value || '';

                try {
                    await App.fetchJSON('/student/api/reviews', {
                        method: 'POST',
                        body: JSON.stringify({
                            order_id: parseInt(form.dataset.orderId),
                            menu_item_id: parseInt(form.dataset.itemId),
                            rating: r,
                            comment: commentText,
                        }),
                    });
                    App.showToast('Thank you! Review submitted successfully.', 'success');
                    form.innerHTML = `
                        <div class="existing-review-display">
                            <span class="text-success"><i class="fas fa-check-circle"></i> Review Submitted!</span>
                            <div class="stars-gold">${'★'.repeat(r)}${'★'.repeat(5 - r)}</div>
                            <p class="review-quote">"${commentText}"</p>
                        </div>
                    `;
                } catch (err) {
                    App.showToast(err.message, 'danger');
                }
            });
        });
    },
};

const ConfirmActions = {
    init() {
        document.querySelectorAll('.confirm-form').forEach(form => {
            form.addEventListener('submit', (e) => {
                const msg = form.dataset.confirm || 'Are you sure you want to perform this action?';
                if (!confirm(msg)) {
                    e.preventDefault();
                }
            });
        });
    },
};

const AdminCharts = {
    charts: [],

    async init(apiUrl) {
        try {
            const data = await App.fetchJSON(apiUrl);
            this.renderDailySales(data.daily_sales || []);
            this.renderWeeklyOrders(data.weekly_orders || []);
            this.renderPopularFoods(data.popular_foods || []);
            this.renderCategoryRevenue(data.revenue_by_category || []);
        } catch (err) {
            console.error('Failed to load admin charts:', err);
        }
    },

    renderDailySales(data) {
        const ctx = document.getElementById('dailySalesChart');
        if (!ctx || !window.Chart) return;
        this.charts.push(new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date ? d.date.slice(5) : ''),
                datasets: [{
                    label: 'Revenue (Rs.)',
                    data: data.map(d => d.revenue),
                    borderColor: '#e85d04',
                    backgroundColor: 'rgba(232, 93, 4, 0.12)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#e85d04',
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => 'Rs. ' + value,
                        },
                    },
                },
            },
        }));
    },

    renderWeeklyOrders(data) {
        const ctx = document.getElementById('weeklyOrdersChart');
        if (!ctx || !window.Chart) return;
        this.charts.push(new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.week),
                datasets: [{
                    label: 'Orders',
                    data: data.map(d => d.orders),
                    backgroundColor: '#f48c06',
                    borderRadius: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } },
                },
            },
        }));
    },

    renderPopularFoods(data) {
        const ctx = document.getElementById('popularFoodsChart');
        if (!ctx || !window.Chart) return;
        this.charts.push(new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.name),
                datasets: [{
                    data: data.map(d => d.quantity),
                    backgroundColor: [
                        '#e85d04', '#f48c06', '#faa307', '#ffba08',
                        '#0284c7', '#059669', '#7c3aed', '#dc2626',
                    ],
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' },
                },
            },
        }));
    },

    renderCategoryRevenue(data) {
        const ctx = document.getElementById('categoryRevenueChart');
        if (!ctx || !window.Chart) return;
        this.charts.push(new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.category),
                datasets: [{
                    label: 'Revenue (Rs.)',
                    data: data.map(d => d.revenue),
                    backgroundColor: '#1e293b',
                    borderRadius: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => 'Rs. ' + value,
                        },
                    },
                },
            },
        }));
    },
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
