# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 14:42:33 2019

@author: iskander.shafikov
"""

from yandexmlengine import Yandexml
import webbrowser
import sys
import click

## ******************************************************************************** ## 
engine = None 

def default_captcha_callback(captcha_url):
    webbrowser.open_new_tab(captcha_url)
    return str(input())

@click.group()
def cli():
    pass 

@cli.command(name='c')
@click.argument('username')
@click.argument('apikey')
@click.option('--mode', '-m', default='world', type=click.Choice(['world', 'ru']), help='Search mode: [world|ru]', show_default=True)
@click.option('--ip', '-i', default='', help='Host IP for search queries (empty=use current)', show_default=True)
@click.option('--proxy', '-p', default='', help='HTTP(S) proxy settings (empty=use system)', show_default=True)
@click.option('--captcha', '-c', default='', help='Path to captcha solver (python script or executable), empty=webbrowser + console input', show_default=True)
def create(username, apikey, mode, ip, proxy, captcha):
    global engine
    proxy = {'http': proxy, 'https': proxy} if proxy else None
    captcha = captcha if captcha else default_captcha_callback
    engine = Yandexml(username, apikey, mode, ip, proxy, captcha)
    
@cli.command(name='s')
@click.option('--username', default='---')
@click.option('--apikey', default='---')
@click.option('--mode', type=click.Choice(['world', 'ru', '---']), default='---')
@click.option('--ip', default='---')
@click.option('--proxy', default='---')
@click.option('--captcha', default='---')
def setparam(username, apikey, mode, ip, proxy, captcha):
    if not engine: 
        click.echo('API engine not initialized. Please use the "c" command first.', file=sys.stderr)
        return
    d = {}
    if username != '---': d['username'] = username
    if apikey != '---': d['apikey'] = apikey
    if mode != '---': d['mode'] = mode
    if ip != '---': d['ip'] = ip
    if proxy != '---': d['proxy'] = proxy
    if captcha != '---': d['captcha_callback'] = captcha
    engine.reset(**d)
    
@cli.command(name='q')
@click.argument('querystr')
@click.option('--group/--no-group', '-g/-n', default=True, help='Group results by domain name (otherwise flat list)', show_default=True)
@click.option('--format', '-f', default='txt', type=click.Choice(['json', 'xml', 'txt']), help='Format results', show_default=True)
@click.argument('file', type=click.Path())
def query(querystr, grouped, txtformat, outfile):
    if not engine: 
        click.echo('API engine not initialized. Please use the "c" command first.', file=sys.stderr)
        return
    if not engine.search(querystr, grouped):
        click.echo('** SEARCH ERROR ! **', file=sys.stderr)
        return
    engine.output_results(txtformat, outfile)
    
@cli.command(name='o')
@click.option('--format', '-f', default='txt', type=click.Choice(['json', 'xml', 'txt']), help='Format results', show_default=True)
@click.argument('file', type=click.Path())
def output(txtformat, outfile):
    if not engine: 
        click.echo('API engine not initialized. Please use the "c" command first.', file=sys.stderr)
        return
    engine.output_results(txtformat, outfile)
    
@cli.command(name='l')
def limits_next():
    if not engine: 
        click.echo('API engine not initialized. Please use the "c" command first.', file=sys.stderr)
        return
    lim = engine.next_limits
    if lim: 
        click.echo('Limit = {} for {}'.format(lim[1], str(lim[0])))
        
@cli.command(name='L')
def limits_all():
    if not engine: 
        click.echo('API engine not initialized. Please use the "c" command first.', file=sys.stderr)
        return
    if not engine.query_limits(): 
        click.echo('** COULD NOT GET LIMITS ! **', file=sys.stderr)
        return
    if engine.hour_limits['day'] >= 0: 
        click.echo('Daily limit = {} for {}'.format(engine.hour_limits['day']))
    for lim in engine.hour_limits['hours']:
        click.echo('Hourly limit from {} = {}'.format(str(lim[0]), lim[1]))
      
        
cli.add_command(create)
cli.add_command(setparam)
cli.add_command(query)
cli.add_command(output)
cli.add_command(limits_next)
cli.add_command(limits_all)

def main():    
    cli()

## ******************************************************************************** ##    
       
if __name__ == '__main__':
    main()