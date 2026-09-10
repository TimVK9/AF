/* =========================================================
   COOKIE-БАННЕР — простая версия
   Показываем уведомление при первом заходе.
   Сохраняем согласие в localStorage.
   Сторонние скрипты не загружаем.
   ========================================================= */

(function () {
    'use strict';

    var STORAGE_KEY = 'cookie_consent_v1';
    var CONSENT_VERSION = 3;

    var banner = document.getElementById('cookieBanner');
    if (!banner) return;

    /* ---------- СОХРАНЕНИЕ / ЧТЕНИЕ ---------- */

    function saveConsent() {
        var data = {
            version: CONSENT_VERSION,
            timestamp: Date.now(),
            necessary: true,
            analytics: false,
            marketing: false
        };
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        } catch (e) { /* приватный режим — игнорируем */ }
    }

    function loadConsent() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            var data = JSON.parse(raw);
            if (!data || data.version !== CONSENT_VERSION) return null;
            return data;
        } catch (e) {
            return null;
        }
    }

    /* ---------- ПОКАЗ / СКРЫТИЕ ---------- */

    function showBanner() {
        banner.hidden = false;
        requestAnimationFrame(function () {
            banner.classList.add('is-visible');
        });
    }

    function hideBanner() {
        banner.classList.remove('is-visible');
        setTimeout(function () {
            banner.hidden = true;
        }, 400);
    }

    /* ---------- ДЕЙСТВИЕ ---------- */

    document.addEventListener('click', function (e) {
        if (e.target.closest('.js-cookie-accept')) {
            saveConsent();
            hideBanner();
        }
    });

    /* ---------- ИНИЦИАЛИЗАЦИЯ ---------- */

    document.addEventListener('DOMContentLoaded', function () {
        var saved = loadConsent();
        if (!saved) {
            setTimeout(showBanner, 500);
        }
    });

    /* Публичный API — на будущее */
    window.hasCookieConsent = function () {
        return !!loadConsent();
    };

    /* Сброс — для страницы /cookies/ */
    window.resetCookieConsent = function () {
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch (e) { /* игнорируем */ }
        location.reload();
    };
})();