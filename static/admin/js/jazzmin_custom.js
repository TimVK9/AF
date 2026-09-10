/* =========================================================
   JAZZMIN — кастомные скрипты для админки
   ========================================================= */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {

        /* Автозакрытие алертов через 5 секунд */
        document.querySelectorAll('.alert').forEach(function (alert) {
            setTimeout(function () {
                alert.style.transition = 'opacity 0.3s ease';
                alert.style.opacity = '0';
                setTimeout(function () { alert.remove(); }, 300);
            }, 5000);
        });

        /* Подсветка поля slug при заполнении */
        var slugField = document.querySelector('#id_slug');
        var titleField = document.querySelector('#id_title');
        if (slugField && titleField) {
            slugField.addEventListener('focus', function () {
                slugField.style.transition = 'background 0.3s';
                slugField.style.background = 'rgba(15, 118, 110, 0.08)';
            });
            slugField.addEventListener('blur', function () {
                slugField.style.background = '';
            });
        }

        /* Сворачивание блоков fieldsets с классом collapse при загрузке */
        document.querySelectorAll('fieldset.collapse').forEach(function (fs) {
            var header = fs.querySelector('h2');
            if (header) {
                header.style.cursor = 'pointer';
            }
        });

        /* Плавная прокрутка к первому полю с ошибкой */
        var firstError = document.querySelector('.errors input, .errors select, .errorlist');
        if (firstError) {
            setTimeout(function () {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 200);
        }
    });
})();