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

    # Custom validation for username and email
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username already exists. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already registered. Please choose another.")
        return email


class DirectPasswordResetForm(forms.Form):
    email = forms.EmailField(label="Enter your email", max_length=254)
    new_password1 = forms.CharField(
        label="New password", widget=forms.PasswordInput, min_length=8
    )
    new_password2 = forms.CharField(
        label="Confirm new password", widget=forms.PasswordInput, min_length=8
    )