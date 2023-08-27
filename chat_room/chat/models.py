from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Chats(models.Model):
    text_message = models.CharField(max_length=2000)
    user = models.ForeignKey(
        User, to_field="id", related_name="chats", on_delete=models.CASCADE, null=True
    )
    room = models.CharField(max_length=300, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    chat_id = models.IntegerField(null=True)

    class Meta:
        unique_together = ["room", "chat_id"]

    def __str__(self):
        return f"id={self.id},room={self.room} by {self.user}"
