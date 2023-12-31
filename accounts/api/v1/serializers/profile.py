from datetime import datetime

from django.core import validators

from rest_framework import serializers

from accounts.models import Profile
from accounts.utils import upload_avatar


class ProfileModelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    name = serializers.CharField(required=False, max_length=128)
    
    profile_avatar = serializers.ImageField(
        required=False,
        write_only=True,
        validators=
        [
            validators.FileExtensionValidator(
                allowed_extensions=['jpeg', 'jpg', 'png']
            )
        ]
    )
    avatar = serializers.CharField(max_length=256, read_only=True)
    thumbnail = serializers.CharField(max_length=256, read_only=True)
    """
    We upload the profile image file to a temporary field called profile_avatar
    and then upload the file and get the path to the avatar field.
    """
    
    class Meta:
        model = Profile
        fields = ['id', 'email', 'username', 'name',
                  'profile_avatar', 'avatar', 'thumbnail']
        read_only_fields = ['id', 'email', 'username', 'avatar']
    
    def validate(self, attrs):
        avatar = attrs.get('profile_avatar', None)
        if avatar:
            """
            If user upload a profile image, we upload the file and get
            the path to the avatar field and then pop the profile_avatar
            because it's not in the user model fields.
            """
            avatar_path, thumbnail_path = upload_avatar(avatar)
            attrs['avatar'] = avatar_path
            attrs['thumbnail'] = thumbnail_path
        attrs.pop('profile_avatar', None)
        
        # birth_date = attrs.get('birth_date', None)
        # if birth_date:
        #     """
        #     The user age at least must be 13 and birth date must be
        #     greater than 1900.
        #     """
        #     max_year = datetime.now().year-13
        #     if birth_date.year < 1900 or birth_date.year > max_year:
        #         raise ValueError(f'Birth date year must be between 1900 and {max_year}')
        
        return super().validate(attrs)
