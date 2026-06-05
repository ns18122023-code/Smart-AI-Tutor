// Global Frontend Logic

$(document).ready(function() {
    // Mobile Menu Toggle
    const mobileMenuBtn = $('#mobileMenuBtn');
    const closeMenuBtn = $('#closeMenuBtn');
    const mobileMenu = $('#mobileMenu');

    if (mobileMenuBtn.length && mobileMenu.length) {
        mobileMenuBtn.on('click', function() {
            mobileMenu.removeClass('translate-x-full');
        });

        closeMenuBtn.on('click', function() {
            mobileMenu.addClass('translate-x-full');
        });
    }

    // Flash messages dismissal (if implemented later)
    $('.dismiss-alert').on('click', function() {
        $(this).closest('.alert').fadeOut(300, function() { $(this).remove(); });
    });
});
