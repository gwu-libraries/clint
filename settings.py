# Local Settings Template
# copy the following settings into a local_settings.py file

inventory_sandbox = {
    'user': 'clint',
    'apikey': '',
    'url': '',
    'port': ''
}

try:
    from local_settings import *
except ImportError:
    pass