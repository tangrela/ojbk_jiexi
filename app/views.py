#-*- coding=utf-8 -*-
from app import app, db
from app.models import *
from flask import render_template, redirect, request, url_for, flash, session, jsonify, make_response, current_app
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import subprocess
import os
from datetime import datetime
#from .tumblr_task import TumblrGet
import re
import requests
import os
from hashlib import md5
import string
import random
import StringIO
from app import db
from app.models import Context
import parser
from . import logger, rd
from config import *
from captcha import *
from decorator import *

basedir = os.path.abspath('.')
clawer = os.path.join(basedir, 'tumblr_v2.py')
weibo_crawler = os.path.join(basedir, 'weibo.py')

#VIDEOREGEX = re.compile('http://media.tumblr.com/(.*?)_frame1')
VIDEOREGEX = re.compile(
    '<meta property="og:image".*?media.tumblr.com/tumblr_(.*?)_')
POSTERREGEX = re.compile('<meta property="og:image" content="(.*?)"')
IMAGEREGEX = re.compile(
    '<meta property="og:image" content="(.*?)" /><meta property="og:image:height"')
vhead = 'https://vt.tumblr.com/tumblr_%s.mp4'
HOME = 'http://%s.tumblr.com/api/read?&num=50'
headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"}
ban = ['TencentCloud', 'Savvis', 'ALICLOUD', 'GOOGLE-CLOUD', 'WANG-SUKEJI']
bad_ua=['FeedDemon ','BOT/0.1 (BOT for JCE)','CrawlDaddy ','Java','Feedly','UniversalFeedParser','ApacheBench','Swiftbot','ZmEu','Indy Library','oBot','jaunty','YandexBot','AhrefsBot','MJ12bot','WinHttp','EasouSpider','HttpClient','Microsoft URL Control','YYSpider','jaunty','Python-urllib','lightDeckReports Bot','PHP','Python','Go']


def check(uid):
    url = HOME % uid
    try:
        cont = requests.get(url)
        if cont.ok:
            if int(re.findall('<posts start="0" total="(.*?)">', cont.content)[0]) != 0:
                return True
            else:
                return False
        else:
            return False
    except:
        return False


def nickname_to_containerid(nickname):
    url = "https://m.weibo.com/n/{}".format(nickname)
    response = requests.get(url=url)
    uid_check = re.search(r'(\d{16})', response.url)
    if uid_check:
        return "107603" + uid_check.group(1)[-10:]


def getmd5():
    a = md5()
    letters = string.ascii_letters + string.digits
    randchar = ''.join(random.sample(letters, 5))
    a.update(randchar)
    return a.hexdigest()


def getipwhois(ip):
    if rd.exists(ip) and rd.get(ip) != 'home':
        netname = rd.get(ip)
        print '{} exists in redis,netname {}'.format(ip, netname)
    else:
        print '{} exists doesn\' exists in redis'.format(ip)
        url = 'http://tool.chinaz.com/ipwhois?q={}'.format(ip)
        try:
            r = requests.get(url, headers=headers, timeout=8)
            try:
                netname = re.findall('netname:(.*?)<br/>',
                                     r.content)[0].replace(' ', '')
            except:
                netname = re.findall('<p>Name : (.*?)</p>',
                                     r.content)[0].replace(' ', '')
            rd.set(ip, netname)
        except Exception, e:
            print e
            netname = 'home'
    return netname


@app.context_processor
def form_trans():
    return dict(method='method')


@app.before_request
def before_request():
    global ua
    global ip
    global netname
    try:
        ua = request.headers.get('User-Agent')
    except:
        ua = "null"
    try:
        ip = request.headers['X-Forwarded-For'].split(',')[0]
    except:
        ip = request.remote_addr
    print ip
    netname = getipwhois(ip)


def log(string):
    global ip
    global ua
    global netname
    logger.info('ip:{ip},netname:{netname},UA:{ua},action:{string}'.format(
        ip=ip, netname=netname, ua=ua, string=string))


