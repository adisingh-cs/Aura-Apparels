from django.db import models
from django.contrib.auth.models import User

class AdminDashboardStats(models.Model):
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_users = models.PositiveIntegerField(default=0)
    total_products = models.PositiveIntegerField(default=0)
    pending_orders = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dashboard Stats - {self.last_updated.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name_plural = "Admin Dashboard Stats"