// ==================
// HAMBURGER DASHBOARD TOGGLE
const hamburger = document.getElementById('hamburger');
const dashboard = document.getElementById('dashboard');
const closeBtn = document.getElementById('close-dashboard');

if (hamburger && dashboard && closeBtn) {
    // Toggle dashboard when hamburger is clicked
    hamburger.addEventListener('click', () => {
        dashboard.classList.toggle('active');
    });

    // Close button hides dashboard
    closeBtn.addEventListener('click', () => {
        dashboard.classList.remove('active');
    });

    // Clicking outside links closes dashboard
    dashboard.addEventListener('click', (e) => {
        if (e.target === dashboard) {
            dashboard.classList.remove('active');
        }
    });
}

// ==================
// FOOTER VISIBILITY ON SCROLL
const footer = document.querySelector('.footer');

window.addEventListener('scroll', () => {
    if (footer) {
        if (window.scrollY > window.innerHeight / 2) {
            footer.classList.add('visible');
        } else {
            footer.classList.remove('visible');
        }
    }
});

// ==================
// BACK ARROW NAVIGATION
const backArrow = document.querySelector('.back-icon');

if (backArrow) {
    backArrow.addEventListener('click', () => {
        // Navigate back to the shop page
        href = '/shop';
    });
}

// Smooth scroll to shop section (if on homepage)
const shopNowBtn = document.getElementById("shopNowBtn")

if (shopNowBtn) {
    shopNowBtn.addEventListener('click', (e) => {
        e.preventDefault(); // prevent default link jump
        const shopUrl = shopNowBtn.getAttribute('href');

        // Animate scroll (if same page)
        if (shopUrl === '#shop') {
            const shopSection = document.querySelector('.shop-container');
            shopSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            // Navigate to shop page route (Flask)
            window.location.href = shopUrl;
        }
    });
}


