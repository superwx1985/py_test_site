# Generated by Django 5.0.2 on 2025-03-25 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_alter_step_ui_special_action'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='suiteresult',
            name='error_handle',
        ),
        migrations.AddField(
            model_name='caseresult',
            name='snapshot',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
