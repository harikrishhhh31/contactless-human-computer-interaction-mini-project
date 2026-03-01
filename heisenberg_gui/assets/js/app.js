// Navigation functions
function navigateTo(page) {
    var currentPath = window.location.href;
    var basePath = currentPath.substring(0, currentPath.lastIndexOf('/') + 1);
    window.location.href = basePath + page;
}

function goBack() {
    window.history.back();
}

// Initialize navigation on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth transitions
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.3s ease';
        document.body.style.opacity = '1';
    }, 50);
});
