from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm

class UserEditForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.fields.pop('username')
        self.fields.pop('password')

    class Meta:
        model = User
        fields = ('is_active', 'is_staff', 'is_superuser', 
                  'groups', 'user_permissions')
