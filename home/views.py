from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from datetime import datetime
import requests
from django.db.models import Max
from home.models import Ingredient, Item, ItemsIngredient, Augmentation, Order, OrdersItem, OrdersItemsAugmentation

# weather API
forecast = requests.get("https://api.weather.gov/gridpoints/HGX/29,134/forecast").json()['properties']['periods'][0]
#return HttpResponse(template.render({'forecast': forecast}, request))
from django.urls import reverse
from django.shortcuts import render

# home page, diverges into cashier / manager.
def index(request):
    template = loader.get_template("home/index.html")
    context = {'forecast': forecast}
    return HttpResponse(template.render(context, request))

# home page of cashier - includes menu items.
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

# Option to remove items from an order.
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

# Add ice level, sugar, milk, and extra to tea.
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

# View inventory and click an ingredient to view it's fill level.
def manager_inventory(request):
    template = loader.get_template("home/manager/inventory.html")
    ingredients = Ingredient.objects.order_by('name').all()
    context = {
        'forecast': forecast,
        'ingredients': ingredients
    }
    return HttpResponse(template.render(context, request))

# Set fill level and restockk ingredient.
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

# Home page for manager.
def manager_index(request):
    template = loader.get_template("home/manager/index.html")
    return HttpResponse(template.render({}, request))

# View past orders.
def manager_order_history(request):
    template = loader.get_template("home/manager/order_history.html")
    return HttpResponse(template.render({}, request))

# View order trends.
def manager_order_trends(request):
    template = loader.get_template("home/manager/order_trends.html")
    return HttpResponse(template.render({}, request))

# View order trends graph.
def manager_order_trends_graph(request):
    template = loader.get_template("home/manager/order_trends_graph.html")
    return HttpResponse(template.render({}, request))


def cashier_teaspecifications(request):
    if request.method == "POST":
        ice_level = request.POST.get('options')
        sweetness_level = request.POST.get('sweetness')
        milk_level = request.POST.get('milk')
        milk_type = request.POST.get('milktype')
        toppings = request.POST.getlist('toppings')

        # Store the information in the session to be retrieved in the next view
        request.session['tea_details'] = {
            'ice_level': ice_level,
            'sweetness_level': sweetness_level,
            'milk_level': milk_level,
            'milk_type': milk_type,
            'toppings': toppings
        }
        
        return HttpResponseRedirect(reverse('cashier_editcart'))

    template = loader.get_template("home/cashier/tea_specifications.html")
    return HttpResponse(template.render({}, request))

def cashier_editcart(request):
    tea_details = request.session.get('tea_details', {})

    context = {
        'ice_level': tea_details.get('ice_level'),
        'sweetness_level': tea_details.get('sweetness_level'),
        'milk_level': tea_details.get('milk_level'),
        'milk_type': tea_details.get('milk_type'),
        'toppings': tea_details.get('toppings', [])
    }

    template = loader.get_template("home/cashier/editcart.html")
    return HttpResponse(template.render(context, request))

def menu(request):

    # if request.method != 'POST':
    #     request.session.flush()

    # request.session.modified = True
    # all_items = Item.objects.all()
    # processed_items = set()
    # unique_items = []

    # for item in all_items:
    #     if item.name not in processed_items:
    #         unique_items.append(item)
    #         processed_items.add(item.name)

    # context = {
    #     'forecast': forecast,  
    #     'items': unique_items
    # }
    # return render(request, "home/menu/menu.html", context)

    request.session.modified = True
    template = loader.get_template("home/menu/index.html")
    items = Item.objects.order_by('category').all()
    images = {}
    for item in items:
        if item.item_id < 129:
            images[item.item_id] = f"tea/{item.item_id // 3}.jpg"
        else:
            images[item.item_id] = "tea/custom.jpg"
    context = {
        'forecast': forecast,
        'items': items,
        'images': images
    }
    return HttpResponse(template.render(context, request))

