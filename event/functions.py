from io import BytesIO
from os.path import splitext, basename

from PIL import Image
from django.core.files.base import ContentFile


def file_visible_condition(request, instance):
    user_logged_in = (not request.user.is_anonymous) and request.user.is_authenticated
    owned_by_this_user = instance.added_by.pk == request.user.pk
    user_is_admin = request.user.is_superuser
    gift_is_unwrapped = not instance.wrapped
    return user_logged_in and (owned_by_this_user or user_is_admin or gift_is_unwrapped)


def _get_pixelated_image(image_obj):
    image_path = image_obj.path
    img = Image.open(BytesIO(image_obj.file.read()))
    img_small = img.resize((16, 16), resample=Image.BILINEAR)
    result = img_small.resize(img.size, Image.NEAREST)
    _, ext = splitext(image_path)
    in_memory_file = BytesIO()
    result.save(in_memory_file, format=ext.lstrip('.'))
    return ContentFile(in_memory_file.getvalue(), 'pixelated-{}'.format(basename(image_path)))