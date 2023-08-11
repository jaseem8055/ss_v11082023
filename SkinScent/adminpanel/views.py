
import datetime
from django.contrib import messages


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse

# Category 
from django.utils.text import slugify
from .models import *
from django.core.paginator import Paginator

#Slug Conflict
from django.db import IntegrityError

# User
from django.contrib.auth.models import User

#Order
from shop.models import *
from django.utils import timezone

# Coupon
from django.utils.dateparse import parse_datetime

# Create your views here.

############################
###### ADMIN DASHBOARD #####
############################
def admin_home(request):
    if request.user.is_authenticated and request.user.is_superuser:        
        adminname = request.user.username

        distinct_years = Order.objects.dates('created_at', 'year', order='DESC').distinct()
        distinct_months = Order.objects.dates('created_at', 'month', order='DESC').distinct()

        context = {
            'distinct_years': distinct_years,
            'distinct_months': distinct_months
        }

        context.update({'username':adminname})
        
        return render(request, 'adminpanel/admin_home.html', context)
    else:
        logout(request)
        return redirect('/adminpanel/admin_signin/')

def admin_signin(request):
    if request.user.is_authenticated:
        adminname = request.user.username
        return render(request, 'adminpanel/admin_home.html', {'username':adminname})
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            # Redirect to the admin dashboard or desired page
            return redirect('/adminpanel/')

        # If user is not authenticated or not a superuser, display an error message
        error_message = 'Invalid credentials for admin login.'
        return render(request, 'adminpanel/a_signin.html', {'error_message': error_message})

    # If it's a GET request, render the login form
    return render(request, 'adminpanel/a_signin.html')

def admin_logout(request):
    logout(request)
    return redirect('/adminpanel/')


################
# SALES REPORT #
################
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph

from io import BytesIO

from django.db.models import Sum
from reportlab.lib.styles import getSampleStyleSheet

import calendar
from reportlab.platypus.doctemplate import PageBreak

# Yearly Sales Report - NOT USED
def generate_monthly_sales_report_pdf(request, year=None):
    from datetime import datetime    
    # If year is not provided, use the current year
    if year is None:
        year = datetime.now().year

    # Query to retrieve monthly sales data
    monthly_sales = Order.objects.annotate(month=ExtractMonth('created_at'))\
        .filter(created_at__year=year)\
        .values('month')\
        .annotate(total_sales=Sum('sub_total'))\
        .order_by('month')

    # Create a response object with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="monthly_sales_report_{year}.pdf"'

    # Create a buffer for the PDF content
    buffer = BytesIO()

    # Create a PDF document using reportlab
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Title Font
    title_font_style = getSampleStyleSheet()["Title"]
    title_text = f"Monthly Sales Report - {year}"
    elements.append(Paragraph(title_text, title_font_style))
    elements.append(Paragraph("<br/><br/>", title_font_style))  # Add some space after the title

    # Body Font
    normal_font_style = getSampleStyleSheet()["Normal"]

    # Add content to the PDF with proper formatting
    for entry in monthly_sales:
        month_number = entry['month']
        month_name = calendar.month_name[month_number]
        total_sales = entry['total_sales']
        elements.append(Paragraph(f"{month_name}: {total_sales}", normal_font_style))

    # Build the PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

# Daily Sales Report
def generate_sales_report_pdf(request, year=None, month=None):
    from datetime import datetime

    # GET from Sales Report Form at "admin_home.html"
    year = int(request.GET.get('year'))
    month = int(request.GET.get('month'))   
        
    # If year and month are not provided, use the current year and month
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
        

    # Query to retrieve monthly sales data
    monthly_sales = Order.objects.annotate(year=ExtractYear('created_at'),
                                           month=ExtractMonth('created_at'))\
        .filter(created_at__year=year, created_at__month=month)\
        .values('year', 'month')\
        .annotate(total_sales=Sum('sub_total'))\
        .order_by('year', 'month')

    # Query to retrieve daily sales data within the specified month
    daily_sales = Order.objects.annotate(year=ExtractYear('created_at'),
                                         month=ExtractMonth('created_at'),
                                         day=ExtractDay('created_at'))\
        .filter(created_at__year=year, created_at__month=month)\
        .values('year', 'month', 'day')\
        .annotate(total_sales=Sum('sub_total'))\
        .order_by('year', 'month', 'day')
    
    # Query to retrieve individual orders for the specified month and year
    orders = Order.objects.filter(created_at__year=year, created_at__month=month)


    # Create a response object with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{year}_{month}.pdf"'

    # Create a buffer for the PDF content
    buffer = BytesIO()

    # Create a PDF document using reportlab
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Title Font
    title_font_style = getSampleStyleSheet()["Title"]
    title_text = f"Sales Report - {calendar.month_name[month]} {year}"
    elements.append(Paragraph(title_text, title_font_style))
    # elements.append(Paragraph("<br/><br/>", title_font_style))  # Add some space after the title

    # Sub-Title
    # Define a style for sub-titles
    subtitle_font_style = getSampleStyleSheet()["Heading2"]
    # subtitle_font_style.alignment = 1  # Center alignment
    subtitle_font_style.fontSize = 12
    subtitle_font_style.leading = 20

    # Body Font
    normal_font_style = getSampleStyleSheet()["Normal"]

    # Add monthly sales content to the PDF
    elements.append(Paragraph("Monthly Sales:", subtitle_font_style))
    for entry in monthly_sales:
        total_sales = entry['total_sales']
        elements.append(Paragraph(f"Total Sales: {total_sales}", normal_font_style))

    # Add a page break to separate monthly and daily sales
    #elements.append(PageBreak())

    # Add space between monthly and daily sales sections
    elements.extend([Paragraph("<br/><br/>", normal_font_style) for _ in range(3)])  # Add 3 empty lines


    # Add daily sales content to the PDF
    elements.append(Paragraph("Daily Sales:", subtitle_font_style))
    for entry in daily_sales:
        day = entry['day']
        total_sales = entry['total_sales']
        elements.append(Paragraph(f"Day {day}: Total Sales: {total_sales}", normal_font_style))

    # Add space before the Order Summary section
    elements.extend([Paragraph("<br/><br/>", normal_font_style) for _ in range(3)])  # Add 3 empty lines

    # Add Order Summary section
    elements.append(Paragraph("Order Summary:", subtitle_font_style))
    for order in orders:
        elements.append(Paragraph(f"Order Number: {order.order_number}", normal_font_style))
        elements.append(Paragraph(f"Shipping Address: {order.shipping_address}", normal_font_style))
        elements.append(Paragraph(f"Total Amount: {order.sub_total}", normal_font_style))
        elements.append(Paragraph("--------------<br/>", normal_font_style))

    # Build the PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

