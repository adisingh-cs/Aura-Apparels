// AURA APPARELS Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            setTimeout(() => {
                bsAlert.close();
            }, 5000);
        });
    }, 1000);
    
    // Quantity input controls
    const quantityPlusButtons = document.querySelectorAll('.quantity-right-plus');
    const quantityMinusButtons = document.querySelectorAll('.quantity-left-minus');
    
    quantityPlusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const quantityInput = document.getElementById('quantity');
            const quantity = parseInt(quantityInput.value);
            const max = parseInt(quantityInput.getAttribute('max') || '100');
            if (quantity < max) {
                quantityInput.value = quantity + 1;
            }
        });
    });
    
    quantityMinusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const quantityInput = document.getElementById('quantity');
            const quantity = parseInt(quantityInput.value);
            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
    });
    
    // Product image gallery
    const productThumbs = document.querySelectorAll('.product-image-thumb');
    productThumbs.forEach(thumb => {
        thumb.addEventListener('click', function() {
            const imageElement = this.querySelector('img');
            const mainImage = document.querySelector('.product-image');
            if (mainImage && imageElement) {
                mainImage.src = imageElement.src;
                document.querySelector('.product-image-thumb.active')?.classList.remove('active');
                this.classList.add('active');
            }
        });
    });
    
    // Add to cart animation
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Add a brief animation for feedback
            this.classList.add('btn-success');
            this.innerHTML = '<i class="fas fa-check me-1"></i> Added to Cart';
            
            setTimeout(() => {
                this.classList.remove('btn-success');
                this.innerHTML = '<i class="fas fa-cart-plus me-1"></i> Add to Cart';
            }, 1500);
        });
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            if (this.getAttribute('href') !== '#') {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    window.scrollTo({
                        top: target.offsetTop - 100,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
    
    // Form validation styling
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Image lazy loading
    if ('loading' in HTMLImageElement.prototype) {
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        // Fallback for browsers that don't support lazy loading
        const lazyImageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImageObserver.unobserve(lazyImage);
                }
            });
        });
        
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(lazyImage => {
            lazyImageObserver.observe(lazyImage);
        });
    }
    
    // Back to top button
    const backToTopButton = document.getElementById('back-to-top');
    if (backToTopButton) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopButton.classList.add('show');
            } else {
                backToTopButton.classList.remove('show');
            }
        });
        
        backToTopButton.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Cart item count update
    function updateCartCount() {
        const cartCountBadge = document.querySelector('.cart-items-count');
        if (cartCountBadge) {
            fetch('/cart/count/')
                .then(response => response.json())
                .then(data => {
                    cartCountBadge.textContent = data.count;
                })
                .catch(error => console.error('Error updating cart count:', error));
        }
    }
    
// Product image gallery functionality
function changeMainImage(thumbnail) {
    const mainImage = document.getElementById('mainProductImage');
    mainImage.src = thumbnail.src;
    
    // Update active state
    document.querySelectorAll('.product-thumbnail').forEach(thumb => {
        thumb.classList.remove('active');
    });
    thumbnail.classList.add('active');
}
// Image zoom functionalitydocument.addEventListener('DOMContentLoaded', function () {
    const mainImage = document.getElementById('mainProductImage');
    if (mainImage) {
        mainImage.addEventListener('click', function () {
            const modal = document.createElement('div');
            modal.className = 'image-modal';
            
            const modalImg = document.createElement('img');
            modalImg.src = this.src;
            modalImg.className = 'modal-image';

            // Close button
            const closeButton = document.createElement('span');
            closeButton.innerHTML = '&times;'; // "×" symbol
            closeButton.className = 'modal-close';
            closeButton.addEventListener('click', function () {
                modal.remove();
            });

            modal.appendChild(closeButton);
            modal.appendChild(modalImg);
            document.body.appendChild(modal);

            // Prevent closing when clicking the image itself
            modalImg.addEventListener('click', function (event) {
                event.stopPropagation();
            });

            modal.addEventListener('click', function () {
                modal.remove();
            });
        });
    }
});
