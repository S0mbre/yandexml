# yandexml
Simple Python implementation of the Yandex search API (https://tech.yandex.com/xml/)

Supported features:
* class-based Yandexml engine for a given Yandex account (username), API key and host IP
* all current Yandex XML API constraints honored in code (search query length etc.)
* request available daily / hourly limits
* return search results in Python native objects (dict, list)
* full Unicode support
* handle Yandex captchas when robot protection activates on the server side
* automatic host IP lookup (with several whats-my-ip online services)
* use requests package for HTTP communication
* Python 3x compatible (2x not supported so far... and hardly will be)