####################################################
####################### OFFERS #####################
####################################################

# OFFER TITLES #
################
def edit_offer(request, offer_id):
    # Fetch the Offer object using the offer_id passed in the URL
    offer = get_object_or_404(Offer, pk=offer_id)

    if request.method == 'POST':
        # Handle form submission for updating the Offer object
        name = request.POST['name']
        start_date = parse_datetime(request.POST['start_date'])
        end_date = parse_datetime(request.POST['end_date'])
        active = bool(request.POST.get('active', False))

        # Check if any of the required fields are missing or empty
        if not name or not start_date or not end_date:
            error_message = "All fields are required."
            return render(request, 'adminpanel/a_offer_create.html', {'error_message': error_message})

         # Check if start_date is after end_date
        if start_date > end_date:
            error_message = " 'Start Date' cannot be after 'End Date' "
            messages.error(request, error_message)               
            return redirect('adminpanel:edit_offer', offer_id=offer_id)

        # Check if there's an active offer with the same name
        active_offer_with_same_name = Offer.objects.filter(name=name, active=True).exclude(pk=offer_id).exists()

        if active and active_offer_with_same_name:
            error_message = "An active offer with the same name already exists."
            return render(request, 'adminpanel/a_offer_edit.html', {'error_message': error_message})

        offer.name = name
        offer.start_date = start_date
        offer.end_date = end_date
        offer.active = active
        offer.save()

        # Redirect to a page displaying the updated offer or any other desired page
        return redirect('adminpanel:offers')

    # Render the form to display the current data for editing
    return render(request, 'adminpanel/a_offer_edit.html', {'offer': offer})

def create_offer(request):
    if request.method == 'POST':
        name = request.POST['name']
        start_date = parse_datetime(request.POST['start_date'])         
        end_date = parse_datetime(request.POST['end_date'])
        active = bool(request.POST.get('active', False))        

        # Check if any of the required fields are missing or empty
        if not name or not start_date or not end_date:
            error_message = "All fields are required."
            return render(request, 'adminpanel/a_offer_create.html', {'error_message': error_message})


        # Check if start_date is after end_date
        if start_date > end_date:
            error_message = " 'Start Date' cannot be after 'End Date' "
            return render(request, 'adminpanel/a_offer_create.html', {'error_message': error_message})      



         # Check if there's an active offer with the same name
        active_offer_with_same_name = Offer.objects.filter(name=name, active=True).exists()

        if active and active_offer_with_same_name:
            error_message = "An active offer with the same name already exists."
            return render(request, 'adminpanel/a_offer_create.html', {'error_message': error_message})

        offer = Offer.objects.create(name=name, start_date=start_date, end_date=end_date, active=active)
        return redirect('adminpanel:offers')
    
    return render(request, 'adminpanel/a_offer_create.html')

def offers(request):
    adminname = None
    if request.user.is_authenticated:
        if request.user.is_superuser:
            adminname = request.user.username
        else:
            return redirect('adminpanel:admin_home')
    
    current_datetime = timezone.now()

    existing_offers = Offer.objects.filter(start_date__lte=current_datetime, end_date__gte=current_datetime, active=True)
    upcoming_offers = Offer.objects.filter(start_date__gt=current_datetime, active=True)
    expired_offers = Offer.objects.filter(end_date__lt=current_datetime, active=True)
    deactivated_offers = Offer.objects.filter(active=False)

    context = {
        'existing_offers': existing_offers,
        'upcoming_offers': upcoming_offers,
        'expired_offers': expired_offers,
        'deactivated_offers': deactivated_offers,
    }

    return render(request, 'adminpanel/a_offers.html', context)


