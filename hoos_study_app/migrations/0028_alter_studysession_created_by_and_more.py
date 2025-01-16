# Generated by Django 4.2.16 on 2024-12-05 01:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hoos_study_app', '0027_alter_studysession_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studysession',
            name='created_by',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='studysession',
            name='description',
            field=models.CharField(max_length=400),
        ),
        migrations.AlterField(
            model_name='studysession',
            name='description_of_location',
            field=models.CharField(max_length=400),
        ),
        migrations.AlterField(
            model_name='studysession',
            name='location_name',
            field=models.CharField(max_length=200, verbose_name='Study Session Location'),
        ),
    ]
