# yandexml
*Simple Python implementation of the Yandex search API (https://tech.yandex.com/xml/)*

## Supported features
* class-based Yandexml engine for a given Yandex account (username), API key and host IP
* all current Yandex XML API constraints honored in code (search query length etc.)
* request available daily / hourly limits
* return search results in Python native objects (dict, list)
* full Unicode support
* handle Yandex captchas when robot protection activates on the server side
* automatic host IP lookup (with several whats-my-ip online services)
* use requests package for HTTP communication
* Python 3x compatible (2x not supported so far... and hardly will be)

## Installation
* check you've got Python 3.7 or later
* `pip install -r requirements.txt` (will install/upgrade the [requests](https://2.python-requests.org/en/master/) package)

## Usage

**1. Command-line interface (CLI)**

```
yandexml.py <username> <apikey> [<mode>:ru|world (default "world")] [<ip> (default: current external ip)]
```

* search (output results to console):
`q "SEARCH QUERY"`
* search and save results to file:
`q "SEARCH QUERY" -o:[xml|json|txt|csv] > "filename.xml"`
* search with external captcha solver:
`q "SEARCH QUERY" -c:"path-to-solver.[py|exe]"`
* get limits for next hour / day:
`l`
* get all limits:
`L`
* options for all commands:
	* `-vv`: verbose (print errors, debug info etc) -- default
	* `-v`: print only critical errors
	* `-q`: quiet (print nothing but results)
		
**2. In Python code**

* create Yandexml object:
    ```python
    yxml = Yandexml(user, username, apikey, searchmode='world', hostip=None, proxies=None, captcha_callback=None)
    ```
    * username = your Yandex account username (as for Yandex mail but without "@yandex.ru|com")
    * apikey = dedicated API key given by Yandex when your register your app at https://xml.yandex.com/settings/
    * searchmode = either of "world" to search worldwide (default) or "ru" to search in Russian web only (see Restrictions and Requirements for each mode at https://tech.yandex.com/xml/doc/dg/concepts/restrictions-docpage/)
    
	**NOTE:** Turkish search (available on Yandex XML) is not currently supported.
    * hostip = IP address used to make search queries (provided once during registration at https://xml.yandex.com/settings/)
    
	**NOTE:** if passed `None`, Yandexml will use your current external IP address determined via online 'whoami' services
    * proxies = dictionaty of HTTP/S proxy servers passed to the requests engine (e.g. `{'http': 'http://my-proxy:port', 'https': 'http://my-proxy:port'}`)
    
	**NOTE:** on most occasions, pass `None` (default) to make requests use your system proxy settings
    * captcha_callback = pointer to external function to handle / solve Yandex captcha images.
    The function must take the captcha URL as its sole argument and return the solved string.
    
	**NOTE:** if callback is not set (=`None`), Yandexml will return error when faced with captcha protection
* search:
    ```python
	if not yxml.search('search for this'): print('search error')
	```
* get limits:
    ```python
	next_lim = yxml.next_limits 
    if next_lim: print('Daily limit = {} for {}'.format(next_lim[1], str(next_lim[0])))
    ```
	
See more examples in tester.py.