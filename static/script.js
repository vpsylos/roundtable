// static/script.js

window.onload = function() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;

    const storedTheme = localStorage.getItem('theme');
    if (storedTheme === 'dark-mode') {
    body.classList.add('dark-mode');
    }

    themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-mode');
    localStorage.setItem('theme', body.classList.contains('dark-mode') ? 'dark-mode' : 'light-mode');
    updateThemeText();
    });

    function updateThemeText() {
        if (body.classList.contains('dark-mode')) {
            themeToggle.textContent = 'Switch to Light Mode';
            document.documentElement.style.setProperty('--primary-color', '#fff');
            document.documentElement.style.setProperty('--background-color', '#333');
            document.documentElement.style.setProperty('--text-color', '#fff');
            document.documentElement.style.setProperty('--table-header-color', '#333');
            document.documentElement.style.setProperty('--link-color', '#fff');
            document.documentElement.style.setProperty('--link--hover-color', '#eee');
        } else {
            themeToggle.textContent = 'Switch to Dark Mode';
            document.documentElement.style.setProperty('--primary-color', '#333');
            document.documentElement.style.setProperty('--background-color', '#f9f9f9');
            document.documentElement.style.setProperty('--text-color', '#333');
            document.documentElement.style.setProperty('--table-header-color', '#f2f2f2');
            document.documentElement.style.setProperty('--link-color', '#660000');
            document.documentElement.style.setProperty('--link--hover-color', '#550000');
        }
    }

    updateThemeText();
}