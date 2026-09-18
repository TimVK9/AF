from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        return user

    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        if not user.pk:
            return

        from accounts.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)

        extra = sociallogin.account.extra_data if sociallogin.account else {}

        # Аватар — VK ID отдаёт под ключом 'avatar'
        avatar = extra.get('avatar')
        if avatar:
            profile.avatar_url = avatar

        # Дата рождения — VK ID отдаёт под ключом 'birthday'
        birthday = extra.get('birthday') or extra.get('bdate')
        if birthday:
            try:
                parts = birthday.split('.')
                if len(parts) == 3:
                    profile.date_of_birth = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            except (ValueError, IndexError):
                pass

        # Пол (1 — женский, 2 — мужской)
        sex = extra.get('sex')
        if sex is not None:
            profile.gender = int(sex)

        profile.save()
