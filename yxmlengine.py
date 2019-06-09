# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Iskander Shafikov <s00mbre@gmail.com>
# GNU General Public License v3.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
This file is part of the Pynxml project hosted at https://github.com/S0mbre/yandexml.

This module implements the main engine - the Yandexml class which does all the work related to
Yandex API search queries. See 'tester.py' and 'yxml.py' for usage examples.
"""

import sys, os
import requests
import ipaddress
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime as dt
from globalvars import *





def print_err(what, file=sys.stderr):
    print(COLOR_ERR + what, file=file)

def print_dbg(what, file=sys.stdout):
    if DEBUGGING:
        print(COLOR_STRESS + what, file=file)
        
def print_help(what, file=sys.stdout):
    print(COLOR_HELP + what, file=file)

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
    
class NoError(RuntimeError):
    pass

class Yandexml:
    
    """
    Yandex.XML homepage: https://tech.yandex.ru/xml/
    Yandex.XML docs: https://tech.yandex.ru/xml/doc/dg/concepts/about-docpage/
    """
    
    
    
    def __init__(self, user, apikey, mode='world', ip='', proxy='', captcha_solver=''):  
        self.reset(user=user, apikey=apikey, mode=mode, ip=ip, proxy=proxy, captcha_solver=captcha_solver)
        
    def reset(self, **kwargs):
        if not kwargs: return
        self.__dict__.update({k: kwargs[k] for k in kwargs if k in('user', 'apikey', 'proxy', 'mode', 'ip', 'captcha_solver')})
        
        if 'proxy' in self.__dict__:
            if isinstance(self.proxy, str):
                self.proxy = {'http': self.proxy, 'https': self.proxy} if self.proxy else None
            elif not isinstance(self.proxy, dict):
                self.proxy = None
        else:
            self.proxy = None
        
        if 'mode' in self.__dict__:
            if self.mode not in ('world', 'ru'): self.mode = 'world'
        else:
            self.mode = 'world'
        
        if 'ip' in self.__dict__:            
            self.ip = ipaddress.ip_address(self.ip if self.ip else self._get_ip())
        else:          
            self.ip = ipaddress.ip_address(self._get_ip())
        
        self.search_cookies = None
        self.search_headers = dict(REQ_HEADERS) 
        self.search_headers['X-Real-Ip'] = str(self.ip)
        self.make_search_url()
        self.raw_results = ''
        self._retry_cnt = 0
        self._last_search_query = None
        self._nullify(True, True)
    
    def make_search_url(self):
        self.baseurl = 'https://yandex.{}/search/xml?l10n={}&user={}&key={}&filter=none'.format(
                'com' if self.mode == 'world' else 'ru',
                'en' if self.mode == 'world' else 'ru', 
                self.user, self.apikey)
        self.limitsurl = 'https://yandex.{}/search/xml?action=limits-info&user={}&key={}'.format(
                'com' if self.mode == 'world' else 'ru', self.user, self.apikey)
        
    def search(self, query, grouped=True):
        
        query = clean_spaces(query)[:MAX_QUERY_CHARS]
        qs = query.split()
        query = ' '.join(qs[:min(len(qs), MAX_QUERY_WORDS)])
        if grouped:
            query_body = XML_QUERY.format(query, 'd', 'deep', MAX_RESULTS_IN_GROUP)
        else:
            query_body = XML_QUERY.format(query, '', 'flat', 1)
        
        try:
            response = requests.post(self.baseurl, data=bytes(query_body, 'utf-8'), 
                                     headers=self.search_headers, proxies=self.proxy, timeout=REQ_TIMEOUT,
                                     cookies=self.search_cookies)
            
            #print(response.headers)
            #print(response.cookies)
            
            self._last_search_query = (query, grouped) 
            self.raw_results = response.text
            return self.parse_results(self.raw_results)
            
        except Exception as err:
            print_err(str(err))
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
                            ***** headline [str]
                            ***** modified [datetime]
                            ***** size [int]
                            ***** type [str]
                            ***** charset [str]
                            ***** language [str]
                            ***** saved-copy-url [str]
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
                dic_gr = {'name': group.find('categ').get('name') if not group.find('categ') is None else '', 
                          'count': int(self._get_node(group, 'doccount', '0')), 'docs': []}
                
                for doc in group.iter('doc'):
                    dic_gr['docs'].append({'url': self._get_node(doc, 'url'), 
                                          'domain': self._get_node(doc, 'domain'),
                                          'headline': self._get_node(doc, 'headline'), 
                                          'title': self._get_node(doc, 'title'), 
                                          'modified': dt.strptime(self._get_node(doc, 'modtime'), '%Y%m%dT%H%M%S') if self._get_node(doc, 'modtime') else None,
                                          'passages': [p.text for p in doc.findall('passages/passage') if p.text],
                                          'size': int(self._get_node(doc, 'size', '0')), 
                                          'type': self._get_node(doc, 'mime-type'),
                                          'charset': self._get_node(doc, 'charset'), 
                                          'language': self._get_node(doc.find('properties'), 'lang'),                                          
                                          'saved_copy': self._get_node(doc, 'saved-copy-url')})
                self.groups.append(dic_gr)
            
            self._retry_cnt = 0
            return True
            
        except ET.ParseError as err:
            print_err(str(err) + '\nВозможно, результат возвращен не в формате XML.')
            return False
        
        except YandexXMLRequestError as err:
            print_err('{}'.format(str(err)))
            print_dbg('ПОЛНЫЙ ТЕКСТ ОТВЕТА СЕРВЕРА:\n{}'.format(err.context))
            
            # Коды ошибок: https://tech.yandex.ru/xml/doc/dg/reference/error-codes-docpage/
            if err.errorcode == 32: 
                # кончились лимиты запросов
                print_help('\nОбратитель к свойству "next_limits" для определения количества оставшихся запросов на ближайши{}.'.format(
                        'й час' if self.mode == 'ru' else 'е сутки'))
                
            elif err.errorcode == 48:
                print_help('\nПроверьте параметр "mode" (должен соответствовать типу поиска для вашего зарегистрированного IP)')
                
            elif err.errorcode == 100:
                # защита от робота, запрос капча                
                return self.process_captcha(result_xml)
                
            return False
        
        except YandexXMLError as err:
            print_err('{}'.format(str(err)))
            print_dbg('ПОЛНЫЙ ТЕКСТ ОТВЕТА СЕРВЕРА:\n{}'.format(err.context))
            return False
        
        except Exception as err:
            print_err(str(err))
            return False
        
    def output_results(self, txtformat='txt', out=sys.stdout):
        """
        """
        f = open(out, 'w', encoding='utf-8') if isinstance(out, str) else out
        try:
            if not self.groups:
                raise NoError
                
            if txtformat=='json':
                data = {k: self.__dict__[k] for k in self.__dict__ if k in ('found', 'found_human', 'groups')}
                json.dump(data, f, ensure_ascii=False, indent=4, default=lambda o: str(o) if isinstance(o, dt) else TypeError())
                
            elif txtformat=='xml':
                f.write(self.raw_results)
                
            elif txtformat=='txt':
                print('FOUND: {}\n{}'.format(self.found, self.found_human), file=f)
                for group in self.groups:
                    print('\n\n----------------\nDOMAIN "{}": {}'.format(group['name'], group['count']), file=f)
                    for doc in group['docs']:
                        print('\n\tURL: {}\n\tTITLE: {}\n\tHEADLINE: {}\n\tLANGUAGE: {}\n\tMODIFIED: {}\n\tPASSAGES: {}\n\tSIZE: {}\n\tTYPE: {}\n\tCHARSET: {}\n\tSAVED COPY: {}'.format(
                                doc['url'], doc['title'], doc['headline'], doc['language'], doc['modified'],  
                                '\n\t\t'.join(doc['passages']) if doc['passages'] else '',
                                doc['size'], doc['type'], doc['charset'], doc['saved_copy']), file=f)   
                        
            else:
                print_err('WRONG FILE FORMAT!')
                
        except NoError:
            pass
        
        except Exception as err:
            print_err(str(err))
        
        finally:
            if f != sys.stdout: f.close()        
        
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
            print(str(err) + '\nВозможно, результат возвращен не в формате XML.')
            return False
        
        except Exception as err:
            print_err(str(err))
            return False
        
    def query_limits(self):
        """
        Запрашивает лимит запросов Яндекс.XML на ближайшие сутки (по часам).
        https://tech.yandex.ru/xml/doc/dg/concepts/limits-docpage/
        """
        try:
            response = requests.get(self.limitsurl, headers=REQ_HEADERS, proxies=self.proxy, timeout=REQ_TIMEOUT)
            return self.parse_limits(response.text)
            
        except Exception as err:
            print_err(str(err))
            return False
        
    @property
    def next_limits(self):
        """
        Извлекает количество оставшихся запросов на ближайший час (или сутки).
        """
        if (self.mode == 'world' and self.hour_limits['day'] == -1) or (self.mode == 'ru' and not self.hour_limits['hours']):
            # надо обновить инфо по лимитам
            if not self.query_limits():
                print_err('Невозможно обновить данные по лимитам запросов.')
                return None
        if self.mode != 'world':            
            this_time = dt.now()
            for tup in self.hour_limits['hours']:
                if tup[0] > this_time:
                    return tup
        return (dt.today().date(), self.hour_limits['day'])
    
    def process_captcha(self, result_xml, retries=-1, retrysearch=True):
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
            * retrysearch - после распознания капчи вернуть результаты исходного запроса 
            (если False: вернуть только результат распознания капчи)
        Возвращает True в случае удачи и False в случае неудачи.
        См. описание https://tech.yandex.ru/xml/doc/dg/concepts/captcha-docpage/
        """
        
        # если не задан обработчик капчи (внешняя фнукция)
        if not self.captcha_solver:
            raise YandexXMLError('Не задан обработчик капчи (captcha_solver)')
        
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
            result = self._solve_captcha(captcha_url)
            # функция должна вернуть непустую строку, иначе ошибочка
            if not result: raise YandexXMLError('Ошибка распознания капчи', captcha_url)
            # отправить результат расшифровки вместе с ключом капчи яндексу
            cap_query = 'https://yandex.{}/xcheckcaptcha?key={}&rep={}'.format(
                    'com' if self.mode == 'world' else 'ru', captcha_key, result)
            resp = requests.get(cap_query, proxies=self.proxy, timeout=REQ_TIMEOUT, headers=self.search_headers)
            
            # если в ответе содержится куки "spravka" - сохраняем в надежном месте для будущих запросов
            if 'Set-Cookie' in resp.headers:
                self.search_headers['Set-Cookie'] = resp.headers['Set-Cookie']
                self.search_cookies = resp.cookies # todo: изменить имя домена в куки! см. пример в docs

            # получаем текст ответа (XML)    
            rtxt = resp.text
            
            # если это новая капча (предыдущая была неверно распознана)
            if '<error code="100">' in rtxt and '<captcha-status>' in rtxt:
                rem_retries = '' if retries < 0 else ', осталось {} попыток'.format(retries - self._retry_cnt - 1)
                print_err('Неверно отгадана капча{}'.format(rem_retries))
                # увеличиваем счетчик попыток
                if retries > 0: self._retry_cnt += 1
                # рекурсивно вызываем себя с новым XML
                return self.process_captcha(rtxt, retries, retrysearch)
            
            if not retrysearch: return True
            
            # если это результаты запроса
            if '<results>' in rtxt and '<found-docs' in rtxt:
                # вызываем parse_results() для обработки результатов
                print_dbg('Капча распознана, получены результаты запроса')
                return self.parse_results(rtxt)
            
            # если ответ не содержит ничего из перечисленного и при этом сохранился текст запроса
            if self._last_search_query:
                # заново делаем запрос (в него уже будет передан правильный заголовок и куки если есть)
                print_dbg('Капча распознана, направляем новый запрос')
                return self.search(*self._last_search_query)
            
            # сюда попадаем, если и ответ невнятный, и запрос не сохранился
            print_dbg('Капча распознана, но нет исходного запроса')
            raise YandexXMLError('Невозможно восстановить запрос после ввода капчи', rtxt)
            
        except ET.ParseError as err:
            print(str(err) + '\nВозможно, результат возвращен не в формате XML.')
            self._retry_cnt = 0
            return False
        
        except YandexXMLError as err:
            print_err('{}{}'.format(str(err), ':\n{}'.format(err.context) if err.context else ''))
            self._retry_cnt = 0
            return False
        
        except Exception as err:
            print_err(str(err))
            self._retry_cnt = 0
            return False
        
    def yandex_logo(self, background='white', fullpage=False, title='', **styleparams):
        """
        Возвращает сформированный HTML элемент (div) или страницу с логотипом Яндекса и данными по найденным
        результатам, как указано на https://tech.yandex.ru/xml/doc/dg/concepts/design-requirements-docpage/#design-requirements
        * background [str] = цвет фона (стандартных 3: red, black, white) - в зависимости от него выбирается логотип и цвет шрифта
        * fullpage [bool] = вернуть HTML полной страницы или только элемента (div)
        * title [str] = заголовок страницы (если fullpage == True)
        * styleparams [kwargs] = дополнительные параметры стиля логотипа (передаются в тег style={...}): 
            ширина, высота, наличие рамки, цвет/размер шрифта, расположение контейнера и т.д.
            При отсутствии берутся стандартные настройки стиля из глобальной DEFAULT_LOGO_STYLE,
            при этом цвет шрифта подбирается исходя из параметра background.
        """
        def _get_logo(bg):
            if bg == 'red': return 'assets/yandex-for-red-background.png'
            if bg == 'black': return 'assets/yandex-for-black-background.png'
            return 'assets/yandex-for-white-background.png' 
        
        def _dict2htm(d):
            return str(d)[1:-2].replace(',', ';').replace("'", '')
        
        def _get_fontcolor(bg):
            if bg == 'white': return 'black'
            return 'white'
        
        return HTML_LOGO_TEMPLATE_FULL.format(title, background,
                    _dict2htm(styleparams) if styleparams else '{}; color: {}'.format(_dict2htm(DEFAULT_LOGO_STYLE), _get_fontcolor(background)),
                    _get_logo(background), self.found_human) if fullpage else \
               HTML_LOGO_TEMPLATE_DIV.format(background,
                _dict2htm(styleparams) if styleparams else '{}; color: {}'.format(_dict2htm(DEFAULT_LOGO_STYLE), _get_fontcolor(background)),
                _get_logo(background), self.found_human)
               
    def solve_sample_captcha(self, retries=3):
        """
        """
        if self.process_captcha(self._get_sample_captcha(), retries, False):
            print('КАПЧА РАСПОЗНАНА!')        
        
    def _get_sample_captcha(self):
        try:
            resp = requests.get('https://yandex.{}/search/xml?&query={}&user={}&key={}&showmecaptcha=yes'.format(
                    'com' if self.mode == 'world' else 'ru', SAMPLE_CAPTCHA_QUERY, self.user, self.apikey), 
                    proxies=self.proxy, timeout=REQ_TIMEOUT, headers=self.search_headers) 
            print_dbg(resp.text)                   
            return resp.text
            
        except Exception as err:
            print_err(str(err))
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
                return requests.get(service, proxies=self.proxy, timeout=REQ_TIMEOUT).text
            except:
                pass
        return ''
    
    def _solve_captcha(self, img_url):
        """
        """
        if callable(self.captcha_solver):
            # pointer to function / callback
            return str(self.captcha_solver(img_url))
        
        if isinstance(self.captcha_solver, str):
            # path to external py / exe
            if os.path.isfile(self.captcha_solver):
                params = [self.captcha_solver, img_url]
                if self.captcha_solver.lower().endswith('.py'):
                    params.insert(0, sys.executable)            
                res = subprocess.run(params, stdout=subprocess.PIPE, encoding='utf-8')
                if not res.returncode: return str(res.stdout)
                raise YandexXMLError(str(res.stderr), self.captcha_solver)
            raise NotImplementedError('captcha_solver должна быть путем к файлу *.exe или *.py')               
            
        raise YandexXMLError('Некорректный тип решателя капчи (captcha_solver)!', type(self.captcha_solver).__name__)

        
        
        
        
        