# PRODUCT OFFER #
#################
def create_product_offer(request):    
    products = Product.objects.all().exclude(is_blocked=True) # All Products
    product_offer_exists = ProductOffer.objects.all().exists()
    if product_offer_exists:
        # Get a list of Products with Active Offer
        products_with_offer = ProductOffer.objects.filter(product__in = products, active=True).values_list('product', flat=True)
        products = products.exclude(pk__in=products_with_offer) # Exclude Products with Offer
    
    current_datetime = timezone.now()
    offers = Offer.objects.all().exclude(active=False, end_date__lt=current_datetime) # Existing Offers
    context = {
        'products': products,
        'offers': offers,        
    }

    if request.method == 'POST':
        offer_id = request.POST.get('offer')
        product_id = request.POST.get('product')
        discount_percentage = int(request.POST.get('discount_percentage', 0))
        start_date = parse_datetime(request.POST.get('start_date'))
        end_date = parse_datetime(request.POST.get('end_date'))
        active = bool(request.POST.get('active', False))   

        # Check if any of the required fields are missing or empty
        if not discount_percentage or not start_date or not end_date:
            error_message = "All fields are required."
            context.update({'error_message': error_message})
            return render(request, 'adminpanel/a_offer_product_create.html', context)     

        # Check if start_date is after end_date
        if start_date > end_date:
            error_message = " 'Start Date' cannot be after 'End Date' "
            context.update({'error_message': error_message})
            return render(request, 'adminpanel/a_offer_product_create.html', context)

        # Check if there's an active offer with the same name
        offer_product = Product.objects.get(pk=product_id)
        active_offer_with_same_name = ProductOffer.objects.filter(product=offer_product, active=True).exists()

        if active and active_offer_with_same_name:
            error_message = "An active offer with the same Product already exists."
            context.update({'error_message': error_message})
            return render(request, 'adminpanel/a_offer_product_create.html', context)

        # Create the object in ProductOffer
        offer_title = Offer.objects.get(pk=offer_id)
        product_offer = ProductOffer.objects.create(
                offer=offer_title,
                product=offer_product,
                discount_percentage=discount_percentage,
                start_date=start_date,
                end_date=end_date,
                active=active,
            )        

        return redirect('adminpanel:product_offers')
           
    return render(request, 'adminpanel/a_offer_product_create.html', context)

from datetime import timedelta

def product_offers(request):
    adminname = None
    if request.user.is_authenticated:
        if request.user.is_superuser:
            adminname = request.user.username
        else:
            return redirect('adminpanel:admin_home')

    # UTC to IST difference
    hours_to_add = 5
    minutes_to_add = 30

    # Calculate the timedelta with the specified hours and minutes
    time_delta = timedelta(hours=hours_to_add, minutes=minutes_to_add)
    IST_local = timezone.now() + time_delta

    # Get all active offers
    # Fetch Existing Offer (Active=True, End_Date > Today, and Start_Date <= Today)
    active_offers = Offer.objects.filter(active=True, end_date__gt=IST_local, start_date__lte=IST_local)
    context = {}    
    
    # Create a dictionary to store offer-product offer pairs
    offer_dict = {}

    # Fetch product offers for each active offer and group them in the dictionary
    for offer in active_offers:
        product_offers = ProductOffer.objects.filter(offer=offer, active=True)
        # Period of the Product is not taken into Account - The period = Offer Period
        if product_offers:
            offer_dict[offer] = product_offers
    context.update( {'offer_dict': offer_dict} )
        
    
    # Fetch Upcoming Offer (Active=True and Start_Date > Today)
    upcoming_active_offers = Offer.objects.filter(active=True, start_date__gt=IST_local,)
    upcoming_offer_dict = {}
    for offer in upcoming_active_offers:
        upcoming_product_offers = ProductOffer.objects.filter(offer=offer, active=True)
        # Period of the Product is not taken into Account - The period = Offer Period
        if upcoming_product_offers:
            upcoming_offer_dict[offer] = upcoming_product_offers
    context.update( {'upcoming_offer_dict': upcoming_offer_dict} )
    
    
    # Fetch Expired Offer (Active=True and End_Date <= Today)
    expired_active_offers = Offer.objects.filter(active=True, end_date__lte=IST_local,)    
    expired_offer_dict = {}
    for offer in expired_active_offers:
        expired_product_offers = ProductOffer.objects.filter(offer=offer, active=True)
        # Period of the Product is not taken into Account - The period = Offer Period
        if expired_product_offers:
            expired_offer_dict[offer] = expired_product_offers
    context.update( {'expired_offer_dict': expired_offer_dict} )
      
    
    # Fetch Inactive Offer (Active=False)
    inactive_offers = Offer.objects.filter(active=False)
    inactive_offer_dict = {}
    for offer in inactive_offers:
        inactive_product_offers = ProductOffer.objects.filter(offer=offer)
        # Period of the Product is not taken into Account - The period = Offer Period
        if inactive_product_offers:
            inactive_offer_dict[offer] = inactive_product_offers
    context.update( {'inactive_offer_dict': inactive_offer_dict} )

    page_loaded_at = IST_local
    context.update( {'page_loaded_at': page_loaded_at} )

    return render(request, 'adminpanel/a_offer_product.html', context )

