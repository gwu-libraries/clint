# Local Settings Template
# copy the following settings into a local_settings.py file

INVENTORY_CREDENTIALS = {
    'user': '',
    'apikey': '',
    'apiversion': '',
    'url': '',
    'port': ''
}

inventory_sandbox = {
    'user': '',
    'apikey': '',
    'url': '',
    'port': ''
}

try:
    from local_settings import *
except ImportError:
    pass
