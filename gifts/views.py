from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, FormView

from gifts.models import Gift


class IndexView(PermissionRequiredMixin, ListView):
    permission_required = 'gifts.view_gift'
    template_name = 'index.html'
    model = Gift

class MyGiftsView(LoginRequiredMixin, ListView):
    template_name = 'index.html'
    model = Gift

    def get_queryset(self):
        return Gift.objects.filter(added_by=self.request.user)


class GiftCreateView(LoginRequiredMixin, CreateView):
    model = Gift
    fields = ['description', 'image']
    template_name = 'gift_form.html'
    success_url = '/gifts/donations'

    def form_valid(self, form):
        gift = form.save(commit=False)
        gift.added_by = self.request.user
        gift.save()
        self.object = gift
        return HttpResponseRedirect(self.get_success_url())


