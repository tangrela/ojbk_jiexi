import os
basedir=os.path.abspath(os.path.dirname(__file__))

SECRET_KEY='SSDFDSFDFD'
#SQLALCHEMY_DATABASE_URI='mysql+pymysql://user:passwd@localhost/db'
SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(basedir,'data.sqlite')
SQLALCHEMY_TRACK_MODIFICATIONS=True
debug=True
domain='http://ojbk.us'
mm2='http://v.33k.im'
porn91='http://91porn.com'
#CELERY_BROKER_URL = 'redis://localhost:6379/0'
#CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
