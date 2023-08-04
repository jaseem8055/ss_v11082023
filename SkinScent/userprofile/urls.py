from django.urls import path
from . import views

urlpatterns = [
    path('', views.myprofile, name='myprofile'),
    path('add_address/', views.add_address, name='add_address'),
    path('list_address/', views.list_address, name='list_address'),
    
    path('edit_address/<int:address_pk>/', views.edit_address, name='edit_address'),
    path('remove_address/<int:address_pk>/', views.remove_address, name='remove_address'),

    path('my_orders/', views.my_orders, name='my_orders'),
    path('my_order_detail/<int:order_id>/', views.my_order_detail, name='my_order_detail'),
    path('my_order_cancel/<int:order_id>/', views.order_cancellation, name='order_cancellation'),

    path('my-wallet/', views.my_wallet, name='my_wallet'),

    path('phone-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/<str:new_contact>', views.verify_otp, name='verify_otp'),

    path('reset-pass/', views.reset_pass, name="reset_pass"),
    path('verify-reset-pass/', views.verify_reset_pass, name="verify_reset_pass"),
    path('forgot-pass/', views.forgot_pass, name="forgot_pass"),

]
