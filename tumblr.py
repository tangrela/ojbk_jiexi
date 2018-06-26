# -*- coding=utf-8 -*-
import grequests
import re
import os
import sys
from time import clock
from app import db
from app.models import Context

# search for url of maxium size of a picture, which starts with '<photo-url max-width="1280">' and ends with '</photo-url>'
extractpicre = re.compile(
    r'(?<=<photo-url max-width="1280">).+?(?=</photo-url>)', flags=re.S)
extractvideore = re.compile(
    '''poster='(.*?)'[\w\W]*?/tumblr_(.*?)" type="video/mp4"''')

video_links = []
pic_links = []
vhead = 'https://vt.tumblr.com/tumblr_%s.mp4'
api_url = 'http://%s.tumblr.com/api/read?&num=50&start='
query_urls = []


def getpost(uid, query_urls):
    import requests
    url = 'http://%s.tumblr.com/api/read?&num=50' % uid
    r = requests.get(url)
    total = re.findall('<posts start="0" total="(.*?)">', r.content)[0]
    total = int(total)
    print uid + ':' + str(total)
    a = [i * 50 for i in range(total / 50 + 1)]
    ul = api_url % uid
    for i in a:
        query_url = ul + str(i)
        query_urls.append(query_url)


def run(query_urls):
    rs = [grequests.get(url) for url in query_urls]
    responses = grequests.map(rs, size=10)
    for resp in responses:
        content = resp.content
        videos = extractvideore.findall(content)
        video_links.extend([(v[0], vhead % v[1]) for v in videos])
        pic_links.extend(extractpicre.findall(content))


def write(name):
    videos = [(i[0], i[1].replace('/480', '')) for i in video_links]
    pictures = pic_links
    for url in list(set(videos)):
        poster, video = url
        data = Context.query.filter_by(id=name, urls=video).first()
        if not data:
            data = Context(id=name, urls=video, isvideo=1, poster=poster)
            db.session.add(data)
        else:
            data = Context.query.filter_by(id=name, urls=video).first()
            data.poster = poster
            db.session.add(data)
    for url in list(set(pictures)):
        dat = Context.query.filter_by(id=name, urls=url).first()
        if not dat:
            data = Context(id=name, urls=url, isvideo=0, poster=url)
            db.session.add(data)
        else:
            data = Context.query.filter_by(id=name, urls=url).first()
            data.poster = url
            data.urls = url
            db.session.add(data)
    db.session.commit()


def TumblrGet(name):
    now = clock()
    getpost(name, query_urls)
    print len(query_urls)
    parts = len(query_urls) / 50 + 1
    print parts
    for part in range(parts):
        urls = query_urls[part:(part + 1) * 50]
        run(urls)
        write(name)
    print "%sparse complete, cose %.1fs" % (name, clock() - now)
    print "pictures %d,videos %d" % (len(pic_links), len(video_links))


if __name__ == '__main__':
    name = sys.argv[1]
    name = name.strip()
    # name=raw_input()
    # now=clock()
    TumblrGet(name)
    # print u"图片%d张，视频%d部"%(len(pic_links),len(video_links))
