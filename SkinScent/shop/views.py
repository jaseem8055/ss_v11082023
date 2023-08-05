import datetime

# For Fixing the Time Zone from UTC
from datetime import timedelta

from django.utils import timezone
from decimal import Decimal
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from adminpanel.models import *
from .models import *
from userprofile.models import *

from django.contrib.auth.decorators import login_required
from django.urls import reverse

from django.contrib.auth import authenticate, login

from django.core.paginator import Paginator

from django.db.models import F, Value
from django.db.models.functions import Concat

# RAZORPAY
from django.views.decorators.csrf import csrf_exempt
import razorpay


# Create your views here.
def home(request):
    username = categories = None
    wishlist_count = 0
    if request.user.is_authenticated:
        username = request.user.username

        user = request.user
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        # Get the updated count of products in the wishlist for the specific product
        wishlist_count = wishlist.products.count()
        # print("Wishlist =", wishlist_count )
        # context = {'username' : username, 'categories':categories, 'wishlist_count': wishlist_count}
    
    categories = Category.objects.all().exclude(is_blocked=True)

    context = {'username' : username, 'categories':categories, 'wishlist_count': wishlist_count}
    
    # OFFER COUNT
    offer_products_count = 0
    # UTC to IST difference
    hours_to_add = 5
    minutes_to_add = 30
    # Calculate the timedelta with the specified hours and minutes
    time_delta = timedelta(hours=hours_to_add, minutes=minutes_to_add)
    IST_local = timezone.now() + time_delta
    # Get all active offers
    active_offers_exists = Offer.objects.filter(active=True, end_date__gt=IST_local, start_date__lte=IST_local).exists()
    
    if active_offers_exists:
        active_offers = Offer.objects.filter(active=True, end_date__gt=IST_local, start_date__lte=IST_local)
        # Fetch product offers for each active offer            
        for offer in active_offers:
            product_offers = ProductOffer.objects.filter(offer=offer, active=True)
            offer_products_count += product_offers.count()
        
    context.update({ 'offer_products_count': offer_products_count})
    
    return render(request, 'index.html', context)

def contact(request):        
    return render(request, 'contact.html')

########
# OFFERS
########
def offer_page(request):
    # UTC to IST difference
    hours_to_add = 5
    minutes_to_add = 30

    # Calculate the timedelta with the specified hours and minutes
    time_delta = timedelta(hours=hours_to_add, minutes=minutes_to_add)
    IST_local = timezone.now() + time_delta

    # Get all active offers
    active_offers = Offer.objects.filter(active=True, end_date__gt=IST_local, start_date__lte=IST_local)
    context = {}
    # Fetch product offers for each active offer
    offers_with_product_offers = []
    offer_products_count = 0
    for offer in active_offers:
        product_offers = ProductOffer.objects.filter(offer=offer, active=True)
        offers_with_product_offers.append({'offer': offer, 'product_offers': product_offers})

        offer_products_count += product_offers.count()
    
    context.update({ 'offer_products_count': offer_products_count})
        
    # Create a dictionary to store offer-product offer pairs
    offer_dict = {}

    # Fetch product offers for each active offer and group them in the dictionary
    for offer in active_offers:
        product_offers = ProductOffer.objects.filter(offer=offer, active=True)
        # offer_dict[offer] = product_offers
        offer_dict[offer] = []

        for product_offer in product_offers:
            product = product_offer.product
            # Retrieve the first image for the product
            first_image = ProductImage.objects.filter(product=product).first()
            offer_dict[offer].append({'product_offer': product_offer, 'first_image': first_image})   
    
    # Wishlist Check
        has_products_wishlist = False
        wishlist_count = 0
        product_ids = []
        try:
            wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
            has_products_wishlist = wishlist.products.exists()
            if has_products_wishlist:
                products_wishlist = wishlist.products.all()
                wishlist_count = wishlist.products.count()                
                for obj in products_wishlist:
                    product_ids.append(obj.product_id)                    

                # print("Wishlist have product!")
                # print(product_ids)
                context.update({'has_products_wishlist': has_products_wishlist,
                                'product_ids': product_ids,
                                'wishlist_count': wishlist_count})
        except:
            has_products_wishlist = False    

    context.update({'offer_dict': offer_dict})
    categories = Category.objects.all().exclude(is_blocked=True)
    context.update({ 'categories': categories }) 
    return render(request, 'offer_page.html', context)


##########
# WISHLIST
##########
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    user = request.user  

    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    # Check if the product is not already in the user's wishlist
    if not Wishlist.objects.filter(user=user, products=product).exists():        
        wishlist.products.add(product)

    # Get the updated count of products in the wishlist for the specific product
    count = wishlist.products.count()

    # Return a JSON response with the updated count
    return JsonResponse({'count': count})

