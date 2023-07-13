from django.urls import path
from . import views

app_name = 'authapp'

urlpatterns = [       
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('signout/', views.signout, name='signout'),
    path('email_otp/', views.email_otp_login, name='email_otp'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('password_reset/', views.password_reset, name='password_reset'),
    
]