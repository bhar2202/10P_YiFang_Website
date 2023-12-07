"""Prepares the backend data and APIs to be displayed on the frontend. """
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import loader
from datetime import datetime
import requests
from django.db.models import Count, Sum
from home.models import Ingredient, Item, ItemsIngredient, Augmentation, Order, OrdersItem, OrdersItemsAugmentation
from django.shortcuts import render
from threading import Thread

# weather API
forecast = requests.get("https://api.weather.gov/gridpoints/HGX/29,134/forecast").json()['properties']['periods'][0]
#return HttpResponse(template.render({'forecast': forecast}, request))

# 
def index(request):
    """home page, diverges into cashier / manager."""
    template = loader.get_template("home/index.html")
    context = {'forecast': forecast}
    return HttpResponse(template.render(context, request))
  
# login redirect, diverges into cashier / manager
def login(request):
    request.session['logged_in'] = True
    request.session.modified = True
    return redirect("/employee/")

#
def logout(request):
    request.session['logged_in'] = False
    request.session.modified = True
    return redirect('/accounts/logout/')

#
def employee(request):
    if redirect_logged_out(request):
        return redirect_logged_out(request)
    template = loader.get_template("home/employee.html")
    context = {'forecast': forecast}
    return HttpResponse(template.render(context, request))

#
def cashier_index(request):
    """home page of cashier - includes menu items."""
    if redirect_logged_out(request):
        return redirect_logged_out(request)
    if request.method == 'POST':

        #delete button functionality
        if request.POST.get("delete"):
            item_to_delete_id = request.POST.get("delete")
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

            item_ids_in_session = [item.split(',')[0] for item in request.session['order_items']]
            items = Item.objects.filter(item_id__in=item_ids_in_session).order_by('category')
            context = {
                'forecast': forecast,
                'items': items,
                'total_price': total_price
            }

            template = loader.get_template("home/cashier/edit_cart.html")
            return HttpResponse(template.render(context, request))

        elif request.POST.get("place_order"):
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
            thread = Thread(target = place_order, args = (request, True, ))
            thread.start()
        elif request.POST.get('category'):
            request.session['category'] = request.POST.get('category')
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
        request.session['logged_in'] = True
        request.session['category'] = Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))[0]['category']

    request.session.modified = True
    template = loader.get_template("home/cashier/index.html")
    
    if 'category' not in request.session:
         request.session['category'] = Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))[0]['category']
    categories = [category['category'] for category in Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))]
    items = Item.objects.order_by('name').filter(category=request.session['category'])
    context = {
        'forecast': forecast,
        'items': items,
        'categories':  categories,
    }
    return HttpResponse(template.render(context, request))

# 
def cashier_edit_cart(request):
    """Option to remove items from an order."""
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
    """Add ice level, sugar, milk, and extra to tea."""
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

# 
def customer_edit_cart(request):
    """Option to remove items from an order."""
    template = loader.get_template("home/customer/edit_cart.html")
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
def customer_tea_specifications(request):
    """Add ice level, sugar, milk, and extra to tea."""
    if request.method == "POST":
        item = request.POST.get('item', None)

    template = loader.get_template("home/customer/tea_specifications.html")

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
    if redirect_logged_out(request):
        return redirect_logged_out(request)
    template = loader.get_template("home/manager/inventory.html")
    ingredients = Ingredient.objects.order_by('name').all()
    context = {
        'forecast': forecast,
        'ingredients': ingredients
    }
    return HttpResponse(template.render(context, request))

# 
def manager_restock_report(request):
    """View inventory items whose stock is below 20% of fill level"""
    if redirect_logged_out(request):
        return redirect_logged_out(request)
    template = loader.get_template("home/manager/restock_report.html")
    ingredient_rows = Ingredient.objects.order_by('name').all()
    ingredients = [ingredient for ingredient in ingredient_rows if ingredient.amount / ingredient.fill_level < 0.2]
    context = {
        'forecast': forecast,
        'ingredients': ingredients
    }
    return HttpResponse(template.render(context, request))

# 
def manager_item_fill_level(request):
    """Set fill level and restockk ingredient."""
    if redirect_logged_out(request):
        return redirect_logged_out(request)
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

# 
def manager_index(request):
    """Home page for manager."""
    if redirect_logged_out(request):
        return redirect_logged_out(request)
    template = loader.get_template("home/manager/index.html")
    return HttpResponse(template.render({}, request))

# 
def manager_order_history(request):
    """View past orders."""
    if redirect_logged_out(request):
        return redirect_logged_out(request)
    template = loader.get_template("home/manager/order_history.html")
    
    orders = Order.objects.order_by('-order_id').all()
    orders = orders[:25]
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
    if redirect_logged_out(request):
        return redirect_logged_out(request)
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        start_datetime = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        end_datetime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')

        orders = Order.objects.filter(time__range=(start_datetime, end_datetime))

        all_ingredients_dict = {ingredient.ingredient_id: ingredient for ingredient in Ingredient.objects.all()}

        ingredient_usage = {ingredient_id: 0 for ingredient_id in all_ingredients_dict}
        if orders.exists():
            item_ingredients_usage = ItemsIngredient.objects.filter(
                item__ordersitem__order__in=orders
            ).values('ingredient_id').annotate(total_amount=Sum('amount'))

            augmentation_ingredients_usage = OrdersItemsAugmentation.objects.filter(
                pair__order__in=orders, 
                augmentation__ingredient_id__isnull=False
            ).values('augmentation__ingredient_id').annotate(total_amount=Sum('augmentation__amount'))

            for usage in item_ingredients_usage:
                ingredient_id = usage['ingredient_id']
                ingredient_usage[ingredient_id] += usage['total_amount']

            for usage in augmentation_ingredients_usage:
                ingredient_id = usage['augmentation__ingredient_id']
                ingredient_usage[ingredient_id] += usage['total_amount']

            excess_inventory = [
                all_ingredients_dict[ingredient_id].name
                for ingredient_id, used_amount in ingredient_usage.items()
                if used_amount < 0.1 * (all_ingredients_dict[ingredient_id].amount+used_amount)
            ]
        else:
            #If no orders exist all ingredients are considered excess
            excess_inventory = list(Ingredient.objects.values_list('name', flat=True))

        context = {
            'excess_inventory': excess_inventory
        }
        return render(request, 'home/manager/excess_report.html', context)
    else:
        return render(request, 'home/manager/excess_report.html')