@app.route('/')
def index():
    hash_ = getmd5()
    session['hash'] = hash_
    log('visit home page')
    return render_template('base.html', hash_=hash_)


@app.route('/api', methods=['POST'])
@ratelimit(limit=5, per=10)
def api():
    global ua
    global ip
    url = request.form.get('url')
    hash_ = request.form.get('hash')
    captcha_code = request.form.get('captcha_code')
    if ip in ['111.231.237.241', '111.230.109.198', '91.121.83.61'] or sum([i.lower() in netname.lower() for i in ban]) > 0 or sum([i.lower() in ua.lower() for i in bad_ua]) > 0:
        log('bad user')
        retdata = {}
        retdata['status'] = 'fail'
        retdata['message'] = '机器人滚！如果不是机器人，请不要通过代理访问本站！'
        return jsonify(retdata)
    if captcha_code is not None:
        log('verify captcha code')
        print 'input code is :', captcha_code
        print 'session code is :', session.get('CAPTCHA')
        if captcha_code.upper() == session.get('CAPTCHA'):
            return jsonify({'captcha': 'pass'})
    if hash_ != session.get('hash') or hash_ is None:
        log('may be a crawler!!! url {}'.format(url))
        return jsonify({'captcha': 'ok'})
    else:
        retdata = {}
        log('fetch url {}'.format(url))
        # tumblr单个视频解析
        if 'tumblr.com/post' in url:
            try:
                video = ''
                cont = requests.get(url).content
                pictures = IMAGEREGEX.findall(cont)
                vid = VIDEOREGEX.findall(cont)
                poster = POSTERREGEX.findall(cont)
                isvideo = 0
                if vid:
                    video = vhead % vid[0]
                    poster = poster[0]
                    isvideo = 1
                    # flash('解析成功')
                    retdata['status'] = 'ok'
                    retdata['total'] = 1
                    retdata['pages'] = 1
                    retdata['video'] = [
                        {'url': video, 'desc': '', 'thumb': poster}]
                    return jsonify(retdata)
                else:
                    # flash('解析失败')
                    retdata['status'] = 'fail'
                    retdata['message'] = '解析失败，请联系站长解决'
                    return jsonify(retdata)
            except Exception, e:
                print e
                # flash('解析失败')
                retdata['status'] = 'fail'
                retdata['message'] = '解析失败，请联系站长解决'
                return jsonify(retdata)
        # tumblr批量解析
        elif 'tumblr.com' in url:
            id = re.findall('://(.*?)\.', url)[0]
            if check(id):
                is_exists = ID.query.filter_by(id=id).first()
                if is_exists is None:
                    now = datetime.now()
                    inserttime = now.strftime('%Y%m%d %H:%M:%S')
                    a = ID(id=id, updateTime=inserttime, parseTimes=1)
                    db.session.add(a)
                    db.session.commit()
                    retdata['status'] = 'fail'
                    retdata['message'] = '正在解析，请稍等15s再试！'
                    subprocess.Popen('python {clawer} {id}'.format(
                        clawer=clawer, id=id), shell=True)
                    return jsonify(retdata)
                else:
                    now = datetime.now()
                    is_exists.updateTime = now.strftime('%Y%m%d %H:%M:%S')
                    is_exists.parseTimes += 1
                    db.session.add(is_exists)
                    db.session.commit()
                    subprocess.Popen('python {clawer} {id}'.format(
                        clawer=clawer, id=id), shell=True)
                    retdata['status'] = 'ok'
                    retdata['total'] = 50
                    retdata['pages'] = 2
                    retdata['html'] = '<a href="/download?id={}&type=video" class="btn btn-primary" role="button" title="导出视频">导出视频 <span class="glyphicon glyphicon-film"></span></a>'.format(
                        id)
                    retdata['html'] += ' | <a href="/download?id={}&type=picture" class="btn btn-primary" role="button" title="导出图片">导出图片 <span class="glyphicon glyphicon-picture"></span></a>'.format(
                        id)
                    videos = Context.query.filter_by(
                        uid=id, isvideo=1).order_by(Context.posttime.desc()).limit(50).all()
                    for video in videos:
                        retdata.setdefault('video', []).append(
                            {'url': video.urls, 'desc': video.description, 'thumb': video.poster})
                    return jsonify(retdata)
            else:
                # flash('解析失败')
                retdata['status'] = 'fail'
                retdata['message'] = '解析失败，请联系站长解决'
                return jsonify(retdata)
        elif url.startswith('@'):
            id = nickname_to_containerid(url.replace('@', ''))
            print 'weibo\'s containerid:{}'.format(id)
            is_exists = ID.query.filter_by(id=id).first()
            if is_exists is None:
                now = datetime.now()
                inserttime = now.strftime('%Y%m%d %H:%M:%S')
                a = ID(id=id, updateTime=inserttime, parseTimes=1)
                db.session.add(a)
                db.session.commit()
                retdata['status'] = 'fail'
                retdata['message'] = '正在解析，请稍等15s再试！'
                subprocess.Popen('python {clawer} {id}'.format(
                    clawer=weibo_crawler, id=id), shell=True)
                return jsonify(retdata)
            else:
                now = datetime.now()
                is_exists.updateTime = now.strftime('%Y%m%d %H:%M:%S')
                is_exists.parseTimes += 1
                db.session.add(is_exists)
                db.session.commit()
                subprocess.Popen('python {clawer} {id}'.format(
                    clawer=weibo_crawler, id=id), shell=True)
                retdata['status'] = 'ok'
                retdata['total'] = 50
                retdata['pages'] = 2
                retdata['html'] = '<a href="/download?id={}&type=video" class="btn btn-primary" role="button" title="导出视频">导出视频 <span class="glyphicon glyphicon-film"></span></a>'.format(
                    id)
                retdata['html'] += ' | <a href="/download?id={}&type=picture" class="btn btn-primary" role="button" title="导出图片">导出图片 <span class="glyphicon glyphicon-picture"></span></a>'.format(
                    id)
                videos = Context.query.filter_by(
                    uid=id, isvideo=1).order_by(Context.posttime.desc()).limit(50).all()
                for video in videos:
                    retdata.setdefault('video', []).append(
                        {'url': video.urls, 'desc': video.description, 'thumb': video.poster})
                return jsonify(retdata)
        else:
            try:
                video, title, picture = parser.main(url)
                retdata['status'] = 'ok'
                retdata['total'] = 1
                retdata['pages'] = 1
                retdata['video'] = [
                    {'url': video, 'desc': title, 'thumb': picture}]
                return jsonify(retdata)
            except Exception, e:
                print e
                retdata['status'] = 'fail'
                retdata['message'] = '解析网站不存在'
                return jsonify(retdata)


@app.route('/download')
def download():
    id = request.args.get('id')
    type = request.args.get('type')
    log('download from {} {}'.format(id, type))
    if type == 'video':
        isvideo = 1
    else:
        isvideo = 0
    query_result = Context.query.filter_by(
        uid=id, isvideo=isvideo).order_by(Context.posttime.desc()).all()
    if len(query_result) <> 0:
        content = ''
        for line in query_result:
            content += '%s\n' % line.urls
        response = make_response(content)
        response.headers["Content-Disposition"] = "attachment; filename=%s.txt" % (
            id + "_" + type)
        return response
    else:
        return redirect(url_for('index'))


@app.route('/captcha', methods=['GET'])
def captcha():
    ic = ImageChar(fontColor=(100, 211, 90))
    strs, code_img = ic.randChinese(4)
    session['CAPTCHA'] = strs
    buf = StringIO.StringIO()
    code_img.save(buf, 'JPEG', quality=80)
    buf_str = buf.getvalue()
    response = current_app.make_response(buf_str)
    response.headers['Content-Type'] = 'image/jpeg'
    return response
