from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class LoginForm(forms.Form):
    username = forms.CharField(label='Your Username', max_length=100)
    password = forms.CharField(label='Your Password', max_length=100)

# Custom Signup Form
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

# Custom Password Reset Form
class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(label="Enter your email", max_length=254)