def edit_product_offer(request, pk):
    product_offer = get_object_or_404(ProductOffer, pk=pk)

    products = Product.objects.all().exclude(is_blocked=True) # All Products
    product_offer_exists = ProductOffer.objects.all().exists()
    if product_offer_exists:
        # Get a list of Products with Active Offer
        products_with_offer = ProductOffer.objects.filter(product__in = products, active=True).exclude(pk=pk).values_list('product', flat=True)
        products = products.exclude(pk__in=products_with_offer) # Exclude Products with Offer        
    
    # UTC to IST difference
    hours_to_add = 5
    minutes_to_add = 30

    # Calculate the timedelta with the specified hours and minutes
    time_delta = timedelta(hours=hours_to_add, minutes=minutes_to_add)
    IST_local = timezone.now() + time_delta
    current_datetime = IST_local

    offers = Offer.objects.all().exclude(active=False, end_date__lt=current_datetime) # Existing Offers
    context = {
        'products': products,
        'offers': offers,   
        'product_offer': product_offer     
    }

    if request.method == 'POST':
        # Process the form submission to update the ProductOffer object
        offer_id = request.POST.get('offer')
        product_id = request.POST.get('product')
        discount_percentage = int(request.POST.get('discount_percentage', 0))
        start_date = parse_datetime(request.POST.get('start_date'))
        end_date = parse_datetime(request.POST.get('end_date'))
        active = bool(request.POST.get('active', False))   

        # Check if any of the required fields are missing or empty
        if not offer_id or not product_id or not discount_percentage or not start_date or not end_date:
            error_message = "All fields are required."
            context.update({'error_message': error_message})
            return render(request, 'adminpanel/a_offer_product_edit.html', context)     

        # Check if start_date is after end_date
        if start_date > end_date:
            error_message = " 'Start Date' cannot be after 'End Date' "
            context.update({'error_message': error_message})
            return render(request, 'adminpanel/a_offer_product_edit.html', context)

        # Check if there's an active offer with the same name
        offer_product = product_offer.product
        active_offer_with_same_name = ProductOffer.objects.filter(product=offer_product, active=True).exclude(pk=pk).exists()

        if active and active_offer_with_same_name:
            error_message = "An active offer with the same Product already exists."
            context.update({'error_message': error_message})
            return render(request, 'adminpanel/a_offer_product_edit.html', context)

        # Update the fields of the ProductOffer object
        offer_title = Offer.objects.get(pk=offer_id)
        offer_product = Product.objects.get(pk=product_id)
        product_offer.offer=offer_title
        product_offer.product=offer_product
        product_offer.discount_percentage = discount_percentage
        product_offer.start_date = start_date
        product_offer.end_date = end_date
        product_offer.active = active
        product_offer.save()

        return redirect('adminpanel:product_offers')
    
    # If it's a GET request, display the edit form with existing data    
    return render(request, 'adminpanel/a_offer_product_edit.html', context)    




#######
# GRAPH
#######
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay
from django.db.models import Count, F, Sum, Avg
from utils.charts import months, colorPrimary, colorSuccess, colorDanger, generate_color_palette, get_year_dict, get_user_dict

def orders_data(request):
    # Fetch order data, you might want to filter it based on date range or other criteria
    orders = Order.objects.all()

    # Perform necessary data aggregation to get order counts per date
    # Example: Suppose you have a 'created_at' field in the Order model
    dates = orders.values_list('created_at', flat=True)  # Get all created_at dates
    order_counts = orders.count()  # Get the count of orders

    # Perform necessary data aggregation to get order counts per date
    # Example: Suppose you have a 'created_at' field in the Order model
    orders_by_date = orders.values('created_at').annotate(order_count=Count('id'))


    # Prepare the data as a dictionary
    data = {
        'dates': [order['created_at'] for order in orders_by_date],
        'order_counts': [order['order_count'] for order in orders_by_date],
    }
    
    return JsonResponse(data)

def get_filter_options(request):
    grouped_purchases = Order.objects.annotate(year=ExtractYear("created_at")).values("year").order_by("-year").distinct()
    options = [purchase["year"] for purchase in grouped_purchases]

    return JsonResponse({
        "options": options,
    })

