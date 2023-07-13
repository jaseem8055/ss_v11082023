import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from adminpanel.models import *
from .models import *
from userprofile.models import *

from django.contrib.auth.decorators import login_required
from django.urls import reverse

from django.contrib.auth import authenticate, login


# Create your views here.
def home(request):     
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    categories = Category.objects.all()
    return render(request, 'index.html', {'username' : username, 'categories':categories})


def contact(request):        
    return render(request, 'contact.html')

############
# SHOP CART
############

# CART - LOGIN
def cart_signin(request, product_id):
    message = "Please login to Proceed!"
    product_id = product_id
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            # Authentication successful
            login(request, user)
            return redirect('/product_detail/' + str(product_id) + '/')            
            # if next_url:
            #     return redirect(next_url)
            # else:
            #     return redirect('/cart/')
        else:
            # Authentication failed
            error_message = 'Invalid username or password'
            return render(request, 'cart_signin.html', {'error_message': error_message})

    # Render the login form for GET requests
    return render(request, 'cart_signin.html', {'error_message': message, 'product_id':product_id})


# @login_required
def add_to_cart(request, variant_id):
    if request.method == 'POST': 
        # Get the user from the request (assuming authentication is enabled)
        user = request.user

        # Create or retrieve the user's cart
        cart, _ = Cart.objects.get_or_create(user=user)

        # Get the variant based on the variant_id
        variant = ProductVariant.objects.get(id=variant_id)

        # Check if the variant already exists in the cart items
        cart_item = CartItem.objects.filter(cart=cart, variant=variant).first()

        if cart_item:
            # Variant already exists, increment the quantity by 1
            cart_item.quantity += 1
            cart_item.save()
        else:
            # Variant does not exist, create a new cart item with a quantity of 1
            cart_item = CartItem.objects.create(cart=cart, product=variant.product, variant=variant, quantity=1)

        # Redirect or perform additional logic as needed

        return redirect('/cart/')  # Example: Redirect to the cart page


def cart_view(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
        # Retrieve the cart and cart items associated with the user (assuming the user is authenticated)
        cart = Cart.objects.get(user=request.user)

        sub_total = cart.get_cart_total()
        print("Sub Total = ",sub_total)

        cart_items = cart.cartitem_set.all()

        context = {
            'username': username,
            'cart': cart,
            'cart_items': cart_items, 
            'sub_total' : sub_total,
        }

        return render(request, 'cart.html', context)
    return redirect('/authapp/signin/')


def update_cart_item_quantity(request):
    print("Updating Cart...")
    # cart_items = request.POST.getlist('cartItemsQty')  # Updated line
    data = json.loads(request.body)
    cart_items = data['cartItemsQty']
    print(cart_items)
    for cart_item_data in cart_items:
        cart_item_id = int(cart_item_data['cartItemId'])
        quantity = int(cart_item_data['quantity'])
        print("Cart_Item_ID =", cart_item_id)
        print("Quantity =", quantity)
        
        cart_item = CartItem.objects.get(id=cart_item_id)
        cart_item.quantity = quantity
        cart_item.save()
    
    return redirect('/')  

def remove_cart_item(request, cart_item_id):
    # Retrieve the cart item object based on the cart_item_id
    try:
        cart_item = CartItem.objects.get(id=cart_item_id)
    except CartItem.DoesNotExist:
        # Handle the case when the cart item does not exist
        # Return an error response or redirect to an appropriate page
        pass

    # Delete the cart item from the database
    cart_item.delete()

    # Redirect to the cart page after successful removal
    return redirect('/cart/')

def checkout(request):
    # Retrieve the default address for the current user
    user_profile = request.user.userprofile
    default_address = DefaultAddress.objects.select_related('address').get(user_profile=user_profile)

    username = request.user.username
    # Retrieve the cart and cart items associated with the user (assuming the user is authenticated)
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.cartitem_set.all()

    sub_total = 0
    for item in cart_items:
        item_total = item.quantity * item.variant.price
        sub_total += item_total
    print("Sub Total = ",sub_total)
    total = sub_total + 10

    # Retrieve all addresses associated with the user
    addresses = Address.objects.filter(user_profile=user_profile)

    context = {
        'addressee': default_address.address.addressee,
        'address_line1': default_address.address.address_line1,
        'address_street': default_address.address.street,
        'address_city': default_address.address.city,
        'address_state': default_address.address.state,
        'address_country': default_address.address.country,
        'address_pincode': default_address.address.pin_code,
        'cart_items': cart_items,
        'sub_total': sub_total,
        'total': total,
        'addresses': addresses,
    }
    return render(request, 'cart_checkout.html', context)

#AJAX Call to Change Address
def get_address(request):
    address_id = request.GET.get('address_id')
    print("Address ID =", address_id)
    try:
        address = Address.objects.get(id=address_id)
        address_data = {
            'addressee': address.addressee,
            'address_line1': address.address_line1,
            'street': address.street,
            'city': address.city,
            'state': address.state,
            'country': address.country,
            'pin_code': address.pin_code,
        }
        return JsonResponse(address_data)
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Address not found.'})

def create_order(request):
    print("Reached Create_order")
    if request.method == 'POST':
        # Assuming the user is authenticated, you can access the current user as follows:
        user = request.user

        # Retrieve the form data
        addressee = request.POST.get('addressee')
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_street')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        zip_code = request.POST.get('zip_code')
        payment_method = request.POST.get('payment')

        sub_total = request.POST.get('sub_total')
        shipment_cost = request.POST.get('shipment_cost')
        

        shipment_address = f'{addressee}\n{address_line1}\n{address_line2}\n{city}, {state}, {country} {zip_code}'

        print("Address :", shipment_address)
        print("Payment by :", payment_method)
        # Create a new order
        order = Order(user=user, 
                      shipping_address=shipment_address, 
                      billing_address=shipment_address, 
                      payment_method=payment_method,
                      shipment_cost=shipment_cost,
                      sub_total=sub_total,
                      # payment_status --> Default = Pending
                      # fulfilment_status --> Default = Pending                      
                      #order_number = Implicitly set by overridden save() method
                      #created_at = auto_now                      
                      )
        order.save()
       
        # Get the cart for the current user
        cart = Cart.objects.get(user=user)

        # Iterate over the cart items and create order items
        cart_items = cart.cartitem_set.all()
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=cart_item.variant.price  # Assuming variant.price is the correct field to use
                # added_at = models.DateTimeField(auto_now_add=True)
            )
            order_item.save()

            # Reduce the quantity of the corresponding ProductVariant
            product_variant = cart_item.variant
            product_variant.quantity -= cart_item.quantity
            product_variant.save()
        
        

        # Clear the cart after creating the order
        cart.cartitem_set.all().delete()

        # Get the order_id for the current user
        order = Order.objects.filter(user=user).last()
        order_id = order.pk

        # Redirect to a success page or order details page
        return redirect(f'/order_success/{order_id}/')

        return HttpResponse("Order Placed!")
    
