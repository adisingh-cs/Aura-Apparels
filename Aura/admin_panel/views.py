from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.http import HttpResponse, JsonResponse
from store import models
from store.models import Category, Product, Order, OrderItem, ProductImage, ProductVariation
from store.models import Category, Product, Order, OrderItem, ProductImage
from accounts.models import UserProfile
from .models import AdminDashboardStats
import csv
import datetime
from django.utils import timezone
from django.core.paginator import Paginator
import xlwt

# Helper function to check if user is admin
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get counts
    total_products = Product.objects.count()
    total_users = User.objects.filter(is_superuser=False).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(order_status='Pending').count()
    
    # Calculate total sales
    total_sales = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Get recent orders
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Update dashboard stats
    try:
        stats = AdminDashboardStats.objects.latest('last_updated')
        stats.total_products = total_products
        stats.total_users = total_users
        stats.total_orders = total_orders
        stats.pending_orders = pending_orders
        stats.total_sales = total_sales
        stats.save()
    except AdminDashboardStats.DoesNotExist:
        stats = AdminDashboardStats.objects.create(
            total_products=total_products,
            total_users=total_users,
            total_orders=total_orders,
            pending_orders=pending_orders,
            total_sales=total_sales
        )
    
    context = {
        'stats': stats,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'admin_panel/products.html', context)
@login_required
@user_passes_test(is_admin)
def add_product(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        stock = request.POST.get('stock')
        is_available = request.POST.get('is_available') == 'on'
        
        # Check if slug already exists
        if Product.objects.filter(slug=slug).exists():
            messages.error(request, 'A product with this slug already exists. Please choose a different slug.')
            return redirect('add_product')
        
        # Create the product
        product = Product(
            name=name,
            slug=slug,
            description=description,
            price=price,
            category_id=category_id,
            stock=stock,
            is_available=is_available
        )
        
        # Handle image uploads
        # Handle image uploads
        images = request.FILES.getlist('images')
        if images:
            # Set the first image as main image
            product.main_image = images[0]
            product.save()
            
            # Create ProductImage objects for all images including the first one
            for image in images:
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=image == images[0]  # Set first image as primary
                )
            
        messages.success(request, 'Product added successfully.')
        return redirect('admin_products')
    
    context = {
        'categories': categories,
    }
    return render(request, 'admin_panel/add_product.html', context)

@login_required
@user_passes_test(is_admin)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        new_slug = request.POST.get('slug')

        # Check if slug changed and already exists
        if new_slug != product.slug and Product.objects.filter(slug=new_slug).exists():
            messages.error(request, 'A product with this slug already exists. Please choose a different slug.')
            return redirect('edit_product', product_id=product.id)

        product.slug = new_slug
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')

        try:
            category_id = request.POST.get('category')
            if not category_id:
                messages.error(request, 'Category is required.')
                context = {
                    'product': product,
                    'categories': categories,
                }
                return render(request, 'admin_panel/edit_product.html', context)
            
            category = Category.objects.get(id=category_id)
            product.category = category
        except (ValueError, TypeError):
            messages.error(request, 'Invalid category ID format.')
            context = {
                'product': product,
                'categories': categories,
            }
            return render(request, 'admin_panel/edit_product.html', context)
        except Category.DoesNotExist:
            messages.error(request, 'Selected category does not exist.')
            context = {
                'product': product,
                'categories': categories,
            }
            return render(request, 'admin_panel/edit_product.html', context)

        product.stock = request.POST.get('stock')
        product.is_available = request.POST.get('is_available', '') == 'on'

        # Handle primary image selection
        primary_image_id = request.POST.get('primary_image')
        if primary_image_id:
            try:
                primary_image_id = int(primary_image_id)
                # Reset all images to non-primary
                ProductImage.objects.filter(product=product).update(is_primary=False)
                # Set selected image as primary
                primary_image = ProductImage.objects.get(id=primary_image_id, product=product)
                primary_image.is_primary = True
                primary_image.save()
                # Update product's main image
                product.image = primary_image.image
                product.save()
            except (ValueError, ProductImage.DoesNotExist):
                messages.error(request, 'Invalid primary image selection.')
                return redirect('edit_product', product_id=product.id)

        # Handle multiple image uploads
        if request.FILES:
            images = request.FILES.getlist('images')
            if images:
                current_max_ordering = ProductImage.objects.filter(product=product).aggregate(max_ordering=models.Max('ordering'))['max_ordering'] or 0
                for index, image in enumerate(images, start=1):
                    # Create new product image
                    product_image = ProductImage.objects.create(
                        product=product,
                        image=image,
                        is_primary=False,  # New images are not primary by default
                        ordering=current_max_ordering + index
                    )
                    
                    # If this is the first image and product has no main image, set it as main
                    if index == 1 and not product.main_image_url:
                        product.image = image
                        product_image.is_primary = True
                        product_image.save()
                        product.save()

        product.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('admin_products')

    context = {
        'product': product,
        'categories': categories,
    }
    return render(request, 'admin_panel/edit_product.html', context)

@login_required
@user_passes_test(is_admin)
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    messages.success(request, f'Product "{product_name}" deleted successfully.')
    return redirect('admin_products')

@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'admin_panel/categories.html', context)

@login_required
@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        
        # Check if slug already exists
        if Category.objects.filter(slug=slug).exists():
            messages.error(request, 'A category with this slug already exists. Please choose a different slug.')
            return redirect('add_category')
        
        # Create the category
        category = Category(
            name=name,
            slug=slug,
            description=description
        )
        
        if 'image' in request.FILES:
            category.image = request.FILES['image']
            
        category.save()
        messages.success(request, 'Category added successfully.')
        return redirect('admin_categories')
    
    return render(request, 'admin_panel/add_category.html')

