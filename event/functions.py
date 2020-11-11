import random
from io import BytesIO
from os.path import splitext, basename

from PIL import Image
from django.core.files.base import ContentFile
from django.db.models import F

from event.models import RaffleEvent, RaffleParticipation, Action


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


def _pick_next_person(current_user, raffle_event):
    assert raffle_event.phase == RaffleEvent.Phase.NORMAL_RAFFLE
    raffle_participants = RaffleParticipation.objects.filter(event_id=raffle_event.id).filter(
        number_of_tickets__gt=F('number_of_times_drawn'))
    weights = [r.number_of_tickets - r.number_of_times_drawn for r in raffle_participants]
    next_person = random.choices(raffle_participants, weights)
    assert len(next_person) == 1, next_person
    next_person = next_person[0]
    action = Action(
        event=raffle_event,
        gift=None,
        from_user=None,
        to_user=next_person.user,
        by_user=current_user,
        action_type=Action.ActionType.CHANGED_USER
    )
    next_person.number_of_times_drawn += 1
    raffle_event.current_user = next_person.user
    raffle_event.save()
    action.save()
    next_person.save()