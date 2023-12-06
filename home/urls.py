from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("0VrKZUG9MpZ0I8In0AeW595r183QjHfL/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("employee/", views.employee, name="employee"),

    path("cashier/", views.cashier_index, name="cashier_index"),
    path("cashier/cart/edit/", views.cashier_edit_cart, name="cashier_edit_cart"),
    path("cashier/tea_specifications/", views.cashier_tea_specifications, name="cashier_tea_specifications"),
    path("menu/", views.menu, name="menu"),
    path("customer/", views.customer_index, name="customer_index"),
    path("customer/cart/edit/", views.customer_edit_cart, name="customer_edit_cart"),
    path("customer/tea_specifications/", views.customer_tea_specifications, name="customer_tea_specifications"),


    path("manager/inventory/", views.manager_inventory, name="manager_inventory"),
    path("manager/inventory/edit/", views.manager_item_fill_level, name="manager_item_fill_level"),
    path("manager/", views.manager_index, name="manager_index"),
    path("manager/order_history/", views.manager_order_history, name="manager_order_history"),
    path("manager/order_trends/", views.manager_order_trends, name="manager_order_trends"),
    path("manager/restock_report/", views.manager_restock_report, name="manager_restock_report"),
    path("manager/excess_report/", views.manager_excess_report, name="manager_excess_report"),
    path("manager/edit_menu/", views.manager_edit_menu, name="manager_edit_menu"),
    path("manager/add_item/", views.manager_add_item, name="manager_add_item")

]