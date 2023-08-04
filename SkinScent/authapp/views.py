
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User	

# signup Validations
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


# For Email Verification by link
from allauth.account.utils import send_email_confirmation

# Email Verification Link - Handling
from django.urls import reverse
from allauth.account.views import ConfirmEmailView

# For Signin
from django.contrib.auth import authenticate, login, logout

# OTP Login
from django.core.mail import send_mail
from random import randint
from twilio.rest import Client

# password reset
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash


# Create your views here.

def signup(request):
    # return render(request, 'authapp/signup.html')
    error_message = None
    if request.method == 'POST':
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password1']
            password_confirm = request.POST['password2']
                        # Check if any field is empty
            if not username or not email or not password or not password_confirm:
                error_message = 'All fields are required.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})

            # Check username format
            if not re.match(r'^[a-zA-Z0-9]+$', username):
                error_message = 'Username must contain only alphanumeric characters.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})


            # Check if passwords match
            if password != password_confirm:
                error_message = 'Passwords do not match.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})

            # Check password format
            if len(password) < 8:
                error_message = 'Password must be at least 8 characters long.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})
            if not any(char.isdigit() for char in password):
                error_message = 'Password must contain at least one digit.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})
            if not any(char.isalpha() for char in password):
                error_message = 'Password must contain at least one letter.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})

            # Check email format
            try:
                validate_email(email)
            except ValidationError:
                error_message = 'Invalid email format.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})

            # Check if username or email already exist
            if User.objects.filter(username=username).exists():
                error_message = 'Username already exists. Please choose a different username.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})

            if User.objects.filter(email=email).exists():
                error_message = 'Email already exists. Please use a different email address.'
                # context = {'form': form, 'error_message': error_message}
                return render(request, 'authapp/signup.html', {'error_message': error_message})
    

            # Create a new User object
            new_user = User.objects.create_user(username=username, email=email, password=password)
            new_user.is_active = False
            new_user.save()

            send_email_confirmation(request, new_user)

            # Redirect to a success page or login page
            context = {
                'message' : f'Please verify your Email. A verification link has been sent to {email}',
                'login_url' : '#'
            }
            return render(request, 'authapp/messagepage.html', context)
    return render(request, 'authapp/signup.html', {'error_message': error_message})


def signin(request):   
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)
    

        if user is not None and user.is_active is True:
            # Authentication successful
            login(request, user)

            # Redirect to the 'next' URL after login
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url) 

            return redirect('/')
            # return render(request, 'index.html')
        else:
            # Authentication failed
            if user is not None and user.is_active is False:
                error_message = 'Email not verified'
            elif user is None:
                error_message = 'Invalid username or password OR Email not verified'
            return render(request, 'authapp/signin.html', {'error_message': error_message})

    # Render the login form for GET requests
    return render(request, 'authapp/signin.html')
    

def signout(request):
    logout(request)
    return redirect('/')


# Email Link Verification - Customization 
class CustomConfirmEmailView(ConfirmEmailView):
    def get(self, *args, **kwargs):
        confirmation = self.get_object()
        user = confirmation.email_address.user
        user.is_active = True
        user.save()

        login_url = 1

        context = {
            'message': 'Email Verified Successfully, Please Login',
            'login_url': login_url
        }
        return render(self.request, 'authapp/messagepage.html', context)



###############################
####### OTP LOGIN #############
###############################
def generate_otp():
    return str(randint(100000, 999999))

def email_otp_login(request):
    flag = False
    msg = None
    if request.method == 'POST':
        email = request.POST.get('email')

         # Retrieve the user based on the email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Handle the case where the user does not exist for the provided email
            msg = 'No User registered with the mail!'
            return render(request, 'authapp/forgotpass.html', {'error_message' : msg, 'flag' : flag})


        # Generate OTP
        # devices = devices_for_user(request.user)
        # for device in device:
        #     otp = device.generate_challenge()
        otp = generate_otp()

        # store OTP in user's session
        request.session['otp'] = otp
        request.session['user_pk'] = user.pk

        # Send OTP via email
        send_mail(
            'OTP Verification',
            f'Your OTP is: {otp}',
            'skinscent69@gmail.com',
            [email],
            fail_silently=False,
        )

        return redirect('/authapp/verify_otp/')

    return render(request, 'authapp/forgotpass.html', {'error_message' : msg, 'flag' : flag})

def verify_otp(request):
    flag = True
    msg = 'OTP Sent!'
    if request.method == 'POST':
        otp = request.POST.get('otp')        

        # retrieve OTP from user's session
        stored_otp = request.session.get('otp')
        stored_user_id = request.session.get('user_pk')

        user = User.objects.get(id=int(stored_user_id))

        if otp == stored_otp:
            # OTP verified
            login(request, user)
            # return redirect('/')
            return redirect('/authapp/password_reset/')
        else:
            msg = 'Invalid OTP'
            return render(request, 'authapp/forgotpass.html', {'error_message' : msg, 'flag' : flag})        


    return render(request, 'authapp/forgotpass.html', {'error_message' : msg, 'flag' : flag})


###############################
####### RESET PASSWORD ########
###############################
@login_required
def password_reset(request):    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password == confirm_password:
            # Check password format
            password = new_password
            if len(password) < 8:
                error_message = 'Password must be at least 8 characters long.'                
                return render(request, 'authapp/resetpass.html', {'error_message':error_message})
            if not any(char.isdigit() for char in password):
                error_message = 'Password must contain at least one digit.'                
                return render(request, 'authapp/resetpass.html', {'error_message':error_message})
            if not any(char.isalpha() for char in password):
                error_message = 'Password must contain at least one letter.'                
                return render(request, 'authapp/resetpass.html', {'error_message':error_message})
            user = request.user
            user.set_password(new_password)
            user.save()

            message = 'Password reset successful!'
            login_url = 1
            return render(request, 'authapp/messagepage.html', {'message':message, 'login_url': login_url})
            
        else:
            messages.error(request, 'Passwords do not match.')
            error_message = 'Passwords do not match!'
            return render(request, 'authapp/resetpass.html', {'error_message':error_message})
    
    error_message = None
    return render(request, 'authapp/resetpass.html', {'error_message':error_message})