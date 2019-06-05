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

@cli.command()
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
@click.option('username', type=str, default='---')
@click.option('apikey', type=str, default='---')
@click.option('mode', type=click.Choice(['world', 'ru', '---']), default='---')
@click.option('ip', type=str, default='---')
@click.option('proxy', type=str, default='---')
@click.option('captcha', type=str, default='---')
def setparam(username, apikey, mode, ip, proxy, captcha):
    if not engine: return
    d = {}
    if username != '---': d['username'] = username
    if apikey != '---': d['apikey'] = apikey
    if mode != '---': d['mode'] = mode
    if ip != '---': d['ip'] = ip
    if proxy != '---': d['proxy'] = proxy
    if captcha != '---': d['captcha_callback'] = captcha
    engine.reset(d)
    
@cli.command(name='q')
@click.argument('query_string')
@click.option('--output', '-o', default='', type=str, help='Output results filepath (empty=console)', show_default=True)
@click.option('--format', '-f', default='json', type=click.Choice(['json', 'xml', 'txt']), help='Format results', show_default=True)
def query():
    pass

def main():
    cli.add_command(create)
    cli.add_command(setparam)
    cli()

## ******************************************************************************** ##    
       
if __name__ == '__main__':
    main()