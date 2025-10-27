from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

class LoginForm(forms.Form):
    """Login form for staff members"""
    username = forms.CharField(
        label='Username or Email',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username or email'
        })
    )
    password = forms.CharField(
        label='Password',
        max_length=100,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
        }

    def clean_email(self):
        """Validate that email is unique (except for current user)"""
        email = self.cleaned_data.get('email')
        user_id = self.instance.id

        if User.objects.filter(email__iexact=email).exclude(id=user_id).exists():
            raise ValidationError("This email is already in use.")
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with enhanced validation"""

    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password'
        })
    )

    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )

    new_password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def clean_new_password1(self):
        """Validate new password meets requirements"""
        password = self.cleaned_data.get('new_password1')

        if not password:
            raise ValidationError("Password cannot be empty.")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter.")

        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one number.")

        if not any(char in "!@#$%^&*" for char in password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&*).")

        return password

    def clean(self):
        """Ensure passwords match"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2:
            if password1 != password2:
                raise ValidationError("The new passwords do not match.")

        return cleaned_data


class NotificationPreferencesForm(forms.Form):
    """Form for managing notification preferences"""

    email_notifications = forms.BooleanField(
        label="Email Notifications",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    sms_notifications = forms.BooleanField(
        label="SMS Notifications",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    prescription_alerts = forms.BooleanField(
        label="Prescription Alerts",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    system_updates = forms.BooleanField(
        label="System Updates",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

# # Custom Signup Form
# class SignupForm(UserCreationForm):
#     email = forms.EmailField(required=True)
#
#     class Meta:
#         model = User
#         fields = ["username", "email", "password1", "password2"]
#
#     # Custom validation for username and email
#     def clean_username(self):
#         username = self.cleaned_data.get("username")
#         if User.objects.filter(username__iexact=username).exists():
#             raise forms.ValidationError("Username already exists. Please choose another.")
#         return username
#
#     def clean_email(self):
#         email = self.cleaned_data.get("email")
#         if User.objects.filter(email__iexact=email).exists():
#             raise forms.ValidationError("Email already registered. Please choose another.")
#         return email
