from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [    
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),

    # User Shop Page
    path('category_page/<int:category_id>/', views.category_page, name='category_page'),
    path('product_detail/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart Page
    path('add_to_cart/<int:variant_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart_signin/<int:product_id>/', views.cart_signin, name='cart_signin'),    
    path('update-cart-items/', views.update_cart_item_quantity, name='update_cart_item_quantity'),
    path('remove_cart_item/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('create_order/', views.create_order, name='create_order'),
    path('order_success/<int:order_id>/', views.order_success, name='order_success'),
    path('get-address/', views.get_address, name="get_address")

]