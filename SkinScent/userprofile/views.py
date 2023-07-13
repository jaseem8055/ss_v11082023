from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse

from .models import *
from shop.models import *


##################
# ORDER MANAGEMENT
##################

# ORDER DETAIL
def my_order_detail(request, order_id):
    order = Order.objects.get(pk=order_id)
    return render(request, 'userprofile/user_order_detail.html', {'order': order})

# ORDER SUMMARY
def my_orders(request):
    user = request.user
    orders = Order.objects.filter(user=user)

    return render(request, 'userprofile/user_orders.html', {'orders': orders})

def order_cancellation(request, order_id):
    if request.method == 'POST':
        print("POST...")
        order = Order.objects.get(id=order_id)

        # Update stock for each canceled order item
        for order_item in order.orderitem_set.all():
            print("Order Found")
            # product_variant = order_item.variant
            # product_variant.quantity += order_item.quantity
            # product_variant.save()
            
        # Flag as cancelled
        order.fulfillment_status = 'Cancelled'
        order.save()
        print("Cancelled!")
        return redirect('/userprofile/my_orders/')  # Redirect to the profile page or any other desired page
    else:
        return redirect('/userprofile/my_orders/')    

####################
# ADDRESS MANAGEMENT
####################

# REMOVE ADDRESS
def remove_address(request, address_pk):
    address = get_object_or_404(Address, pk=address_pk)
    address.delete()
    return redirect('/userprofile/list_address/')
    
# EDIT ADDRESS
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

    return render(request, 'userprofile/user_address_edit.html', context)


# LIST ADDRESS
def list_address(request):
    user_profile = request.user.userprofile
    addresses = Address.objects.filter(user_profile=user_profile)

    default_address = DefaultAddress.objects.filter(user_profile=user_profile).first()

    context = {
        'addresses': addresses,
        'default_address': default_address,
    }
    return render(request, 'userprofile/user_address_list.html', context)
    
# ADD ADDRESS
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

    return render(request, 'userprofile/user_address_add.html')

############
# MY PROFILE
############
def myprofile(request):
    # Get the current user
    user = request.user
    # User Profile is Blank
    context = None

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

    
    try:
        user_profile = UserProfile.objects.get(user=user)

    except UserProfile.DoesNotExist:
        user_profile = None
    
    if user_profile:                
        default_address = DefaultAddress.objects.filter(user_profile=user_profile).first()
        context = {
        'user_profile': user_profile,
        'default_address': default_address,
        }

    return render(request,'userprofile/user_home.html', context) 