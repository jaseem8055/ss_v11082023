from django.db import models

# Create your models here.

from django.utils.text import slugify

# from PIL import Image

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    is_blocked = models.BooleanField(default="False")
    
    def save(self, *args, **kwargs):
        # Auto-generate the slug based on the name field
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class UnitOfMeasurement(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=5)

    class Meta:
        unique_together = ['name', 'unit']

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_id = models.AutoField(primary_key=True)
    # unit_of_measurement = models.CharField(max_length=100)
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

    class Meta:
        unique_together = ['product', 'variant_value']