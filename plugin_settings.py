''' Settings for the Merritt plugin for Janeway '''
import os
from utils import models
from utils.logger import get_logger

logger = get_logger(__name__)

PLUGIN_NAME = 'Merritt Plugin'
DISPLAY_NAME = 'Merritt'
DESCRIPTION = 'Use Merritt to preserve preprints in Janeway.'
AUTHOR = 'California Digital Library'
VERSION = '0.1'
SHORT_NAME = 'merritt'
MANAGER_URL = 'merritt_manager'
JANEWAY_VERSION = "1.5.0"
IS_WORKFLOW_PLUGIN = True
JUMP_URL = 'merritt_article'
HANDSHAKE_URL = 'merritt_articles'
ARTICLE_PK_IN_HANDSHAKE_URL = True
STAGE = 'merritt_plugin'
KANBAN_CARD = 'merritt/elements/card.html'
DASHBOARD_TEMPLATE = 'merritt/elements/dashboard.html'

PLUGIN_PATH = os.path.dirname(os.path.realpath(__file__))

def install():
    ''' install this plugin '''
    plugin, created = models.Plugin.objects.get_or_create(
        name=SHORT_NAME,
        defaults={
            "enabled": True,
            "version": VERSION,
            "display_name": DISPLAY_NAME,
        }
    )

    if created:
        print('Plugin {0} installed.'.format(PLUGIN_NAME))
    elif plugin.version != VERSION:
        print('Plugin updated: {0} -> {1}'.format(VERSION, plugin.version))
        plugin.version = VERSION
        plugin.display_name = DISPLAY_NAME
        plugin.save()

    else:
        print('Plugin {0} is already installed.'.format(PLUGIN_NAME))




def register_for_events():
    '''register for events '''
    #TODO: add events we need to listen for here
    pass

def hook_registry():
    ''' connect a hook with a method in this plugin's logic '''
    logger.debug('>>>>>>>>>>>>>>>>> hook_registry called for merritt plugin')
    #TODO: add here when needed

