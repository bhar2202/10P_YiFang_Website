from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from datetime import datetime
import requests
from home.models import Ingredient, Item, Augmentation, Order, OrdersItem, OrdersItemsAugmentation

forecast = requests.get("https://api.weather.gov/gridpoints/HGX/29,134/forecast").json()['properties']['periods'][0]
#return HttpResponse(template.render({'forecast': forecast}, request))
from django.urls import reverse
from django.shortcuts import render

def index(request):
    template = loader.get_template("home/index.html")
    context = {'forecast': forecast}
    return HttpResponse(template.render(context, request))

def cashier_index(request):
    if request.method == 'POST':
        if request.POST.get("place_order"):
            order = Order(len(Order.objects.all()), None, datetime.now())
            order.save()
            if 'order_items' not in request.session:
                request.session['order_items'] = []
            for item in request.session['order_items']:
                order_item = OrdersItem(
                    len(OrdersItem.objects.all()), 
                    order.order_id, 
                    item.split(',')[0], 
                    None
                )
                
                order_item.save()
                if 'order_item_augs' not in request.session:
                    request.session['order_item_augs'] = []
                for augmentation in request.session['order_item_augs']:
                    if augmentation[0] == item:
                        order_item_aug = OrdersItemsAugmentation(
                            len(OrdersItemsAugmentation.objects.all()), 
                            order_item.pair_id, 
                            augmentation[1]
                        )
                        order_item_aug.save()
            request.session.flush()
        else:
            ice_level = int(request.POST.get('ice'))
            sweetness_level = int(request.POST.get('sweetness'))
            milk_level = int(request.POST.get('milk'))
            milk_type = int(request.POST.get('milktype'))
            toppings = [int(i) for i in request.POST.getlist('toppings')]
            augmentations = [ice_level, sweetness_level, milk_type * 5 + milk_level, *tuple(toppings)]
            if 'order_items' not in request.session:
                request.session['order_items'] = []
            item_id = f"{request.session['item_id']},{len(request.session['order_items'])}"
            request.session['order_items'].append(item_id)
            if 'order_item_augs' not in request.session:
                request.session['order_item_augs'] = []
            if 'total_price' not in request.session:
                request.session['total_price'] = 0
            request.session['total_price'] += Item.objects.get(item_id=request.session['item_id']).price
            for aug in augmentations:
                request.session['total_price'] += Augmentation.objects.get(augmentation_id=aug).price
            for augmentation_id in augmentations:
                request.session['order_item_augs'].append((item_id, augmentation_id))
    else:
        request.session.flush()

    request.session.modified = True
    template = loader.get_template("home/cashier/index.html")
    items = Item.objects.order_by('category').all()
    context = {
        'forecast': forecast,
        'items': items
    }
    return HttpResponse(template.render(context, request))

def cashier_edit_cart(request):
    template = loader.get_template("home/cashier/edit_cart.html")
    items = []
    if 'order_items' in request.session:
        items = [Item.objects.get(item_id=i.split(',')[0]) for i in request.session['order_items']]
    total_price = request.session.get('total_price', 0)
    context = {
        'forecast': forecast,
        'items': items,
        'total_price': total_price
    }
    return HttpResponse(template.render(context, request))

def cashier_tea_specifications(request):
    if request.method == "POST":
        item = request.POST.get('item', None)

    template = loader.get_template("home/cashier/tea_specifications.html")

    if item != None:
        item = Item.objects.get(item_id=item)

    request.session['item_id'] = item.item_id

    request.session.modified = True
    
    context = {
        'forecast': forecast,
        'item': item
    }
    return HttpResponse(template.render(context, request))

def manager_inventory(request):
    template = loader.get_template("home/manager/inventory.html")
    ingredients = Ingredient.objects.order_by('name').all()
    context = {
        'forecast': forecast,
        'ingredients': ingredients
    }
    return HttpResponse(template.render(context, request))

def manager_item_fill_level(request):
    if request.method == "POST":
        # Handle the form submission
        id = request.POST.get("ingredient")
        new_fill_level = request.POST.get("new_fill_level")
        restock = request.POST.get("restock")

    template = loader.get_template("home/manager/item_fill_level.html")

    # Handle Item Click / Reload Page (using session)
    if (id == None):
        id = request.session['ingredient']
    else:
        request.session['ingredient'] = id

    ingredient = Ingredient.objects.get(ingredient_id = id)

    # Handle 'Set Fill Level'
    if new_fill_level:
        ingredient.fill_level = float(new_fill_level)
    else:
        new_fill_level = ingredient.fill_level

    # Handle 'Restock to Fill Level'
    if restock:
        ingredient.amount = ingredient.fill_level

    ingredient.save()
    request.session.modified = True

    context = {
        'forecast': forecast,
        'ingredient': ingredient,
        'new_fill_level': new_fill_level,
    }
    return HttpResponse(template.render(context, request))

def manager_index(request):
    template = loader.get_template("home/manager/index.html")
    return HttpResponse(template.render({}, request))

def manager_order_history(request):
    template = loader.get_template("home/manager/order_history.html")
    return HttpResponse(template.render({}, request))

def manager_order_trends(request):
    template = loader.get_template("home/manager/order_trends.html")
    return HttpResponse(template.render({}, request))

def manager_order_trends_graph(request):
    template = loader.get_template("home/manager/order_trends_graph.html")
    return HttpResponse(template.render({}, request))

def menu(request):
    template = loader.get_template("home/menu.html")
    return HttpResponse(template.render({}, request))

def customer(request):
    template = loader.get_template("home/customer.html")
    return HttpResponse(template.render({}, request))

