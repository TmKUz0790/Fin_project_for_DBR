# Generated by Django 5.1.1 on 2024-12-11 12:37

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fin_app_v2', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
