# Generated by Django 2.0.5 on 2018-07-05 03:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0064_auto_20180704_1426'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'ordering': ['type', 'order']},
        ),
    ]