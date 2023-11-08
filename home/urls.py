from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("cashier/", views.cashier_index, name="cashier_index"),
    path("cashier/cart/edit/", views.cashier_edit_cart, name="cashier_edit_cart"),
    path("cashier/cart/add/", views.cashier_tea_specifications, name="cashier_tea_specifications"),
    path("manager/inventory/", views.manager_inventory, name="manager_inventory"),
    path("manager/inventory/edit/", views.manager_item_fill_level, name="manager_item_fill_level"),
    path("manager/", views.manager_index, name="manager_index"),
    path("manager/orderhistory/", views.manager_order_history, name="manager_order_history"),
    path("manager/ordertrends/", views.manager_order_trends, name="manager_order_trends"),
    path("manager/ordertrends/graph/", views.manager_order_trends_graph, name="order_trends_graph"),

    path("menu/", views.menu, name="menu"),
    path("customer/", views.customer, name="customer"),


]