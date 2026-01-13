from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import MedicalReport

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class UploadReportForm(forms.ModelForm):
    def clean_upload(self):
        file = self.cleaned_data["upload"]
        if not file.name.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
            raise forms.ValidationError("Only image or PDF reports allowed.")
        return file
    
    class Meta:
        model = MedicalReport
        fields = ["upload"]
