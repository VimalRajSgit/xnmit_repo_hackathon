#views.py
from email import message
from itertools import product
from multiprocessing import context
from operator import is_not
from urllib import response
from django.shortcuts import render, redirect
from .models import *
from .forms import *
import csv
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime
from .filter import *
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import Group
from django.contrib import messages
from .decorators import unauthenticated_user, allowed_users, admin_only
from django.contrib.auth.decorators import login_required

# Create your views here.

@unauthenticated_user
def register(request):
    form = BuyerUserForm()
    if request.method == 'POST':
        form = BuyerUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
        
            group = Group.objects.get(name='Buyer')
            user.groups.add(group)

            Buyer.objects.create(user=user)

            messages.success(request, f'Buyer Account Successfully created for {username}')
            return redirect('/login')

    context = {'form':form}
    return render(request, 'registration.html', context)

@unauthenticated_user
def register_seller(request):
    form = CustomerUserForm()
    if request.method == 'POST':
        form = CustomerUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
        
            group = Group.objects.get(name='Customer')
            user.groups.add(group)

            Customer.objects.create(user=user)

            messages.success(request, f'Seller Account Successfully created for {username}')
            return redirect('/login')

    context = {'form':form}
    return render(request, 'registration.html', context)

@unauthenticated_user
def login_buyer(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name
            if group == 'Customer':
                return redirect('/sellerdashboard')
            if group == 'Admin':
                return redirect('/')
            else:
                return redirect('/buyerdashboard')
        else:
            messages.warning(request, f"Username or Password does not exist")

    context = {}
    return render(request, 'login.html', context)

@allowed_users(allowed_roles=['Buyer','Admin','Customer'])
def logout_buyer(request):
    logout(request)
    return redirect('/login')

@login_required(login_url='login')
@allowed_users(allowed_roles=['Buyer'])
def buyer_dashboard(request):
    product_pages = Product.objects.all()
    total_products = Product.objects.count()
    myfilter = ProductFilter(request.GET, queryset=product_pages)
    product_pages = myfilter.qs

    context = {'product_pages':product_pages, 'myfilter':myfilter, 'total_products':total_products}
    return render(request, 'buyer_dashboard.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Buyer'])
def buyer_account_settings(request):
    buyer = request.user.buyer
    form = BuyerForm(instance=buyer)
    if request.method == 'POST':
        form = BuyerForm(request.POST, request.FILES, instance=buyer)
        if form.is_valid():
            form.save()
            return redirect('/buyerdashboard')
    
    context = {'form':form}
    return render(request, 'buyer_account_settings.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer', 'Admin'])
def room(request, pk):
    # Get the customer (seller) - handle both Admin and Customer users
    try:
        if request.user.groups.all()[0].name == 'Admin':
            # Admin users can view any customer's messages
            customer = Customer.objects.get(id=pk)
        else:
            # Customer users can only view their own messages
            customer = request.user.customer
            if customer.id != int(pk):
                return redirect('login')
    except:
        # If customer doesn't exist or user doesn't have proper access, redirect to login
        return redirect('login')
    
    # Get all buyers who have messaged this customer
    buyers_with_messages = Buyer.objects.filter(
        message__receiver=customer
    ).distinct()
    
    # Get all messages received by this customer (from buyers)
    received_messages = Message.objects.filter(receiver=customer).order_by('created')
    
    # Get all messages sent by this customer (to buyers)
    sent_messages = PostMessage.objects.filter(sender=customer).order_by('created')
    
    # Get the last message for display
    last_message = Message.objects.filter(receiver=customer).last()
    
    # Count total messages
    total_messages = Message.objects.filter(receiver=customer).count()
    
    # Handle POST request for sending messages
    if request.method == 'POST':
        buyer_id = request.POST.get('buyer_id')
        message_body = request.POST.get('body')
        
        if buyer_id and message_body:
            try:
                buyer = Buyer.objects.get(id=buyer_id)
                PostMessage.objects.create(
                    sender=customer,
                    receiver=buyer,
                    body=message_body
                )
                # Redirect to avoid duplicate submissions
                return redirect('room', pk=customer.id)
            except Buyer.DoesNotExist:
                pass

    context = {
        'customer': customer,
        'buyers': buyers_with_messages,
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'last_message': last_message,
        'total_messages': total_messages,
    }
    return render(request, 'room.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer'])
