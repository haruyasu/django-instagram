from django.db import models
from django.utils import timezone


class Insight(models.Model):
    follower = models.IntegerField('フォロワー')
    follows = models.IntegerField('フォロー')
    created = models.DateField("作成日", default=timezone.now)

    def __str__(self):
        return str(self.created)
