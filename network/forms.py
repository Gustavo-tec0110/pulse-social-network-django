from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Comment, Post, Profile


User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="E-mail")
    first_name = forms.CharField(max_length=150, required=True, label="Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("content", "image")
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "O que está acontecendo?",
                    "maxlength": 280,
                    "data-character-counter": "post",
                }
            )
        }
        labels = {"content": "", "image": "Adicionar imagem"}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Escreva um comentário...", "maxlength": 500}
            )
        }
        labels = {"content": ""}


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "Nome", "last_name": "Sobrenome", "email": "E-mail"}


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("avatar", "bio", "location", "website")
        labels = {
            "avatar": "Foto de perfil",
            "bio": "Biografia",
            "location": "Localização",
            "website": "Site",
        }
        widgets = {"bio": forms.Textarea(attrs={"rows": 3, "maxlength": 160})}
