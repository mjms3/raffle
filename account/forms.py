from django.contrib.auth import forms, get_user_model


class CustomUserCreationForm(forms.UserCreationForm):

    class Meta:
        fields = ('username', 'email')
        model = get_user_model()



class CustomUserChangeForm(forms.UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email')