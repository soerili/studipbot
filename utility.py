import re


def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)