# menu/admin.py
from django.contrib import admin
from .models import Categories, MenuItems, Variations

class VariationInline(admin.TabularInline):
    model = Variations
    extra = 1 

@admin.register(MenuItems)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_available') 
    list_filter = ('category', 'is_available') 
    inlines = [VariationInline]

admin.site.register(Categories)