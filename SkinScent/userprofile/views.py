from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse

# OTP Login
from django.core.mail import send_mail
from random import randint
from twilio.rest import Client

# Password Reset
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout

from .models import *
from shop.models import *

################
# PASSWORD RESET
################
@login_required
def forgot_pass(request):
    logout(request)
    return redirect('/authapp/email_otp/')


@login_required
def verify_reset_pass(request):
    if request.method == 'POST':
        password_now = request.POST.get('password_now')
        
        # Get the currently logged-in user
        user = request.user

        # Authenticate the user with the provided password
        authenticated_user = authenticate(username=user.username, password=password_now)

        if authenticated_user is not None:
            # Password is correct, continue with the password reset process
            success_message = "Verified! Fill the form to reset password."
            
            # Redirect the user to the password reset page
            return render(request, 'userprofile/user_resetpass.html', {'success_message': success_message})           
            
        else:
            # Password is incorrect, display an error message to the user
            error_message = 'Incorrect Password! Please try again.'
            return render(request, 'userprofile/user_resetpass_prepend.html', {'error_message': error_message})           
        

    return render(request, 'userprofile/user_resetpass_prepend.html')

@login_required
def reset_pass(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password == confirm_password:
            # Check password format
            password = new_password
            if len(password) < 8:
                error_message = 'Password must be at least 8 characters long.'                
                return render(request, 'userprofile/user_resetpass.html', {'error_message':error_message})
            if not any(char.isdigit() for char in password):
                error_message = 'Password must contain at least one digit.'                
                return render(request, 'userprofile/user_resetpass.html', {'error_message':error_message})
            if not any(char.isalpha() for char in password):
                error_message = 'Password must contain at least one letter.'                
                return render(request, 'userprofile/user_resetpass.html', {'error_message':error_message})
            user = request.user
            user.set_password(new_password)
            user.save()

            message = 'Password reset successful!'            
            return render(request, 'userprofile/user_messagepage.html', {'message':message})
            
        else:            
            error_message = 'Passwords do not match!'
            return render(request, 'userprofile/user_resetpass.html', {'error_message':error_message})
    
    error_message = None
    return render(request, 'userprofile/user_resetpass.html', {'error_message':error_message})

#####################
# MOBILE REGISTRATION
#####################
def generate_otp():
    return str(randint(100000, 999999))

def send_otp_via_sms(phone_number, otp):
    # Replace these values with your actual Twilio credentials
    account_sid = 'AC6f04adb8fab15476c44fee0b6919fea5'
    auth_token = 'b4853f0fa6faf48328ccf9976edc48dd'
    twilio_phone_number = '+19382014096'

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f'Your OTP is: {otp}',
        from_=twilio_phone_number,
        to=phone_number
    )

    return message.sid

@login_required
def send_otp(request):
    flag = False
    msg = None
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        phone_number = "+91" + phone_number
        # print("Phone_Number = ", phone_number)        
        otp = generate_otp()

        # Save the OTP to the user's session or database for verification later        
        request.session['otp'] = otp

        send_otp_via_sms(phone_number, otp)

        return redirect(f'/userprofile/verify-otp/{phone_number}')
        # return HttpResponse('OTP sent successfully!')
    return render(request, 'userprofile/user_mobile_otp.html', {'error_message' : msg, 'flag' : flag})

@login_required
def verify_otp(request, new_contact):
    flag = True
    msg = f'OTP has been sent to {new_contact}!'
    if request.method == 'POST':
        otp = request.POST.get('otp')
        # print("Input OTP =", otp)        

        # retrieve OTP from user's session
        stored_otp = request.session.get('otp')
        # print("Stored OTP =", stored_otp)                

        if otp == stored_otp:
            # OTP verified
            
            # Save the Mobile as Registered Contact Number 
            user_profile = UserProfile.objects.get(user=request.user)
            try:                
                phone, created = ContactMobile.objects.get_or_create(user_profile=user_profile)
                message = "OTP Verified! Successfully updated your Phone Number."
                phone.mobile_number = new_contact
                phone.save()
                return render(request, 'userprofile/user_messagepage.html', {'message': message})

            except ContactMobile.DoesNotExist:            
                return HttpResponse("Error Occured With 'ContactMobile' Model!!!")
        else:
            msg = 'Invalid OTP'
            return render(request, 'userprofile/user_mobile_otp.html', {'error_message' : msg, 'flag' : flag})

    return render(request, 'userprofile/user_mobile_otp.html', {'success_message' : msg, 'flag' : flag, 'new_contact': new_contact})


