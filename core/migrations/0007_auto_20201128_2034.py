# Generated by Django 3.1.3 on 2020-11-29 02:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_item_quantity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='quantity',
        ),
        migrations.AddField(
            model_name='orderitem',
            name='quantity',
            field=models.IntegerField(default=1),
        ),
    ]
