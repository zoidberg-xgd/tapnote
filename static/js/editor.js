document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.querySelector('textarea[name="content"]');
    if (textarea) {
        // Auto-grow function
        function autoGrow(elem) {
            // Store current scroll position
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            elem.style.height = 'auto';
            elem.style.height = (elem.scrollHeight) + 'px';

            // Restore scroll position
            window.scrollTo(scrollLeft, scrollTop);
        }

        // Add input listener
        textarea.addEventListener('input', function() {
            autoGrow(textarea);
        });

        // Initialize on load
        autoGrow(textarea);
    }
}); 