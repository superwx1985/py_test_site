# Generated by Django 5.0.2 on 2024-10-30 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_step_api_response_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='step',
            name='api_response_status',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
