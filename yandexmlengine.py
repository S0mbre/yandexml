# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 13:03:48 2019

@author: iskander.shafikov
"""

import sys
import requests
import ipaddress
import xml.etree.ElementTree as ET
from datetime import datetime as dt


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
<groupby attr="{{}}" mode="{{}}" groups-on-page="{}" docs-in-group="{}" />
</groupings>        
</request>
""".format(MAX_PASSAGES, MAX_GROUPS_ON_PAGE, 1)
STOP_SYMBS = list('.,:;?~!@#$%^&*()+=_<>{}[]\\|/"\'')
IPSERVICES = ['https://api.ipify.org', 'https://ident.me', 'https://ipecho.net/plain', 'https://myexternalip.com/raw']
SAMPLE_CAPTCHA_QUERY = 'e48a2b93de1740f48f6de0d45dc4192a'

def clean_spaces(s):
    ss = s.replace('\r\n', ' ').replace('\n', ' ').replace('\t', ' ')
    while '  ' in ss:
        ss = ss.replace('  ', ' ')
    return ss

class YandexXMLError(RuntimeError):
    def __init__(self, message, context=''):
        self.message = message
        self.context = context
        
    def __str__(self):
        return self.message

class YandexXMLRequestError(YandexXMLError):
    def __init__(self, message, context='', errorcode=0):
        self.message = message
        self.context = context
        self.errorcode = errorcode
        
    def __str__(self):
        return 'ERROR {}: {}'.format(self.errorcode, self.message)

