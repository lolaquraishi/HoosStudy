# Generated by Django 4.2.16 on 2024-10-18 16:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hoos_study_app', '0006_studysessionattendee_studysessionlocation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='studysession',
            name='course_name',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='hoos_study_app.course'),
        ),
    ]
