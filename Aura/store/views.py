import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from django.http import HttpResponse, JsonResponse
import datetime

def home(request):
    featured_products = Product.objects.filter(is_available=True)[:8]
    categories = Category.objects.all()
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)

def shop(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/shop.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
        'product_images': product.images.all(),
    }
    return render(request, 'store/product_detail.html', context)

def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category, is_available=True)
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'store/category_products.html', context)

def search(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    else:
        products = Product.objects.none()
    
    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'store/search_results.html', context)

@login_required
def cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        cart_items = []
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if item exists in cart
    cart_item = CartItem.objects.filter(
        cart=cart, 
        product=product
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
        cart_item.save()
    else:
        CartItem.objects.create(
            cart=cart, 
            product=product, 
            quantity=quantity
        )
    
    messages.success(request, f"{product.name} added to your cart.")
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"{product_name} removed from your cart.")
    return redirect('cart')

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('cart')

@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items:
            messages.warning(request, "Your cart is empty.")
            return redirect('cart')
    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': cart.get_cart_subtotal,
        'shipping_cost': cart.get_shipping_cost,
        'tax': cart.get_tax,
        'total': cart.get_cart_total,
    }
    return render(request, 'store/checkout.html', context)

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            
            if not cart_items:
                return JsonResponse({'success': False, 'message': 'Your cart is empty.'})
            
            # Create the order
            order = Order(
                user=request.user,
                full_name=request.POST.get('full_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                pincode=request.POST.get('pincode'),
                total_amount=cart.get_cart_total,
                order_status='Pending'
            )
            order.save()
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
                
                # Update product stock
                product = item.product
                product.stock -= item.quantity
                if product.stock <= 0:
                    product.is_available = False
                product.save()
            
            # Clear the cart
            cart_items.delete()
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('order_complete', args=[order.id])
            })
        
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Your cart is empty.'})
    
    return redirect('checkout')

@login_required
def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'store/order_complete.html', context)

def contact(request):
    return render(request, 'store/contact.html')