# Generated by Django 3.1.3 on 2020-11-05 12:54

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Insight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('follower', models.IntegerField(verbose_name='フォロワー')),
                ('follows', models.IntegerField(verbose_name='フォロー')),
                ('created', models.DateField(default=django.utils.timezone.now, verbose_name='作成日')),
            ],
        ),
    ]