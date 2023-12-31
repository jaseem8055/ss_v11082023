# Generated by Django 4.2.3 on 2023-07-31 14:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0010_offer_referraloffer_productoffer_categoryoffer'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoryoffer',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='categoryoffer',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='categoryoffer',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='categoryoffer',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='offer',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='productoffer',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='productoffer',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='productoffer',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='productoffer',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='referraloffer',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='referraloffer',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
