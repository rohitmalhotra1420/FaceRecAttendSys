from django import forms
from models import UserModel


class SignUpForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields=['email','name','unique_id','number','department']
