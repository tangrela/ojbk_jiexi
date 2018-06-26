#-*- coding=utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
#from celery import Celery,platforms
from flask_pagedown import PageDown
import logging
import datetime
from redis import Redis

# 日志记录
logger = logging.getLogger("ojbk")
logger.setLevel(logging.DEBUG)
ch = logging.FileHandler("/root/ojbk_jiexi/logs/2mm_%(date)s.log" %
                         {'date': datetime.datetime.now().strftime('%Y-%m-%d')})
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

rd = Redis(host='localhost', port=6379, db=0)

app = Flask(__name__)
app.config.from_object('config')
# Celery configuration
#celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
db = SQLAlchemy(app, use_native_unicode='utf8')
bootstrap = Bootstrap(app)
pagedown = PageDown(app)
# celery.conf.update(app.config)
#platforms.C_FORCE_ROOT = True

from app import views
