document.addEventListener("DOMContentLoaded", function() {
    // Initialize AOS (Animate On Scroll) library
    AOS.init({
        duration: 1000, // animation duration
        once: true,     // whether animation should happen only once - while scrolling down
    });

    // Smooth scrolling for navigation links
    document.querySelectorAll("#navbarNav .nav-link").forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();

            document.querySelector(this.getAttribute("href")).scrollIntoView({
                behavior: "smooth"
            });

            // Close the navbar on mobile after clicking a link
            const navbarCollapse = document.getElementById("navbarNav");
            if (navbarCollapse.classList.contains("show")) {
                new bootstrap.Collapse(navbarCollapse, { toggle: false }).hide();
            }
        });
    });

    // Add a class to the navbar when scrolled for styling changes
    window.addEventListener("scroll", function() {
        const navbar = document.getElementById("mainNav");
        if (window.scrollY > 50) {
            navbar.classList.add("navbar-scrolled");
        }
        else {
            navbar.classList.remove("navbar-scrolled");
        }
    });
});


