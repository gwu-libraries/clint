# Local Settings Template
# copy the following settings into a local_settings.py file

INVENTORY_CREDENTIALS = {
    'user': '',
    'apikey': '',
    'apiversion': '',
    'url': '',
    'port': '',
    'verify_ssl_cert': True
}

inventory_sandbox = {
    'user': '',
    'apikey': '',
    'url': '',
    'port': '',
    'verify_ssl_cert': True
}

try:
    from local_settings import *
except ImportError:
    pass