def get_sales_chart(request, year):
    purchases = Order.objects.filter(created_at__year=year)
    # grouped_purchases = purchases.annotate(price=F("item__price")).annotate(month=ExtractMonth("time"))\
    #     .values("month").annotate(average=Sum("item__price")).values("month", "average").order_by("month")    
    
    # Group and calculate the total order sub_total for each month in the specified year.
    grouped_purchases = purchases.annotate(month=ExtractMonth("created_at")) \
                            .values("month") \
                            .annotate(total=Sum("sub_total")) \
                            .order_by("month")

    sales_dict = get_year_dict()
    
    for group in grouped_purchases:
        sales_dict[months[group["month"]-1]] = round(group["total"], 2)

    return JsonResponse({
        "title": f"Sales in {year}",
        "data": {
            "labels": list(sales_dict.keys()),
            "datasets": [{
                "label": "Amount (₹)",
                "backgroundColor": colorPrimary,
                "borderColor": colorPrimary,
                "data": list(sales_dict.values()),
            }]
        },
    })

def spend_per_customer_chart(request, year):
    purchases = Order.objects.filter(created_at__year=year)

    # Group order by user and calculate the sum of sub_total for each month in the specified year.
    grouped_purchases = purchases.annotate(month=ExtractMonth("created_at")) \
                            .values("user") \
                            .annotate(total=Sum("sub_total")) \
                            .order_by("month")
    
    
    users_dict = get_user_dict()
    
    users_dict_order = {}
    for group in grouped_purchases:        
        users_dict_order[users_dict.get(group["user"], "Default Value")] = 0

    
    # Iterate through the users_dict keys and update users_dict_order with total values
    for user_id, username in users_dict.items():
        if username in users_dict_order:  # Check if the username exists in users_dict_order
            for group in grouped_purchases:
                if group['user'] == user_id:
                    users_dict_order[username] = round(group['total'], 2)
                    break  # Break the inner loop once the total value is updated
    
    return JsonResponse({
        "title": f"Sales in {year}",
        "data": {
            "labels": list(users_dict_order.keys()),
            "datasets": [{
                "label": "Amount (₹)",
                "backgroundColor": colorPrimary,
                "borderColor": colorPrimary,
                "data": list(users_dict_order.values()),
            }]
        },
    })



def payment_success_chart(request, year):
    purchases = Order.objects.filter(created_at__year=year)

    return JsonResponse({
        "title": f"Payment success rate in {year}",
        "data": {
            "labels": ["Paid", "Pending"],
            "datasets": [{
                "label": "Number of Orders",
                "backgroundColor": [colorSuccess, colorDanger],
                "borderColor": [colorSuccess, colorDanger],
                "data": [
                    purchases.filter(payment_status='Paid').count(),
                    purchases.filter(payment_status='Pending').count(),
                ],
            }]
        },
    })

def payment_method_chart(request, year):
    purchases = Order.objects.filter(created_at__year=year)
    grouped_purchases = purchases.values("payment_method").annotate(count=Count("id"))\
        .values("payment_method", "count").order_by("payment_method")

    payment_method_dict = dict()

    PAYMENT_METHODS = [
        ("COD", "Cash On Delivery"),
        ("razorpay", "Razor Pay"),        
    ]

    for payment_method in PAYMENT_METHODS:
        payment_method_dict[payment_method[1]] = 0

    for group in grouped_purchases:
        payment_method_dict[dict(PAYMENT_METHODS)[group["payment_method"]]] = group["count"]

    return JsonResponse({
        "title": f"Payment method rate in {year}",
        "data": {
            "labels": list(payment_method_dict.keys()),
            "datasets": [{
                "label": "Payment Method",
                "backgroundColor": generate_color_palette(len(payment_method_dict)),
                "borderColor": generate_color_palette(len(payment_method_dict)),
                "data": list(payment_method_dict.values()),
            }]
        },
    })


def statistics_view(request):
    return render(request, "adminpanel/statistics.html", {})

###################
# COUPON MANAGEMENT
###################
def edit_coupon(request, coupon_id):
    # Get the specific coupon object using the coupon_id
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        # Get the updated values from the form
        code = request.POST['code']
        discount = float(request.POST['discount'])
        valid_from = parse_datetime(request.POST['valid_from'])
        valid_to = parse_datetime(request.POST['valid_to'])
        minimum_purchase = float(request.POST['minimum_purchase'])  # Add minimum purchase value from form
        active = bool(request.POST.get('active', False))

        # Update the coupon object with the new values
        coupon.code = code
        coupon.discount = discount
        coupon.valid_from = valid_from
        coupon.valid_to = valid_to
        coupon.minimum_purchase=minimum_purchase  # Save the minimum purchase value to the model
        coupon.active = active
        coupon.save()

        # Redirect to the coupon list page or any other relevant page
        return redirect('/adminpanel/coupon/')

    return render(request, 'adminpanel/a_coupon_edit.html', {'coupon': coupon})
 
