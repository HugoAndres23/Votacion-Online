from django import forms
from .models import *


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    contraseña = forms.CharField(widget=forms.PasswordInput)

    widget = {
        'contraseña': forms.PasswordInput(),
    }

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            instance = kwargs.get('instance').__dict__
            self.fields['contraseña'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['contraseña'].widget.attrs['placeholder'] = "Rellene los campos si desea cambiar su contraseña."
        else:
            self.fields['nombre'].required = True
            self.fields['apellido'].required = True

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "Este email ya ha sido registrado")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk).email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError(
                        "Este email ya ha sido registrado")
        return formEmail

    def clean_password(self):
        contraseña = self.cleaned_data.get("contraseña", None)
        if self.instance.pk is not None:
            if not contraseña:
                # return None
                return self.instance.contraseña

        return make_password(contraseña)

    class Meta:
        model = CustomUser
        fields = ['apellido', 'nombre', 'email', 'contraseña', ]