#############
# USER WALLET
#############
@login_required
def my_wallet(request):
    user = request.user
    user_wallet, created = Wallet.objects.get_or_create(user=user)
    context = {'user': user,
               'user_wallet': user_wallet}
    username = request.user.username
    context.update({'username': username})
    return render(request, 'userprofile/user_wallet.html', context)


##################
# ORDER MANAGEMENT
##################

# ORDER DETAIL
@login_required
def my_order_detail(request, order_id):
    user = request.user
    order = Order.objects.get(pk=order_id)

    total = order.sub_total - order.coupon_discount + order.shipment_cost

    coupon_discount = coupon_code = None
    if order.couponhistory_id != '':
        applied_coupon = CouponHistory.objects.filter(used_order_id=order_id, return_status=False).exists()
        if applied_coupon:
            coupon_obj = CouponHistory.objects.get(used_order_id=order_id, return_status=False)
            coupon_code = coupon_obj.coupon.code
            coupon_discount = coupon_obj.coupon.discount

    track_order, _ = TrackOrder.objects.get_or_create(user=user, order=order)
    context = {}
    context.update({'order': order, 'track_order': track_order, 'total': total, 'coupon_code': coupon_code, 'coupon_discount': coupon_discount})
    username = request.user.username
    context.update({'username': username})
    return render(request, 'userprofile/user_order_detail.html', context)

