# Generated by Django 4.2.3 on 2023-07-28 05:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0006_delete_couponhistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='image',
            field=models.ImageField(default='default_image.jpg', upload_to='category_images/'),
        ),
    ]