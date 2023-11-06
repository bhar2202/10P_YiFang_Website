from django.contrib import admin

# Register your models here.

# Register your models here.
from django.contrib import admin
from .models import Augmentation, Employee, Item, Order, OrdersItem, OrdersItemsAugmentation, Ingredient, ItemsIngredient


# Add your admin classes here.
class AugmentationAdmin(admin.ModelAdmin):
  list_display = ('augmentation_id', 'ingredient_id', 'amount', 'unit',
                  'price', 'display')
  list_filter = ('augmentation_id', 'ingredient_id', 'amount', 'unit', 'price',
                 'display')


# Add your admin classes here.
class EmployeeAdmin(admin.ModelAdmin):
  list_display = ('employee_id', 'name', 'level', 'username', 'password')
  list_filter = ('employee_id', 'name', 'level', 'username', 'password')


# Add your admin classes here.
class ItemAdmin(admin.ModelAdmin):
  list_display = ('item_id', 'name', 'category', 'price', 'size')
  list_filter = ('item_id', 'name', 'category', 'price', 'size')


  # Add your admin classes here.
class ItemsIngredientAdmin(admin.ModelAdmin):
  list_display = ('pair_id', 'item_id', 'ingredient_id', 'amount', 'unit')
  list_filter = ('pair_id', 'item_id', 'ingredient_id', 'amount', 'unit')


  # Add your admin classes here.
class OrdersAdmin(admin.ModelAdmin):
  list_display = ('order_id', 'employee_id', 'time')
  list_filter = ('order_id', 'employee_id', 'time')


  # Add your admin classes here.
class OrdersItemAdmin(admin.ModelAdmin):
  list_display = ('pair_id', 'order_id', 'item_id', 'info')
  list_filter = ('pair_id', 'order_id', 'item_id', 'info')


  # Add your admin classes here.
class IngredientAdmin(admin.ModelAdmin):
  list_display = ('ingredient_id', 'name', 'amount', 'unit', 'fill_level',
                  'recommended_fill_level')
  list_filter = ('ingredient_id', 'name', 'amount', 'unit', 'fill_level',
                 'recommended_fill_level')


  # Add your admin classes here.
class OrdersItemsAugmentationAdmin(admin.ModelAdmin):
  list_display = ('augmentation_pair_id', 'pair_id', 'augmentation_id')
  list_filter = ('augmentation_pair_id', 'pair_id', 'augmentation_id')


# Register your models here.
admin.site.register(Augmentation, AugmentationAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Order, OrdersAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(ItemsIngredient, ItemsIngredientAdmin)
admin.site.register(OrdersItem, OrdersItemAdmin)
admin.site.register(OrdersItemsAugmentation, OrdersItemsAugmentationAdmin)
