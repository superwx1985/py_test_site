# Generated by Django 2.0.7 on 2018-09-29 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_step_api_save'),
    ]

    operations = [
        migrations.AddField(
            model_name='step',
            name='api_method',
            field=models.IntegerField(choices=[(1, 'GET'), (2, 'HEAD'), (3, 'POST'), (4, 'PUT'), (5, 'PATCH'), (6, 'DELETE'), (7, 'OPTIONS'), (8, 'TRACE')], default=1),
        ),
    ]