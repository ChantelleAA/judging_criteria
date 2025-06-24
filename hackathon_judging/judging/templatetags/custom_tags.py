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
    """Alternative dictionary lookup filter - handles both string and int keys"""
    if not dictionary:
        return None
    
    # Try to convert key to int if it's a string representation of a number
    try:
        if isinstance(key, str) and key.isdigit():
            key = int(key)
    except (ValueError, TypeError):
        pass
    
    return dictionary.get(key)

@register.filter
def get_nested_value(dictionary, key_path):
    """
    Get nested dictionary value using dot notation
    Usage: {{ judge_scores|get_nested_value:"1.final_score" }}
    """
    if not dictionary:
        return None
        
    keys = str(key_path).split('.')
    value = dictionary
    
    for key in keys:
        try:
            if isinstance(value, dict):
                # Try as string first, then as int
                if key in value:
                    value = value[key]
                elif key.isdigit() and int(key) in value:
                    value = value[int(key)]
                else:
                    return None
            else:
                return None
        except (KeyError, ValueError, TypeError):
            return None
    
    return value