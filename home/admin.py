from django.contrib import admin
from .models import Item, Cart, CartItem
# Register your models here.

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    pass

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    pass