# https://live.kuaishou.com/live_api/liveroom/websocketinfo?liveStreamId=2SNt9-_ZuKQ
# https://livev.m.chenzhongtech.com/wap/live/feed?liveStreamId=2SNt9-_ZuKQ
import sys
import os
import yaml
import signal
from giftJson import giftDict
from playwright.sync_api import sync_playwright
import threading
import os
import time
import json
from google.protobuf.json_format import MessageToDict
from configparser import ConfigParser
# import kuaishou_pb2
from ks_pb2 import SocketMessage
from ks_pb2 import SCWebFeedPush
from ks_pb2 import SCWebLiveWatchingUsers
from ks_pb2 import PayloadType
import argparse
import win32file

BARRAGE_PIPE_NAME = r"\\.\pipe\kspy_barrage_msg_pipe"
EXIT_PIPE_NAME = r"\\.\pipe\kspy_exit_msg_pipe"

user_data_dir = "ms-playwright/firefox-1429/firefox/user data"  # 指定缓存目录，用相对路径
# executable_path = "ms-playwright/firefox-1429/firefox/firefox.exe"
executable_path = "dist/ms-playwright/firefox-1429/firefox/firefox.exe"


class kslive(object):
    def __init__(self, **defaultDict):
        self.path = os.path.abspath('')
        # self.chrome_path = r"\firefox-1419\firefox\firefox.exe"
        self.chrome_path = r"\firefox-1419\chrome\chrome.exe"
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
        self.uri = 'https://live.kuaishou.com/u/'
        self.context = None
        self.browser = None
        self.page = None
        self.file_path = os.path.join(self.path, "config.ini")
        if os.path.exists(self.file_path):
            self.conn = ConfigParser()
            self.conn.read(self.file_path)

            # if not self.conn.has_option('set', 'thread'):
            #     self.conn.set('set', 'thread', '2')
            # if not self.conn.has_option('set', 'live_ids'):
            #     self.conn.set('set', 'live_ids', '')
            # if not self.conn.has_option('set', 'phone'):
            #     self.conn.set('set', 'phone', '')
            #
            # self.conn.write(open(self.file_path, "w"))
            self.thread = self.conn.getint('set', 'thread')
            self.mode = self.conn.getboolean('set', 'debug')

            if len(defaultDict):
                self.live_ids = defaultDict['live_ids']
                self.phone = defaultDict['phone']
                self.pwd = defaultDict['pwd']
            else:
                self.live_ids = self.conn.get('set', 'live_ids')
                self.phone = self.conn.get('set', 'phone')
                self.pwd = self.conn.get('set', 'pwd')
        # TODO 关注包
        self.barrageLists = []  # 弹幕
        self.watchingUsersLists = []  # 进入直播间
        self.giftLists = []  # 礼物
        self.likeLists = []  # 点赞

        self.lock = threading.Lock()

    def find_file(self, find_path, file_type) -> list:
        """
        寻找文件
        :param find_path: 子路径
        :param file_type: 文件类型
        :return:
        """
        path = self.path + "\\" + find_path
        data_list = []
        for root, dirs, files in os.walk(path):
            if root != path:
                break
            for file in files:
                file_path = os.path.join(root, file)
                if file_path.find(file_type) != -1:
                    data_list.append(file_path)
        return data_list

    def sendThread(self):
        time.sleep(10)
        print('start pipe thread')
        with open('./avatarfile/cfg/avatarXM.yaml', 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        BARRAGE_INTERVAL = config["TEST"]["BARRAGE_INTERVAL"]
        while True:
            try:
                _pipe = win32file.CreateFile(BARRAGE_PIPE_NAME,
                                             win32file.GENERIC_WRITE,
                                             0, None,
                                             win32file.OPEN_EXISTING, 0, None)
                if _pipe != win32file.INVALID_HANDLE_VALUE:
                    break
            except Exception as e:
                print(e)

        while True:
            try:
                # msg_list = ['测试弹幕 0', '测试弹幕 1', '测试弹幕 2']
                # with open(
                #         f"./avatarfile/bin/obs-kuaishou-live-main/logs/{int(time.time())}.log",
                #         "a") as f:
                #     f.write("pass barrage msg \n")
                self.lock.acquire()

                postStr = json.dumps(dict(aBarrage=self.barrageLists,
                                          aMember=self.watchingUsersLists,
                                          aLike=self.likeLists,
                                          aGift=self.giftLists),
                                     ensure_ascii=False)
                self.barrageLists.clear()
                self.watchingUsersLists.clear()
                self.likeLists.clear()
                self.giftLists.clear()

                self.lock.release()
                print(f"{postStr}")
                postStr = postStr.encode()
                result = win32file.WriteFile(_pipe, postStr)
                print(f"pass barrage message done {result}")
                time.sleep(BARRAGE_INTERVAL)
            except Exception as e:
                print(e)
                break
        win32file.CloseHandle(_pipe)
        # sys.exit()
        pid = os.getpid()  # 获取当前进程的PID
        os.kill(pid, signal.SIGTERM)  # 主动结束指定ID的程序运行

    def main(self, lid, semaphore):
        with semaphore:
            thread_name = threading.current_thread().name.split("-")[0]
            print('start conect web')
            with sync_playwright() as p:
                # self.browser = p.firefox.launch(headless=False)
                if self.mode:
                    self.context = p.firefox.launch_persistent_context(
                        user_data_dir="",
                        executable_path=executable_path,
                        headless=False)
                else:
                    self.context = p.firefox.launch_persistent_context(
                        user_data_dir="",
                        executable_path=executable_path,
                        headless=True)
                # self.browser = p.firefox.launch(headless=True)
                # executable_path=self.path + self.chrome_path
                # cookie_list = self.find_file("cookie", "json")
                # self.context = self.browser.new_context(storage_state=cookie_list[0], user_agent=self.ua)
                # self.context = self.browser.new_context(user_agent=self.ua)
                self.page = self.context.new_page()
                self.page.add_init_script(
                    "Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});")
                self.page.goto("https://live.kuaishou.com/")
                element = self.page.get_attribute('.no-login', "style")
                if not element:
                    self.page.locator('.login').click()
                    self.page.locator(
                        'li.tab-panel:nth-child(2) > h4:nth-child(1)').click()
                    self.page.locator('.change-login').click()
                    self.page.locator(
                        'div.normal-login-item:nth-child(1) > div:nth-child(1) > input:nth-child(1)').fill(
                        self.phone)
                    self.page.locator(
                        'div.normal-login-item:nth-child(2) > div:nth-child(1) > input:nth-child(1)').fill(
                        self.pwd)
                    self.page.locator('.login-button').click()
                try:
                    self.page.wait_for_selector(
                        "#app > section > div.header-placeholder > header > div.header-main > "
                        "div.right-part > div.user-info > div.tooltip-trigger > span",
                        timeout=1000 * 60 * 2)
                    if not os.path.exists(self.path + "\\cookie"):
                        os.makedirs(self.path + "\\cookie")
                    # self.context.storage_state(path=self.path + "\\cookie\\" + self.phone + ".json")
                    # 检测是否开播
                    selector = "html body div#app div.live-room div.detail div.player " \
                               "div.kwai-player.kwai-player-container.kwai-player-rotation-0 " \
                               "div.kwai-player-container-video div.kwai-player-plugins div.center-state div.state " \
                               "div.no-live-detail div.desc p.tip"  # 检测正在直播时下播的选择器
                    # try:
                    #     msg = self.page.locator(selector).text_content(timeout=3000)
                    #     print("当前%s" % thread_name + "，" + msg)
                    #     self.context.close()
                    #     # self.browser.close()
                    #
                    # except Exception as e:
                    #     print("当前%s，[%s]正在直播" % (thread_name, lid))
                    #     self.page.goto(self.uri + lid)
                    #     self.page.on("websocket", self.web_sockets)
                    #     self.page.wait_for_selector(selector, timeout=86400000)
                    #     print("当前%s，[%s]的直播结束了" % (thread_name, lid))
                    #     self.context.close()
                    # self.browser.close()

                    print("当前%s，[%s]正在直播" % (thread_name, lid))
                    self.page.goto(self.uri + lid)
                    self.page.on("websocket", self.web_sockets)
                    self.page.wait_for_selector(selector, timeout=86400000)
                    print("当前%s，[%s]的直播结束了" % (thread_name, lid))
                    self.context.close()



                except Exception:
                    print("登录失败")
                    self.context.close()
                    # self.browser.close()

    def web_sockets(self, web_socket):
        urls = web_socket.url
        print(f"urls -- {urls}")
        if '/websocket' in urls:
            web_socket.on("close", self.websocket_close)
            web_socket.on("framereceived", self.handler)

    def websocket_close(self):
        print('websocket close')
        self.context.close()
        # self.browser.close()

    def handler(self, websocket):
        # Message = kuaishou_pb2.SocketMessage()
        Message = SocketMessage()
        Message.ParseFromString(websocket)
        if Message.payloadType == 310:
            self.parseFeedPushPack(Message.payload)
        if Message.payloadType == PayloadType.SC_LIVE_WATCHING_LIST:
            self.parseSCWebLiveWatchingUsers(Message.payload)

    def parseFeedPushPack(self, message: bytes):
        # SCWebFeedPUsh = kuaishou_pb2.SCWebFeedPush()
        SCWebFeedPUsh = SCWebFeedPush()
        SCWebFeedPUsh.ParseFromString(message)
        obj = MessageToDict(SCWebFeedPUsh, preserving_proto_field_name=True)

        if obj.get('commentFeeds', ''):
            msg_list = obj.get('commentFeeds', '')
            self.lock.acquire()
            for i in msg_list:
                userName = i['user']['userName']
                pid = i['user']['principalId']
                content = i['content']
                print("msg - %s  -->  %s  -->  %s" % (userName, pid, content))
                self.barrageLists.append(dict(user=userName, content=content))
            self.lock.release()
        if obj.get('giftFeeds', ''):
            msg_list = obj.get('giftFeeds', '')
            self.lock.acquire()
            for i in msg_list:
                userName = i['user']['userName']
                giftId = i['giftId']
                giftDic = giftDict["data"].get(str(giftId), {
                    "giftName": "荧光棒",
                    "giftUrl": "http://p1-live.a.yximgs.com/uhead/AB/2020/01/13/10/BMjAyMDAxMTMxMDE5MTZfMF9nMV9sdg==.jpg"
                })
                giftName = giftDic["giftName"]
                print("giftFeeds - %s  -->  %s" % (userName, giftName))
                self.giftLists.append(dict(user=userName, gift=giftName))
            self.lock.release()
        if obj.get('likeFeeds', ''):
            msg_list = obj.get('likeFeeds', '')
            self.lock.acquire()
            for i in msg_list:
                userName = i['user']['userName']
                pid = i['user']['principalId']
                print("likeFeeds - %s -->  %s" % (userName, pid))
                self.likeLists.append(dict(user=userName))
            self.lock.release()

    def parseSCWebLiveWatchingUsers(self, message: bytes):
        # scWebLiveWatchingUsers = kuaishou_pb2.SCWebLiveWatchingUsers()
        scWebLiveWatchingUsers = SCWebLiveWatchingUsers()
        scWebLiveWatchingUsers.ParseFromString(message)
        obj = MessageToDict(scWebLiveWatchingUsers,
                            preserving_proto_field_name=True)
        if obj.get('watchingUser', ''):
            msg_list = obj.get('watchingUser', '')
            self.lock.acquire()
            for i in msg_list:
                userName = i['user']['userName']
                print("enterRoom - %s " % (userName))
                self.watchingUsersLists.append(dict(user=userName))
            self.lock.release()


class run(kslive):
    def __init__(self, **defaultDict):
        super().__init__(**defaultDict)
        self.ids_list = self.live_ids.split(",")
        self.defaultDict = defaultDict

    def run_live(self):
        """
        主程序入口
        :return:
        """
        t_list = []
        # 允许的最大线程数
        if self.thread < 1:
            self.thread = 1
        elif self.thread > 8:
            self.thread = 8
            print("线程最大允许8，线程数最好设置cpu核心数")

        semaphore = threading.Semaphore(self.thread)
        # 用于记录数量
        n = 0
        if not self.live_ids:
            print("请导入网页直播id，多个以','间隔")
            return

        for i in self.ids_list:
            n += 1
            ksliveHandler = kslive(**self.defaultDict)
            t = threading.Thread(target=ksliveHandler.main, args=(i, semaphore),
                                 name=f"线程：{n}-{i}")
            t_con = threading.Thread(target=ksliveHandler.sendThread, args=(),
                                     name=f"线程：{n}-{i} sendThread")
            t.start()
            t_con.start()
            t_list.append(t)
            t_list.append(t_con)
        for i in t_list:
            i.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="avatar engine")
    parser.add_argument('-m', "--mobile", type=str, default='13260271063',
                        help="mobile phone")
    parser.add_argument('-p', "--pwd", type=str, default="123qweqwe",
                        help="pass word")
    parser.add_argument('-r', '--roomId', type=str, default='KPL704668133',
                        help='live room id')
    cmd_args = parser.parse_args()

    # cmd_args.roomId = 'KPL704668133'

    run(live_ids=cmd_args.roomId, phone=cmd_args.mobile,
        pwd=cmd_args.pwd).run_live()
