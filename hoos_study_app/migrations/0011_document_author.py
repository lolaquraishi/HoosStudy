# Generated by Django 4.2.16 on 2024-10-15 01:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hoos_study_app', '0010_user_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
