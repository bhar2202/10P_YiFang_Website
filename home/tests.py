from django.test import TestCase

# Create your tests here.
from django.http import HttpResponse
from django.template import loader


def index(request):
    template = loader.get_template("home/index.html")
    return HttpResponse(template.render({}, request))