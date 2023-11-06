from django.db import models


class Augmentation(models.Model):
    augmentation_id = models.IntegerField(primary_key=True)
    ingredient_id = models.IntegerField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    unit = models.CharField(max_length=30, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    display = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'augmentations'


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
    item_id = models.IntegerField()
    ingredient_id = models.IntegerField()
    amount = models.FloatField()
    unit = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'items_ingredients'


class Order(models.Model):
    order_id = models.IntegerField(primary_key=True)
    employee_id = models.IntegerField(blank=True, null=True)
    time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'orders'


class OrdersItem(models.Model):
    pair_id = models.IntegerField(primary_key=True)
    order_id = models.IntegerField()
    item_id = models.IntegerField()
    info = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders_items'


class OrdersItemsAugmentation(models.Model):
    augmentation_pair_id = models.IntegerField(primary_key=True)
    pair_id = models.IntegerField()
    augmentation_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'orders_items_augmentations'
