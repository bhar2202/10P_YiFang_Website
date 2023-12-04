from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from datetime import datetime
import requests
from django.db.models import Count, Sum
from home.models import Ingredient, Item, ItemsIngredient, Augmentation, Order, OrdersItem, OrdersItemsAugmentation
from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import render

# weather API
forecast = requests.get("https://api.weather.gov/gridpoints/HGX/29,134/forecast").json()['properties']['periods'][0]
#return HttpResponse(template.render({'forecast': forecast}, request))

# home page, diverges into cashier / manager.
def index(request):
    template = loader.get_template("home/index.html")
    context = {'forecast': forecast}
    return HttpResponse(template.render(context, request))

# home page of cashier - includes menu items.
def cashier_index(request):
    if request.method == 'POST':

        #delete button functionality
        if request.POST.get("delete"):
            print("delete")
            item_to_delete_id = request.POST.get("delete")
            print("hi",request.session['order_items'])
            updated_order_items = []
            deleted = False

            for item in request.session.get('order_items', []):
                if item.split(',')[0] == item_to_delete_id and not deleted:
                    deleted = True  
                    continue  
                updated_order_items.append(item)

            request.session['order_items'] = updated_order_items
            total_price = 0
            for item in request.session['order_items']:
                item_id = item.split(',')[0]
                total_price += Item.objects.get(item_id=item_id).price
                for augmentation in request.session.get('order_item_augs', []):
                    if augmentation[0] == item:
                        total_price += Augmentation.objects.get(augmentation_id=augmentation[1]).price
            
            request.session['total_price'] = total_price
            request.session.modified = True
            print("final",request.session['order_items'])

            item_ids_in_session = [item.split(',')[0] for item in request.session['order_items']]
            items = Item.objects.filter(item_id__in=item_ids_in_session).order_by('category')
            context = {
                'forecast': forecast,
                'items': items,
                'total_price': total_price
            }

            template = loader.get_template("home/cashier/edit_cart.html")
            return HttpResponse(template.render(context, request))

        if request.POST.get("place_order"):
            #checking to see if there are enough ingredients to place an order
            total_ingredients_required = {}

            for item in request.session.get('order_items', []):
                itemid = item.split(',')[0]
                for item_ingredient in ItemsIngredient.objects.filter(item_id=itemid):
                    total_ingredients_required[item_ingredient.ingredient_id] = (
                        total_ingredients_required.get(item_ingredient.ingredient_id, 0) 
                        + item_ingredient.amount
                    )

            ignore_augmentation_ids = [20, 21, 22, 23, 24] # Ice
            for augmentation in request.session.get('order_item_augs', []):
                if augmentation[0] == item and augmentation[1] not in ignore_augmentation_ids:
                    augmentation_obj = Augmentation.objects.get(augmentation_id=augmentation[1])
                    total_ingredients_required[augmentation_obj.ingredient_id] = (
                        total_ingredients_required.get(augmentation_obj.ingredient_id, 0) 
                        + augmentation_obj.amount
                    )
            item_ids_in_session = [item.split(',')[0] for item in request.session['order_items']]
            items = Item.objects.filter(item_id__in=item_ids_in_session).order_by('category')
            for ingredient_id, required_amount in total_ingredients_required.items():
                ingredient = Ingredient.objects.get(ingredient_id=ingredient_id)
                if ingredient.amount < required_amount:
                    total_price=0
                    context = {
                        'forecast': forecast,
                        'items': items,
                        'total_price': total_price,
                        'message': 'Cannot place order due to insufficient ingredients.',
                    }
                    template = loader.get_template("home/cashier/edit_cart.html")
                    return HttpResponse(template.render(context, request))

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
                
                for item in request.session['order_items']:
                    itemid = item.split(',')[0]
                    print("itemid:", itemid) #getting the correct item id
                    ingredients_used = ItemsIngredient.objects.filter(item_id=itemid)
                    print("ingre:", ingredients_used)
                    for ingredient_used in ingredients_used:
                        print("Ingredient ID:", ingredient_used.ingredient_id)
                        print("Amount used:", ingredient_used.amount)
                        ingredient = Ingredient.objects.get(ingredient_id=ingredient_used.ingredient_id)
                        print(ingredient.amount)
                        ingredient.amount -= ingredient_used.amount
                        ingredient.save()


                ignore_augmentation_ids = [20,21,22,23,24] #ice
                for augmentation in request.session['order_item_augs']:
                    print("order_item_augs:",request.session['order_item_augs'])
                    if augmentation[0] == item:
                        print("augmentation[0]:",augmentation[0],item)
                        aug_id = augmentation[1]
                        print("aug_id",aug_id)
                        if aug_id in ignore_augmentation_ids:
                            continue
                        augmentation_obj = Augmentation.objects.get(augmentation_id=aug_id)
                        ingredient = Ingredient.objects.get(ingredient_id=augmentation_obj.ingredient_id)
                        ingredient.amount -= augmentation_obj.amount
                        ingredient.save()
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
        'items': items,
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

