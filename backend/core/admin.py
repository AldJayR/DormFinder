from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Dorm, Booking, Review, Payment, Amenity

class CustomUserAdmin(UserAdmin):
    # PH-specific admin configuration
    list_display = ('username', 'role', 'phone', 'school_id_number', 'is_verified')
    list_filter = ('role', 'is_verified')
    search_fields = ('username', 'phone', 'school_id_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('PH Information', {
            'fields': ('role', 'phone', 'school_id_number', 'is_verified')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Make encrypted fields read-only
    readonly_fields = ('phone', 'school_id_number')

class DormAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'monthly_rate', 'distance_from_school', 'created_at')
    list_filter = ('owner', 'monthly_rate')
    search_fields = ('name', 'address')
    raw_id_fields = ('owner', 'amenities')
    
    # PH-specific default filters
    list_filter = ('monthly_rate', 'distance_from_school')

class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'dorm', 'move_in_date', 'status', 'created_at')
    list_filter = ('status', 'move_in_date')
    raw_id_fields = ('user', 'dorm')
    
    # PH academic calendar awareness
    date_hierarchy = 'move_in_date'

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'dorm', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    raw_id_fields = ('user', 'dorm')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'method', 'is_verified', 'created_at')
    list_filter = ('method', 'is_verified')
    search_fields = ('reference_number',)
    
    # PH currency formatting
    readonly_fields = ('amount',)

class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

# PH-centric admin site registration
admin.site.register(User, CustomUserAdmin)
admin.site.register(Dorm, DormAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Amenity, AmenityAdmin)

# Optional: Customize admin site header for PH context
admin.site.site_header = "NEUST DormFinder Administration"
admin.site.site_title = "NEUST DormFinder Admin Portal"