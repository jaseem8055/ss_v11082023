# Generated by Django 4.2.3 on 2023-07-24 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0011_alter_couponhistory_used_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='couponhistory',
            name='used_order_id',
            field=models.CharField(default='', max_length=50, null=True),
        ),
    ]
