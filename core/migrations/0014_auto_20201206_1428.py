# Generated by Django 3.1.4 on 2020-12-06 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20201202_2131'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='item',
            options={'ordering': ('id',)},
        ),
        migrations.AddField(
            model_name='item',
            name='image',
            field=models.ImageField(default='https://mdbootstrap.com/img/Photos/Horizontal/E-commerce/Vertical/12.jpg', upload_to=''),
            preserve_default=False,
        ),
    ]