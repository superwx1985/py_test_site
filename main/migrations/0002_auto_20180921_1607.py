# Generated by Django 2.0.7 on 2018-09-21 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='step',
            name='db_data',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='step',
            name='db_host',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='step',
            name='db_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='step',
            name='db_password',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='step',
            name='db_port',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='step',
            name='db_sql',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='step',
            name='db_type',
            field=models.IntegerField(choices=[(1, 'oracle'), (2, 'mysql')], default=1),
        ),
        migrations.AddField(
            model_name='step',
            name='db_user',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]