# View order trends.
def manager_order_trends(request):
    """View order trends."""
    if redirect_logged_out(request):
        return redirect_logged_out(request)
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
    """gets menu data"""
    if request.method == 'POST':
        request.session['category'] = request.POST.get('category')
    else:
        request.session.flush()

    request.session.modified = True
    template = loader.get_template("home/menu/index.html")
    
    if 'category' not in request.session:
         request.session['category'] = Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))[0]['category']
    categories = [category['category'] for category in Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))]
    items = Item.objects.order_by('name').filter(category=request.session['category'])
    images = {}
    for item in items:
        if item.item_id < 129:
            images[item.item_id] = f"tea/{item.item_id // 3}.jpg"
        else:
            images[item.item_id] = "tea/custom.jpg"
    context = {
        'forecast': forecast,
        'categories': categories,
        'items': items,
        'images': images
    }
    return HttpResponse(template.render(context, request))

def customer_index(request):
    """gets menu items for customer to add"""
    # template = loader.get_template("home/customer/index.html")
    if request.method == 'POST':
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
            thread = Thread(target = place_order, args = (request, False, ))
            thread.start()
        elif request.POST.get("category"):
            request.session['category'] = request.POST.get("category")
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

    if 'category' not in request.session:
         request.session['category'] = Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))[0]['category']
    request.session.modified = True
    template = loader.get_template("home/customer/index.html")
    categories = [category['category'] for category in Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))]
    items = Item.objects.order_by('name').filter(category=request.session['category'])
    images = {}
    for item in items:
        if item.item_id < 129:
            images[item.item_id] = f"tea/{item.item_id // 3}.jpg"
        else:
            images[item.item_id] = "tea/custom.jpg"
    context = {
        'forecast': forecast,
        'categories': categories,
        'images': images,
        'items': items,
    }
    return HttpResponse(template.render(context, request))

#
def manager_edit_menu(request):
    """Modify ingredient specification within a menu item by clicking on it."""
    if redirect_logged_out(request):
        return redirect_logged_out(request)
    if request.method == 'POST':
        if request.POST.get('update_item'):
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
            request.session.flush()
            request.session['logged_in'] = True
            request.modified = True
        elif request.POST.get('category'):
            request.session['category'] = request.POST.get('category')
    else:
        request.session.flush()
        request.session['logged_in'] = True
       
    if 'category' not in request.session:
         request.session['category'] = Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))[0]['category']
    template = loader.get_template("home/manager/edit_menu.html")
    categories = [category['category'] for category in Item.objects.order_by('category').values('category').annotate(dcount=Count('category'))]
    items = Item.objects.order_by('name').filter(category=request.session['category'])
    context = {
        'forecast': forecast,
        'items': items,
        'categories': categories,
    }


    return HttpResponse(template.render(context, request))

# 
def manager_add_item(request):
    """Add a new item to the menu. Specify ingredients and amounts."""
    if redirect_logged_out(request):
        return redirect_logged_out(request)
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

def redirect_logged_out(request):
    if 'logged_in' not in request.session or not request.session['logged_in']:
        return redirect("/")
    else:
        return None
        
def place_order(request, logged_in):
    order_items = []
    order_item_augs = []
    if 'order_items' in request.session:
        order_items = request.session['order_items']
    if 'order_item_augs' in request.session:
        order_item_augs = request.session['order_item_augs']
    request.session.flush()
    if logged_in:
        request.session['logged_in'] = True
    order = Order(len(Order.objects.all()), None, datetime.now())
    order.save()
    for item in order_items:
        order_item = OrdersItem(
            len(OrdersItem.objects.all()), 
            order.order_id, 
            item.split(',')[0], 
            None
        )
        
        order_item.save()
        for augmentation in order_item_augs:
            if augmentation[0] == item:
                order_item_aug = OrdersItemsAugmentation(
                    len(OrdersItemsAugmentation.objects.all()), 
                    order_item.pair_id, 
                    augmentation[1]
                )
                order_item_aug.save()
        

        
    for item in order_items:
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
            ingredient.recommended_fill_level += ingredient_used.amount
            ingredient.save()


        ignore_augmentation_ids = [20,21,22,23,24] #ice
        for augmentation in order_item_augs:
            print("order_item_augs:", order_item_augs)
            if augmentation[0] == item:
                print("augmentation[0]:",augmentation[0],item)
                aug_id = augmentation[1]
                print("aug_id",aug_id)
                if aug_id in ignore_augmentation_ids:
                    continue
                augmentation_obj = Augmentation.objects.get(augmentation_id=aug_id)
                ingredient = Ingredient.objects.get(ingredient_id=augmentation_obj.ingredient_id)
                ingredient.amount -= augmentation_obj.amount
                ingredient.recommended_fill_level += augmentation_obj.amount
                ingredient.save()
