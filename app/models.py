from django.db import models
from django.utils import timezone


class Insight(models.Model):
    follower = models.IntegerField('フォロワー')
    follows = models.IntegerField('フォロー')
    label = models.CharField("作成日", max_length=200)

    def __str__(self):
        return str(self.label)

class Post(models.Model):
    like = models.IntegerField('いいね')
    comments = models.IntegerField('コメント')
    count = models.IntegerField('投稿数')
    label = models.CharField("投稿日", max_length=200)

    def __str__(self):
        return str(self.label)
