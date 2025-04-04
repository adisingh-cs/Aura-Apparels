from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    @property
    def image_url(self):
        try:
            if self.image and hasattr(self.image, 'url') and self.image.url:
                return self.image.url
            return Product.DEFAULT_IMAGE_URL
        except (AttributeError, ValueError, Exception) as e:
            return Product.DEFAULT_IMAGE_URL

    @property
    def safe_image_url(self):
        try:
            if self.image and hasattr(self.image, 'url') and self.image.url:
                from django.core.files.storage import default_storage
                if default_storage.exists(self.image.name):
                    return self.image.url
            return Product.DEFAULT_IMAGE_URL
        except (AttributeError, ValueError, Exception) as e:
            return Product.DEFAULT_IMAGE_URL

class Product(models.Model):
    DEFAULT_IMAGE_URL = '/static/images/default-product.png'
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def main_image_url(self):
        try:
            # First try to get the primary image
            primary_image = self.images.filter(is_primary=True).first()
            if primary_image and primary_image.image and hasattr(primary_image.image, 'url'):
                return primary_image.image.url
            
            # Then try to get the main image
            main_image = self.images.filter(is_main=True).first()
            if main_image and main_image.image and hasattr(main_image.image, 'url'):
                return main_image.image.url
            
            # Then try the product's direct image
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
            
            # Finally try the first product image
            first_image = self.images.first()
            if first_image and first_image.image and hasattr(first_image.image, 'url'):
                return first_image.image.url
            
            return self.DEFAULT_IMAGE_URL
        except (AttributeError, ValueError, Exception) as e:
            return self.DEFAULT_IMAGE_URL
    
    @property
    def image_url(self):
        try:
            if self.image and hasattr(self.image, 'url') and self.image.url:
                return self.image.url
            return self.DEFAULT_IMAGE_URL
        except (AttributeError, ValueError, Exception) as e:
            return self.DEFAULT_IMAGE_URL
        
    def get_all_images(self):
        return self.images.all().order_by('ordering')

    @property
    def safe_image_url(self):
        try:
            if self.image and hasattr(self.image, 'url') and self.image.url:
                from django.core.files.storage import default_storage
                if default_storage.exists(self.image.name):
                    return self.image.url
            return self.DEFAULT_IMAGE_URL
        except (AttributeError, ValueError, Exception) as e:
            return self.DEFAULT_IMAGE_URL


    def get_main_image(self):
        try:
            main_image = self.images.filter(is_main=True, image__isnull=False).first()
            if not main_image:
                main_image = self.images.exclude(image='').first()
            if not main_image and self.image:
                return self
            return main_image
        except Exception:
            return None

    def get_thumbnail_url(self):
        try:
            main_image = self.get_main_image()
            if main_image and main_image.image:
                return main_image.image.url
            if self.image:
                return self.image.url
            return self.DEFAULT_IMAGE_URL
        except Exception:
            return self.DEFAULT_IMAGE_URL

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    ordering = models.IntegerField(default=0)
    is_main = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    DEFAULT_IMAGE_URL = '/static/images/default-product.jpg'

    def get_primary_image(self):
        """Return the primary image for this product or the first image if no primary image exists"""
        primary_images = self.images.filter(is_primary=True)
        if primary_images.exists():
            return primary_images.first()
        return self.images.first() if self.images.exists() else None
    
    def get_primary_image_url(self):
        """Return the URL of the primary image or a default image URL"""
        primary_image = self.get_primary_image()
        if primary_image and primary_image.image:
            return primary_image.safe_image_url
        return self.DEFAULT_IMAGE_URL

    def image_exists(self):
        if self.image:
            from django.core.files.storage import default_storage
            return default_storage.exists(self.image.name)
        return False

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).exclude(id=self.id).update(is_main=False)
        elif not ProductImage.objects.filter(product=self.product, is_main=True).exists():
            self.is_main = True
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    @property
    def image_url(self):
        try:
            if self.image and hasattr(self.image, 'url') and self.image.url:
                from django.core.files.storage import default_storage
                if default_storage.exists(self.image.name):
                    return self.image.url
            return Product.DEFAULT_IMAGE_URL
        except (AttributeError, ValueError, Exception) as e:
            return Product.DEFAULT_IMAGE_URL

    @property
    def safe_image_url(self):
        try:
            if self.image and hasattr(self.image, 'url') and self.image.url:
                from django.core.files.storage import default_storage
                if default_storage.exists(self.image.name):
                    return self.image.url
            return self.product.DEFAULT_IMAGE_URL if hasattr(self.product, 'DEFAULT_IMAGE_URL') else ''
        except (AttributeError, ValueError, Exception) as e:
            return self.product.DEFAULT_IMAGE_URL if hasattr(self.product, 'DEFAULT_IMAGE_URL') else ''

class ProductVariation(models.Model):
    product = models.ForeignKey(Product, related_name='variations', on_delete=models.CASCADE)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=10)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    class Meta:
        unique_together = ('product', 'color', 'size')
        verbose_name = 'Product Variation'
        verbose_name_plural = 'Product Variations'
    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size}"
class ProductColor(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7)  # For storing color codes like #FF0000
    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Cart #{self.id} - {self.user.username}"
    
    @property
    def get_cart_total(self):
        """Total = Subtotal + Shipping + Tax"""
        return float(self.get_cart_subtotal) + float(self.get_shipping_cost) + float(self.get_tax)
    
    @property
    def get_cart_items(self):
        """Returns the total number of items in the cart"""
        cart_items = self.cartitem_set.all()
        return sum(item.quantity for item in cart_items)
    
    @property
    def get_cart_subtotal(self):
        """Returns the subtotal of all items in the cart before shipping"""
        cart_items = self.cartitem_set.all()
        return sum(float(item.product.price) * item.quantity for item in cart_items)
    
    @property
    def get_shipping_cost(self):
        """Returns fixed shipping cost of 75"""
        return 75.0
    
    @property
    def get_tax(self):
        """Returns tax as 1/50 of subtotal"""
        return float(self.get_cart_subtotal) * (1/50)

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def get_total(self):
        return float(self.product.price) * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, default='prepaid')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
        
    def save(self, *args, **kwargs):
        # Update payment_status based on order_status
        if self.order_status == 'Cancelled':
            self.payment_status = 'cancelled'
        elif self.order_status != 'Pending':
            self.payment_status = 'paid'
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def get_total(self):
        return self.price * self.quantity