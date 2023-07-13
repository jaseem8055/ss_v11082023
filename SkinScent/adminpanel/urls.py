from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.admin_home, name='admin_home'), 
    path('admin_signin/', views.admin_signin, name='admin_signin'), 
    path('admin_logout/', views.admin_logout, name='admin_logout'),

    # CATEGORY MANAGEMENT
    path('add_cat/', views.add_category, name='add_cat'),
    path('list_cat/', views.list_category, name='list_cat'),
    path('edit_cat/<int:category_id>/', views.edit_category, name='edit_cat'),
    path('block_cat/<int:category_id>/', views.block_category, name='block_category'),

    # PRODUCT MANAGEMENT
    path('add_product/', views.add_product, name='add_product'),
    path('list_product/', views.list_product, name='list_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('block_product/<int:product_id>/', views.block_product, name='block_product'),

    # VARIANTS
    path('start_variant/', views.start_product_variant, name='start_variant'),
    path('list_variant/<int:product_id>/', views.list_variant, name='list_variant'),
    path('add_variant/<int:product_id>/', views.add_variant, name='add_variant'),

    # USER MANAGEMENT
    path('list_users/', views.list_user, name='list_users'),
    path('block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock_user/<int:user_id>/', views.unblock_user, name='unblock_user'),

    #ORDER
    path('order_summary/', views.order_summary, name='order_summary'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),

]