# View inventory items whose stock is below 20% of fill level
def manager_restock_report(request):
    template = loader.get_template("home/manager/restock_report.html")
    ingredient_rows = Ingredient.objects.order_by('name').all()
    ingredients = [ingredient for ingredient in ingredient_rows if ingredient.amount / ingredient.fill_level < 0.2]
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
    
    orders = Order.objects.order_by('-order_id').all()
    orders = orders[:100]
    prices = []
    items_strings = []
    for order in orders:
        items = OrdersItem.objects.filter(order_id=order.order_id)
        item_string = ""
        total_price = 0.0
        for obj in items:
            item_string += obj.item.name + ", "
            # ordersAug = OrdersItemsAugmentation.objects.filter(order_id=order.order_id,item_id=obj.item.item_id)
            total_price += obj.item.price

        item_string = item_string[:-2] #removes last ", " 
        items_strings.append(item_string)
        prices.append(total_price)

        # items += OrdersItem.objects.filter(order_id=orders[i].order_id)

    # employees = []
    # for order in orders:
    #         employees.append(Employee.objects.get(employee_id=order.employee.employeeID).name)

    data = zip(orders, items_strings, prices)

    context = {
        'data':data,
    }
    return HttpResponse(template.render(context, request))

def manager_excess_report(request):
    if request.method == "POST":
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        initial_inventory = Ingredient.objects.all().values("ingredient_id", "name", "amount")

        ingredient_usage = OrdersItem.objects.filter(
            order__time__range=[start_time, end_time]
        ).values('item__itemsingredient__ingredient_id').annotate(
            total_used=Sum('item__itemsingredient__amount')
        ).order_by()

        excess_inventory = []
        for ingredient in initial_inventory:
            usage = next((usage for usage in ingredient_usage if usage["item__itemsingredient__ingredient_id"] == ingredient["ingredient_id"]), None)
            if usage:
                percentage_used = (usage["total_used"] / ingredient["amount"]) * 100
                if percentage_used < 10:
                    excess_inventory.append(ingredient["name"])

        context = {'excess_inventory': excess_inventory}
        return render(request, 'home/manager/excess_report.html', context)
    else:
        return render(request, 'home/manager/excess_report.html')

# View order trends.
def manager_order_trends(request):
    if request.method == "POST":
        item = request.POST.get("item")
        start = datetime.strptime(request.POST.get("start"), "%Y-%m-%dT%H:%M")
        end = datetime.strptime(request.POST.get("end"), "%Y-%m-%dT%H:%M")
        interval = (end - start) / 15
        current = start
        sales_data = {}
        while current < end:
            item_sales = OrdersItem.objects.filter(order__time__gte=current, order__time__lte=(current+interval), item__name=item).aggregate(Sum("item__price"))
            augmentation_sales = OrdersItemsAugmentation.objects.filter(pair__order__time__gte=current, pair__order__time__lte=(current+interval), pair__item__name=item).aggregate(Sum("augmentation__price"))
            sales_data[current] = 0
            if item_sales:
                sales_data[current] += item_sales["item__price__sum"] if item_sales["item__price__sum"] else 0
            if augmentation_sales:
                sales_data[current] += augmentation_sales["augmentation__price__sum"] if augmentation_sales["augmentation__price__sum"] else 0
            current += interval
        labels = [label for label in sales_data]
        values = [sales_data[label] for label in sales_data]
        start = start.strftime("%Y-%m-%d %H:%M")
        end = end.strftime("%Y-%m-%d %H:%M")
    else:
        start = end = "2022-12-01 00:00"
        labels = values = []
    items = Item.objects.values("name").annotate(dcount=Count("name")).all()

    template = loader.get_template("home/manager/order_trends.html")
    context = {
        "forecast": forecast,
        "start": start,
        "end": end,
        "items": items,
        "labels": labels,
        "values": values,
    }
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

def manager_start_screen(request):
    template = loader.get_template("home/manager/index.html")
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