def add_coupon(request):
    if request.method == 'POST':
        code = request.POST['code']
        discount = float(request.POST['discount'])
        valid_from = parse_datetime(request.POST['valid_from'])
        valid_to = parse_datetime(request.POST['valid_to'])
        minimum_purchase = float(request.POST['minimum_purchase'])  # Add minimum purchase value from form
        active = bool(request.POST.get('active', False))

        coupon = Coupon.objects.create(
            code=code,
            discount=discount,
            valid_from=valid_from,
            valid_to=valid_to,
            minimum_purchase=minimum_purchase,  # Save the minimum purchase value to the model
            active=active
        )

        return redirect('/adminpanel/coupon/')
        # return HttpResponse(f"Coupon '{coupon.code}' created successfully!") # You can redirect to another page if needed

    return render(request, 'adminpanel/a_coupon_add.html')

def list_coupon(request):
    # Get all active coupons (coupons that haven't expired yet)
    active_coupons = Coupon.objects.filter(valid_to__gte=date.today(), active = True)

    # Get all expired coupons
    expired_coupons = Coupon.objects.filter(valid_to__lt=date.today(), active = True)

    # Get all De-activated Coupons
    removed_coupons = Coupon.objects.filter(active = False)

    context = {
        'active_coupons': active_coupons,
        'expired_coupons': expired_coupons,
        'removed_coupons': removed_coupons,
    }    

    return render(request, 'adminpanel/a_coupon_list.html', context)

##################
# ORDER MANAGEMENT
##################
def change_delivery_status(request, order_id):
    user = request.user
    order = get_object_or_404(Order, id=order_id)
    track_order, _ = TrackOrder.objects.get_or_create(user=user, order=order)

    if request.method == 'POST':
        new_delivery_status = request.POST.get('delivery_status')
        if new_delivery_status:
            order.fulfillment_status = new_delivery_status

            # Update the corresponding date fields in TrackOrder based on the selected delivery status.
            if new_delivery_status == 'Shipped':
                track_order.shipped_date = timezone.now()
            elif new_delivery_status == 'Delivery Center':
                track_order.delivery_center_date = timezone.now()
            elif new_delivery_status == 'Delivered':
                track_order.delivered_date = timezone.now()

            order.save()
            track_order.save()
            
            go_url = "/adminpanel/order_detail/" + str(order_id) + "/"
            return redirect(go_url)

    return render(request, 'adminpanel/a_order_delivery.html', {'order': order, 'track_order': track_order})

def change_payment_status(request, order_id):

    # Get Order object for the 'order_id'
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
        }

    if order.payment_method != 'COD' and order.fulfillment_status != 'Cancelled':        
        try:
            razor_payment = RazorPayment.objects.get(order_id=order_id)
            context = {'order': order, 
                    'razor_payment': razor_payment,
                    }
        except RazorPayment.DoesNotExist:
            # Some Conflict Occured and failed to create Object for the Order in Razorpayment Model.
            # The case to be handled by DB Manager
            msg = "Data Error: Contact Database Manager for Order with ID: " + str(order_id) + " & " + " Order No." + order.order_number
            go_url = "/adminpanel/order_detail/" + str(order_id) + "/"
            return render(request, 'page404.html', {'message': msg, 'go_url': go_url}) 

    if request.method == 'POST':
        new_payment_status = request.POST.get('payment_status')
        if new_payment_status:
            order.payment_status = new_payment_status
            order.save()
            # Add any other logic you want to perform here after updating the payment status.
        go_url = "/adminpanel/order_detail/" + str(order_id) + "/"
        return redirect(go_url)

    return render(request, 'adminpanel/a_order_payment.html', context)

def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    context = {'order': order}
    return render(request, 'adminpanel/a_order_detail.html', context)

def order_summary(request):
    adminname = None
    if request.user.is_authenticated:
        if request.user.is_superuser:
            adminname = request.user.username
        else:
            return redirect('adminpanel:admin_home')
    
    orders = Order.objects.all()
    context = {'orders': orders}
    return render(request, 'adminpanel/a_orders_summary.html', context)



##########################
#### USERS MANAGEMENT ####
##########################
def list_user(request):
    adminname = None
    if request.user.is_authenticated:
        if request.user.is_superuser:
            adminname = request.user.username
        else:
            return redirect('adminpanel:admin_home')
    
    if request.user.is_authenticated:
        if request.user.is_superuser:
            adminname = request.user.username
            # context = {'login_user' : login_user}
            users_data=User.objects.all()
            return render(request,'adminpanel/a_users_list.html', {'users':users_data, 'username':adminname})
            
    return render(request,'adminpanel/a_signin.html')

def block_user(request, user_id):
    user = User.objects.get(pk=user_id)
    user.is_active = False
    user.save()

    # Redirect to a success page or another view
    return redirect('/adminpanel/list_users/')


def unblock_user(request, user_id):
    user = User.objects.get(pk=user_id)
    user.is_active = True
    user.save()

    # Redirect to a success page or another view
    return redirect('/adminpanel/list_users/')



