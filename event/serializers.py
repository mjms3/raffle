from django.contrib.auth import get_user_model
from rest_framework.fields import ChoiceField, SerializerMethodField
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
    summary = SerializerMethodField()

    class Meta:
        model = RaffleEvent
        fields = '__all__'

    def get_summary(self, obj):
        summary_data = {}
        participations = obj.raffleparticipation_set.select_related('user').all()
        transfers = obj.action_set.filter(action_type=Action.ActionType.TRANSFERRED).select_related('by_user').all()
        gifts = obj.gift_set.select_related('added_by').select_related('given_to').all()

        total_tickets = sum(r.number_of_tickets for r in participations)
        summary_data['total_tickets'] = total_tickets
        summary_data['number_of_swaps'] = len(transfers)
        summary_data['total_raised'] = 5 * (summary_data['total_tickets'] + summary_data['number_of_swaps'])
        user_summary = {p.user.username:
            {
                'username': p.user.username,
                'email': p.user.email,
                'display_name': p.user.display_name,
                'tickets_purchased': p.number_of_tickets,
                'times_drawn': p.number_of_times_drawn,
                'total_owed_for_tickets': 5 * p.number_of_tickets,
                'raffle_prizes': [],
                'donation_final_locations': [],
                'transfers': [],
            } for p in participations
        }
        for gift in gifts:
            user_summary[gift.given_to.username]['raffle_prizes'].append(gift.description)
            user_summary[gift.added_by.username]['donation_final_locations'].append(
                {
                    'gift': gift.description,
                    'user': {
                        'username': gift.given_to.username,
                        'display_name': gift.given_to.display_name,
                        'email': gift.given_to.email,
                    }
                }
            )
        for transfer in transfers:
            user_summary[transfer.by_user.username]['transfers'].append(transfer.message)
        for v in user_summary.values():
            v['total_transfers'] = len(v['transfers'])
            v['total_owed_for_transfers'] = 5*v['total_transfers']
            v['total_owed'] = v['total_owed_for_transfers']+v['total_owed_for_tickets']
        summary_data['user_summary'] = user_summary
        return summary_data