class Yandexml:
    
    """
    Yandex.XML homepage: https://tech.yandex.ru/xml/
    Yandex.XML docs: https://tech.yandex.ru/xml/doc/dg/concepts/about-docpage/
    """
    
    
    
    def __init__(self, username, apikey, searchmode='world', hostip=None, proxies=None, captcha_callback=None):                
        self.user = username
        self.apikey = apikey
        self.proxies = proxies
        self.captcha_callback = captcha_callback       # foo(captcha_img_url) --> reply [str]
        self.search_cookies = None
        if searchmode in ('world', 'ru'):
            self.mode = searchmode 
        else:
            print('Параметр searchmode должен быть либо "world" либо "ru"!', file=sys.stderr)
            raise ValueError
        self.ip = ipaddress.ip_address(hostip if hostip else self._get_ip())
        self.search_headers = dict(REQ_HEADERS) 
        self.search_headers['X-Real-Ip'] = str(self.ip)
        self.make_search_url()
        self._retry_cnt = 0
        self._nullify(True, True)
    
    def make_search_url(self):
        self.baseurl = 'https://yandex.{}/search/xml?l10n={}&user={}&key={}&filter=none'.format(
                'com' if self.mode == 'world' else 'ru',
                'en' if self.mode == 'world' else 'ru', 
                self.user, self.apikey)
        self.limitsurl = 'https://yandex.{}/search/xml?action=limits-info&user={}&key={}'.format(
                'com' if self.mode == 'world' else 'ru', self.user, self.apikey)
        
    def search(self, query):
        
        query = clean_spaces(query)[:MAX_QUERY_CHARS]
        qs = query.split()
        query = ' '.join(qs[:min(len(qs), MAX_QUERY_WORDS)])
        query_body = XML_QUERY.format(query, 'd', 'deep')
        #print(query_body)
        
        try:
            if self.search_cookies and 'Set-Cookie' in self.search_cookies:
                self.search_headers['Set-Cookie'] = self.search_cookies['Set-Cookie']
            
            response = requests.post(self.baseurl, data=bytes(query_body, 'utf-8'), 
                                     headers=self.search_headers, proxies=self.proxies, timeout=REQ_TIMEOUT,
                                     cookies=self.search_cookies)
            
            #print(response.headers)
            #print(response.cookies)
            
            return self.parse_results(response.text)
            
        except Exception as err:
            print(str(err), file=sys.stderr)
            return False
        
    def parse_results(self, result_xml):        
        """
        Final properties structure: 
            REQUEST:
            * query [str]
            * page [int]
            * maxpassages [int]
            * grouped [bool]
            * groups_on_page [int]
            * results_in_group [int]
            RESULTS:
            * found [int]
            * found_human [str]
            * groups [list]
                ** group [dict]
                    *** name [str]
                    *** count [int]
                    *** docs [list]
                        **** doc [dict]
                            ***** url [str]
                            ***** domain [str]
                            ***** title [str]
                            ***** modtime [str]
                            ***** passages [list]
                                ****** passage [str]
                                ...
                        ...
                ...
        """
        
        self._nullify(True, False)        
        
        try:
            tree = ET.fromstring(result_xml)
            
            node_response = tree.find('./response')
            if node_response is None:
                raise YandexXMLError('В возвращенном результате нет секции "response"', result_xml)
                
            yxml_error = node_response.find('error')
            if not yxml_error is None:
                raise YandexXMLRequestError(yxml_error.text, result_xml, int(yxml_error.get('code')))
            
            node_request = tree.find('./request')
            if node_request is None:
                raise YandexXMLError('В возвращенном результате нет секции "request"', result_xml)
                
            self.query = self._get_node(node_request, 'query')
            self.page = int(self._get_node(node_request, 'page', '0'))
            self.maxpassages = int(self._get_node(node_request, 'maxpassages', '0'))
            self.grouped = node_request.find('groupings/groupby').get('attr') == 'd'
            self.groups_on_page = int(node_request.find('groupings/groupby').get('groups-on-page'))
            self.results_in_group = int(node_request.find('groupings/groupby').get('docs-in-group'))
            
            node_results = node_response.find('results/grouping')
            if node_results is None:
                raise YandexXMLError('В возвращенном результате нет секции "results/grouping"', result_xml)
            
            self.found = int(self._get_node(node_results, "found-docs[@priority='all']", '0'))
            self.found_human = self._get_node(node_results, 'found-docs-human')
            
            for group in node_results.iter('group'):
                dic_gr = {'name': group.find('categ').get('name'), 'count': int(self._get_node(group, 'doccount', '0')), 'docs': []}
                
                for doc in group.iter('doc'):
                    dic_gr['docs'].append({'url': self._get_node(doc, 'url'), 'domain': self._get_node(doc, 'domain'),
                                          'title': self._get_node(doc, 'title'), 'modtime': self._get_node(doc, 'modtime'),
                                          'passages': [p.text for p in doc.findall('passages/passage')],
                                          'saved-copy-url': self._get_node(doc, 'saved-copy-url')})
                self.groups.append(dic_gr)
            
            self._retry_cnt = 0
            return True
            
        except ET.ParseError as err:
            print(str(err) + '\nВозможно, результат возвращен не в формате XML.', file=sys.stderr)
            return False
        
        except YandexXMLRequestError as err:
            print('{}\nПОЛНЫЙ ТЕКСТ ОТВЕТА СЕРВЕРА:\n{}'.format(str(err), err.context), file=sys.stderr)
            
            # Коды ошибок: https://tech.yandex.ru/xml/doc/dg/reference/error-codes-docpage/
            if err.errorcode == 32: 
                # кончились лимиты запросов
                print('\nОбратитель к свойству "next_limits" для определения количества оставшихся запросов на ближайши{}.'.format(
                        'й час' if self.mode == 'ru' else 'е сутки'))
                
            elif err.errorcode == 48:
                print('\nПроверьте параметр "mode" (должен соответствовать типу поиска для вашего зарегистрированного IP)')
                
            elif err.errorcode == 100:
                # защита от робота, запрос капча                
                return self.process_captcha(result_xml)
                
            return False
        
        except YandexXMLError as err:
            print('{}\nПОЛНЫЙ ТЕКСТ ОТВЕТА СЕРВЕРА:\n{}'.format(str(err), err.context), file=sys.stderr)
            return False
        
        except Exception as err:
            print(str(err), file=sys.stderr)
            return False
        
    def parse_limits(self, result_xml):
        
        self._nullify(False, True)
        try:
            tree = ET.fromstring(result_xml)
            node_response = tree.find('./response/limits')
            if node_response is None:
                raise YandexXMLError('В возвращенном результате нет секции "response/limits"')
            day_limit = 0
            for interval in node_response.iter('time-interval'):
                try:
                    lim = int(interval.text)
                except ValueError:
                    lim = 0               
                if self.mode == 'ru':
                    day_limit += lim
                    self.hour_limits['hours'].append((dt.strptime(interval.get('from'), '%Y-%m-%d %H-%M-%S %z'), lim))
                else:
                    day_limit = lim
                    break
                
            if self.hour_limits['hours']:
                self.hour_limits['hours'].sort(key=lambda tup: tup[0])
                
            self.hour_limits['day'] = day_limit
            
            return True
            
        except ET.ParseError as err:
            print(str(err) + '\nВозможно, результат возвращен не в формате XML.', file=sys.stderr)
            return False
        
        except Exception as err:
            print(str(err), file=sys.stderr)
            return False
        
    def query_limits(self):
        """
        Запрашивает лимит запросов Яндекс.XML на ближайшие сутки (по часам).
        https://tech.yandex.ru/xml/doc/dg/concepts/limits-docpage/
        """
        try:
            response = requests.get(self.limitsurl, headers=REQ_HEADERS, proxies=self.proxies, timeout=REQ_TIMEOUT)
            return self.parse_limits(response.text)
            
        except Exception as err:
            print(str(err), file=sys.stderr)
            return False
        
    @property
    def next_limits(self):
        """
        Извлекает количество оставшихся запросов на ближайший час (или сутки).
        """
        if (self.mode == 'world' and self.hour_limits['day'] == -1) or (self.mode == 'ru' and not self.hour_limits['hours']):
            # надо обновить инфо по лимитам
            if not self.query_limits():
                print('Невозможно обновить данные по лимитам запросов.', file=sys.stderr)
                return None
        if self.mode != 'world':            
            this_time = dt.now()
            for tup in self.hour_limits['hours']:
                if tup[0] > this_time:
                    return tup
        return (dt.today().date(), self.hour_limits['day'])
    
    def process_captcha(self, result_xml, retries=-1):
        """
        При получении от Яндекса запроса на ввод капчи, процессирует ее и 
        заново вводит исходный запрос (передавая необходимые куки) и обрабатывает
        при помощи parse_results().
            ПАРАМЕТРЫ:
            * result_xml - XML текст от Яндекса, содержащий:
                <?xml version="1.0" encoding="utf-8"?>
                <yandexsearch version="1.0">
                <response>
                   <error code="100">Robot request</error>
                </response>
                <captcha-img-url>http://captcha.image.gif</captcha-img-url>
                <captcha-key>Идентификационный номер CAPTCHA</captcha-key>
                <captcha-status>Статус</captcha-status>
                </yandexsearch>
            * retries - количество попыток ввода капчи (отрицательное значение = бесконечно)
        Возвращает True в случае удачи и False в случае неудачи.
        См. описание https://tech.yandex.ru/xml/doc/dg/concepts/captcha-docpage/
        """
        
        # если не задан обработчик капчи (внешняя фнукция)
        if not self.captcha_callback:
            raise YandexXMLError('Не задан обработчик капчи (captcha_callback)')
        
        # если достигли макс. число попыток
        if retries > 0 and self._retry_cnt >= retries:
            raise YandexXMLError('Достигнут лимит попыток ввода капчи')
        
        try:
            # получаем параметры капчи от яндекса из XML... (если их нет -- ошибка парсинга)
            tree = ET.fromstring(result_xml)
            captcha_url = tree.find('./captcha-img-url').text            # URL картинки капчи
            captcha_key = tree.find('./captcha-key').text                # ключ капчи
            #captcha_status = tree.find('./captcha-status').text         # статус (если повторная попытка = "failed")
            
            # передаем капчу на обработку в коллбак функцию
            result = self.captcha_callback(captcha_url)
            # функция должна вернуть непустую строку, иначе ошибочка
            if not result: raise YandexXMLError('Ошибка распознания капчи', captcha_url)
            # отправить результат расшифровки вместе с ключом капчи яндексу
            cap_query = 'https://yandex.{}/xcheckcaptcha?key={}&rep={}'.format(
                    'com' if self.mode == 'world' else 'ru', captcha_key, result)
            resp = requests.get(cap_query, proxies=self.proxies, timeout=REQ_TIMEOUT, headers=self.search_headers)
            
            # если в ответе содержится куки "spravka" - сохраняем в надежном месте для будущих запросов
            if 'Set-Cookie' in resp.headers:
                self.search_cookies = resp.cookies
                self.search_cookies['Set-Cookie'] = resp.headers['Set-Cookie'] 
            # получаем текст ответа (XML)    
            rtxt = resp.text
            
            # если это новая капча (предыдущая была неверно распознана)
            if '<error code="100">' in rtxt and '<captcha-status>' in rtxt:
                rem_retries = '' if retries < 0 else ', осталось {} попыток'.format(retries - self._retry_cnt - 1)
                print('Неверно отгадана капча{}'.format(rem_retries), file=sys.stderr)
                # увеличиваем счетчик попыток
                if retries > 0: self._retry_cnt += 1
                # рекурсивно вызываем себя с новым XML
                return self.process_captcha(rtxt, retries)
            
            # если это результаты запроса
            if '<results>' in rtxt and '<found-docs' in rtxt:
                # вызываем parse_results() для обработки результатов
                print('Капча распознана, получены результаты запроса')
                return self.parse_results(rtxt)
            
            # если ответ не содержит ничего из перечисленного и при этом сохранился текст запроса
            if self.query:
                # заново делаем запрос (в него уже будет передан правильный заголовок и куки если есть)
                print('Капча распознана, направляем новый запрос')
                return self.search(self.query)
            
            # сюда попадаем, если и ответ невнятный, и запрос не сохранился
            print('Капча распознана, но нет исходного запроса')
            raise YandexXMLError('Невозможно восстановить запрос после ввода капчи', rtxt)
            
        except ET.ParseError as err:
            print(str(err) + '\nВозможно, результат возвращен не в формате XML.', file=sys.stderr)
            self._retry_cnt = 0
            return False
        
        except YandexXMLError as err:
            print('{}:\n{}'.format(str(err), err.context), file=sys.stderr)
            return False
        
        except Exception as err:
            print(str(err), file=sys.stderr)
            self._retry_cnt = 0
            return False
        
    def _get_sample_captcha(self):
        try:
            resp = requests.get('https://yandex.{}/search/xml?&query={}&user={}&key={}&showmecaptcha=yes'.format(
                    'com' if self.mode == 'world' else 'ru', SAMPLE_CAPTCHA_QUERY, self.user, self.apikey), 
                    proxies=self.proxies, timeout=REQ_TIMEOUT, headers=self.search_headers)                    
            return resp.text
            
        except Exception as err:
            print(str(err), file=sys.stderr)
            return False
        
        
    def _get_node(self, node, nodename, default=''):
            nd = node.find(nodename)
            return nd.text if not nd is None else default
        
    def _nullify(self, nullify_results=True, nullify_limits=False):
        if nullify_results:
            self.__dict__.update({'query': '', 'page': 0, 'maxpassages': 0, 'grouped': True, 
                                  'groups_on_page': 0, 'results_in_group': 0, 
                                  'found': 0, 'found_human': '', 'groups': []})
        if nullify_limits:
            self.hour_limits = {'day': -1, 'hours': []}
            
    def _get_ip(self):
        """
        Вернуть текущий внешний IP хоста.
        """
        for service in IPSERVICES:
            try:
                return requests.get(service, proxies=self.proxies, timeout=REQ_TIMEOUT).text
            except:
                pass
        return ''

        
        
        
        
        