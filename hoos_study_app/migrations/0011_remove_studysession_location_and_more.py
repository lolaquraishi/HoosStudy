# Generated by Django 4.2.16 on 2024-10-30 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hoos_study_app', '0010_alter_studysessionlocation_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studysession',
            name='location',
        ),
        migrations.AddField(
            model_name='studysession',
            name='description_of_location',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='studysession',
            name='location_name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Study Session Location'),
        ),
        migrations.AddField(
            model_name='studysession',
            name='room_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
