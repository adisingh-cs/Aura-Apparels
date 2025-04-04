from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('products/', views.admin_products, name='admin_products'),
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('categories/', views.admin_categories, name='admin_categories'),
    path('add_category/', views.add_category, name='add_category'),
    path('edit_category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete_category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('orders/', views.admin_orders, name='admin_orders'),
    path('order_detail/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('users/', views.admin_users, name='admin_users'),
    path('user_detail/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('inventory/', views.admin_inventory, name='admin_inventory'),
    path('export_orders/', views.export_orders, name='export_orders'),
    path('export_users/', views.export_users, name='export_users'),
    path('export_sales/', views.export_sales, name='export_sales'),
    path('export_sales/', views.export_sales, name='export_sales'),
    path('delete_product_image/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
    path('manage_variations/<int:product_id>/', views.manage_variations, name='manage_variations'),
    path('add_variation/<int:product_id>/', views.add_variation, name='add_variation'),
    path('delete_variation/<int:variation_id>/', views.delete_variation, name='delete_variation'),
    path('delete_product_image/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
]