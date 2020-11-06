from django.db import models
from django.utils import timezone


class Insight(models.Model):
    follower = models.IntegerField('フォロワー')
    follows = models.IntegerField('フォロー')
    label = models.CharField("作成日", max_length=200)

    def __str__(self):
        return str(self.label)