# ORDER SUMMARY
@login_required
def my_orders(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('created_at')

    context = {'orders': orders}
    username = request.user.username
    context.update({'username': username})

    return render(request, 'userprofile/user_orders.html', context)

@login_required
def order_cancellation(request, order_id):
    user = request.user
    if request.method == 'POST':
        # print("Posting for Cancellation...")
        order = Order.objects.get(id=order_id)

        # Update stock for each canceled order item
        for order_item in order.orderitem_set.all():
            # print("Adding Back to Stock!")
            product_variant = order_item.variant
            product_variant.quantity += order_item.quantity
            product_variant.save()
            
        # Flag as cancelled
        order.fulfillment_status = 'Cancelled'
        order.save()
        # print("Cancelled!")

        if order.payment_method == 'razorpay':
            # Make Refund of the amount to wallet
            user_wallet, created = Wallet.objects.get_or_create(user=user)
            refund_amount = order.get_cart_total()
            user_wallet.balance += refund_amount
            user_wallet.save()
            msg = "The Amount Paid has been refunded. Check your Wallet in Userprofile!"
            user_orders = Order.objects.filter(user=user)
            return render(request, 'userprofile/user_orders.html', {'orders': user_orders, 'error_message': msg})

        return redirect('/userprofile/my_orders/')  # Redirect to the profile page or any other desired page
    else:
        return redirect('/userprofile/my_orders/')    

def order_refund(request, order_id):
    if request.method == 'POST':
        # print("Posting for Refund...")
        order = Order.objects.get(id=order_id)

####################
# ADDRESS MANAGEMENT
####################

# REMOVE ADDRESS
@login_required
def remove_address(request, address_pk):
    address = get_object_or_404(Address, pk=address_pk)
    address.delete()
    return redirect('/userprofile/list_address/')
    
# EDIT ADDRESS
@login_required
def edit_address(request, address_pk):
    address = get_object_or_404(Address, pk=address_pk)
    
    if request.method == 'POST':
        # Retrieve form data from the request
        addressee = request.POST.get('addressee')
        address_line1 = request.POST.get('address_line1')
        street = request.POST.get('street')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        pin_code = request.POST.get('pin_code')
        is_default = is_default = request.POST.get('is_default')

        # Update the address object with the new data
        address.addressee = addressee
        address.address_line1 = address_line1
        address.street = street
        address.city = city
        address.state = state
        address.country = country
        address.pin_code = pin_code
        address.save()

        if is_default:
            user_profile = address.user_profile
            # Update the DefaultAddress for the current UserProfile        
            default_address = DefaultAddress.objects.filter(user_profile=user_profile).first()

            if default_address:
                # Update existing default address
                default_address.address = address
                default_address.save()
            else:
                # Create new default address
                DefaultAddress.objects.create(user_profile=user_profile, address=address)

        return redirect('/userprofile/list_address/')

    context = {
        'address': address,
    }
    username = request.user.username
    context.update({'username': username})
    return render(request, 'userprofile/user_address_edit.html', context)


# LIST ADDRESS
@login_required
def list_address(request):
    user_profile = request.user.userprofile
    addresses = Address.objects.filter(user_profile=user_profile)

    default_address = DefaultAddress.objects.filter(user_profile=user_profile).first()

    context = {
        'addresses': addresses,
        'default_address': default_address,
    }
    username = request.user.username
    context.update({'username': username})
    return render(request, 'userprofile/user_address_list.html', context)
    
# ADD ADDRESS
@login_required
def add_address(request):
    if request.method == 'POST':
        user_profile = request.user.userprofile
        # Retrieve form data from the request
        addressee = request.POST.get('addressee')
        address_line1 = request.POST.get('address_line1')
        street = request.POST.get('street')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        pin_code = request.POST.get('pin_code')
        is_default = request.POST.get('is_default')

        # Create a new Address object
        address = Address.objects.create(
            user_profile=user_profile,
            addressee=addressee,
            address_line1=address_line1,
            street=street,
            city=city,
            state=state,
            country=country,
            pin_code=pin_code
        )

        if is_default:
            # Update the DefaultAddress for the current UserProfile        
            default_address = DefaultAddress.objects.filter(user_profile=user_profile).first()

            if default_address:
                # Update existing default address
                default_address.address = address
                default_address.save()
            else:
                # Create new default address
                DefaultAddress.objects.create(user_profile=user_profile, address=address)

        return redirect('/userprofile/list_address/')
    username = request.user.username    
    return render(request, 'userprofile/user_address_add.html', {'username': username})

############
# MY PROFILE
############
@login_required
def myprofile(request):
    # Get the current user
    user = request.user    
    
    display_default_address = None

    # POST
    if request.method == 'POST':
        # Get the form data from the request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')        

        # Update the user profile or create a new one if it doesn't exist
        try:
            user_profile = UserProfile.objects.get(user=user)
            user_profile.first_name = first_name
            user_profile.last_name = last_name
            user_profile.dob = dob
            user_profile.save()
        except UserProfile.DoesNotExist:
            user_profile = UserProfile(user=user, first_name=first_name, last_name=last_name, dob=dob)
            user_profile.save()
            return redirect('/userprofile/')            

    # GET
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    context = {'user_profile': user_profile}
    # print(context)
    try:
        phone = ContactMobile.objects.get(user_profile=user_profile)
        context.update({'phone': phone})
        # print(context)
       
    except ContactMobile.DoesNotExist:        
        # print("No registered Mobile Number!")
        # print(context)
        pass
    
    try:                
        default_address = DefaultAddress.objects.filter(user_profile=user_profile).first()

        if default_address is not None:
            display_default_address = f'{default_address.address.addressee}, {default_address.address.address_line1}, {default_address.address.street}, {default_address.address.city}, {default_address.address.state}, {default_address.address.country}, PINCODE:{default_address.address.pin_code} '
        
        context.update({'display_default_address': display_default_address})
        # print(context)

    except DefaultAddress.DoesNotExist:
        # print("No Default Address!")
        # print(context)
        pass

    wishlist_count = 0
    if request.user.is_authenticated:
        username = request.user.username

        user = request.user
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        # Get the updated count of products in the wishlist for the specific product
        wishlist_count = wishlist.products.count()
        context.update({'wishlist_count': wishlist_count})
        context.update({'username': username})        
            
    return render(request,'userprofile/user_home.html', context) 