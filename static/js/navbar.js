// Navbar "scroll spy": highlights the link of the section that is currently on screen.
(function () {
    var navbar = document.querySelector(".navbar");
    if (!navbar) return;

    var links = Array.prototype.slice
        .call(document.querySelectorAll(".nav-links .nav-link"))
        .filter(function (link) {
            var href = link.getAttribute("href");
            return href && href.length > 1 && href.charAt(0) === "#";
        });

    var items = links
        .map(function (link) {
            return { link: link, section: document.querySelector(link.getAttribute("href")) };
        })
        .filter(function (item) {
            return item.section;
        });

    if (items.length === 0) return;

    var offset = 0;

    function measure() {
        offset = navbar.offsetHeight + 24;
        document.documentElement.style.setProperty("--nav-offset", offset + "px");
    }

    function update() {
        var current = items[0];

        items.forEach(function (item) {
            if (item.section.getBoundingClientRect().top <= offset + 2) {
                current = item;
            }
        });

        var pageScrolls = document.documentElement.scrollHeight > window.innerHeight + 10;
        var atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
        if (pageScrolls && atBottom) {
            current = items[items.length - 1];
        }

        links.forEach(function (link) {
            link.classList.toggle("active", link === current.link);
        });
    }

    var waiting = false;
    function onScroll() {
        if (waiting) return;
        waiting = true;
        window.requestAnimationFrame(function () {
            waiting = false;
            update();
        });
    }

    function refresh() {
        measure();
        update();
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", refresh);
    window.addEventListener("load", refresh);
    refresh();
})();