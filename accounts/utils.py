from random import randint
from uuid import uuid4
import os

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.serializers import ValidationError
from rest_framework.permissions import BasePermission
from celery import shared_task
from PIL import Image

BASE_DIR = settings.BASE_DIR
HOST = getattr(settings, 'HOST', 'http://127.0.0.1:8000')
FROM = getattr(settings, 'EMAIL_HOST_USER', 'admin@web-site.com')


def user_6_digit():
    """Default value for username."""
    
    return f'user{randint(100_000, 1_000_000_000)}'


def get_activation_token(user):
    """
    Returns a jwt access token for the given user
    and manually adding 'user_id' (if there is one because sometimes we
        send an email to an AnonymousUser and that user does not has an ID yet)
    and 'email' to the jwt token payload for the receiver.
    """
    
    access_token = AccessToken()
    access_token.payload['user_id'] = user.id or None
    access_token.payload['email'] = user.email
    return str(access_token)


@shared_task
def send_activation_email(user):
    """
    Send an account activation email link to the given user.
    """
    
    token = get_activation_token(user)
    address = reverse('accounts:api-v1:user-activation', args=(token,))
    link = HOST + address
    send_mail(
        'Activation Link',
        f'Link: {link}',
        FROM,
        [user.email,],
        fail_silently=False,
    )


@shared_task
def send_reset_password_email(user):
    """
    Send a reset password email link to the given user.
    """
    
    token = get_activation_token(user)
    address = reverse('accounts:api-v1:user-forgot-password-verify', args=(token,))
    link = HOST + address
    send_mail(
        'Reset-Password Link',
        f"Link: {link}",
        FROM,
        [user.email,],
        fail_silently=False,
    )


@shared_task
def send_reset_email_email(user):
    """
    Send a reset-email email link to the given user.
    """
    
    token = get_activation_token(user)
    address = reverse('accounts:api-v1:user-reset-email-verify', args=(token,))
    link = HOST + address
    send_mail(
        'Reset-Email Link',
        f"Link: {link}",
        FROM,
        [user.email,],
        fail_silently=False,
    )


def check_file_size(file, size, msg=None):
    """
    Takes a file and a size in byte
    and checks if the file size is in the given size range.
    """
    
    file_size = file.size
    min_size, max_size = size
    if file_size < min_size or file_size > max_size:
        raise ValidationError(msg or f'File size must be between: {min_size} and {max_size}')


def check_image_size(file, size, msg=None):
    """
    Checks if file image size(width, height) is at least
    10px both width and height.
    """
    
    x, y = file.image.size
    _x, _y = size
    if x < _x or y < _y:
        raise ValidationError(msg or f'Image resolution at least must be Width: {_x}px, Height: {_y}px')


def upload_file(uploaded_file, dir=['media'], size=None, msg=None):
    """
    Uploads the given uploaded file to the given directory with the given size(in byte).
    and then return the uploaded file path.
    """
    
    if size:
        check_file_size(uploaded_file, size, msg)
    
    name = str(uuid4())
    ext = uploaded_file.name.split('.')[-1] or 'unknown'
    filename = f'{name}.{ext}'
    
    if dir != ['media']:
        dir = ['media'] + dir + [filename]
    
    _dir = [settings.MEDIA_ROOT]
    _dir.extend(dir[1:])
    path = os.path.join(*_dir)
    """
    MEDIA_ROOT_BASE_PATH + folders path (minus the first folder because
    with giving MEDIA_ROOT we already gave /media/ part of path) + filename .
    """
    
    open(path, 'wb').write(uploaded_file.file)
    return '/' + '/'.join(dir)


def upload_image(uploaded_file, dir=['media'], size=None, res=None, thumbnail_size=None, msg=None):
    """
    Uploads the given uploaded file to the given directory with
    the given size(in byte) and res(width and height).
    also you can give a thumbnail size if you want to create a thumbnail too.
    and then return the uploaded file path.
    """
    
    if size:
        check_file_size(uploaded_file, size, msg)
    
    if dir != ['media']:
        dir = ['media'] + dir
    
    name = str(uuid4())
    ext = uploaded_file.name.split('.')[-1] or 'unknown'
    filename = f'{name}.{ext}'
    
    _dir = [settings.MEDIA_ROOT]
    _dir.extend(dir[1:])
    _dir.append(filename)
    path = os.path.join(*_dir)
    """
    MEDIA_ROOT_BASE_PATH + folders path (minus the first folder because
    with giving MEDIA_ROOT we already gave /media/ part of path) + filename .
    """
    
    image = Image.open(uploaded_file.file)
    
    if res:
        """If we want to resize the image."""
        image.resize(res).save(path)
    else:
        """Otherwise we just save it."""
        image.save(path)
    
    if thumbnail_size:
        """If want a thumbnail we resize the image and save it."""
        image = image.resize(thumbnail_size)
        
        _dir = [settings.MEDIA_ROOT]
        _dir.extend(dir[1:])
        _dir.append('thumbnail')
        _dir.append(filename)
        thumbnail_path = os.path.join(*_dir)
        image.save(thumbnail_path)
    
    file_path = dir + [filename]
    file_path = '/' + '/'.join(file_path)
    thumbnail_file_path = dir + ['thumbnail', filename]
    thumbnail_file_path = '' if not thumbnail_size else '/' + '/'.join(thumbnail_file_path)
    return file_path, thumbnail_file_path


@shared_task
def upload_avatar(avatar):
    """
    Uploading avatar image with a min filesize and a max file size.
    also we can add res(width, height) to resize
    and thumbnail res to make a one.
    """
    
    min_size = 1024
    max_size = 1 * 1024 * 1024
    error_message = f'File size must be between {min_size//1024}KB and {max_size//1024//1024}MB.'
    size = min_size, max_size
    
    dir = ['user', 'profile', 'avatar']
    path = upload_image(avatar, dir, size, thumbnail_size=(200, 200), msg=error_message)
    return path


class IsNotAuthenticated(BasePermission):
    """
    Check if the user is not authenticated.
    """
    
    def has_permission(self, request, view):
        return str(request.user) == 'AnonymousUser'
