from django.http import HttpResponse
from django.template import loader
import requests
from home.models import Ingredient, Item

forecast = requests.get("https://api.weather.gov/gridpoints/HGX/29,134/forecast").json()['properties']['periods'][0]

def index(request):
    template = loader.get_template("home/index.html")
    context = {'forecast': forecast}
    return HttpResponse(template.render(context, request))

def cashier_index(request):
    template = loader.get_template("home/cashier/index.html")
    items = Item.objects.order_by('category').all()
    context = {
        'forecast': forecast,
        'items': items
    }
    return HttpResponse(template.render(context, request))

def cashier_edit_cart(request):
    template = loader.get_template("home/cashier/edit_cart.html")
    return HttpResponse(template.render({}, request))

def cashier_tea_specifications(request):
    if request.method == "POST":
        item = request.POST.get('item', None)

    template = loader.get_template("home/cashier/tea_specifications.html")

    if item != None:
        item = Item.objects.get(item_id=item)
    
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