##########################
### PRODUCT - VARIANTS ###
##########################
def add_variant(request, product_id):
    if request.method == 'POST':
        # Process the form data
        varied_by = request.POST.get('varied_by')
        variant_value = request.POST.get('variant_value')
        quantity = request.POST.get('quantity')
        price = request.POST.get('price')
        
        # Perform further actions with the form data, such as saving to the database
        # Create a new ProductVariant object
        variant = ProductVariant(
            product_id=product_id,
            varied_by=varied_by,
            variant_value=variant_value,
            quantity=quantity,
            price=price
        )

        # Save the variant object to the database
        variant.save()
        # Redirect to a success page or return an appropriate response
        return render(request, 'adminpanel/a_variant_success.html', {'product_id': product_id})
        
    
    # If the request method is GET, render the form template
    # return render(request, 'your_template.html')
    return HttpResponse("No Get Method")


from django.core.exceptions import ObjectDoesNotExist

def list_variant(request, product_id):
    adminname = None
    if request.user.is_authenticated:
        adminname = request.user.username
    
    products = Product.objects.get(pk=product_id)
    # variants = ProductVariant.objects.get(product_id=product_id)

    try:
        variants = ProductVariant.objects.filter(product_id=product_id)
        # Do something with the variant object
    except ObjectDoesNotExist:
    # Handle the case where no matching variant is found
    # For example, you can return an error message or redirect to another page
        # return HttpResponse("Product variant does not exist.")
        variants = None


    # paginator = Paginator(products, 10)  # Display 10 categories per page
    
    # page_number = request.GET.get('page')
    # products = paginator.get_page(page_number)

    return render(request, 'adminpanel/a_variant_list.html', {'product': products, 'variants':variants, 'username':adminname})


def start_product_variant(request):
    adminname = None
    if request.user.is_authenticated:
        if request.user.is_superuser:
            adminname = request.user.username
        else:
            return redirect('adminpanel:admin_home')
    
    products = Product.objects.all().order_by('pk')
    paginator = Paginator(products, 10)  # Display 10 categories per page
    
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'adminpanel/a_variant_products.html', {'products': products, 'username':adminname})


##########################
### PRODUCT MANAGEMENT ###
##########################
def list_product(request):    
    adminname = None
    if request.user.is_authenticated:
        if request.user.is_superuser:
            adminname = request.user.username
        else:
            return redirect('adminpanel:admin_home')
    
    products = Product.objects.all().order_by('pk')
    paginator = Paginator(products, 10)  # Display 10 categories per page
    
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)


    return render(request, 'adminpanel/a_product_list.html', {'products': products, 'username':adminname})

def add_product(request):
    # Below are required for the page
    categories = Category.objects.all().exclude(is_blocked=True)
    units = UnitOfMeasurement.objects.all()

    if request.method == 'POST':
        # Retrieve form data
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        unit_of_measurement_id = request.POST.get('unit_of_measurement')
        description = request.POST.get('description')
        
        # Prevent ERROR through for Unique Constraint for 'name'        
        has_product = Product.objects.filter(name=name).exists()
        if has_product:
            context = {
                        'categories': categories, 
                        'units': units,
                        'error_message': f"Product Name: '{name}' Already Exists! Choose another name."
                        }
            return render(request, 'adminpanel/a_product_add.html', context)
        else:            
            # Get the UnitOfMeasurement instance
            unit_of_measurement = get_object_or_404(UnitOfMeasurement, id=unit_of_measurement_id)
            category = get_object_or_404(Category, id=category_id)            

            # Create a new Product instance
            product = Product(
                name=name,
                category=category,
                unit_of_measurement=unit_of_measurement,
                description=description
            )
            product.save()
        
            # Handle uploaded images
            images = request.FILES.getlist('images')
            for image in images:                
                ProductImage.objects.create(product=product, image=image)
            
            # Redirect or perform further actions
            return redirect('/adminpanel/list_product/')
    
    # Render the form for GET request        
    return render(request, 'adminpanel/a_product_add.html', {'categories': categories, 'units': units})

def edit_product(request, product_id):
    categories = Category.objects.all()
    units = UnitOfMeasurement.objects.all()
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        # Handle the case where the product is not found
        # Redirect or show an error message
        return HttpResponse("Warning: The Product doesn't exist. Contact your DB Manager! ")

    # Fetch related images for the product
    images = ProductImage.objects.filter(product=product)

    
    # product = get_object_or_404(Product, pk=product_id)
    # images = product.images.all()

    if request.method == 'POST':
        # Retrieve form inputs
        name = request.POST['name']
        category_id = request.POST['category']
        unit_id = request.POST['unit']
        description = request.POST['description']
        new_images = request.FILES.getlist('new_images')  # Get the list of uploaded images
        
        # Prevent ERROR through for Unique Constraint for 'name'
        has_product = Product.objects.filter(name=name).exclude(pk=product_id).exists()
        
        if has_product:
            context = {
                        'categories': categories, 
                        'units': units,
                        'error_message': f"Product Name: '{name}' Already Exists! Choose another name.",
                        'product': product,
                        }            
            return render(request, 'adminpanel/a_product_edit.html', context)
        else:
            # Fetch the Category, unit instances based on the provided category name
            category = get_object_or_404(Category, id=category_id)
            unit = get_object_or_404(UnitOfMeasurement, id=unit_id)            
            
            # Update the product object
            product.name = name
            product.category = category
            product.unit_of_measurement = unit
            product.description = description
            product.save()
        
            if new_images:
                # Delete the existing images associated with the product
                product.images.all().delete()

                # Process the new images
                for image in new_images:
                    # Create a new ProductImage object and associate it with the product
                    product_image = ProductImage(product=product, image=image)
                    product_image.save()
            
            # Redirect to product list
            return redirect('/adminpanel/list_product/')
    
    return render(request, 'adminpanel/a_product_edit.html', {'product': product, 'images': images, 'categories': categories, 'units': units})