def order_success(request, order_id):
    # Retrieve the order object based on the order_id
    order = Order.objects.get(id=order_id)

    # Render the order_success.html template and pass the order object to it
    return render(request, 'order_success.html', {'order': order})

################################
# SHOP PAGE - CATEGORY / PRODUCT
################################
def category_page(request, category_id):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    
    category = Category.objects.get(id=category_id)
    products = Product.objects.filter(category_id=category)
    images = ProductImage.objects.filter(product__in=products).order_by('product').distinct('product')
    
    return render(request, 'category_page.html', {'username': username, 'category': category, 'images': images, 'products':products})


def product_detail(request, product_id):
    username = None
    warn_message = None
    success_message = None
    if request.user.is_authenticated:
        username = request.user.username
        success_message = "Hey! select the size and Add to the Cart!"
    else:
        warn_message = "Aww! You shall Sign-in to own a cart"

    product_obj = Product.objects.get(product_id=product_id)    
    images_list = ProductImage.objects.filter(product=product_id)
    product_unit = product_obj.unit_of_measurement
    # product_unit = int(product_unit)
    # unit_obj = UnitOfMeasurement.objects.get(id=product_unit)
    unit = product_unit.unit
    variant_obj = ProductVariant.objects.filter(product_id=product_obj.product_id)
    
    return render(request, 'product_detail.html', {'username': username, 'product_obj': product_obj, 'images_list': images_list, 'variant_obj':variant_obj, 'unit':unit, 'warn_message':warn_message, 'success_message':success_message })




# @login_required(login_url='/cart_signin/')
# def add_to_cart(request):    
#     # Additional logic can be added here if needed
#     # Add the product to the cart
#     # ...
#     #     
#     # Redirect to the cart page
#     return redirect(reverse('shop:cart'))
#     # return render(request, 'cart.html')

# def add_to_cart(request):
#     product_id = request.GET.get('product_id')
#     variant_value = request.GET.get('variant')
#     quantity = int(request.GET.get('quantity', 1))

#     # Retrieve the product and variant objects based on the IDs and values
#     product = Product.objects.get(product_id=product_id)
#     variant = product.productvariant_set.get(variant_value=variant_value)

#     # Save the cart item to the cart model
#     cart, created = Cart.objects.get_or_create(user=request.user)
#     cart_item = CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=quantity)

#     # Redirect to the cart view
#     return redirect('/cart/')

# # @login_required(login_url='/cart_signin/')
# def add_to_cart(request, variant_id):
    
#     # Retrieve the necessary data from the request

#     product_id = request.POST.get('productId')
#     variant_value_id = request.POST.get('variantValueId')
#     quantity = int(request.POST.get('quantity'))
#     response_data = {
#         'message': 'Item added to cart successfully'
#     }
#     return JsonResponse(response_data)
#     return HttpResponse("Hello")
#     # return render(request, 'test.html', {'product_id': product_id, 'variant_value_id': variant_value_id, 'quantity':quantity})
#     # return render(request, 'test.html', {'variant_value_id': variant_value_id, 'quantity':quantity})

#     # Assuming you have the user available in the request
#     user = request.user

#     # Find or create the user's cart
#     cart, _ = Cart.objects.get_or_create(user=user)

#     # Find the product variant based on the variant value
#     # Assuming you have a way to retrieve the correct variant based on the value    
#     product = Product.objects.get(pk=product_id)
#     variant = ProductVariant.objects.get(pk=variant_value_id)

#     # Create a new cart item
#     cart_item = CartItem.objects.create(cart=cart, variant=variant, quantity=quantity, product=product)

#     return redirect('/cart/')  
