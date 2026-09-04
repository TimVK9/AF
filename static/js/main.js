// ===== Открытие формы =====
function openForm() {
    const wrap = document.getElementById('formWrap');
    wrap.classList.add('open');
    setTimeout(() => {
        const card = wrap.querySelector('.form-card');
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 350);
}

function scrollToForm() {
    const wrap = document.getElementById('formWrap');
    if (!wrap.classList.contains('open')) {
        wrap.classList.add('open');
    }
    setTimeout(() => {
        const card = wrap.querySelector('.form-card');
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

// ===== Модалка политики =====
function openModal(e) {
    if (e) e.preventDefault();
    document.getElementById('modalOverlay').classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('show');
    document.body.style.overflow = '';
}

function closeModalOnOverlay(e) {
    if (e.target === e.currentTarget) {
        closeModal();
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
});

// ===== Cookie-баннер =====
(function() {
    const accepted = localStorage.getItem('cookieAccepted');
    if (!accepted) {
        setTimeout(() => {
            document.getElementById('cookieBanner').classList.add('show');
        }, 1500);
    }
})();

function acceptCookies() {
    localStorage.setItem('cookieAccepted', 'true');
    document.getElementById('cookieBanner').classList.remove('show');
}
