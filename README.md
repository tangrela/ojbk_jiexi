# OJBK视频解析网站搭建教程
1. 首先安装Python。linux自带了python，windows请自行下载python。推荐Centos7/Python2.7
2. 这时候，pip应该可以用了。如果不行，linux请按下面的命令安装pip：
    `wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py`
3. `/root`目录下解压/git clone下源码:`git clone https://github.com/tangrela/ojbk_jiexi.git`
4. 安装依赖库：`cd ojbk_jiexi && pip install -r requirement.txt`
5. 创建一个`logs`目录: `mkdir logs`
6. 创建数据库：`mv config.sample.py config.py && python rebuildDB.py`
7. 安装`redis`：建议先安装宝塔，然后直接用宝塔安装redis(ps.必须安装redis)
8. 网站目录下运行：`gunicorn -w4 -b 0.0.0.0:5000 run:app`

然后访问 ip:5000 试试
如果不能访问，看看防火墙是否开了5000端口？

------

## 以上都是基本的安装。
### 修改域名
`config.py`中：

    - `domain`：是你的网站域名，用于显示在前端

    - `mm2`：恋恋影视的最新域名

    - `porn91`：91porn的域名

### 如果你需要使用MySQL
修改`config.py`：注释第六行 --> 第五行开头#去掉，修改`user`、`passwd`、`database`

### 配置自启动
1. 修改`supervisord.conf`，将`directory`修改为脚本根目录
2. echo "supervisord -c 网站根目录/supervisord.conf" >> /etc/rc.d/rc.local
3. chmod +x /etc/rc.d/rc.local

### 配置nginx
修改nginx配置文件，添加`server`
```
server {
        listen       80;
        server_name t.v4s0.us; #域名
        charset utf-8;

        access_log  /www/wwwlogs/t.v4s0.us.log;

        location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_redirect off;
        proxy_set_header Host $host:80;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        location /(images|javascript|js|css|flash|media|static)/ {
                root /root/tumblr_clawer/app/static; #目录修改好
                expires 1d;
        }

        #error_page  404              /404.html;

        # redirect server error pages to the static page /50x.html
        #
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
   }

  }
```

### 其他需求请加[qq群](https://jq.qq.com/?_wv=1027&k=5G8OtPx)

------
示例网站：http://ojbk.us

-----

## 2018-01-30更新

支持Tumblr导出视频和图片

## 2018-02-04更新

1. 新增微博批量解析
2. 优化爬虫
3. 上线1.0反爬虫策略