def seller_dashboard(request):
    """Dashboard for sellers to view their products and messages"""
    try:
        customer = request.user.customer
    except:
        return redirect('login')
    
    # Get seller's products
    products = Product.objects.filter(customer=customer)
    
    # Get recent messages
    recent_messages = Message.objects.filter(receiver=customer).order_by('-created')[:5]
    
    # Count unread messages (you can add a read/unread field later)
    total_messages = Message.objects.filter(receiver=customer).count()
    
    context = {
        'customer': customer,
        'products': products,
        'recent_messages': recent_messages,
        'total_messages': total_messages,
    }
    return render(request, 'seller_dashboard.html', context)

@login_required(login_url='login')
@admin_only
def home(request):
    customers = Customer.objects.all()

    context = {'customers':customers}
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def add_customer(request):
    form = CustomerForm()
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form':form}
    return render(request, 'add_customer.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin','Customer'])
def customer_page(request, pk):
    customer = Customer.objects.get(id=pk)
    products = customer.product_set.all()

    total_products = products.count()
    myfilter = ProductFilter(request.GET, queryset=products)
    products = myfilter.qs

    context = {'customer':customer, 'products':products, 'total_products':total_products, 'myfilter':myfilter}
    return render(request, 'customer_page.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def update_customer(request, pk):
    customer = Customer.objects.get(id=pk)
    form = CustomerForm(instance=customer)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('/')
    
    context = {'form':form}
    return render(request, 'update_customer.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def delete_customer(request, pk):
    customer = Customer.objects.get(id=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('/')

    context = {'customer':customer}
    return render(request, 'delete_customer.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Buyer'])
def product_page(request, pk):
    product = Product.objects.get(id=pk)
    buyer = request.user.buyer
    
    # Get messages from buyer to seller
    buyer_messages = Message.objects.filter(
        sender=buyer,
        receiver=product.customer
    ).order_by('created')
    
    # Get replies from seller to buyer
    seller_replies = PostMessage.objects.filter(
        sender=product.customer,
        receiver=buyer
    ).order_by('created')
    
    # Combine all messages for chronological display
    all_messages = []
    
    # Add buyer messages with type indicator
    for msg in buyer_messages:
        all_messages.append({
            'type': 'buyer',
            'message': msg,
            'created': msg.created
        })
    
    # Add seller replies with type indicator
    for reply in seller_replies:
        all_messages.append({
            'type': 'seller',
            'message': reply,
            'created': reply.created
        })
    
    # Sort all messages by creation time
    all_messages.sort(key=lambda x: x['created'])
    
    if request.method == 'POST':
        message_body = request.POST.get('body')
        if message_body:
            Message.objects.create(
                sender=buyer,
                receiver=product.customer,
                body=message_body
            )
            return redirect('product_page', pk=pk)

    context = {
        'product': product, 
        'buyer_messages': buyer_messages,
        'seller_replies': seller_replies,
        'all_messages': all_messages,
    }
    return render(request, 'product_page.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def products(request, pk):
    customer = Customer.objects.get(id=pk)
    form = ProductForm(initial={'customer':customer})
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, initial={'customer':customer})
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form':form}
    return render(request, 'products.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def update_product(request, pk):
    product = Product.objects.get(id=pk)
    form = ProductForm(instance=product)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form':form}
    return render(request, 'update_product.html', context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['Admin'])
def export_csv(request):
    current_date_time = datetime.now()
    response = HttpResponse(
        content_type = 'text/csv',
        headers = {'Content-Disposition': f'attachment; filename="customer_records {str(current_date_time)}.csv"'},
    )
    writer = csv.writer(response)
    writer.writerow(['Id No.','Name','Phone No','Gender','Residence'])

    customers = Customer.objects.all()

    for customer in customers:
        writer.writerow([customer.id_no, customer.name, customer.phone_no, customer.gender, customer.residence])

    return response 

def export_pdf(request):
    return render(request, 'pdf_output.html')
