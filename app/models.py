#-*- coding=utf-8 -*-
from app import db

# Tumblr


class ID(db.Model):
    __tablename__ = 'id_table'
    id = db.Column(db.String(64), primary_key=True)
    parseTimes = db.Column(db.Integer, default=0)  # 解析次数
    updateTime = db.Column(db.String(64))  # 最近更新时间
    postnum = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super(ID, self).__init__(**kwargs)

    def __repr__(self):
        return self.id

#


class Context(db.Model):
    __tablename__ = 'context_table'
    uid = db.Column(db.String(64), primary_key=True)
    pid=db.Column(db.String(64),primary_key=True)
    urls = db.Column(db.String(200))
    isvideo = db.Column(db.Integer, default=0)  # 0=no,1=yes
    poster = db.Column(db.String(200))
    posttime = db.Column(db.DateTime())
    description = db.Column(db.String(500))

    def __init__(self, **kwargs):
        super(Context, self).__init__(**kwargs)

    def __repr__(self):
        return self.uid
