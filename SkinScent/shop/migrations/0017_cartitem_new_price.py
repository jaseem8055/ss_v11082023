# Generated by Django 4.2.3 on 2023-08-03 08:51

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0016_wishlist'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='new_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=Decimal('0.00'), max_digits=10, null=True),
        ),
    ]
