# Generated by Django 2.0.5 on 2018-06-20 09:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0041_auto_20180620_1023'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stepresult',
            name='screenshots',
        ),
        migrations.DeleteModel(
            name='ImageStore',
        ),
    ]