from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Post, Comment, Profile


class UserRegistrationForm(UserCreationForm):
    """Extended registration form with email and name fields."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if field_name == 'username':
                field.widget.attrs['placeholder'] = 'Username'
            elif field_name == 'email':
                field.widget.attrs['placeholder'] = 'Email address'
            elif field_name == 'first_name':
                field.widget.attrs['placeholder'] = 'First name'
            elif field_name == 'last_name':
                field.widget.attrs['placeholder'] = 'Last name'
            elif field_name == 'password1':
                field.widget.attrs['placeholder'] = 'Password'
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Confirm password'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class PostForm(forms.ModelForm):
    """Form for creating and editing posts."""

    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "What's on your mind?",
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }


class CommentForm(forms.ModelForm):
    """Form for adding a comment to a post."""

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Write a comment...',
            }),
        }


class ProfileForm(forms.ModelForm):
    """Form for editing a user profile."""

    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'location']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tell us about yourself...',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, Country',
            }),
        }
