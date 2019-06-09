# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Iskander Shafikov <s00mbre@gmail.com>
# GNU General Public License v3.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
This file is part of the Pynxml project hosted at https://github.com/S0mbre/yandexml.

This module provides a testing-ground for the Yandex API engine. 
Inside its main() function, a Yandexml object is initialized and then used by a number of
nested functions to do various stuff. 

Use this module like this:
python tester.py "your-username" "your-apikey"

For the 'ip' argument, your current IP will be guessed by the engine. If you'd like to change this and other
arguments, just use the object's reset() method at any point after initialization.
"""

import sys
from yandexmlengine import Yandexml
import webbrowser

## ******************************************************************************** ##

def captcha_callback(captcha_url):
    webbrowser.open_new_tab(captcha_url)
    print('\tEnter captcha text (see your browser) >', end='\t')
    return str(input())

def main():
    if len(sys.argv) != 3:
        print('USAGE: tester.py <username> <apikey>')
        return
        
    user = sys.argv[1]
    api = sys.argv[2]
    mode = 'world'
    query = "Let me not to the marriage of true minds admit impediments"
    
    yxml = Yandexml(user, api, mode, captcha_solver=captcha_callback)
    
    def run1():
        yxml.process_captcha(yxml._get_sample_captcha(), 5)
        return
            
    def run2(): 
        if not yxml.search(query, False): return
        print('Query "{}" returned {} results\n\n\n\n'.format(yxml.query, yxml.found))
            
    def run3():
        for group in yxml.groups[:min(20, len(yxml.groups))]:
            print('\n\n----------------\nDOMAIN "{}": {}'.format(group['name'], group['count']))
            for doc in group['docs']:
                print('\n\tURL: {}\n\tTITLE: {}\n\tHEADLINE: {}\n\tLANGUAGE: {}\n\tMODIFIED: {}\n\tPASSAGES: {}'.format(
                        doc['url'], doc['title'], doc['headline'], doc['language'], doc['modified'],  
                        '\n\t\t'.join(doc['passages']) if doc['passages'] else ''))
        
    def run4():
        next_lim = yxml.next_limits 
        if next_lim:
            print('Daily limit = {} for {}'.format(next_lim[1], str(next_lim[0])))
            
    def run5():
        htm = yxml.yandex_logo('white', True, 'LOGO')
        with open('htmlogo.html', 'w') as f:
            f.write(htm)
        webbrowser.open_new_tab('htmlogo.html')
        
    def run6():
        yxml.output_results('json')

    run2()
    run6()

## ******************************************************************************** ##    
       
if __name__ == '__main__':
    main()