def wishlist_products(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username

    user = request.user  # Assuming the user is logged in
    try:
        wishlist = get_object_or_404(Wishlist, user=user)

        # Retrieve all products in the user's wishlist
        products = wishlist.products.all()

        images = ProductImage.objects.filter(product__in=products).order_by('product').distinct('product')
    except:
        message = "Wishlist is Empty!"
        pass

    paginator = Paginator(images, 6)  # Display 10 products per page    
    page_number = request.GET.get('page')
    images = paginator.get_page(page_number)

    # NAVBAR CAtegories Display
    categories = Category.objects.all().exclude(is_blocked = True)

    context = {
        'username': username,        
        'images': images,
        'products':products,
        'categories': categories,        
    }

    return render(request, 'wishlist.html', context)

def remove_from_wishlist(request, product_id):
    user = request.user  # Assuming the user is logged in
    wishlist = get_object_or_404(Wishlist, user=user)

    try:
        product = Product.objects.get(pk=product_id)
        wishlist.products.remove(product)

    except Product.DoesNotExist:
        message= 'Product not found in the wishlist'
        # print(message)
    return redirect('/wishlist/')
    

# ###################
# # PDF DOC
# ###################

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from io import BytesIO

from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Count, F, Sum, Avg

def generate_pdf(request, order_id):
    # Fetch the object from the database
    order_obj = get_object_or_404(Order, id=order_id)

    # Create a response object with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{order_obj.order_number}.pdf"'

    # Create a buffer for the PDF content
    buffer = BytesIO()

    # Create a PDF document using reportlab
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Title Font
    title_font_style = getSampleStyleSheet()["Title"]
    title_text = 'Skin & Scent - Order Invoice'
    elements.append(Paragraph(title_text, title_font_style))
    elements.append(Paragraph("<br/><br/>", title_font_style))  # Add some space after the title

    # Body Font
    normal_font_style = getSampleStyleSheet()["Normal"]

    # Add content to the PDF with proper formatting
    elements.append(Paragraph(f"<b>Order Number:</b> {order_obj.order_number}", normal_font_style))
    elements.append(Paragraph(f"<b>Shipping Address:</b><br/>{order_obj.shipping_address}", normal_font_style))
    elements.append(Paragraph(f"<b>Payment Method:</b> {order_obj.payment_method}", normal_font_style))

    elements.append(Paragraph("<br/><b>Order Items:</b>", normal_font_style))

    # Add a table for order items
    items = [["Product", "Variant", "Quantity", "Price", "Total"]]
    for item in order_obj.orderitem_set.all():
        unit = item.product.unit_of_measurement.unit
        variant_val = item.get_variant_value()
        variant = variant_val + unit
        items.append([
            item.product.name,
            variant,
            str(item.quantity),
            str(item.price),
            str(item.get_item_total())
        ])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 1), (-1, -1), 1, colors.grey),
    ])

    table = Table(items)
    table.setStyle(table_style)
    elements.append(table)

    # Add the total
    elements.append(Paragraph(f"<br/><b>Sub Total:</b> {order_obj.sub_total}", normal_font_style))
    elements.append(Paragraph(f"<b>Shipment Cost:</b> {order_obj.shipment_cost}", normal_font_style))
    elements.append(Paragraph(f"<b>Discount:</b> {order_obj.coupon_discount}", normal_font_style))
    total = order_obj.sub_total - order_obj.coupon_discount + order_obj.shipment_cost
    elements.append(Paragraph(f"<b>Total Bill:</b> {total}", normal_font_style))

    # On Coupon Discount
    if order_obj.couponhistory_id != '':
        coupon_history_id = order_obj.couponhistory_id
        try:
            coupon_history = CouponHistory.objects.get(id=coupon_history_id)
            discount = coupon_history.coupon.discount
            code = coupon_history.coupon.code
            elements.append(Paragraph(f"<br/><b>In this Order, You have availed {discount}% Off by using coupon code: {code}</b>", normal_font_style))
        except CouponHistory.DoesNotExist:
            pass

    # Build the PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

