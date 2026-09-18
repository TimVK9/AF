# accounts/adapter.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.dateparse import parse_date

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        # Сначала сохраняем базовые данные (имя, email) через родителя
        user = super().populate_user(request, sociallogin, data)
        
        # Получаем или создаем профиль
        profile, created = user.profile.get_or_create(user=user)
        
        # 1. Дата рождения (VK присылает в формате DD.MM.YYYY)
        bdate_str = data.get('bdate')
        if bdate_str:
            # parse_date умеет работать с форматом YYYY-MM-DD, VK шлет DD.MM.YYYY
            try:
                day, month, year = map(int, bdate_str.split('.'))
                profile.date_of_birth = f"{year}-{month}-{day}"
            except ValueError:
                pass # Если формат не тот, игнорируем
        
        # 2. Пол (VK: 1 - женский, 2 - мужской, 0 - не указан)
        sex = data.get('sex')
        if sex:
            profile.gender = int(sex)
            
        # 3. Аватар (VK присылает поле 'photo', это маленькая картинка)
        photo_url = data.get('photo')
        if photo_url:
            profile.avatar_url = photo_url
            
        profile.save()
        return user
