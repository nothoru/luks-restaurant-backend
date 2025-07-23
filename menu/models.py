# menu/models.py
from django.db import models

class Categories(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class MenuItems(models.Model):
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name="menu_items")
    name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    @property
    def is_fully_out_of_stock(self):
        return not self.variations.filter(is_available=True, stock_level__gt=0).exists()

    def __str__(self):
        return self.name

class Variations(models.Model):
    menu_item = models.ForeignKey(MenuItems, on_delete=models.CASCADE, related_name="variations")
    size_name = models.CharField(max_length=100) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_level = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)


    class Meta:
        unique_together = ('menu_item', 'size_name')

    def __str__(self):
        return f"{self.menu_item.name} - {self.size_name}"