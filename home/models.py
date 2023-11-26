from django.db import models


class Employee(models.Model):
    employee_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30, blank=True, null=True)
    level = models.CharField(max_length=30, blank=True, null=True)
    username = models.CharField(max_length=30, blank=True, null=True)
    password = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employees'


class Ingredient(models.Model):
    ingredient_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    amount = models.FloatField()
    unit = models.CharField(max_length=30)
    fill_level = models.FloatField(blank=True, null=True)
    recommended_fill_level = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ingredients'


class Augmentation(models.Model):
    augmentation_id = models.IntegerField(primary_key=True)
    ingredient = models.ForeignKey(Ingredient, models.RESTRICT)
    amount = models.FloatField(blank=True, null=True)
    unit = models.CharField(max_length=30, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    display = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'augmentations'


class Item(models.Model):
    item_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=30)
    price = models.FloatField()
    size = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'items'


class ItemsIngredient(models.Model):
    pair_id = models.IntegerField(primary_key=True)
    item = models.ForeignKey(Item, models.RESTRICT)
    ingredient = models.ForeignKey(Ingredient, models.RESTRICT)
    amount = models.FloatField()
    unit = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'items_ingredients'


class Order(models.Model):
    order_id = models.IntegerField(primary_key=True)
    employee = models.ForeignKey(Employee, models.RESTRICT)
    time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'orders'


class OrdersItem(models.Model):
    pair_id = models.IntegerField(primary_key=True)
    order = models.ForeignKey(Order, models.RESTRICT)
    item = models.ForeignKey(Item, models.RESTRICT)
    info = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders_items'


class OrdersItemsAugmentation(models.Model):
    augmentation_pair_id = models.IntegerField(primary_key=True)
    pair = models.ForeignKey(OrdersItem, models.RESTRICT)
    augmentation = models.ForeignKey(Augmentation, models.RESTRICT)

    class Meta:
        managed = False
        db_table = 'orders_items_augmentations'