# Generated by Django 4.2.16 on 2024-11-26 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hoos_study_app', '0026_usercoursepreference'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='semester',
            field=models.CharField(default='N/A', max_length=20),
        ),
    ]
