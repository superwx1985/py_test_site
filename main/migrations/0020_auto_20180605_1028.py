# Generated by Django 2.0.5 on 2018-06-05 02:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_auto_20180605_1021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='main.ActionType'),
        ),
    ]