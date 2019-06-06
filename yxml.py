# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 14:42:33 2019

@author: iskander.shafikov
"""

from yandexmlengine import Yandexml
import webbrowser
import sys
import fire

## ******************************************************************************** ## 

class Yxml:
    
    def __init__(self, user, apikey, mode='world', ip='', proxy='', captcha_solver=''):
        self.engine = Yandexml(user, apikey, mode, ip, proxy, captcha_solver if captcha_solver else Yxml.default_captcha_callback)
        self.commands = {'r': self.reset, 'q': self.query, 'l': self.limits_next, 'L': self.limits_all, 
                'y': self.yandex_logo, 'v': self.view_params, 'w': None}
        self.usage = 'USAGE:\t[{}] [ARGS]'.format('|'.join(sorted(self.commands.keys())))
        self.usage2 = '\n\t'.join(['{}:{}'.format(fn, self.commands[fn].__doc__) for fn in self.commands if fn != 'w'])
        
    def run(self):
        """
        Todo:
        """
        entered = ''
        while True:
            try:
                print('\nENTER COMMAND:', end='\t')
                entered = str(input())
                if not entered:
                    print('Empty command!')
                    continue
                e = entered[0]
                if e in self.commands:
                    if self.commands[e] is None: 
                        print('QUITTING APP...')
                        break
                    cmds = entered.split(' ')
                    fire.Fire(self.commands[e], ' '.join(cmds[1:]) if len(cmds) > 1 else '-')
                else:
                    print('Wrong command!\n{}\n\t{}'.format(self.usage, self.usage2))
                    continue     
            except KeyboardInterrupt:
                print('QUITTING APP...')
                break
            
            except Exception:
                continue
        
    def default_captcha_callback(captcha_url):
        webbrowser.open_new_tab(captcha_url)
        return str(input())
    
    def view_params(self, detail=1):
        """
        View engine properties
        
        PARAMS:
            - detail [int]: how many properties to show (1 | 2 | 3, default=1)
        RETURNS:
            - dict of properties
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
            - status string
        """
        self.engine.reset(params)
        if not self.engine.captcha_solver: 
            self.engine.captcha_solver = Yxml.default_captcha_callback
        return 'Parameters have been reset'
        
    def query(self, querystr='', grouped=True, txtformat='txt', outfile=None):
        """
        Todo:
        """
        if self.engine.search(querystr, grouped):
            self.engine.output_results(txtformat, sys.stdout if outfile is None else outfile)
            
    def output(self, txtformat='txt', outfile=None):
        """
        Todo:
        """
        self.engine.output_results(txtformat, sys.stdout if outfile is None else outfile) 
        
    def limits_next(self):
        """
        Todo:
        """
        lim = self.engine.next_limits        
        return 'Limit = {} for {}'.format(lim[1], str(lim[0])) if lim else ''
    
    def limits_all(self):
        """
        Todo:
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
        Todo:
        """
        logo = self.engine.yandex_logo(background, fullpage, title, **styleparams)
        if outfile is None: return logo
        with open(outfile, 'w') as f:
            f.write(logo)
        return 'Yandex logo saved to: {}'.format(outfile)
    
def main():    
    fire.Fire(Yxml)

## ******************************************************************************** ##    
       
if __name__ == '__main__':
    main()