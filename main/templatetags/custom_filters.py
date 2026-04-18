from django import template

register = template.Library()

@register.filter
def sum_hours(certificates):
    return sum(cert.hours for cert in certificates)