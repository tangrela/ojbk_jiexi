# -*- coding: utf-8 -*-
import os
import sys
import locale
import json
import re
import time
import requests
import threading
import datetime
from app import db
from app.models import Context, ID

try:
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning)
except:
    pass

try:
    reload(sys)
    sys.setdefaultencoding('utf8')
except:
    pass

try:
    input = raw_input
except NameError:
    pass

IS_PYTHON2 = sys.version[0] == "2"
SYSTEM_ENCODE = sys.stdin.encoding or locale.getpreferredencoding(True)
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
PIC_AMOUNT = 0
SAVE_PATH = ""
pictures = []
videos = []


def print_fit(string, flush=False):
    if IS_PYTHON2:
        string = string.encode(SYSTEM_ENCODE)
    if flush == True:
        sys.stdout.write("\r" + string)
        sys.stdout.flush()
    else:
        sys.stdout.write(string + "\n")


def requests_retry(url, max_retry=0):
    retry = 0
    while True:
        if retry > max_retry:
            return
        try:
            response = requests.request(
                "GET", url, headers={"User-Agent": USER_AGENT}, timeout=5, verify=False)
            return response
        except:
            retry = retry + 1


def uid_to_containerid(uid):
    if re.search(r'^\d{10}$', uid):
        return "107603" + uid


def nickname_to_containerid(nickname):
    url = "https://m.weibo.com/n/{}".format(nickname)
    response = requests_retry(url=url)
    uid_check = re.search(r'(\d{16})', response.url)
    if uid_check:
        return "107603" + uid_check.group(1)[-10:]


def parse_url(url):
    response = requests_retry(url=url, max_retry=3)
    json_data = response.json()
    try:
        cards = json_data["data"]["cards"]
        for card in cards:
            get_pic_and_video(card)
    except Exception as e:
        print(e)
        print('empty')


def get_img_urls(containerid):
    global pictures
    global videos
    id = ID.query.filter_by(id=containerid).first()
    page = 1
    amount = 0
    total = 0
    url = "https://m.weibo.cn/api/container/getIndex?count={}&page={}&containerid={}".format(
        25, 1, containerid)
    response = requests_retry(url=url, max_retry=3)
    json_data = response.json()
    total = json_data["data"]["cardlistInfo"]["total"]
    if id is None:
        pages = int(round(total / 25.0, 0))
    elif id.postnum is None:
        pages = int(round(total / 25.0, 0))
        id.postnum = total
        db.session.add(id)
        db.session.commit()
    else:
        pages = int(round((total - id.postnum) / 25.0, 0))
        id.postnum = total
        db.session.add(id)
        db.session.commit()
    urls = ["https://m.weibo.cn/api/container/getIndex?count={}&page={}&containerid={}".format(
        25, i, containerid) for i in range(1, pages + 1)]
    threads = []
    for url in urls:
        t = threading.Thread(target=parse_url, args=(url,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print_fit("\n分析完毕, 视频数 {}, 图片数 {}".format(len(videos), len(pictures)))


def get_pic_and_video(card):
    global pictures
    global videos
    if 'mblog' in card.keys():
        blog = card['mblog']
        try:
            posttime = datetime.datetime.strptime(
                blog['created_at'], '%Y-%m-%d')
        except:
            try:
                year = str(datetime.datetime.now().year)
                posttime = datetime.datetime.strptime(
                    year + '-' + blog['created_at'], '%Y-%m-%d')
            except:
                posttime=datetime.datetime.now()
        description = ''.join(re.findall(u'[\u4e00-\u9fa5]',blog['text']))
        pid=blog['id']
        if 'retweeted_status' in blog.keys():
            if "pics" in blog["retweeted_status"]:
                for pic in blog["retweeted_status"]["pics"]:
                    if "large" in pic:
                        picture = pic["large"]["url"]
                        pictures.append((pid,posttime, description, picture))
            elif "page_info" in blog["retweeted_status"]:
                if "media_info" in blog["retweeted_status"]["page_info"]:
                    video = blog["retweeted_status"]["page_info"]["media_info"]["stream_url"]
                    poster = blog["retweeted_status"]["page_info"]["page_pic"]["url"]
                    videos.append((pid,posttime, description, poster, video))
        else:
            if "pics" in blog:
                for pic in blog["pics"]:
                    if "large" in pic:
                        picture = pic["large"]["url"]
                        pictures.append((pid,posttime, description, picture))
            elif "page_info" in blog:
                if "media_info" in blog["page_info"]:
                    video = blog["page_info"]["media_info"]["stream_url"]
                    poster = blog["page_info"]["page_pic"]["url"]
                    videos.append((pid,posttime, description, poster, video))


def write(containerid):
    global pictures
    global videos
    for url in videos:
        pid,posttime, description, poster, video = url
        data = Context.query.filter_by(uid=containerid, pid=pid).first()
        if data is None:
            data = Context(uid=containerid,pid=pid, urls=video, isvideo=1,
                           poster=poster, posttime=posttime, description=description[:500])
            db.session.add(data)
    for url in pictures:
        pid,posttime, description, picture = url
        dat = Context.query.filter_by(uid=containerid, pid=pid).first()
        if dat is None:
            data = Context(uid=containerid,pid=pid, urls=picture, isvideo=0,
                           poster=picture, posttime=posttime, description=description[:500])
            db.session.add(data)
    db.session.commit()


def main(name):
    #containerid = nickname_to_containerid(name)
    containerid = name
    get_img_urls(containerid)
    write(containerid)


if __name__ == "__main__":
    name = sys.argv[1]
    name = name.strip()
    main(name)
