# Generated by Django 2.0.5 on 2018-06-19 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0037_auto_20180615_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='suiteresult',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]