def block_product(request, product_id):
    if request.method == 'POST':
        product = Product.objects.get(pk=product_id)
        product.is_blocked = True
        product.save()

        # Redirect to a success page or another view
        return redirect('/adminpanel/list_product/')
    
    product = Product.objects.get(pk=product_id)
    
    return render(request, 'adminpanel/a_product_block.html', {'product': product})


############################
### CATEGORY MANAGEMENT ###
############################
def list_category(request):
    adminname = None
    if request.user.is_authenticated:
        if request.user.is_superuser:
            adminname = request.user.username
        else:
            return redirect('adminpanel:admin_home')

    all_categories = Category.objects.all().order_by('name')
    paginator = Paginator(all_categories, 10)  # Display 10 categories per page

    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)

    return render(request, 'adminpanel/a_category_list.html', {'categories': categories, 'username':adminname})

def add_category(request):
    adminname = None
    if request.user.is_authenticated:
        adminname = request.user.username
    if request.method == 'POST':
        category_name = request.POST['category_name']
        description = request.POST['description']
        # Handle uploaded images
        image = request.FILES.get('category_image')
        
        # Check if any required fields are empty
        if not category_name or not description or not image:
            context = {
                'error_message': "All fields are required.",
                'username': adminname
            }
            return render(request, 'adminpanel/a_category_add.html', context)


        # Prevent ERROR through for Unique Constraint for 'name'        
        has_product = Category.objects.filter(name=category_name).exists()
        
        if has_product:
            context = { 
                        'error_message': f"Category Name: '{category_name}' Already Exists! Choose another name.",
                        'username':adminname
                        }
            return render(request, 'adminpanel/a_category_add.html', context)
                
        # Generate the slug based on the category name
        slug_new = slugify(category_name)
        
        # Handle slug duplication
        slug_obj = Category.objects.all().filter(slug=slug_new)
        # if Category.objects.all().filter(slug=slug_new).exists():
        if slug_obj.exists():
            # If the slug already exists, append a unique identifier to the slug
            slug_new = f"{slug_new}-{slug_obj.count() + 1}"            
        
        try:
            # Create a new Category object
            category = Category(name=category_name, slug=slug_new, description=description, image=image)
            category.save()
        except IntegrityError:
            # Handle the case where another thread/process created a category with the same slug concurrently
            # You can choose to retry with a different slug or handle the error as per your application's logic
            # In this example, let's raise an exception to indicate the error
            raise IntegrityError("Failed to create category due to slug conflict. Please Use different Category Name.")
        # Redirect to a success page or another view
        return redirect('/adminpanel/list_cat/')
    
    return render(request, 'adminpanel/a_category_add.html', {'username':adminname})

def edit_category(request, category_id):
    cat_update = Category.objects.get(id=category_id)
    adminname = None
    if request.user.is_authenticated:
        adminname = request.user.username
    # category = get_object_or_404(Category, slug=slug)
    
    if request.method == 'POST':
        category_name = request.POST['category_name']
        description = request.POST['description']

        # Prevent ERROR through for Unique Constraint for 'name'        
        has_product = Category.objects.filter(name=category_name).exclude(pk=category_id).exists()
        
        if has_product:
            context = { 
                        'error_message': f"Category Name: '{category_name}' Already Exists! Choose another name.",
                        'username':adminname,
                        'category':cat_update
                        }
            return render(request, 'adminpanel/a_category_edit.html', context)
        
        # Generate the slug based on the category name
        slug = slugify(category_name)
        
        # Update the Category object with 'id = category_id'
        # category = Category(name=category_name, slug=slug, description=description)
        cat_update.name = category_name
        cat_update.slug = slug
        cat_update.description = description

        # Handle uploaded images (if the field exists in the form)
        if 'category_image' in request.FILES:
            image = request.FILES['category_image']
            cat_update.image = image

        # cat_update.image = new_image
        cat_update.save()        

        # Redirect to a success page or another view
        return redirect('/adminpanel/list_cat/')    
       
    return render(request, 'adminpanel/a_category_edit.html', {'username':adminname, 'category':cat_update})

def block_category(request, category_id):
    if request.method == 'POST':
        category = Category.objects.get(id=category_id)
        category.is_blocked = True
        category.save()

        # Redirect to a success page or another view
        return redirect('/adminpanel/list_cat/')
    
    category = Category.objects.get(id=category_id)
    
    return render(request, 'adminpanel/a_category_block.html', {'category': category})
