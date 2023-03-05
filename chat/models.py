from django.db import models

# Create your models here.
class Message(models.Model):
    role = models.CharField(max_length=200)
    sender_name = models.CharField(max_length=200)
    content = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    audio = models.FileField(blank=True, null=True)

    def __str__(self):
        return self.content