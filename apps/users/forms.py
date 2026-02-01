from django import forms
from .models import CustomUser


class ExpandedSignUpForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nombre",
        widget=forms.TextInput(attrs={"placeholder": "Nombre"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Apellido",
        widget=forms.TextInput(attrs={"placeholder": "Apellido"}),
    )
    field_order = [
        "first_name",
        "last_name",
        "email",
        "password1",
        "password2",
    ]

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
