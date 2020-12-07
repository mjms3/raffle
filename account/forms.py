from django.contrib.auth import forms, get_user_model


class CustomUserCreationForm(forms.UserCreationForm):

    class Meta:
        fields = ('username', 'email', '_display_name')
        model = get_user_model()



class CustomUserChangeForm(forms.UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('email', '_display_name')