def customer_index(request):
    # template = loader.get_template("home/customer/index.html")
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
    template = loader.get_template("home/customer/index.html")
    items = Item.objects.order_by('category').all()
    context = {
        'forecast': forecast,
        'items': items
    }
    return HttpResponse(template.render(context, request))

def inventory(request):
    template = loader.get_template("home/inventory.html")
    return HttpResponse(template.render({}, request))

def item_filllevel(request):
    template = loader.get_template("home/itemfilllevel.html")
    return HttpResponse(template.render({}, request))

def manager_startscreen(request):
    template = loader.get_template("home/manager/index.html")
    return HttpResponse(template.render({}, request))

def order_history(request):
    template = loader.get_template("home/orderhistory.html")
    return HttpResponse(template.render({}, request))

def order_trends(request):
    template = loader.get_template("home/ordertrends.html")
    return HttpResponse(template.render({}, request))

def order_trendsgraph(request):
    template = loader.get_template("home/ordertrendsgraph.html")
    return HttpResponse(template.render({}, request))

def manager_login(request):
    template = loader.get_template("home/managerlogin.html")
    return HttpResponse(template.render({}, request))

# Modify ingredient specification within a menu item by clicking on it.
def manager_edit_menu(request):
    if request.method == 'POST':
        updated_amounts = [float(i) for i in request.POST.getlist('ingredient_input')]
        item_id = request.session['item_id']
        item = Item.objects.get(item_id = item_id)
        item.category = request.POST.get('category')
        item.name = request.POST.get('item_name')
        item.size = request.POST.get('size')
        item.price = request.POST.get('price')
        item.save()
        for i in range(len(updated_amounts)):
            amount = updated_amounts[i]
            item_ingredient = ItemsIngredient.objects.filter(item=item, ingredient=i)
            item_ingredient = item_ingredient[0] if len(item_ingredient) else 0
            if item_ingredient:
                item_ingredient.amount = amount
                item_ingredient.save()
            elif amount:
                ingredient = Ingredient.objects.get(ingredient_id=i)
                item_ingredient = ItemsIngredient(
                    pair_id = len(ItemsIngredient.objects.all()),
                    item = item,
                    ingredient_id = i,
                    amount = amount,
                    unit = ingredient.unit
                )
                item_ingredient.save()
        request.session.clear()
        request.modified = True
            

    template = loader.get_template("home/manager/edit_menu.html")
    items = Item.objects.order_by('category', 'item_id').all()
    context = {
        'forecast': forecast,
        'items': items
    }


    return HttpResponse(template.render(context, request))

# Add a new item to the menu. Specify ingredients and amounts.
def manager_add_item(request):
    if request.method == "POST":
        # Handle the form submission
        name,size = tuple(request.POST.get("item").split(","))
        id = Item.objects.filter(name=name,size=size)[0].item_id
        request.session['item_id'] = id
        request.session.modified = True
        item_ingredients_list = ItemsIngredient.objects.order_by('ingredient__name').filter(item_id = id)
        
        item = Item.objects.get(item_id = id)
    else: 
        item_ingredients_list = []
        item = Item(len(Item.objects.all()), "", "Tea", 0, 0)
        item.save()
        request.session['item_id'] = item.item_id
        request.session.modified = True

    ingredients = Ingredient.objects.order_by('ingredient_id').all()
    item_ingredients_dict = {}
    for item_ingredient in item_ingredients_list:
        item_ingredients_dict[item_ingredient.ingredient.name] = item_ingredient.amount

    template = loader.get_template("home/manager/add_item.html")
    
    context = {
        'forecast': forecast,
        'ingredients': ingredients,
        'item_ingredients': item_ingredients_dict,
        'item': item
    }


    return HttpResponse(template.render(context, request))

def cashier_login(request):
    template = loader.get_template("home/cashierlogin.html")
    return HttpResponse(template.render({}, request))


