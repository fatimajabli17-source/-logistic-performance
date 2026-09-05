from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0


@register.filter
def badge_class(status):
    mapping = {
        "livree": "success", "realise": "success", "resolu": "success", "clos": "secondary",
        "retardee": "danger", "retarde": "danger", "bloque": "danger", "annule": "secondary", "annulee": "secondary",
        "en_cours": "info", "planifie": "info", "en_transit": "info", "ouvert": "warning",
        "a_faire": "secondary", "dedouane": "success", "arrive": "success",
    }
    return mapping.get(status, "secondary")