###################
# COUPON MANAGEMENT
###################
def apply_coupon(request):
    username = None
    discount = 0 # Default value for Coupon Discount
    if request.user.is_authenticated:
        username = request.user.username

    if request.method == 'POST':
            try:
                coupon_code = request.POST.get('coupon_code')  # Get the entered coupon code from the form
                sub_total = request.POST.get('subtotal') 
                # print("Input... Coupon: ",coupon_code, " Sub Total: ", sub_total)
                # print("time =", timezone.now())
                now = datetime.datetime.now()                
                # print("now =", now)
                # Check if the coupon exists, is valid, and active
                check_code = Coupon.objects.get(code=coupon_code, active=True, valid_from__lte=now, valid_to__gte=now)
                # print("Valid From =", check_code.valid_from, " Valid To = ", check_code.valid_to)

                if not (check_code.minimum_purchase <= float(sub_total)):
                    return JsonResponse({'error': f'Coupon Code: {coupon_code}, Minimum Purchase: ₹{check_code.minimum_purchase}, Add more Products!', 'discount': discount}, status=400)        

                if coupon_code == "FIRSTBUY":
                    # Check if the user had any Order history
                    has_orders = Order.objects.filter(user=request.user).exists()
                    # print(has_orders)
                    if not has_orders:
                        if not (check_code.minimum_purchase <= float(sub_total)):
                            return JsonResponse({'error': f'Sorry! To Apply the coupon, Subtotal shall be minimum of ₹{check_code.minimum_purchase}!', 'discount': discount}, status=400)        
                        
                        # Else - Fetch discount, if coupon is valid,active and If FIRST ORDER!
                        discount = check_code.discount                        
                        # print(discount)
                        # Get the user's cart and Create object in CouponHistory
                        user_cart = Cart.objects.get(user=request.user)
                        coupon_history = CouponHistory.objects.create(coupon=check_code, cart=user_cart, user=request.user)
                        # print("Updated Coupon History :", coupon_history)
                        return JsonResponse({'discount': discount})
                    else:
                        return JsonResponse({'error': 'Coupon Applicable Only For First Order, Sorry!', 'discount': discount}, status=400)        

                else:
                    # Check if the user has already applied the coupon
                    coupon_applied = CouponHistory.objects.filter(coupon=check_code, user=request.user).exists()
                    if coupon_applied:
                        # Check if the coupon used, Order has been placed with Coupon
                        check_use = CouponHistory.objects.get(coupon=check_code, user=request.user)
                        # Check if the Order has been placed with Coupon
                        if check_use.used_order_id != '' and check_use.return_status == False:
                            # The coupon has been used!
                            return JsonResponse({'error': 'Coupon Already Used!', 'discount': discount}, status=400)

                        # Fetch discount
                        discount = check_code.discount
                        # print(discount)
                        return JsonResponse({'discount': discount})
                    # The Coupon is not yet applied - First Time Click of "Apply Coupon"
                    # Get the user's cart and Create object in CouponHistory
                    user_cart = Cart.objects.get(user=request.user)
                    coupon_history = CouponHistory.objects.create(coupon=check_code, cart=user_cart, user=request.user)
                    # print("Updated Coupon History :", coupon_history)
                    
                    # Fetch discount
                    discount = check_code.discount
                    # print(discount)
                    return JsonResponse({'discount': discount})            
            
            except Coupon.DoesNotExist:
                # print("Exception!")
                return JsonResponse({'error': 'Invalid coupon code', 'discount': discount}, status=400)        
        
    # Return the default discount value as a JSON response
    return JsonResponse({'discount': discount})

