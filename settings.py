from efforia.settings import *
import os

ADMINS = (('William Oliveira de Lagos', 'william@efforia.com.br'),)
MANAGERS = ADMINS
SECRET_KEY = 'x5dvfbk$u-(07^f1229p*_%rcuc+nka45j6awo==*jkyjiucql'

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'd6i6a0klirtqjd',
    'HOST': 'ec2-54-243-243-176.compute-1.amazonaws.com',
    'PORT': 5432,
    'USER': 'kkoaphemdgvutt',
    'PASSWORD': 'ztTIw8EcIYX2UlNolrVmTb8yZQ'
  }
}

EFFORIA_APPS = ('spread','promote')
EFFORIA_OBJS = {
    'spread':  ['Playable','Spreadable','Image','Product'],
    'promote': ['Project','Event']
}
EFFORIA_NAMES = {
    'spread': ('Espalhe','spreads'),
    'promote': ('Promova','create')
}

STATICFILES_DIRS.extend((
    os.path.abspath('spread/public'),
    os.path.abspath('promote/public'),
))
INSTALLED_APPS.extend(EFFORIA_APPS)

PAYPAL_RECEIVER_EMAIL = 'caokzu@gmail.com'
PAYPAL_NOTIFY_URL = 'http://www.efforia.com.br/paypal'
PAYPAL_RETURN_URL = 'http://www.efforia.com.br/'
PAYPAL_CANCEL_RETURN = 'http://www.efforia.com.br/cancel'

PAGSEGURO_EMAIL_COBRANCA = 'contato@efforia.com.br' 
PAGSEGURO_TOKEN = '1a3ea7wq2e7eq8e1e223add23ad23'
PAGSEGURO_URL_RETORNO = '/pagseguro/retorno/'
PAGSEGURO_URL_FINAL = '/obrigado/' 
PAGSEGURO_ERRO_LOG  = '/tmp/pagseguro_erro.log'
