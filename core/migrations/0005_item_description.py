# Generated by Django 3.1.3 on 2020-11-28 04:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_item_discount_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='description',
            field=models.TextField(default='this is a test description'),
            preserve_default=False,
        ),
    ]