def clear_coupon(request):
    if request.method == 'POST':
        cart = Cart.objects.get(user=request.user)
        
        try:
            coupon_history = CouponHistory.objects.get(cart=cart, used_order_id='')
            coupon_history.delete()  # Remove the applied coupon from the cart
            return JsonResponse({'message': 'Coupon cleared successfully!'})
        except CouponHistory.DoesNotExist:
            return JsonResponse({'error': 'No applied coupon found.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


#############
# RAZOR PAY #
#############
import requests
def has_internet_connection():
    try:
        # Make a simple request to a reliable server to check internet connectivity
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.RequestException:
        return False

def initiate_payment(request):
    if not has_internet_connection():
        error_message = "No internet connection. Please check your network settings."
        return JsonResponse({'error': error_message}, status=400)
       
    if request.method == 'POST':
        # Fetch all fields to be stored in Order Model
        addressee = request.POST.get("addressee")
        address_line1 = request.POST.get("address_line1")
        address_line2 = request.POST.get("address_street")
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")
        zip_code = request.POST.get("zip_code")

        if addressee == '' or address_line1 == '' or address_line2 == '' or city == '' or state == '' or country == '' or zip_code == '':
            error_message = "All Fields in Address Field are Required! Select Your Address."
            return JsonResponse({'error': error_message}, status=400)


        payment_method = request.POST.get("payment_method")
        sub_total = request.POST.get("sub_total")
        shipment_cost = request.POST.get("shipment_cost")

        discount_amount = request.POST.get("discount_amount")
        
        shipment_address = f'{addressee}, {address_line1}, {address_line2}, {city}, {state}, {country} {zip_code}'
        user = request.user

        # Create a new order
        order = Order(user=user, 
                      shipping_address=shipment_address, 
                      billing_address=shipment_address, 
                      payment_method=payment_method,
                      shipment_cost=shipment_cost,
                      sub_total=sub_total,
                      coupon_discount=discount_amount,
                      # payment_status --> Default = Pending
                      # fulfilment_status --> Default = Pending                      
                      #order_number = Implicitly set by overridden save() method
                      #created_at = auto_now                      
                      )
        order.save()

        # Get the order_id for the current user
        # Used for updating 'CouponHistory' and to render into 'order_success'
        order = Order.objects.filter(user=user).last()
        order_id = order.pk  

        # Update Use of Coupon in 'CouponHistory'
        coupon_applied = CouponHistory.objects.get(user=request.user, used_order_id='', return_status=False)
        coupon_applied.used_order_id = order_id
        coupon_applied.save()                

        # Update 'Order' with 'id' of 'CouponHistory'
        coupon_applied = CouponHistory.objects.get(user=request.user, used_order_id=order_id, return_status=False)
        order.couponhistory_id = coupon_applied.pk
        order.save()

        # Increase the usage count in the Coupon model - When creating the order!
        coupon_applied.coupon.increase_usage_count()

        # Initialize the Razorpay client with your key and secret
        razorpay_client = razorpay.Client(auth=("rzp_test_scLGFrR0R5zejV", "ZtPHrmQQ5jK2u4ytxDFHhcNm"))
        # client = razorpay.Client(auth=('rzp_test_scLGFrR0R5zejV', 'ZtPHrmQQ5jK2u4ytxDFHhcNm'))

        # Create a Razorpay order with relevant details
        razorpay_order = razorpay_client.order.create(
            {
                # "amount": int(sub_total) * 100,  # Amount in paise
                "amount": 100,  # Amount in paise
                "currency": "INR",
                "receipt": str(uuid.uuid4()), 
                "payment_capture": 1  # Auto-capture the payment after successful verification
            }
        )

        # Return the necessary information as a JSON response
        response_data = {
            "key": "rzp_test_scLGFrR0R5zejV",
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "receipt": razorpay_order["receipt"],
            "order_id": razorpay_order["id"]
        }

        return HttpResponse(json.dumps(response_data), content_type="application/json")
    else:
        return HttpResponse(status=405)  # Method Not Allowed

def handle_payment_success(request):
    user = request.user
    if request.method == "POST":
        # Process the payment success data here
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        # Fetch the last obj of 'Order' for the user
        order_obj = Order.objects.filter(user=user).last()
        
        # Create & Save new object in 'RazorPayment' for the 'order'
        rp_obj = RazorPayment(order = order_obj,
                              razorpay_order_id = razorpay_order_id,
                              razorpay_payment_id = razorpay_payment_id,
                              razorpay_signature = razorpay_signature,
                              )
        rp_obj.save()

        # Get the cart for the current user
        cart = Cart.objects.get(user=user)

        # Iterate over the cart items and create order items
        cart_items = cart.cartitem_set.all()
        for cart_item in cart_items:
            variant_price = cart_item.variant.price
            set_new_price = cart_item.new_price # Product Offer Discount Price
            if set_new_price is not None and set_new_price > 0.00:
                variant_price = set_new_price

            order_item = OrderItem(
                order=order_obj,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=variant_price
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
        order_id = order_obj.pk

        response_data = {
            "order_id": order_id,
            "status": "success",
            }
        
        return HttpResponse(json.dumps(response_data), content_type="application/json")


#################
# PROCESS FILTER
#################

def process_filter(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username

    if request.method == 'GET':
        # Retrieve the values from the 'input' element
        size_all = request.GET.get('size-all') == 'on'  # Checkbox value (True if checked)
        size_list = request.GET.getlist('size')  # List of selected sizes
        # list_variant_value_unit = request.GET.get('list-of-size')        
        price_range = request.GET.get('price-range')
        # print(list_variant_value_unit, price_range)            

        variant_val_list = []
        unit_list = []
        product_with_unit_list = []
        for size in size_list:
            variant_val, unit = size.split(" ")
            variant_val_list.append(variant_val)
            unit_list.append(unit)
            
            product_with_unit = Product.objects.filter(unit_of_measurement__unit = unit)
            # product_with_unit_list.append(product_with_unit)
            product_with_unit_list.extend(product_with_unit)
        
        variants_with_value = ProductVariant.objects.filter(variant_value__in = variant_val_list)
        variants_with_value_unit = variants_with_value.filter(product__in = product_with_unit_list)
        products = variants_with_value_unit.values_list('product_id', flat=True)
        images = ProductImage.objects.filter(product__in = products).distinct('product').order_by('product')

        # FILTER BY SIZE
        ################
        variant_values = ProductVariant.objects.filter(product__in=products).values('variant_value', 'product__unit_of_measurement__unit')
        
        size_unit = variant_values.annotate(
            value_unit=Concat('variant_value', Value(' '), 'product__unit_of_measurement__unit'))
        # for i in size_unit:
        #     print("size_unit =", i['value_unit'])

        distinct_size_unit = size_unit.distinct()
        
        variant_value_unit = distinct_size_unit.values('value_unit')
        
        list_variant_value_unit = []
        for item in variant_value_unit:
            list_variant_value_unit.append(item['value_unit'])
        
        # FILTER BY PRICE
        ##################        
        dict_variant_prices = ProductVariant.objects.filter(product__in=products).values('price').distinct()       

        list_variant_price = []
        for price_key in dict_variant_prices:
            price = float(price_key['price'])
            list_variant_price.append(price_key['price'])
            max_price = max(list_variant_price)        

        set_max_range = max_price % 100
        if set_max_range == 0:
            max_range = max_price
        else:
            max_range = max_price + (100 - set_max_range)

        range_inc = 0
        price_range = []
        while(range_inc<max_range):
            price_range.append(range_inc)
            range_inc += 50
        

        
        # NAVBAR CAtegories Display
        categories = Category.objects.all().exclude(is_blocked = True)

        

        context = {
        'username': username,
        'products': products,        
        'images' : images,
        'categories': categories,
        'list_of_sizes': list_variant_value_unit,
        'price_range': price_range,

                
        # Inputs
        'size_all': size_all, 
        'size_list': size_list,
        }
    
        
        # Render a response or redirect to another page
        return render(request, 'category_page.html', context)
        # return render(request, 'test.html', context)



#################
# SEARCH PRODUCTS
#################
def search_products(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username

    query = request.GET.get('q')  # Get the search query from the request's GET parameters

    if query:
        products = Product.objects.filter(name__icontains=query)  # Perform case-insensitive search for the product name
        images = ProductImage.objects.filter(product__in=products).order_by('product').distinct('product')
        paginator = Paginator(images, 6)  # Display 10 products per page    
        page_number = request.GET.get('page')
        images = paginator.get_page(page_number)
    else:
        products = Product.objects.all().exclude(is_blocked = True)
        images = ProductImage.objects.filter(product__in=products).order_by('product').distinct('product')
        paginator = Paginator(images, 6)  # Display 10 products per page    
        page_number = request.GET.get('page')
        images = paginator.get_page(page_number)
    
    # NAVBAR CAtegories Display
    categories = Category.objects.all().exclude(is_blocked = True)

    
    # FILTER BY SIZE
    ################
    
    variant_values = ProductVariant.objects.filter(product__in=products).values('variant_value', 'product__unit_of_measurement__unit')
    # print("All Variant Values = ",variant_values)
    
    # size_unit = variant_values.annotate(value_unit=F('variant_value') + F('product__unit_of_measurement__unit'))
    size_unit = variant_values.annotate(
        value_unit=Concat('variant_value', Value(' '), 'product__unit_of_measurement__unit'))
    # for i in size_unit:
    #     print("size_unit =", i['value_unit'])

    distinct_size_unit = size_unit.distinct()
    # print("Distinct Sizes = ", distinct_size_unit)
    # # Distinct Sizes =  <QuerySet [{'variant_value': '150', 'product__unit_of_measurement__unit': 'g', 'value_unit': '150 g'}, {'variant_value': '200', 'product__unit_of_measurement__unit': 'ml', 'value_unit': '200 ml'},

    variant_value_unit = distinct_size_unit.values('value_unit')
    # print("Dict of Distinct Sizes = ", variant_value_unit)
    # # Dict of Distinct Sizes =  <QuerySet [{'value_unit': '200 ml'}, {'value_unit': '150 g'}, {'value_unit': '300 g'}, {'value_unit': '150 ml'}, {'value_unit': '100 ml'}, {'value_unit': '300 ml'}]>

    list_variant_value_unit = []
    for item in variant_value_unit:
        list_variant_value_unit.append(item['value_unit'])
    # print("List of Distinct size with their unit =", list_variant_value_unit)
    # # List of Distinct size with their unit = ['200 ml', '150 g', '300 g', '150 ml', '100 ml', '300 ml']

    
    # FILTER BY PRICE
    ##################
    
    dict_variant_prices = ProductVariant.objects.filter(product__in=products).values('price').distinct()
    

    list_variant_price = []
    for price_key in dict_variant_prices:
        price = float(price_key['price'])
        list_variant_price.append(price_key['price'])
        max_price = max(list_variant_price)

    
    # print("List of Price =", list_variant_price)
    # print("MAX = ", max_price)

    set_max_range = max_price % 100
    if set_max_range == 0:
        max_range = max_price
    else:
        max_range = max_price + (100 - set_max_range)

    range_inc = 0
    price_range = []
    while(range_inc<max_range):
        price_range.append(range_inc)
        range_inc += 50    
    
    # Pass in Context. 'price_range'
    # print("Price Range = ", price_range)

    # Wishlist Check
    # Wishlist Check
    has_products_wishlist = False
    wishlist_count = 0
    product_ids = []
    try:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        has_products_wishlist = wishlist.products.exists()
        if has_products_wishlist:
            products_wishlist = wishlist.products.all()
            wishlist_count = wishlist.products.count()                
            for obj in products_wishlist:
                product_ids.append(obj.product_id)

            # print("Wishlist have product!")
            # print(product_ids)
    except:
        has_products_wishlist = False
       
    
    context = {
        'username': username,
        'products': products,
        'query': query,
        'images' : images,
        'categories': categories,
        'list_of_sizes': list_variant_value_unit,
        'price_range': price_range,
        'has_products_wishlist': has_products_wishlist,
        'product_ids': product_ids,
        'wishlist_count': wishlist_count
    }

    return render(request, 'search_results.html', context)

def filter_products(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    # print("min = ", min_price + "&" + "max =", max_price)
    # Filter products based on the received price range
    filter_variants = ProductVariant.objects.filter(price__gte=min_price, price__lte=max_price)
    filtered_products = filter_variants.values_list('product', flat=True).distinct()
    images = ProductImage.objects.filter(product__in=filtered_products).order_by('product').distinct('product')
    # print("Image List =",images)
    #For Context
    products = filtered_products

    # NAVBAR CAtegories Display
    categories = Category.objects.all().exclude(is_blocked = True)

    context = {
        'username': username,
        'products': products,        
        'images' : images,
        'categories': categories,    
    }

    # Render a partial HTML template with the filtered products
    return render(request, 'search_results.html', context)
    # return render(request, 'filtered_products.html', {'filtered_products': filtered_products})


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

        # Check if the variant - product has Offer
        new_price = 0
        discount_pc = get_discount_percentage(variant_id)
        if discount_pc is not None:
            discount_amount = variant.price * discount_pc /100
            new_price = variant.price - discount_amount
            # print("New Price =", new_price)

        # Check if the variant already exists in the cart items
        cart_item = CartItem.objects.filter(cart=cart, variant=variant).first()

        if cart_item:
            # Variant already exists, increment the quantity by 1
            cart_item.quantity += 1
            cart_item.new_price = new_price
            cart_item.save()
        else:
            # Variant does not exist, create a new cart item with a quantity of 1
            cart_item = CartItem.objects.create(cart=cart, product=variant.product, variant=variant, quantity=1, new_price=new_price)

        # Redirect or perform additional logic as needed

        return redirect('/cart/')  # Example: Redirect to the cart page


# Function to get discount percentage
def get_discount_percentage(variant_id):
    try:
        # Find the product variant based on the provided variant_id
        variant = ProductVariant.objects.get(pk=variant_id)

        # UTC to IST difference
        hours_to_add = 5
        minutes_to_add = 30
        # Calculate the timedelta with the specified hours and minutes
        time_delta = timedelta(hours=hours_to_add, minutes=minutes_to_add)
        IST_local = timezone.now() + time_delta

        # Check if there is an active offer associated with the product variant
        product_offer = ProductOffer.objects.filter(
            product=variant.product,
            offer__active=True,
            offer__start_date__lte=IST_local,  # Check if the current date is after or equal to start_date
            offer__end_date__gte=IST_local     # Check if the current date is before or equal to end_date
        ).first()

        # If there is an active offer associated with the product variant
        if product_offer:
            # Return the discount percentage for the offer
            return product_offer.discount_percentage

    except ProductVariant.DoesNotExist:
        pass

    # If there is no offer or the variant_id is invalid, return None
    return None

def cart_view(request):
    username = None
    discount = 0 # Default value for Coupon Discount
    if request.user.is_authenticated:
        username = request.user.username
        # Retrieve the cart and cart items associated with the user (assuming the user is authenticated)        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        sub_total = float(cart.get_cart_total())
        # print("Sub Total = ",sub_total)

        try:
            coupon_history = CouponHistory.objects.get(cart=cart, used_order_id='')            
            applied_coupon = coupon_history.coupon
            if not (applied_coupon.minimum_purchase <= sub_total):
                # Remove the Applied Coupon on the cart
                coupon_history.delete()
                applied_coupon = None                           
            else:
                # Else - Eleigible for discount with Coupon            
                discount = applied_coupon.discount
        except CouponHistory.DoesNotExist:
            # If there is no applied coupon, set default values
            applied_coupon = None
            discount = 0

        

        # Calculate the new total amount with the discount        
        shipment_cost = 10  # Replace this with your actual shipment cost
        discount_amount = (sub_total * discount) / 100
        total = sub_total - discount_amount + shipment_cost

        cart_items = cart.cartitem_set.all()


        context = {
            'username': username,
            'cart': cart,
            'cart_items': cart_items, 
            'sub_total' : sub_total,
            'discount' : discount,
            'discount_amount' : discount_amount,
            'applied_coupon': applied_coupon,
            'total': total
        }
        
        wishlist_count = 0
        if request.user.is_authenticated:
            username = request.user.username

            user = request.user
            wishlist, _ = Wishlist.objects.get_or_create(user=user)
            # Get the updated count of products in the wishlist for the specific product
            wishlist_count = wishlist.products.count()
            context.update({'wishlist_count': wishlist_count})
            # print("Wishlist =", wishlist_count )
            # context = {'username' : username, 'categories':categories, 'wishlist_count': wishlist_count}

        return render(request, 'cart.html', context)
    return redirect('/authapp/signin/')

def update_cart_item_quantity(request):
    # print("Updating Cart...")
    # cart_items = request.POST.getlist('cartItemsQty')  # Updated line
    data = json.loads(request.body)
    cart_items = data['cartItemsQty']
    # print(cart_items)
    for cart_item_data in cart_items:
        cart_item_id = int(cart_item_data['cartItemId'])
        quantity = int(cart_item_data['quantity'])
        # print("Cart_Item_ID =", cart_item_id)
        # print("Quantity =", quantity)
        
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
    user = request.user
    # Retrieve the default address for the current user
    try:
        user_profile = user.userprofile
    except UserProfile.DoesNotExist:
        # Create a new userprofile if it doesn't exist
        user_profile = UserProfile.objects.create(user=user)

    
    # default_address = DefaultAddress.objects.select_related('address').get(user_profile=user_profile)

    username = request.user.username
    # Retrieve the cart and cart items associated with the user (assuming the user is authenticated)
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.cartitem_set.all()

    sub_total = 0
    for item in cart_items:
        item_total = item.quantity * item.variant.price
        sub_total += item_total
    # print("Sub Total = ",sub_total)

    discount = 0
     # Check if the user has already applied the coupon
    coupon_applied = CouponHistory.objects.filter(cart=cart, user=request.user, used_order_id='').exists()
    if coupon_applied:
        # Check if the coupon used, Order has been placed with Coupon
        current_coupon = CouponHistory.objects.get(cart=cart, user=request.user, used_order_id='')
        coupon_obj = current_coupon.coupon  # Get respective object from 'Coupon' Model
        discount = Decimal(coupon_obj.discount)
        # # Check if the Order has been placed with Coupon
        # if check_use.used_order_id != '' and check_use.return_status == False:
        #     # The coupon has been used!
        #     discount = 0
        
            
    # print("Type of Sub Total : ", type(sub_total))
    # print("Type of discount : ", type(discount))
    discount_amount = (sub_total * discount) / 100
    shipment_cost = 10
    total = sub_total - discount_amount + shipment_cost

    # total = sub_total + 10

    # Retrieve all addresses associated with the user
    addresses = Address.objects.filter(user_profile=user_profile)

    context = {
        # 'addressee': default_address.address.addressee,
        # 'address_line1': default_address.address.address_line1,
        # 'address_street': default_address.address.street,
        # 'address_city': default_address.address.city,
        # 'address_state': default_address.address.state,
        # 'address_country': default_address.address.country,
        # 'address_pincode': default_address.address.pin_code,
        'cart_items': cart_items,
        'sub_total': sub_total,
        'total': total,
        'addresses': addresses,
        'discount_amount': discount_amount,
    }
    return render(request, 'cart_checkout.html', context)


#############################
# AJAX Call to Change Address
#############################
def get_address(request):
    address_id = request.GET.get('address_id')
    # print("Address ID =", address_id)
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
    # print("Reached Create_order")
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
        
        discount_amount = request.POST.get('discount_amount')    

        shipment_cost = request.POST.get('shipment_cost')        

        shipment_address = f'{addressee}, {address_line1}, {address_line2}, {city}, {state}, {country} {zip_code}'

        # print("Address :", shipment_address)
        # print("Payment by :", payment_method)

        # Create a new order
        order = Order(user=user, 
                      shipping_address=shipment_address, 
                      billing_address=shipment_address, 
                      payment_method=payment_method,
                      shipment_cost=shipment_cost,
                      sub_total=sub_total,
                      coupon_discount=discount_amount,
                      # payment_status --> Default = Pending
                      # fulfilment_status --> Default = Pending                      
                      #order_number = Implicitly set by overridden save() method
                      #created_at = auto_now                      
                      )
        order.save()
        
        # if payment_method == 'razorpay':
        #     return redirect('/initiate-payment/')

        # Get the order_id for the current user
        # Used for updating 'CouponHistory' and to render into 'order_success'
        order = Order.objects.filter(user=user).last()
        order_id = order.pk  

        # Update Use of Coupon in 'CouponHistory'
        coupon_applied = CouponHistory.objects.get(user=request.user, used_order_id='', return_status=False)
        coupon_applied.used_order_id = order_id
        coupon_applied.save()                

        # Update 'Order' with 'id' of 'CouponHistory'
        coupon_applied = CouponHistory.objects.get(user=request.user, used_order_id=order_id, return_status=False)
        order.couponhistory_id = coupon_applied.pk
        order.save()

        # Increase the usage count in the Coupon model - When creating the order!
        coupon_applied.coupon.increase_usage_count()
       
        # Get the cart for the current user
        cart = Cart.objects.get(user=user)

        # Iterate over the cart items and create order items
        cart_items = cart.cartitem_set.all()
        
        for cart_item in cart_items:
            variant_price = cart_item.variant.price
            set_new_price = cart_item.new_price # Product Offer Discount Price
            if set_new_price is not None and set_new_price > 0.00:
                variant_price = set_new_price 

            order_item = OrderItem(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=variant_price 
                # added_at = models.DateTimeField(auto_now_add=True)
            )
            order_item.save()

            # Inventory Management
            # Reduce the quantity of the corresponding ProductVariant
            product_variant = cart_item.variant
            product_variant.quantity -= cart_item.quantity
            product_variant.save()       
        

        # Clear the cart after creating the order
        cart.cartitem_set.all().delete()        

        # Redirect to a success page or order details page
        return redirect(f'/order_success/{order_id}/')

        return HttpResponse("Order Placed!")
    
def order_success(request, order_id):
    # Retrieve the order object based on the order_id
    order = Order.objects.get(id=order_id)
    
    total = order.sub_total - order.coupon_discount + order.shipment_cost

    coupon_discount = coupon_code = None
    if order.couponhistory_id != '':
        applied_coupon = CouponHistory.objects.filter(used_order_id=order_id, return_status=False).exists()
        if applied_coupon:
            coupon_obj = CouponHistory.objects.get(used_order_id=order_id, return_status=False)
            coupon_code = coupon_obj.coupon.code
            coupon_discount = coupon_obj.coupon.discount

    # Render the order_success.html template and pass the order object to it
    return render(request, 'order_success.html', {'order': order, 'total': total, 'coupon_code': coupon_code, 'coupon_discount': coupon_discount})

################################
# SHOP PAGE - CATEGORY / PRODUCT
################################
def category_page(request, category_id):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    
    category = Category.objects.get(id=category_id)
    products = Product.objects.filter(category_id=category).exclude(is_blocked = True)
    images = ProductImage.objects.filter(product__in=products).order_by('product').distinct('product')
    # variant = ProductVariant.objects.filter(product__in=products).distinct('product')
    variant = None
    paginator = Paginator(images, 6)  # Display 10 products per page    
    page_number = request.GET.get('page')
    images = paginator.get_page(page_number)

    # variant_price = []
    # for obj in variant:
    #     variant_price.append(obj.price)
    # print("Varinat Prices: ", variant_price)
    
    # NAVBAR CAtegories Display
    categories = Category.objects.all().exclude(is_blocked = True)

    ##################
    # FILTER BY PRICE
    ##################
    
    dict_variant_prices = ProductVariant.objects.filter(product__in=products).values('price').distinct().order_by('price')    

    list_variant_price = []
    for price_key in dict_variant_prices:
        price = float(price_key['price'])
        list_variant_price.append(price_key['price'])
        max_price = max(list_variant_price)

    # print("List of Price =", list_variant_price)
    # print("MAX = ", max_price)

    set_max_range = max_price % 100
    if set_max_range == 0:
        max_range = max_price
    else:
        max_range = max_price + (100 - set_max_range)

    range_inc = 0
    price_range = []
    while(range_inc<max_range):
        price_range.append(range_inc)
        range_inc += 50    
    
    # Pass in Context. 'price_range'
    # print("Price Range = ", price_range)


    ################
    # FILTER BY SIZE
    ################
    
    variant_values = ProductVariant.objects.filter(product__in=products).values('variant_value', 'product__unit_of_measurement__unit')
    # print("All Variant Values = ",variant_values)
    
    # size_unit = variant_values.annotate(value_unit=F('variant_value') + F('product__unit_of_measurement__unit'))
    size_unit = variant_values.annotate(
        value_unit=Concat('variant_value', Value(' '), 'product__unit_of_measurement__unit'))
    # for i in size_unit:
    #     print("size_unit =", i['value_unit'])

    distinct_size_unit = size_unit.distinct()
    # print("Distinct Sizes = ", distinct_size_unit)
    # # Distinct Sizes =  <QuerySet [{'variant_value': '150', 'product__unit_of_measurement__unit': 'g', 'value_unit': '150 g'}, {'variant_value': '200', 'product__unit_of_measurement__unit': 'ml', 'value_unit': '200 ml'},

    variant_value_unit = distinct_size_unit.values('value_unit')
    # print("Dict of Distinct Sizes = ", variant_value_unit)
    # # Dict of Distinct Sizes =  <QuerySet [{'value_unit': '200 ml'}, {'value_unit': '150 g'}, {'value_unit': '300 g'}, {'value_unit': '150 ml'}, {'value_unit': '100 ml'}, {'value_unit': '300 ml'}]>

    list_variant_value_unit = []
    for item in variant_value_unit:
        list_variant_value_unit.append(item['value_unit'])
    # print("List of Distinct size with their unit =", list_variant_value_unit)
    # # List of Distinct size with their unit = ['200 ml', '150 g', '300 g', '150 ml', '100 ml', '300 ml']

    # Wishlist Check
        has_products_wishlist = False
        wishlist_count = 0
        product_ids = []
        try:
            wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
            has_products_wishlist = wishlist.products.exists()
            if has_products_wishlist:
                products_wishlist = wishlist.products.all()
                wishlist_count = wishlist.products.count()                
                for obj in products_wishlist:
                    product_ids.append(obj.product_id)

                # print("Wishlist have product!")
                # print(product_ids)
        except:
            has_products_wishlist = False


    context = {
        'username': username,
        'category': category,
        'images': images,
        'products':products,
        'categories': categories,
        'list_of_sizes': list_variant_value_unit,
        'price_range': price_range,
        'variant': variant,
        'has_products_wishlist': has_products_wishlist,
        'product_ids': product_ids,
        'wishlist_count': wishlist_count

    }

    return render(request, 'category_page.html', context)

def product_detail(request, product_id):
    username = None
    warn_message = None
    success_message = None
    context = {}
    if request.user.is_authenticated:
        username = request.user.username
        success_message = "Hey! select the size and Add to the Cart!"
    else:
        warn_message = "Aww! You shall Sign-in to own a cart"

    product_obj = Product.objects.get(product_id=product_id)    
    images_list = ProductImage.objects.filter(product=product_id)
    product_unit = product_obj.unit_of_measurement    
    unit = product_unit.unit
    variant_obj = ProductVariant.objects.filter(product_id=product_obj.product_id).order_by('variant_value')
    context.update({'username': username, 'product_obj': product_obj, 
                    'images_list': images_list, 'variant_obj':variant_obj, 
                    'unit':unit, 'warn_message':warn_message, 
                    'success_message':success_message })
    
    # Check if the product has Offer
    product_has_offer = ProductOffer.objects.filter(product=product_obj).exists()
    if product_has_offer:
        product_Offer_obj = ProductOffer.objects.get(product=product_obj)
        discount_percent = product_Offer_obj.discount_percentage
        discount_multiple = product_Offer_obj.discount_percentage / 100
        context.update({'product_has_offer': product_has_offer, 'discount_percent': discount_percent, 
                        'discount_multiple': discount_multiple})
    
    return render(request, 'product_detail.html', context)

