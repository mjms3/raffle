from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.views.generic import FormView

from account.forms import CustomUserCreationForm


class NewUserView(FormView):
    form_class = CustomUserCreationForm
    template_name = 'user_form.html'
    success_url = '/gifts/donate'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.success_url)
        else:
            return super(NewUserView, self).dispatch(request, *args, **kwargs)


    def form_valid(self, form):
        form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(self.request, user)
        return super(NewUserView, self).form_valid(form)