# Generated by Django 2.0.7 on 2018-09-25 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20180921_1749'),
    ]

    operations = [
        migrations.AddField(
            model_name='step',
            name='db_lang',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='config',
            name='ui_driver_ff_profile',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='config',
            name='ui_remote_ip',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]