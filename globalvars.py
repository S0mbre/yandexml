# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Iskander Shafikov <s00mbre@gmail.com>
# GNU General Public License v3.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
This file is part of the Pynxml project hosted at https://github.com/S0mbre/yandexml.

This module contains the global variables used in any other modules.
"""

# debug messages
DEBUGGING = True

# for colorama colored console output
COLORED_OUTPUT = True           # will work only if colorama is installed; set to False to switch off colored output
COLOR_PROMPT = ''
COLOR_HELP = ''
COLOR_ERR = ''
COLOR_STRESS = ''
COLOR_BRIGHT = ''

if COLORED_OUTPUT:
    try:
        import colorama
        colorama.init(autoreset=True)
        COLOR_PROMPT = colorama.Fore.GREEN
        COLOR_HELP = colorama.Fore.YELLOW
        COLOR_ERR = colorama.Fore.RED
        COLOR_STRESS = colorama.Fore.CYAN
        COLOR_BRIGHT = colorama.Style.BRIGHT
    except ImportError:
        COLORED_OUTPUT = False

REQ_TIMEOUT = 5                 # ожидание соединения и ответа (сек.) None = вечно
REQ_HEADERS = {'Content-Type': 'text/xhtml+xml; charset=UTF-8', 
               'Accept': 'application/xhtml+xml,application/xml', 
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
               'Accept-Charset': 'utf-8',
               'Accept-Language': 'ru,en-us',
               'Connection': 'close'}
MAX_QUERY_WORDS = 40
MAX_QUERY_CHARS = 400
MAX_PASSAGES = 5
MAX_RESULTS = 1000
MAX_GROUPS_ON_PAGE = 100
MAX_RESULTS_IN_GROUP = 3

XML_QUERY = \
r"""
<request>    
<query>{{}}</query>
<maxpassages>{}</maxpassages>
<groupings>
<groupby attr="{{}}" mode="{{}}" groups-on-page="{}" docs-in-group="{{}}" />
</groupings>        
</request>
""".format(MAX_PASSAGES, MAX_GROUPS_ON_PAGE)

STOP_SYMBS = list('.,:;?~!@#$%^&*()+=_<>{}[]\\|/"\'')
IPSERVICES = ['https://api.ipify.org', 'https://ident.me', 'https://ipecho.net/plain', 'https://myexternalip.com/raw']
SAMPLE_CAPTCHA_QUERY = 'e48a2b93de1740f48f6de0d45dc4192a'

HTML_LOGO_TEMPLATE_FULL = \
"""
<!DOCTYPE html>
<html>
 <head>
  <meta charset="utf-8">
  <title>{}</title>
  <style>
   .layer1 {{
    background: {};
    {}
   }}
  </style>
 </head> 
 <body><div class="layer1"><a href="https://yandex.ru"><img src="{}" /></a>  {}</div></body>
</html>
"""

HTML_LOGO_TEMPLATE_DIV = \
"""
<div style={{ background: {}; {} }}><a href="https://yandex.ru"><img src="{}" /></a>  {}</div>
"""

DEFAULT_LOGO_STYLE = {'float': 'left', 'padding': '10px', 'width': '120 px', 'font-size': '12pt'}

IMAGE_TYPES = {'gif': '.gif', 'jpeg': '.jpg', 'png': '.png', 'jpg': '.jpg'}