from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), blank=False)
    _display_name = models.CharField(_('display name'), blank=True, null=True, max_length=250)

    @property
    def display_name(self):
        return self._display_name or self.username

    def __str__(self):
        return self.display_name

class CustomUserManager(UserManager):
    pass

