from datetime import date
from decimal import Decimal
import uuid
from django.db import models

from adminpanel.models import Product, ProductVariant, Coupon

from django.contrib.auth.models import User

# Signal Handler (Used for 'CouponHistory' field)
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone


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
    # New field for saving the "new price" after discount
    new_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)

    def get_item_total(self):
        return self.variant.price * self.quantity
    
    def get_item_total_new(self):
        return self.new_price * self.quantity


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
    fulfillment_status = models.CharField(max_length=128, default='Processing')
    couponhistory_id = models.CharField(max_length=50, default='')
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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
        return self.price * self.quantity

    def get_variant_value(self):
        return self.variant.variant_value
    
    
class RazorPayment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
    receipt = models.CharField(max_length=100, blank=True, null=True)
      

class TrackOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    tracking_number = models.CharField(blank=True, null=True, unique=True)
    shipped_date = models.DateTimeField(blank=True, null=True)
    delivery_center_date = models.DateTimeField(blank=True, null=True)
    delivered_date = models.DateTimeField(blank=True, null=True)
    cancelled_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Tracking Number: {self.tracking_number} - Order Number: {self.order.order_number}"
    
    def get_tracking_status_icon(self):
        # Define a dictionary mapping fulfillment_status to the corresponding icon filename or CSS class
        status_icons = {
            'Processing': 'processing-icon.png',
            'Shipped': 'shipped-icon.png',
            'In Transit': 'in-transit-icon.png',
            'Out for Delivery': 'out-for-delivery-icon.png',
            'Delivered': 'delivered-icon.png',
            'Failed Delivery': 'failed-delivery-icon.png',
        }

        return status_icons.get(self.order.fulfillment_status, 'default-icon.png')
    

# The below Model is related with CART. To store Coupon used.
# The Model object will be deleted in cascade with 'CART' deletion for the user. 'CART' has to be kept without deletion.
class CouponHistory(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    return_status = models.BooleanField(default=False)  # Add the return status field
    used_order_id = models.CharField(max_length=50, default='')
    order_date = models.DateField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} - {self.coupon.code}"


# Define the signal handler function
# To auto-fill the order_date field in the CouponHistory model when the used_order_id field is updated or saved
@receiver(pre_save, sender=CouponHistory)
def update_order_date(sender, instance, **kwargs):
    if instance.used_order_id and not instance.order_date:
        instance.order_date = timezone.now().date()

# Connect the signal handler to the pre_save signal
pre_save.connect(update_order_date, sender=CouponHistory)


#####################
##### WISH LIST #####
#####################

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # If you want to associate the wishlist with a specific user
    products = models.ManyToManyField(Product)  # Many-to-many relationship with Product model
    added_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist for {self.user}"