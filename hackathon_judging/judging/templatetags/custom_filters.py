from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Look up a dictionary value by key in template"""
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

@register.filter
def get_item(dictionary, key):
    """Alternative dictionary lookup filter"""
    return dictionary.get(key) if dictionary else None