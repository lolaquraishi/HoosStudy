# Generated by Django 4.2.16 on 2024-10-18 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hoos_study_app', '0008_rename_data_studysession_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studysession',
            name='created_by',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='studysessionattendee',
            name='last_name',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
