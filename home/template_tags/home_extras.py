from django.template.defaulttags import register

@register.filter
def keyvalue(dict, key):    
    return dict[key]