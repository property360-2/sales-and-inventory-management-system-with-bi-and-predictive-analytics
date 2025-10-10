from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model with branch association"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=20, blank=True)
    branches = models.ManyToManyField('inventory.Branch', related_name='users', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    def is_manager(self):
        return self.role in ['admin', 'manager'] or self.is_superuser
    
    def can_access_branch(self, branch):
        """Check if user has access to a specific branch"""
        if self.is_admin():
            return True
        return self.branches.filter(id=branch.id).exists()