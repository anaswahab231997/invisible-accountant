import re

with open('landing_page.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Lenis script to head
if 'lenis.min.js' not in content:
    content = content.replace(
        '<script src="https://unpkg.com/lucide@latest"></script>',
        '<script src="https://unpkg.com/lucide@latest"></script>\n    <script src="https://unpkg.com/@studio-freight/lenis@1.0.39/dist/lenis.min.js"></script>'
    )

# 2. Add Lenis CSS styles
lenis_css = '''
        /* Lenis Smooth Scroll Recommended CSS */
        html.lenis, html.lenis body {
            height: auto;
        }
        .lenis.lenis-smooth {
            scroll-behavior: auto !important;
        }
        .lenis.lenis-smooth [data-lenis-prevent] {
            overscroll-behavior: contain;
        }
        .lenis.lenis-stopped {
            overflow: hidden;
        }
        .lenis.lenis-scrolling iframe {
            pointer-events: none;
        }
        
        /* High-end reveal animations */
        .reveal {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .reveal.active {
            opacity: 1;
            transform: translateY(0);
        }
'''
if 'html.lenis' not in content:
    content = content.replace('<style>', '<style>\n' + lenis_css)

# 3. Add reveal classes to major sections
content = content.replace('<section class="relative pt-24 pb-12', '<section class="relative pt-24 pb-12 reveal"')
content = content.replace('<div class="bg-cardbg rounded-2xl p-4 md:p-8 border border-gray-200 shadow-soft max-w-4xl mx-auto', '<div class="bg-cardbg rounded-2xl p-4 md:p-8 border border-gray-200 shadow-soft max-w-4xl mx-auto reveal"')

# 4. Initialize Lenis and the IntersectionObserver in JS
lenis_js = '''
        // Initialize High-End Smooth Scrolling (Lenis)
        const lenis = new Lenis({
            duration: 1.2,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), 
            direction: 'vertical', 
            gestureDirection: 'vertical', 
            smooth: true,
            mouseMultiplier: 1,
            smoothTouch: false,
            touchMultiplier: 2,
            infinite: false,
        });

        function raf(time) {
            lenis.raf(time);
            requestAnimationFrame(raf);
        }
        requestAnimationFrame(raf);

        // High-end Intersection Observer for Fade-Ins
        document.addEventListener("DOMContentLoaded", () => {
            const reveals = document.querySelectorAll(".reveal");
            const revealObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("active");
                        observer.unobserve(entry.target);
                    }
                });
            }, {
                root: null,
                threshold: 0.1,
                rootMargin: "0px 0px -50px 0px"
            });
            
            reveals.forEach(reveal => {
                revealObserver.observe(reveal);
            });
            
            // Immediately activate the first section so it doesn't wait for scroll
            setTimeout(() => {
                if(reveals[0]) reveals[0].classList.add("active");
            }, 100);
        });

'''

if 'const lenis = new Lenis' not in content:
    content = content.replace('lucide.createIcons();', 'lucide.createIcons();\n\n' + lenis_js)


with open('landing_page.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Smooth scrolling and animations successfully injected!")
