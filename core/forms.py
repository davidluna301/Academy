from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User

from .models import Comentario, Proyecto


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["titulo", "descripcion", "documento"]
        widgets = {
            "titulo": forms.TextInput(attrs={"autocomplete": "off"}),
            "descripcion": forms.Textarea(attrs={"rows": 6}),
        }


class DocenteRevisionForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["estado", "calificacion"]


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ["texto"]
        widgets = {"texto": forms.Textarea(attrs={"rows": 4})}


class RegisterForm(UserCreationForm):
    """
    Extiende el formulario estándar para pedir email y validar contraseña.
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            grupo, _ = Group.objects.get_or_create(name="Estudiante")
            user.groups.add(grupo)
        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

