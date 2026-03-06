"""Forms for user registration and authentication."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User


class SignupForm(UserCreationForm):
    """
    Registration form for new users.
    New users are created as Observers by default.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    
    def save(self, commit=True):
        """Save user with Observer role by default."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'observer'  # New users are always Observers
        if commit:
            user.save()
        return user
