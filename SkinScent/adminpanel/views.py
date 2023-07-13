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

# Create your views here.

############################
###### ADMIN DASHBOARD #####
############################
def admin_home(request):
    if request.user.is_authenticated and request.user.is_superuser:        
        adminname = request.user.username
        return render(request, 'adminpanel/admin_home.html', {'username':adminname})
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

# ORDER MANAGEMENT
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    context = {'order': order}
    return render(request, 'adminpanel/a_order_detail.html', context)


def order_summary(request):
    orders = Order.objects.all()
    context = {'orders': orders}
    return render(request, 'adminpanel/a_orders_summary.html', context)



##########################
#### USERS MANAGEMENT ####
##########################
def list_user(request):
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
        adminname = request.user.username
    
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
        adminname = request.user.username
    
    products = Product.objects.all().order_by('pk')
    paginator = Paginator(products, 10)  # Display 10 categories per page
    
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)


    return render(request, 'adminpanel/a_product_list.html', {'products': products, 'username':adminname})


def add_product(request):
    if request.method == 'POST':
        # Retrieve form data
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        unit_of_measurement_id = request.POST.get('unit_of_measurement')
        description = request.POST.get('description')
        
        # Get the UnitOfMeasurement instance
        unit_of_measurement = get_object_or_404(UnitOfMeasurement, id=unit_of_measurement_id)
        

        # Create a new Product instance
        product = Product(
            name=name,
            category_id=category_id,
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
    else:
        # Render the form for GET request
        categories = Category.objects.all()
        units = UnitOfMeasurement.objects.all()
        return render(request, 'adminpanel/a_product_add.html', {'categories': categories, 'units': units})


def edit_product(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        # Handle the case where the product is not found
        # Redirect or show an error message
        pass

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
        
        # Redirect to a success page or another view
        return redirect('/adminpanel/list_product/')  # Replace with the appropriate URL
    categories = Category.objects.all()
    units = UnitOfMeasurement.objects.all()
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
        adminname = request.user.username

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
            category = Category(name=category_name, slug=slug_new, description=description)
            category.save()
        except IntegrityError:
            # Handle the case where another thread/process created a category with the same slug concurrently
            # You can choose to retry with a different slug or handle the error as per your application's logic
            # In this example, let's raise an exception to indicate the error
            raise IntegrityError("Failed to create category due to slug conflict. Please Use different Category Name.")
        

        # # Create a new Category object
        # category = Category(name=category_name, slug=slug_new, description=description)
        # category.save()
        
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
        
        # Generate the slug based on the category name
        slug = slugify(category_name)
        
        # Update the Category object with 'id = category_id'
        # category = Category(name=category_name, slug=slug, description=description)
        cat_update.name = category_name
        cat_update.slug = slug
        cat_update.description = description
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
