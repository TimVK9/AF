from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Здесь НЕ трогаем profile — пользователь ещё не сохранён.
        # Данные из VK сохраняем в extra_data, достанем позже.
        return user

    def pre_social_login(self, request, sociallogin):
        # Здесь пользователь уже сохранён в БД.
        # Сохраняем данные из VK в профиль.
        user = sociallogin.user
        if not user.pk:
            return

        from accounts.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)

        extra = sociallogin.account.extra_data if sociallogin.account else {}

        # Аватар
        photo = extra.get('photo') or extra.get('photo_200')
        if photo:
            profile.avatar_url = photo

        # Дата рождения (VK: DD.MM.YYYY или DD.MM)
        bdate = extra.get('bdate')
        if bdate:
            try:
                parts = bdate.split('.')
                if len(parts) == 3:
                    profile.date_of_birth = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                elif len(parts) == 2:
                    # VK иногда не отдаёт год — пропускаем
                    pass
            except (ValueError, IndexError):
                pass

        # Пол (1 — женский, 2 — мужской)
        sex = extra.get('sex')
        if sex is not None:
            profile.gender = int(sex)

        profile.save()
