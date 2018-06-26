# -*- coding=utf-8 -*-
import re
import os
import sys
from time import clock
import time
import json
import requests
import threading
from app import db
from app.models import Context, ID

# search for url of maxium size of a picture, which starts with '<photo-url max-width="1280">' and ends with '</photo-url>'
extractpicre = re.compile(
    r'(?<=<photo-url max-width="1280">).+?(?=</photo-url>)', flags=re.S)
extractvideore = re.compile(
    '''poster='(.*?)'[\w\W]*?/tumblr_(.*?)" type="video/mp4"''')

video_links = []
pic_links = []
vhead = 'https://vt.tumblr.com/tumblr_{}.mp4'
api_url = 'http://%s.tumblr.com/api/read/json?callback=tumblrBadge.listItems&num=50&start='
query_urls = []


def getpost(uid, query_urls):
    import requests
    url = 'http://%s.tumblr.com/api/read?&num=50' % uid
    r = requests.get(url)
    total = re.findall('<posts start="0" total="(.*?)">', r.content)[0]
    total = int(total)
    id = ID.query.filter_by(id=uid).first()
    if id is None:
        print uid + ' : ' + str(total)
        a = [i * 50 for i in range(total / 50 + 1)]
        ul = api_url % uid
        for i in a:
            query_url = ul + str(i)
            query_urls.append(query_url)
    elif id.postnum is None:
        print uid + ' : ' + str(total) + ' get 2'
        id.postnum = total
        db.session.add(id)
        db.session.commit()
        a = [i * 50 for i in range(total / 50 + 1)]
        ul = api_url % uid
        for i in a:
            query_url = ul + str(i)
            query_urls.append(query_url)
    elif id.postnum < total:
        print uid + ' : ' + str(total) + ' renew'
        id.postnum = total
        db.session.add(id)
        db.session.commit()
        a = [i * 50 for i in range((total - id.postnum) / 50 + 1)]
        ul = api_url % uid
        for i in a:
            query_url = ul + str(i)
            query_urls.append(query_url)


def parse_post(post):
    global video_links
    global pic_links
    posttime = time.localtime(post['unix-timestamp'])
    desc = post['slug']
    pid=post['id']
    if post.has_key('video-player'):
        videosource = post['video-player']
        poster = re.findall("poster='(.*?)'", videosource)[0]
        vid = re.findall(
            '''poster='.*?[\w\W]*?/tumblr_(.*?)_.*?''', videosource)[0]
        video = vhead.format(vid)
        video_links.append((pid,desc, posttime, poster, video))
    if post.has_key('photo-caption'):
        if len(post['photos']) == 0:
            picture = post['photo-url-1280']
            pic_links.append((pid,desc, posttime, picture))
        else:
            for pic in post['photos']:
                picture = pic['photo-url-1280']
                pic_links.append((pid,desc, posttime, picture))


def parse_page(url):
    r = requests.get(url)
    json_data = json.loads(r.content.replace(
        'tumblrBadge.listItems(', '').replace(");", ''))
    if len(json_data['posts']) != 0:
        for post in json_data['posts']:
            parse_post(post)


def write(name):
    videos = video_links
    pictures = pic_links
    for url in videos:
        pid,desc, posttime, poster, video = url
        data = Context.query.filter_by(uid=name, pid=pid).first()
        if data is None:
            data = Context(uid=name,pid=pid, urls=video, isvideo=1,
                           poster=poster, posttime=posttime, description=desc)
            db.session.add(data)
    for url in pictures:
        pid,desc, posttime, picture = url
        dat = Context.query.filter_by(uid=name, pid=pid).first()
        if dat is None:
            data = Context(uid=name,pid=pid, urls=picture, isvideo=0,
                           poster=picture, posttime=posttime, description=desc)
            db.session.add(data)
    db.session.commit()


def TumblrGet(name):
    now = clock()
    getpost(name, query_urls)
    print '{} has {} posts'.format(name, len(query_urls))
    threads = []
    for url in query_urls:
        t = threading.Thread(target=parse_page, args=(url,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    write(name)
    print "%s parse complete, cose %.1fs" % (name, clock() - now)
    print "pictures %d,videos %d" % (len(pic_links), len(video_links))


if __name__ == '__main__':
    name = sys.argv[1]
    name = name.strip()
    # name=raw_input()
    # now=clock()
    TumblrGet(name)
    # print u"图片%d张，视频%d部"%(len(pic_links),len(video_links))
