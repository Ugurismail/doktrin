from django import template
import re

register = template.Library()

@register.filter(name='highlight_mentions')
def highlight_mentions(text):
    """@mention'ları vurgular"""
    if not text:
        return text

    # @username pattern'i bul ve vurgula
    pattern = r'@(\w+)'

    def replace_mention(match):
        username = match.group(1)
        return f'<span class="mention">@{username}</span>'

    return re.sub(pattern, replace_mention, text)


@register.filter(name='mul')
def mul(value, arg):
    """İki sayıyı çarpar (margin hesaplaması için)"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0
