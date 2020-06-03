import re

import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def error(msg):
    logger.error(msg)


def log(msg):
    logger.info(msg)


def debug(msg):
    logger.debug(msg)
