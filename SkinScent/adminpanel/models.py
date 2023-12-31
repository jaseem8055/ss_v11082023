from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone

# Create your models here.

from django.utils.text import slugify

# from PIL import Image

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    is_blocked = models.BooleanField(default="False")
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Auto-generate the slug based on the name field
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def count_products(self):
        return self.product_set.exclude(is_blocked=True).count()


class UnitOfMeasurement(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=5)

    class Meta:
        unique_together = ['name', 'unit']

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_id = models.AutoField(primary_key=True)
    unit_of_measurement = models.ForeignKey(UnitOfMeasurement, on_delete=models.CASCADE)
    description = models.TextField()
    is_blocked = models.BooleanField(default="False")
    # To store multiple images, used a separate model and create a foreign key relationship.
    # Alternatively, can use a package like django-multiupload to handle multiple images.
    # Here's an example using a separate model:
    # images = models.ManyToManyField('ProductImage')

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    varied_by = models.CharField(max_length=255)
    variant_value = models.CharField(max_length=255)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)    


#####################
# COUPON MANAGEMENT #
#####################

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.FloatField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    minimum_purchase = models.FloatField(default=0)
    usage_count = models.PositiveIntegerField(default=0)
    # Add more fields if necessary (e.g., minimum purchase amount)

    def __str__(self):
        return self.code
    
    def increase_usage_count(self):
        self.usage_count += 1
        self.save()


######################
# OFFERS
######################
from django.core.validators import MinValueValidator

class Offer(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)  

    def __str__(self):
        return self.name

class ProductOffer(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)    
    
    def __str__(self):
        return f"{self.offer.name} - {self.product.name}"

class CategoryOffer(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)  
    
    def __str__(self):
        return f"{self.offer.name} - {self.category.name}"

class ReferralOffer(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.offer.name} - Referral Offer"
