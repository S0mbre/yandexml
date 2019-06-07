# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 14:42:33 2019

@author: iskander.shafikov
"""

import webbrowser
import sys
import fire
from yandexmlengine import Yandexml
from globalvars import *

COMMAND_PROMPT = COLOR_PROMPT + '\nCOMMAND? [w to quit] >'
CAPTCHA_PROMPT = COLOR_PROMPT + '\tEnter captcha text >'
BYE_MSG = COLOR_STRESS + 'QUITTING APP...'
WRONG_CMD_MSG = COLOR_ERR + 'Wrong command! Type "h" for help.'
EMPTY_CMD_MSG = COLOR_ERR + 'Empty command!'

## ******************************************************************************** ## 

def print_splash():
    with open('assets/splash', 'r') as f:
        print(COLOR_STRESS + f.read())
        
## ******************************************************************************** ## 
class Yxml:
    
    def __init__(self, user, apikey, mode='world', ip='', proxy='', captcha_solver='', debug=True):
        global DEBUGGING
        DEBUGGING = debug
        self.engine = Yandexml(user, apikey, mode, ip, proxy, captcha_solver if captcha_solver else Yxml.default_captcha_callback)
        self.commands = {'r': self.reset, 'q': self.query, 'l': self.limits_next, 'L': self.limits_all, 
                'y': self.yandex_logo, 'v': self.view_params, 'h': self.showhelp, 'c': self.sample_captcha, 'w': None}
        self.usage = COLOR_HELP + COLOR_BRIGHT + '\nUSAGE:\t[{}] [value1] [value2] [--param3=value3] [--param4=value4]'.format('|'.join(sorted(self.commands.keys())))
        self.usage2 = COLOR_HELP + '\t' + '\n\t'.join(['{}:{}'.format(fn, self.commands[fn].__doc__) for fn in self.commands if fn != 'w'])
        
    
    def showhelp(self, detail=1):
        """
        Show CLI help.
        
        PARAMS:
            - detail [int]: if == 1: show the "USAGE [...]" string; 
                            if == 2: show comprehensive docs for each command / function
        RETURNS:
            None
        """
        print(self.usage)
        print(COLOR_HELP + 'Enter "h 2" to show more detail.' if detail < 2 else self.usage2)
        
    def run(self):
        """
        Provides a continuously running commandline shell.
        
        The one-letter commands used are listed in the commands dict.
        """
        print_splash()
        entered = ''
        while True:
            try:
                print(COMMAND_PROMPT, end='\t')
                entered = str(input())
                if not entered:
                    print(EMPTY_CMD_MSG)
                    continue
                e = entered[0]
                if e in self.commands:
                    if self.commands[e] is None: 
                        print(BYE_MSG)
                        break
                    cmds = entered.split(' ')
                    fire.Fire(self.commands[e], ' '.join(cmds[1:]) if len(cmds) > 1 else '-')
                else:
                    print(WRONG_CMD_MSG)
                    self.showhelp()
                    continue     
            except KeyboardInterrupt:
                print(BYE_MSG)
                break
            
            except Exception:
                continue
        
    def default_captcha_callback(captcha_url):
        webbrowser.open_new_tab(captcha_url)
        print(CAPTCHA_PROMPT, end='\t')
        return str(input())
    
    def view_params(self, detail=1):
        """
        View engine properties
        
        PARAMS:
            - detail [int]: how many properties to show (1 | 2 | 3, default=1)
        RETURNS:
            [dict] of properties
        """
        params = ['user', 'apikey', 'mode', 'ip']
        if detail > 1: 
            params += ['proxy', 'search_cookies', 'search_headers', 'captcha_solver', 
                       'query', 'page', 'maxpassages', 'grouped', 'groups_on_page', 'results_in_group', 
                       'found', 'found_human', 'hour_limits']
        if detail > 2: 
            params += ['_retry_cnt', 'baseurl', 'limitsurl', '_last_search_query', 'raw_results']
            
        return {k: self.engine.__dict__[k] for k in self.engine.__dict__ if k in params}
        
    def reset(self, **params):
        """
        Reset engine properties
        
        PARAMS:
            - params: keyword args (param1=value1, param2=value2, ...) to set engine properties
        RETURNS:
            Status string
        """
        if not params: return
        self.engine.reset(**params)
        if not self.engine.captcha_solver: 
            self.engine.captcha_solver = Yxml.default_captcha_callback
        return 'Parameters have been reset'
        
    def query(self, querystr='', grouped=True, txtformat='txt', outfile=None):
        """
        Search Yandex and output the search results.
        
        PARAMS:
            - querystr [str]: the search query (as you would type into the Yandex searchbar)
            - grouped [bool]: whether the search results will be grouped by domain name (default) or ungrouped
            - txtformat [str]: one of [txt|json|xml]: the output format for the results
                NOTE: 'txt' will use 'pretty' formatting with human-readable words inserted;
                'json' will output the results as 'dictionary' (with pretty-printing, i.e. indentations);
                'xml' will output the raw XML results from Yandex, including some values not retrieved
                in the other formats
            - outfile [None|str]: path to output file [str] or None to output to console (stdout)
        RETURNS:
            None
        """
        if self.engine.search(querystr, grouped):
            self.engine.output_results(txtformat, sys.stdout if outfile is None else outfile)
            
    def output(self, txtformat='txt', outfile=None):
        """
        Save previous search results to a file or console window.
        
        PARAMS:
            See "query".
        RETURNS:
            None
        """
        self.engine.output_results(txtformat, sys.stdout if outfile is None else outfile) 
        
    def limits_next(self):
        """
        Get the request limit for next hour or current day.
        
        See https://tech.yandex.com/xml/doc/dg/concepts/limits-docpage/ for details.
        RETURNS:
            Formatted output [str] with daily limit.
        """
        lim = self.engine.next_limits        
        return 'Limit = {} for {}'.format(lim[1], str(lim[0])) if lim else ''
    
    def limits_all(self):
        """
        Get the request limits for current day by hours (if applicable) and for whole day.
        
        See https://tech.yandex.com/xml/doc/dg/concepts/limits-docpage/ for details.
        RETURNS:
            Formatted output [str] with daily (and hourly) limits.
        """
        if not self.engine.query_limits(): return ''
        out = ''
        if self.engine.hour_limits['day'] >= 0:
            out += 'Daily limit = {}'.format(self.engine.hour_limits['day'])
        for lim in self.engine.hour_limits['hours']:
            out += '\nHourly limit from {} = {}'.format(str(lim[0]), lim[1])
        return out
    
    def yandex_logo(self, background='white', fullpage=False, title='', outfile=None, **styleparams):
        """
        Create HTML code (div or page) containing the Yandex logo and search results info
        as stipulated at https://tech.yandex.com/xml/doc/dg/concepts/design-requirements-docpage/#design-requirements
        PARAMS:
            - background [str]: background color (3 standard: red, black, white); logo image and font color will be selected accordingly
            - fullpage [bool]: whether to generate code for whole page or a single div section
            - title [str]: HTML page title (if fullpage == True)
            - outfile [None|str]: path to output file [str] or None to output to console (stdout)
            - styleparams [kwargs]: additional CSS styles for HTML element (passed to style={...}), such as:
                width, height, border, font, position etc.
                If style is not assigned, the default DEFAULT_LOGO_STYLE template will be used,
                and font color will be selected to contrast the background.
        RETURNS:
            Generated HTML code (if outfile == None) or status text (if outfile == full path).
        """
        logo = self.engine.yandex_logo(background, fullpage, title, **styleparams)
        if outfile is None: return logo
        with open(outfile, 'w') as f:
            f.write(logo)
        return 'Yandex logo saved to: {}'.format(outfile)
    
    def sample_captcha(self, retries=3):
        """
        Retrieves a sample captcha from Yandex XML and attempts to solve it using the
        captcha_solver parameter passed to the engine.
        PARAMS:
            - retries [int]: max number of attempts before failure
        RETURNS:
            Status text on success (otherwise any error messages).
        """
        return self.engine.solve_sample_captcha(retries)
    
def main():    
    fire.Fire(Yxml)

## ******************************************************************************** ##    
       
if __name__ == '__main__':
    main()