document.addEventListener('DOMContentLoaded', function() {
    // Navigation Menu Toggle
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    
    if (hamburger) {
        hamburger.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // Close menu when clicking a nav link
    const links = document.querySelectorAll('.nav-links a');
    links.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.classList.remove('active');
        });
    });
    
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Contact form submission
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const organization = document.getElementById('organization').value;
            const message = document.getElementById('message').value;
            
            // Form validation
            if (!name.trim() || !email.trim() || !message.trim()) {
                alert('Please fill all required fields');
                return;
            }
            
            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                alert('Please enter a valid email address');
                return;
            }
            
            // Here you would normally send the data to a server
            // For demo purposes, we'll just show a success message
            alert('Thank you for contacting us! We will get back to you soon.');
            contactForm.reset();
        });
    }
    
    // Intersection Observer for scroll animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fadeIn');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Elements to animate
    const animateElements = document.querySelectorAll('.section-header, .problem-card, .feature, .tech, .use-case-card, .solution-image, .solution-text');
    animateElements.forEach(element => {
        element.style.opacity = '0';
        observer.observe(element);
    });
    
    // Highlight active nav item based on scroll position
    const sections = document.querySelectorAll('section');
    window.addEventListener('scroll', function() {
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (window.scrollY >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });
        
        links.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
    
    // Function to add hover effect to stats
    const stats = document.querySelectorAll('.stat h4');
    stats.forEach(stat => {
        const value = parseInt(stat.innerText);
        stat.innerText = '0';
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    let count = 0;
                    const interval = setInterval(() => {
                        count += Math.ceil(value / 50);
                        if (count >= value) {
                            stat.innerText = value + '%';
                            clearInterval(interval);
                        } else {
                            stat.innerText = count + '%';
                        }
                    }, 30);
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        observer.observe(stat);
    });
    
    // Pulse animation for dots
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        setTimeout(() => {
            dot.style.animationDelay = index * 0.5 + 's';
        }, 100);
    });
});