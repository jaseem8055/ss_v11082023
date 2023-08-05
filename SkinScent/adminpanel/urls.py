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
    path('change-payment-status/<int:order_id>/', views.change_payment_status, name='change_payment_status'),
    path('change-delivery-status/<int:order_id>/', views.change_delivery_status, name='change_delivery_status'),

    # COUPON
    path('coupon/', views.list_coupon, name='list_coupon'),
    path('add-coupon/', views.add_coupon, name='add_coupon'),
    path('edit-coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),

    # GRAPH
    path('orders_data/', views.orders_data, name='orders_data'),
    path("chart/filter-options/", views.get_filter_options, name="chart-filter-options"),
    path("chart/sales/<int:year>/", views.get_sales_chart, name="chart-sales"),
    path("chart/spend-per-customer/<int:year>/", views.spend_per_customer_chart, name="chart-spend-per-customer"),
    path("chart/payment-success/<int:year>/", views.payment_success_chart, name="chart-payment-success"),
    path("chart/payment-method/<int:year>/", views.payment_method_chart, name="chart-payment-method"),

    path("statistics/", views.statistics_view, name="shop-statistics"),

    # OFFERS
    
    # Offer Management
    path('offers/edit/<int:offer_id>', views.edit_offer, name='edit_offer'),
    path('offers/create/', views.create_offer, name='create_offer'),
    path('offers/', views.offers, name='offers'),

    # Product Offers    
    path('offers/product/', views.product_offers, name='product_offers'),
    path('offers/product/create/', views.create_product_offer, name='create_product_offer'),
    path('offers/product/edit/<int:pk>', views.edit_product_offer, name='edit_product_offer'),

    # Category Offers
    # path('offers/category/', views.category_offers, name='category_offers'),
    # path('offers/category/create/', views.create_category_offer, name='create_category_offer'),

    # Referral Offers
    # path('offers/referral/', views.referral_offers, name='referral_offers'),
    # path('offers/referral/create/', views.create_referral_offer, name='create_referral_offer'),

    # Sales Report
    path("sales-report/", views.generate_monthly_sales_report_pdf, name="sales-report"),
    path("sales-report/daily", views.generate_sales_report_pdf, name="sales-report-daily"),




]
