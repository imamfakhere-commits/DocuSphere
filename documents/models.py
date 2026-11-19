from django.db import models
from django.conf import settings


class Document(models.Model):

    CATEGORY_CHOICES = [
        ('Education', 'Education'),
        ('Technology', 'Technology'),
        ('Business', 'Business'),
        ('Personal', 'Personal'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)

    file = models.FileField(upload_to='documents/')

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='Other'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ChatHistory(models.Model):

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chat_history'
    )

    question = models.TextField()

    answer = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat for {self.document.title}"
