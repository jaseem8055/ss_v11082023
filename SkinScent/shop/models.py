from datetime import date
import uuid
from django.db import models

from adminpanel.models import Product, ProductVariant

from django.contrib.auth.models import User

# Create your models here.

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_cart_total(self):
        total = 0
        cart_items = self.cartitem_set.all()
        for item in cart_items:
            total += item.get_item_total()
        return total


class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_item_total(self):
        return self.variant.price * self.quantity

    def get_variant_value(self):
        return self.variant.variant_value

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    order_number = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    shipment_cost = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.CharField(max_length=255)
    billing_address = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=128, default='Pending')
    fulfillment_status = models.CharField(max_length=128, default='Pending')

    def save(self, *args, **kwargs):
        if not self.order_number:
            current_date = date.today().strftime("%m%d%Y")  # Get current date in MMDDYYYY format
            unique_id = str(uuid.uuid4())  # Generate UUID
            self.order_number = f"{current_date}-{unique_id}"  # Append date to UUID for the order number
        super().save(*args, **kwargs)
    
    def get_cart_total(self):
        return self.shipment_cost + self.sub_total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    added_at = models.DateTimeField(auto_now_add=True)

    def get_item_total(self):
        return self.variant.price * self.quantity

    def get_variant_value(self):
        return self.variant.variant_value
    
