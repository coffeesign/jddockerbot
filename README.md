# 去my.telegram.org获取api_id api_hash千万不要点错成delete账户！！！！
#### 这个是多docker版，配置好直接在宿主机运行 
#### 修改自:https://github.com/SuMaiKaDe/jddockerbot/tree/master ，一个docker建议用回原版
#### 自己添加了许多功能，自用为主
***
- 使用方法：
    - git clone https://github.com/coffeesign/jddockerbot
    - cd jddockerbot  
    - pip install -r requirements.txt
    - 配置config下的配置文件config_muldk.py，按照提示配置就行了
    - python3 botV4_muldk.py运行bot
    - 如果需要更换机器人token，需要将bot.session删除后，重新运行
***
- 主要实现功能：
   - /start 开始使用本程序
   - /node 执行js脚本文件，目前仅支持/scirpts、/config目录下js，直接输入/node jd_bean_change 即可进行执行。该命令会等待脚本执行完，期间不能使用机器人，建议使用snode命令。
   - /cmd 执行cmd命令,例如/cmd python3 /python/bot.py 则将执行python目录下的bot.py
   - /scmd 执行自定义命令
   - /snode 命令可以选择脚本执行，只能选择/jd/scripts目录下的脚本，选择完后直接后台运行，不影响机器人响应其他命令
   - /log 选择查看执行日志
   - /bean 获取指定容器内各个帐号一周内每天新增京东
   - /getcookie 扫码获取cookie 期间不能进行其他交互
   - /scookie cookie字符串 功能：设置cookie'''

- todo:
    - ~~snode忽略非js文件，由于tg最大支持100个按钮，需要进行排除非js文件~~ 已完成
    - ~~V4更新了，还没来得及看，后期新增~~ V4版本已更新
    - ~~扫码获取cookie~~ 采用lof大佬方案
    - 一键生成提交互助码格式 某些原因，不更新该功能（对 就是因为我太菜了）