@login_required
@user_passes_test(is_admin)
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        new_slug = request.POST.get('slug')
        
        # Check if slug changed and already exists
        if new_slug != category.slug and Category.objects.filter(slug=new_slug).exists():
            messages.error(request, 'A category with this slug already exists. Please choose a different slug.')
            return redirect('edit_category', category_id=category.id)
        
        category.slug = new_slug
        category.description = request.POST.get('description')
        
        if 'image' in request.FILES:
            category.image = request.FILES['image']
        elif request.POST.get('delete_image'):
            category.image.delete()
            category.image = None
            
        category.save()
        messages.success(request, 'Category updated successfully.')
        return redirect('admin_categories')
    
    context = {
        'category': category,
    }
    return render(request, 'admin_panel/edit_category.html', context)

@login_required
@user_passes_test(is_admin)
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category_name = category.name
    
    # Check if there are products in this category
    if Product.objects.filter(category=category).exists():
        messages.error(request, f'Cannot delete category "{category_name}" because it contains products. Please move or delete these products first.')
        return redirect('admin_categories')
    
    category.delete()
    messages.success(request, f'Category "{category_name}" deleted successfully.')
    return redirect('admin_categories')

@login_required
@user_passes_test(is_admin)
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        orders = orders.filter(order_status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 20)  # Show 20 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_status': status_filter or 'all',
    }
    return render(request, 'admin_panel/orders.html', context)

@login_required
@user_passes_test(is_admin)
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'admin_panel/order_detail.html', context)

@login_required
@user_passes_test(is_admin)
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('order_status')
        order.order_status = new_status
        order.save()
        messages.success(request, f'Order #{order.id} status updated to {new_status}.')
    
    return redirect('admin_order_detail', order_id=order.id)

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)  # Show 20 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'admin_panel/users.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = None
    
    # Get user's orders
    orders = Order.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'user_detail': user,
        'profile': profile,
        'orders': orders,
    }
    return render(request, 'admin_panel/user_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_inventory(request):
    low_stock_products = Product.objects.filter(stock__lt=10).order_by('stock')
    out_of_stock_products = Product.objects.filter(stock=0)
    
    context = {
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
    }
    return render(request, 'admin_panel/inventory.html', context)

@login_required
@user_passes_test(is_admin)
def export_orders(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="orders_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Orders')
    
    # Sheet header, first row
    row_num = 0
    
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    columns = ['Order ID', 'Customer', 'Email', 'Amount', 'Status', 'Date']
    
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    
    rows = Order.objects.all().values_list(
        'id', 'full_name', 'email', 'total_amount', 'order_status', 'created_at'
    )
    
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            if col_num == 5:  # Date column
                ws.write(row_num, col_num, row[col_num].strftime('%Y-%m-%d %H:%M:%S'), font_style)
            else:
                ws.write(row_num, col_num, str(row[col_num]), font_style)
    
    wb.save(response)
    return response

@login_required
@user_passes_test(is_admin)
def export_users(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Users')
    
    # Sheet header, first row
    row_num = 0
    
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    columns = ['User ID', 'Username', 'Email', 'First Name', 'Last Name', 'Date Joined']
    
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    
    rows = User.objects.filter(is_superuser=False).values_list(
        'id', 'username', 'email', 'first_name', 'last_name', 'date_joined'
    )
    
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            if col_num == 5:  # Date column
                ws.write(row_num, col_num, row[col_num].strftime('%Y-%m-%d %H:%M:%S'), font_style)
            else:
                ws.write(row_num, col_num, str(row[col_num]), font_style)
    
    wb.save(response)
    return response

@login_required
@user_passes_test(is_admin)
def export_sales(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="sales_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Sales')
    
    # Sheet header, first row
    row_num = 0
    
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    columns = ['Order ID', 'Product', 'Quantity', 'Price', 'Total', 'Date']
    
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    
    # Get all order items with related data
    order_items = OrderItem.objects.select_related('order', 'product').all()
    
    for item in order_items:
        row_num += 1
        row = [
            item.order.id,
            item.product.name,
            item.quantity,
            float(item.price),
            float(item.get_total),
            item.order.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    
    wb.save(response)
    return response

@login_required
@user_passes_test(is_admin)
def delete_product_image(request, image_id):
    if request.method == 'POST':
        try:
            image = ProductImage.objects.get(id=image_id)
            image.delete()
            return JsonResponse({'success': True})
        except ProductImage.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Image not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def manage_variations(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variations = product.variations.all().order_by('color', 'size')
    
    context = {
        'product': product,
        'variations': variations,
    }
    return render(request, 'admin_panel/manage_variations.html', context)

@login_required
@user_passes_test(is_admin)
def add_variation(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        color = request.POST.get('color')
        size = request.POST.get('size')
        stock = request.POST.get('stock', 0)
        is_available = request.POST.get('is_available') == 'on'
        
        variation = ProductVariation.objects.create(
            product=product,
            color=color,
            size=size,
            stock=stock,
            is_available=is_available
        )
        messages.success(request, 'Variation added successfully.')
        return redirect('manage_variations', product_id=product.id)
    
    return redirect('manage_variations', product_id=product.id)

@login_required
@user_passes_test(is_admin)
def delete_variation(request, variation_id):
    variation = get_object_or_404(ProductVariation, id=variation_id)
    product_id = variation.product.id
    variation.delete()
    messages.success(request, 'Variation deleted successfully.')
    return redirect('manage_variations', product_id=product_id)