from django.db import models
from django.contrib.auth.models import User

class MedicalReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upload = models.FileField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    report_json = models.JSONField(null=True, blank=True)
    llm_explanation = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.upload.name}"
