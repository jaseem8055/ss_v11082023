from django.urls import path
from . import views
from authapp.views import contact_us

app_name = 'shop'

urlpatterns = [    
    path('', views.home, name='home'),
    path('contact/', contact_us, name='contact'),

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
    path('get-address/', views.get_address, name="get_address"),

    # Razor Pay
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('handle-payment-success/', views.handle_payment_success, name='handle_payment_success'),    
    path('reset-order/', views.reset_order, name='reset_order'),    

    # Search Options
    path('search-products/', views.search_products, name='search_products'),
    path('filter-products/', views.filter_products, name='filter_products'),
    path('process-filter/', views.process_filter, name='process_filter'),

    # Coupon Management
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('clear-coupon/', views.clear_coupon, name='clear_coupon'),

    # PDF Exporting
    path('download-pdf/<int:order_id>/', views.generate_pdf, name='download_pdf'),

    # Wishlist
    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/', views.wishlist_products, name='wishlist_products'),
    path('remove_from_wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Offers
    path('offers/', views.offer_page, name='offer_page'),


]