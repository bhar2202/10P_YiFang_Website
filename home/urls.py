from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("cashier/", views.cashier_index, name="cashier_index"),
    path("cashierlogin/", views.cashier_login, name="cashier_login"),
    path("cashier/editcart/", views.cashier_edit_cart, name="cashier_edit_cart"),
    path("cashier/cart/edit/", views.cashier_edit_cart, name="cashier_edit_cart"),
    path("cashierteaspecifications/", views.cashier_tea_specifications, name="cashier_tea_specifications"),
    path("menu/", views.menu, name="menu"),
    path("customer/", views.customer_index, name="customer_index"),



    path("manager/inventory/", views.manager_inventory, name="manager_inventory"),
    path("manager/inventory/edit/", views.manager_item_fill_level, name="manager_item_fill_level"),
    path("manager/", views.manager_index, name="manager_index"),
    path("manager/orderhistory/", views.manager_order_history, name="manager_order_history"),
    path("manager/ordertrends/", views.manager_order_trends, name="manager_order_trends"),


    path("manager/edit_menu/", views.manager_edit_menu, name="manager_edit_menu"),
    path("manager/add_item/", views.manager_add_item, name="manager_add_item"),

    path("manager/ordertrends/graph/", views.manager_order_trends_graph, name="manager_order_trends_graph"),


]