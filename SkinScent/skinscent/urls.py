"""
URL configuration for skinscent project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

# from allauth.account.views import ConfirmEmailView
from authapp.views import CustomConfirmEmailView

# Media Config
from django.conf import settings
from django.conf.urls.static import static

# Login Required
from authapp.views import signin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('authapp/', include('authapp.urls')),
    path('accounts/confirm-email/<str:key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),
    path('adminpanel/', include('adminpanel.urls')),
    path('userprofile/', include('userprofile.urls')),

    # Login required url path
    path('accounts/login/', signin, name='login'),

    # Handle Favicon 404
    path('favicon.ico', lambda request: HttpResponse(status=204)),
] 

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



