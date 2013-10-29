# Local Settings Template
# copy the following settings into a local_settings.py file

import logging

LOG_LEVEL = logging.ERROR

INVENTORY_CREDENTIALS = {
    'user': '',
    'apikey': '',
    'apiversion': '',
    'url': '',
    'verify_ssl_cert': False
}

inventory_sandbox = {
    'user': '',
    'apikey': '',
    'url': '',
    'verify_ssl_cert': False
}

try:
    from local_settings import *
except ImportError:
    pass

#Example settings
#INVENTORY_CREDENTIALS = {
#        'user': 'admin',
#        'apikey': 'b531f6599f78asbf279fd38c4665sd76f8794207a',
#        'apiversion': 'v1',
#        'url': 'https://inventory.example.com',
                    #URL should be without the trailing slash and must have
                       #the port number if different from default port 80
#        'verify_ssl_cert': False
#}
