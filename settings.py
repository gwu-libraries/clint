
import logging

LOG_LEVEL = logging.WARNING

# the path to clint instance on remote server
#CLINT_INSTALLATION_PATH = '/clint/clint/'
#Path should include a trailing slash
CLINT_INSTALLATION_PATH = ''

FREE_PARTITION_SPACE = 10

try:
    from local_settings import *
except ImportError:
    pass
