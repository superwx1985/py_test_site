# Generated by Django 2.0.5 on 2018-06-15 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_auto_20180614_1553'),
    ]

    operations = [
        migrations.RenameField(
            model_name='caseresult',
            old_name='init_error',
            new_name='result_error',
        ),
        migrations.AddField(
            model_name='caseresult',
            name='result_message',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='caseresult',
            name='result_status',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='suiteresult',
            name='result_status',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]