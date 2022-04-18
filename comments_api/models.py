from django.db import models

# Create your models here.
class Comment(models.Model):
    text = models.TextField()
    datetime_created = models.DateTimeField(auto_now=True)
    owner_id = models.IntegerField()
    parent_id = models.IntegerField()

    