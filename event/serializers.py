from django.contrib.auth import get_user_model
from rest_framework.fields import ChoiceField
from rest_framework.serializers import ModelSerializer, HyperlinkedModelSerializer

from event.models import RaffleEvent, RaffleParticipation, Action, Gift


class UserSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'display_name', 'email']

class RaffleParticipationSerializer(ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = RaffleParticipation
        fields = '__all__'

class ActionSerializer(ModelSerializer):
    from_user = UserSerializer()
    to_user = UserSerializer()
    by_user = UserSerializer()

    class Meta:
        model = Action
        fields = '__all__'

class GiftSerializer(ModelSerializer):
    given_to = UserSerializer()
    added_by = UserSerializer()

    class Meta:
        model = Gift
        fields = '__all__'

class RaffleEventSerializer(ModelSerializer):
    raffle_participations = RaffleParticipationSerializer(source='raffleparticipation_set', many=True)
    actions = ActionSerializer(source='action_set', many=True)
    gifts = GiftSerializer(source='gift_set', many=True)

    class Meta:
        model = RaffleEvent
        fields = '__all__'
