# Generated by Django 4.2.3 on 2023-07-24 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_couponhistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='couponhistory',
            name='order_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='couponhistory',
            name='used_order_id',
            field=models.CharField(default=None, max_length=50),
        ),
    ]