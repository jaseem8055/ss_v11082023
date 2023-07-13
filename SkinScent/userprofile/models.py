from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    dob = models.DateField(null=True, blank=True)

class Address(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    addressee = models.CharField(max_length=100, default='')
    address_line1 = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)

class DefaultAddress(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, primary_key=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)

class ContactMobile(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=20)
