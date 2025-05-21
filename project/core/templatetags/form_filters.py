from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})  

@register.filter(name='add_attr')
def add_attr(field, attr):
    attrs = {}
    definition = attr.split('=')
    if len(definition) == 2:
        attrs[definition[0]] = definition[1]
        return field.as_widget(attrs=attrs)
    return field