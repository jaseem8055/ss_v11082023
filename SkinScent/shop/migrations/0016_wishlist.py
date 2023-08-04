# Generated by Django 4.2.3 on 2023-07-27 10:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0006_delete_couponhistory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0015_order_coupon_discount_order_couponhistory_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_date', models.DateTimeField(auto_now_add=True)),
                ('products', models.ManyToManyField(to='adminpanel.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
