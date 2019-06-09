# yandexml
*Simple Python implementation of the Yandex search API (https://tech.yandex.com/xml/)*

## Supported features
* class-based Yandexml engine for a given Yandex account (username), API key and host IP
* all current Yandex XML API constraints honored in code (search query length etc.)
* request available daily / hourly limits
* return search results in Python native objects (dict, list), as well as JSON and formatted text
* output results to file
* full Unicode support
* handle Yandex captchas when robot protection activates on the server side
* automatic host IP lookup (with several whats-my-ip online services)
* use requests package for HTTP communication
* easy CLI or use engine manually in Python
* Python 3x compatible (2x not supported so far... and hardly will be)

## Installation
* check you've got Python 3.7 or later
* `pip install -r requirements.txt` (will install/upgrade [requests](https://2.python-requests.org/en/master/) and [fire](https://github.com/google/python-fire))

## Usage

**1. Command-line interface (CLI)**

`python yxml.py --username <username> --apikey <apikey> run`

* (re)set engine parameters, e.g. switch mode to "ru" and ip to 127.0.0.1:
`r --mode=ru ip=127.0.0.1`
* view current engine parameters:
`v` or `v 2` or `v 3` (output more detail)
* search (output results to console):
`q "SEARCH QUERY"`
* search and save results to file:
`q "SEARCH QUERY" --txtformat=[xml|json|txt] --outfile="filename[.xml]"`
* search without grouping by domain:
`q "SEARCH QUERY" --grouped=False`
* output previous search results to file:
`o --txtformat=json --outfile="filename.json"`
* get limits for next hour / day:
`l`
* get all limits:
`L`
* create Yandex logo:
`y --background==[red|white|black|any...] --fullpage=[True|False] --title='Logo' --outfile=[None|"myfile.html"]`
* logo with custom CSS styles:
`y --fullpage=True --outfile="myfile.html" --width="100px" --font-size="12pt" --font-family="Arial"`
* solve sample captcha (download sample using Yandex XML API, use passed `captcha_solver` to solve):
`c --retries=[1|2|...]`
* show help (usage string):
`h`
* show detailed help:
`h 2`
* quit CLI:
`w`

**2. In Python code**

See comments in yxmlengine.py and examples in tester.py.