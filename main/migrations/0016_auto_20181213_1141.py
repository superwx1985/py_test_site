# Generated by Django 2.0.7 on 2018-12-13 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_auto_20181210_1513'),
    ]

    operations = [
        migrations.AddField(
            model_name='suite',
            name='ui_step_interval',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='config',
            name='ui_selenium_client',
            field=models.IntegerField(choices=[(0, '不启用'), (1, 'Selenium - 服务器本地浏览器'), (2, 'Selenium - 远程浏览器')], default=0),
        ),
    ]