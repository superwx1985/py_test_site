# Generated by Django 5.0.2 on 2025-01-23 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_alter_stepresult_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='suiteresult',
            name='snapshot',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
