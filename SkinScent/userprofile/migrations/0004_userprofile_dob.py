# Generated by Django 4.2.3 on 2023-07-11 04:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0003_alter_address_addressee'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='dob',
            field=models.DateField(blank=True, null=True),
        ),
    ]
