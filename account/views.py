from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView

from account.forms import CustomUserCreationForm, CustomUserChangeForm


class NewUserView(FormView):
    form_class = CustomUserCreationForm
    template_name = 'user_form.html'
    success_url = reverse_lazy('user_profile')

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

class UserProfileView(LoginRequiredMixin, FormView):
    form_class = CustomUserChangeForm
    template_name = 'profile.html'
    success_url = reverse_lazy('user_profile')

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('user_profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })