from allauth.socialaccount.models import SocialAccount
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from .models import User

import requests
from django.core.files.base import ContentFile

@receiver(user_signed_up)
def set_google_profile_picture(request, user, **kwargs):
    try:
        social_account = SocialAccount.objects.filter(user=user, provider='google').first()
        if social_account:
            google_profile_picture_url = social_account.extra_data.get('picture', '')
            if google_profile_picture_url:
                response = requests.get(google_profile_picture_url)
                if response.status_code == 200:
                    # Save the picture
                    file_name = f"{user.username}_google_profile.jpg"
                    content = ContentFile(response.content)

                    # Save using the default storage backend
                    user.profile_picture.save(file_name, content, save=False)
                    user.save()
    except requests.exceptions.RequestException as e:
        print(f"HTTP error while fetching Google profile picture: {e}")
    except Exception as e:
        print(f"Unexpected error setting Google profile picture: {e}")
