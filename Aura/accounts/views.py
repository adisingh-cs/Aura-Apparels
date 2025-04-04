import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from store.models import Order, OrderItem
from django.http import HttpResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    context = {
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def update_profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Update user information
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.save()
        
        # Update profile information
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.pincode = request.POST.get('pincode')
        
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']
        
        profile.save()
        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('profile')
    
    context = {
        'profile': profile,
    }
    return render(request, 'accounts/update_profile.html', context)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/order_history.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'accounts/order_detail.html', context)

@login_required
def download_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setTitle(f"Receipt - Order #{order.id}")

    # === HEADER WITH LOGO ===
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'favicon.png')
    
    if os.path.exists(logo_path):  # Ensure the logo exists before drawing
        p.drawImage(logo_path, 50, 725, width=80, height=60, mask='auto')

    p.setFont("Helvetica-Bold", 18)
    p.drawString(130, 770, "AURA APPARELS")

    p.setFont("Helvetica", 12)
    p.drawString(130, 750, f"Receipt - Order #{order.id}")
    p.drawString(130, 730, f"Date: {order.created_at.strftime('%d %b, %Y')}")

    # === CUSTOMER DETAILS ===
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 670, "Customer Details:")

    p.setFont("Helvetica", 12)
    p.drawString(50, 650, f"Name: {order.full_name}")
    p.drawString(50, 630, f"Email: {order.email}")
    p.drawString(50, 610, f"Phone: {order.phone}")
    p.drawString(50, 590, f"Address: {order.address}")
    p.drawString(50, 570, f"{order.city}, {order.state} - {order.pincode}")

    # === ORDER DETAILS ===
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 530, "Order Details:")

    # Create order items table
    data = [["Product", "Price", "Quantity", "Total"]]
    for item in order_items:
        data.append([
            item.product.name,
            str(item.price),
            str(item.quantity),
            str(item.get_total)
        ])

    data.append(["", "", "Grand Total:", str(order.total_amount)])

    table = Table(data, colWidths=[200, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    table.wrapOn(p, 400, 500)
    table.drawOn(p, 50, 450)

    # === FOOTER ===
    p.setFont("Helvetica-Oblique", 12)
    p.drawString(50, 350, "Thank you for shopping with AURA APPARELS!")
    p.drawString(50, 330, "For any inquiries, please contact: eternals.hub@gmail.com")

    p.setFont("Helvetica", 10)
    p.drawString(50, 300, f"Payment Status: {order.payment_status}")
    p.drawString(50, 285, f"Order Status: {order.order_status}")

    p.setFont("Helvetica", 8)
    p.drawString(50, 50, "This is a computer-generated receipt and does not require a signature.")
    p.drawString(50, 35, "© 2025 AURA APPARELS. All rights reserved.")

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receipt_Order_{order.id}.pdf"'

    return response