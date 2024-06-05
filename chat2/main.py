# coding:utf-8
import json
import math
import os
import re
import threading
import socket
import sqlite3
import sys
import datetime
import time
from functools import partial

import numpy as np
import pandas as pd
import zhipuai
import requests
import winsound
from PyQt5.QtWidgets import QComboBox
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
from PyQt5.QtGui import QFont, QFontMetrics, QPixmap
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtCore import QObject, pyqtSignal
from matplotlib import pyplot as plt

from ui.LogInAndSignUp import Ui_Form_LogInAndSignUp  # 登录与注册窗口
from ui.Menu import Ui_MenuWindow  # 主菜单窗口
from ui.Chat import Ui_ChatWindow  # 聊天窗口
from ui.crawler import Ui_CrawlerWindow  # 每日资讯窗口
from ui.settings import Ui_SettingsWindow  # 设置窗口
from ui.settings2 import Ui_SettingsWindow2  # 设置窗口
from ui.AiFriends import Ui_MainWindow  # 虚拟伙伴窗口
from crawlerWeatherAsync import WeatherCrawler  # 异步爬虫
from crawlerNewsAsync import NewsCrawler  # 异步爬虫

# 全局实例化另外一个窗口
global_menuWd = None
global_chatWd = None
global_settingsWd = None
global_crawlerWd = None
global_aiWd = None
# 客户端设置
IP = socket.gethostbyname(socket.gethostname())  # 自动获取本机IP地址 #'127.0.0.1'
PORT = '5050'
NAME = '刘培富'
connect_init = True  # 初始化标志
connect_flag = False  # 连接标志
receive_flag = False  # 接收消息标志
exit_flag = False  # 退出接收标志
con = None  # 套接字
'''
登录与注册部分
'''


class LogInAndSignUpWindow(QWidget, Ui_Form_LogInAndSignUp):
    """登录与注册窗口"""

    def __init__(self, parent=None):
        """初始化函数"""
        super(LogInAndSignUpWindow, self).__init__(parent)
        self.setupUi(self)

        # 提示
        self.lineEdit_LogInID.setPlaceholderText('请输入账号')
        self.lineEdit_LogInPW.setPlaceholderText('请输入密码')
        self.lineEdit_SignUpID.setPlaceholderText('账号为11位')
        self.lineEdit_SignUpUser.setPlaceholderText('用户名不超过6位')
        self.lineEdit_SignUpPW.setPlaceholderText('两次密码要相同')
        self.lineEdit_SignUpPW2.setPlaceholderText('两次密码要相同')

        # 操作
        self.pushButton_LogIn.clicked.connect(self.LogIn)
        self.pushButton_SignUp.clicked.connect(self.SingUp)

    def LogIn(self):
        """登录函数"""
        LogInID = self.lineEdit_LogInID.text()
        LogInPW = self.lineEdit_LogInPW.text()

        user = self.check_login(LogInID, LogInPW)

        if user != None:
            # 设置用户账号和用户名为全局变量
            global global_id
            global global_user
            global_id = LogInID
            global_user = user

            QMessageBox.information(
                self,
                '登录成功',
                '欢迎使用本系统！')
            # 实例化另外一个窗口
            global global_menuWd
            global_menuWd = MenuWindow()
            # 显示新窗口
            global_menuWd.show()
            # 关闭自己
            self.close()
        else:
            print('error')
            QMessageBox.critical(
                self,
                '错误',
                '账号或密码错误，请重新输入！')

    def SingUp(self):
        """注册函数"""
        SignUpID = self.lineEdit_SignUpID.text()
        SignUpUser = self.lineEdit_SignUpUser.text()
        SignUpPW = self.lineEdit_SignUpPW.text()
        SignUpPW2 = self.lineEdit_SignUpPW2.text()

        if len(SignUpID) != 11:
            QMessageBox.critical(
                self,
                '错误',
                '账号不满足11位')
        elif len(SignUpUser) > 6:
            QMessageBox.critical(
                self,
                '错误',
                '用户名不满足小于6位')
        elif SignUpPW != SignUpPW2:
            QMessageBox.critical(
                self,
                '错误',
                '两次密码不相同')
        else:
            self.insert_signup(SignUpID, SignUpUser, SignUpPW)
            QMessageBox.information(
                self,
                '注册成功',
                '注册成功！')

    def check_login(self, LogInID, LogInPW):
        """判断账号密码是否正确"""
        conn = sqlite3.connect("./data/Users.db")
        cur = conn.cursor()
        # 查询是否存在匹配的 LogInID
        cur.execute("SELECT * FROM T_users WHERE SignUpID=?", (LogInID,))
        row = cur.fetchone()
        if row:
            # 如果找到了匹配的LogInID，检查密码是否匹配
            if row[3] == LogInPW:
                return row[2]  # 返回SignUpUser
        conn.close()
        return None  # 如果没有匹配的LogInID或密码不匹配，返回None

    def insert_signup(self, SignUpID, SignUpUser, SignUpPW):
        """插入数据库"""
        conn = sqlite3.connect("./data/Users.db")  # 建立一个基于硬盘的数据库实例
        cur = conn.cursor()  # 通过建立数据库游标对象，准备读写操作
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='T_users'")  # 判断表是否存在
        existing_table = cur.fetchone()
        if not existing_table:  # ID列在插入数据时会自动递增
            cur.execute(
                "CREATE TABLE T_users(ID INTEGER PRIMARY KEY AUTOINCREMENT, SignUpID TEXT, SignUpUser TEXT, SignUpPW TEXT)")  # 根据上表结构建立对应的表结构对象
        cur.execute("INSERT INTO T_users(SignUpID, SignUpUser, SignUpPW) VALUES(?, ?, ?)",
                    (SignUpID, SignUpUser, SignUpPW))  # 示例插入一行记录
        conn.commit()  # 保存提交，确保数据保存成功
        conn.close()  # 关闭与数据库的连接


'''
主菜单部分
'''


class MenuWindow(QMainWindow, Ui_MenuWindow):
    """主菜单窗口"""

    def __init__(self, parent=None):
        """初始化函数"""
        super(MenuWindow, self).__init__(parent)
        self.setupUi(self)

        # 实例化另外一个窗口
        # global global_chatWd
        global global_settingsWd
        global global_crawlerWd
        global global_aiWd
        # global_chatWd = ChatWindow()
        global_settingsWd = SettingsWindow()
        global_crawlerWd = CrawlerWindow()
        global_aiWd = AiFriendsWindow()

        # 设置槽函数
        self.pushButton_ChatNetwork.clicked.connect(self.to_chat)
        self.pushButton_Settings.clicked.connect(self.to_settings)
        self.pushButton_Query.clicked.connect(self.to_crawler)
        self.pushButton_AiFriends.clicked.connect(self.to_ai)

    def to_chat(self):
        """跳转到聊天窗口"""
        global IP
        global PORT
        global NAME
        # global connect_flag
        #
        # if connect_flag == False:
        #     QMessageBox.warning(self, '警告', '服务器链接失败，请重新设置连接参数！')
        #     return

        if IP is None:
            QMessageBox.warning(self, '警告', 'IP未设置！')
            return
        if PORT is None:
            QMessageBox.warning(self, '警告', 'PORT未设置！')
            return
        if NAME is None:
            QMessageBox.warning(self, '警告', '昵称未设置！')
            return

        # 显示新窗口
        # global connect_init
        # connect_init = False
        # print("初始化")
        # print(connect_init)
        global global_chatWd
        if not global_chatWd:
            global_chatWd = ChatWindow()
        global_chatWd.show()

        # 关闭自己
        self.close()

    def to_settings(self):
        """跳转到设置窗口"""
        # 显示新窗口
        global global_settingsWd
        global_settingsWd.show()
        # 关闭自己
        self.close()

    def to_crawler(self):
        """跳转到爬虫窗口"""
        # 显示新窗口
        global global_crawlerWd
        global_crawlerWd.show()
        # 关闭自己
        self.close()

    def to_ai(self):
        """跳转到虚拟伙伴窗口"""
        # 显示新窗口
        global global_aiWd
        global_aiWd.show()
        # 关闭自己
        self.close()


'''
聊天部分
'''


class MySignals(QObject):
    """自定义的信号"""
    update = pyqtSignal(str)  # 更新聊天内容信号
    weather = pyqtSignal(str)  # 更新聊天内容信号
    news = pyqtSignal(str)  # 更新新闻内容信号
    get_news = pyqtSignal(str)  # 获取新闻内容信号
    get_res = pyqtSignal(str)  # 获取新闻内容信号


class ChatWindow(QMainWindow, Ui_ChatWindow):
    """聊天窗口"""
    re_flag = True
    con_flag = False
    online = None  # 在线用户列表

    def __init__(self, parent=None):
        """初始化函数"""
        super(ChatWindow, self).__init__(parent)
        self.setupUi(self)

        # 接收者
        self.receiver = None

        # 初始化信号
        self.ms = MySignals()
        self.ms.update.connect(self.update_text)  # 接收到信号后调用槽函数

        # 绑定槽函数
        self.pushButton_Exit.clicked.connect(self.to_menu)
        self.pushButton_ChatList.clicked.connect(self.frameController)  # 群聊
        self.pushButton_MyFriend.clicked.connect(self.frameController)  # 单聊

        self.pushButton_Send.clicked.connect(self.send_msg_many)  # 发送群聊消息
        self.pushButton_Send_alone.clicked.connect(self.send_msg_alone)  # 发送单聊消息
        self.pushButton_Refresh.clicked.connect(self.refresh_online)
        self.pushButton_Refresh_alone.clicked.connect(self.refresh_online)

        # 监听状态
        scrollbar = self.scrollArea_Chat.verticalScrollBar()
        scrollbar.rangeChanged.connect(self.adjustScrollToMaxValue)  # 监听窗口滚动条范围
        scrollbar_alone = self.scrollArea_Chat_alone.verticalScrollBar()
        scrollbar_alone.rangeChanged.connect(self.adjustScrollToMaxValue)  # 监听窗口滚动条范围

        # 客户端socket初始化
        global IP
        global PORT
        global NAME
        self.label.setText(NAME)  # 设置昵称
        self.SERVER = IP  # 本机IP地址
        self.PORT = int(PORT)  # 端口号，5050比较安全
        self.ADDR = (self.SERVER, self.PORT)  # 地址元组
        self.BUFFER_SIZE = 1024  # 标头
        self.FORMAT = 'utf-8'  # 字符编码
        self.DISCONNECT_MSG = 'exit'  # 断开连接标志

        # 客户端连接服务器
        self.c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.c.connect(self.ADDR)
        self.client_ip, self.client_port = self.c.getsockname()

        # 启动时发一次消息
        def client_init():
            try:
                global IP
                global PORT
                global NAME
                # 构建JSON格式的消息
                data = {
                    "ip": IP,
                    "port": PORT,
                    "mode": "init",
                    "sender": NAME,
                    "receiver": "all",
                    "format": "text",
                    "online": [],
                    "message": "init",
                }
                self.c.send(json.dumps(data).encode(self.FORMAT))  # 发送消息给服务器
                print("初始化完成")
            except Exception as e:
                print("初始化失败！")
                print(e)
                QMessageBox.warning(self, '初始化失败', str(e))
                return

        # 接收子线程
        def receive():  # 接收消息
            global connect_flag
            connect_flag = True

            # cnt = 1
            # while cnt == 1:
            # if ChatWindow.con_flag:
            #     cnt = 0
            while True:
                # if ChatWindow.con_flag:
                #     break
                msg = self.c.recv(self.BUFFER_SIZE).decode(self.FORMAT)
                print("已接收")
                print(msg)
                self.ms.update.emit(msg)  # 发出信号

        if ChatWindow.re_flag:
            print("创建初始化线程")
            thread_client_init = threading.Thread(target=client_init)
            thread_client_init.start()
            print("创建接收线程")
            thread_receive = threading.Thread(target=receive)
            thread_receive.start()
            ChatWindow.re_flag = False

        # global connect_init
        # global receive_flag
        # print(connect_init)
        # if not connect_init:
        #     # 创建一个初始化线程
        #     print("创建初始化线程")
        #     thread_client_init = threading.Thread(target=client_init)
        #     thread_client_init.start()
        #     connect_init = True
        #     receive_flag = True
        # if receive_flag:
        #     # 创建一个接收消息线程
        #     print("创建接收线程")
        #     thread_receive = threading.Thread(target=receive)
        #     thread_receive.start()
        #     receive_flag = False

    def to_menu(self):
        """跳转到主菜单窗口"""
        # # 隐藏当前窗口
        self.hide()
        # 显示新窗口
        global global_menuWd
        if not global_menuWd:
            global_menuWd = MenuWindow()
        global_menuWd.show()

        # # 关闭自己
        # self.close()
        # def client_exit():
        #     ChatWindow.con_flag=True
        #     try:
        #         global IP
        #         global PORT
        #         global NAME
        #         # 构建JSON格式的消息
        #         data = {
        #             "ip": IP,
        #             "port": PORT,
        #             "mode": "exit",
        #             "sender": NAME,
        #             "receiver": "all",
        #             "format": "text",
        #             "online": [],
        #             "message": "exit",
        #         }
        #         self.c.send(json.dumps(data).encode(self.FORMAT))  # 发送消息给服务器
        #     except Exception as e:
        #         print("退出失败！")
        #         print(e)
        #         QMessageBox.warning(self, '退出失败', str(e))
        #         return
        #
        # # 创建一个退出线程
        # thread = threading.Thread(target=client_exit)
        # thread.start()
        # thread.join()
        # # 销毁 ChatWindow() 实例
        # self.deleteLater()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        super().closeEvent(event)  # 调用父类的closeEvent方法，确保原始的关闭逻辑得到执行
        self.to_menu()  # 调用跳转到主菜单的方法

    def frameController(self):  # 页面控制函数
        sender = self.sender().objectName()  # 获取当前信号 sender
        index = {
            "pushButton_ChatList": 0,  # page_0
            "pushButton_MyFriend": 1,  # page_1
        }
        self.stackedWidget.setCurrentIndex(index[sender])  # 根据信号 index 设置所显示的页面

    # 群聊部分########################################################################################################
    # def client_init(self):
    #     if self.CONNECT == False:
    #         # 客户端连接服务器
    #         self.c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         self.c.connect(self.ADDR)

    def send_msg_many(self):
        """发送群聊消息"""
        global NAME
        self.add_bubble_many_right(self.plainTextEdit_InPut.toPlainText(), NAME)

        def send():  # 发送函数
            try:
                print("已发送群聊消息")
                global IP
                global PORT

                # 构建JSON格式的消息
                data = {
                    "ip": IP,
                    "port": PORT,
                    "mode": "group_chat",
                    "sender": NAME,
                    "receiver": "all",
                    "format": "text",
                    "online": [],
                    "message": self.plainTextEdit_InPut.toPlainText(),
                }
                self.c.send(json.dumps(data).encode(self.FORMAT))  # 发送消息给服务器
                self.plainTextEdit_InPut.clear()  # 清空输入框
            except Exception as e:
                print("发送失败！")
                print(e)
                QMessageBox.warning(self, '发送失败', str(e))
                return

        # 子线程发送信号更新界面，发送和接收各开一个线程
        thread = threading.Thread(target=send)
        thread.start()

    def refresh_online(self):
        global NAME
        # 实例化列表模型，添加数据
        slm = QStringListModel()
        ChatWindow.online.remove(NAME)  # 把自己删掉
        qList = ChatWindow.online
        # 设置模型列表视图，加载数据列表
        slm.setStringList(qList)
        # 设置列表视图的模型
        self.listView_ChatList.setModel(slm)
        self.listView_ChatList_alone.setModel(slm)
        # 单击触发自定义的槽函数
        self.listView_ChatList_alone.clicked.connect(partial(self.set_receiver, qList))

    def set_receiver(self, qList, qModelIndex):
        receiver = qList[qModelIndex.row()]
        self.receiver = receiver
        print("你选择了：", self.receiver)

    def update_text(self, msg):
        """更新消息显示框函数"""
        global NAME
        try:
            data = json.loads(msg)
            ip = data["ip"]
            port = data["port"]
            mode = data["mode"]
            sender = data["sender"]
            receiver = data["receiver"]
            format = data["format"]
            online = data["online"]
            message = data["message"]
            ChatWindow.online = online
            if mode == 'group_chat':
                print("已经群聊")
                if sender != NAME:  # 发送者不为自己
                    self.add_bubble_many_left(message, sender)
            elif mode == 'group_alone':
                print("已经单聊")
                self.add_bubble_alone_left(message, sender)
        except Exception as e:
            print("聊天出错！")
            print(e)
            QMessageBox.warning(self, '聊天出错', str(e))
            return

    def add_bubble_many_left(self, text, user):
        """群聊左气泡"""
        print("增加群聊左气泡")
        self.widget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QtCore.QSize(300, 120))
        self.widget.setMaximumSize(QtCore.QSize(300, 120))
        self.widget.setObjectName("widget")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.label_Avatar = QtWidgets.QLabel(self.widget)
        self.label_Avatar.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar.setText("")
        self.label_Avatar.setPixmap(QtGui.QPixmap("./img/lpf.jpg"))
        self.label_Avatar.setScaledContents(True)
        self.label_Avatar.setObjectName("label_Avatar")
        self.verticalLayout_9.addWidget(self.label_Avatar)
        spacerItem1 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_9.addItem(spacerItem1)
        self.verticalLayout_9.setStretch(0, 3)
        self.verticalLayout_9.setStretch(1, 7)
        self.horizontalLayout_9.addLayout(self.verticalLayout_9)
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.label_Time = QtWidgets.QLabel(self.widget)
        self.label_Time.setObjectName("label_Time")
        self.verticalLayout_8.addWidget(self.label_Time)
        self.textBrowser_OutPut = QtWidgets.QTextBrowser(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textBrowser_OutPut.sizePolicy().hasHeightForWidth())
        self.textBrowser_OutPut.setSizePolicy(sizePolicy)
        self.textBrowser_OutPut.setStyleSheet("background-color: rgba(71,121,214,20);")
        self.textBrowser_OutPut.setOpenExternalLinks(True)
        self.textBrowser_OutPut.setObjectName("textBrowser_OutPut")
        self.textBrowser_OutPut.setText(text)  # 设置文本
        self.verticalLayout_8.addWidget(self.textBrowser_OutPut)
        self.verticalLayout_8.setStretch(0, 2)
        self.verticalLayout_8.setStretch(1, 8)
        self.horizontalLayout_9.addLayout(self.verticalLayout_8)
        self.verticalLayout_7.addWidget(self.widget)
        self.scrollArea_Chat.setWidget(self.scrollAreaWidgetContents)

        # 设置昵称
        name = str(user) + '||' + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        _translate = QtCore.QCoreApplication.translate
        self.label_Time.setText(_translate("MainWindow", name))

    def add_bubble_many_right(self, text, user):
        """群聊右气泡"""
        print("增加群聊右气泡")
        self.widget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.widget.setLayoutDirection(QtCore.Qt.RightToLeft)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QtCore.QSize(300, 120))
        self.widget.setMaximumSize(QtCore.QSize(300, 120))
        self.widget.setObjectName("widget")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.label_Avatar = QtWidgets.QLabel(self.widget)
        self.label_Avatar.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar.setText("")
        self.label_Avatar.setPixmap(QtGui.QPixmap("./img/lpf.jpg"))
        self.label_Avatar.setScaledContents(True)
        self.label_Avatar.setObjectName("label_Avatar")
        self.verticalLayout_9.addWidget(self.label_Avatar)
        spacerItem1 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_9.addItem(spacerItem1)
        self.verticalLayout_9.setStretch(0, 3)
        self.verticalLayout_9.setStretch(1, 7)
        self.horizontalLayout_9.addLayout(self.verticalLayout_9)
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.label_Time = QtWidgets.QLabel(self.widget)
        self.label_Time.setObjectName("label_Time")
        self.verticalLayout_8.addWidget(self.label_Time)
        self.textBrowser_OutPut = QtWidgets.QTextBrowser(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textBrowser_OutPut.sizePolicy().hasHeightForWidth())
        self.textBrowser_OutPut.setSizePolicy(sizePolicy)
        self.textBrowser_OutPut.setStyleSheet("background-color: rgba(71,121,214,20);")
        self.textBrowser_OutPut.setOpenExternalLinks(True)
        self.textBrowser_OutPut.setObjectName("textBrowser_OutPut")
        self.textBrowser_OutPut.setText(text)  # 设置文本
        self.verticalLayout_8.addWidget(self.textBrowser_OutPut)
        self.verticalLayout_8.setStretch(0, 2)
        self.verticalLayout_8.setStretch(1, 8)
        self.horizontalLayout_9.addLayout(self.verticalLayout_8)
        self.verticalLayout_7.addWidget(self.widget)
        self.scrollArea_Chat.setWidget(self.scrollAreaWidgetContents)

        # 设置昵称
        name = str(user) + '||' + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        _translate = QtCore.QCoreApplication.translate
        self.label_Time.setText(_translate("MainWindow", name))
        self.label_Time.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)  # 右对齐

    def adjustScrollToMaxValue(self):
        """窗口滚动到最底部"""
        scrollbar = self.scrollArea_Chat.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        scrollbar = self.scrollArea_Chat_alone.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # 单聊部分#####################################
    def send_msg_alone(self):
        """发送单聊消息"""
        global NAME
        self.add_bubble_alone_right(self.plainTextEdit_InPut_alone.toPlainText(), NAME)
        receiver = self.receiver
        if receiver is None:
            QMessageBox.warning(self, '警告', '未选择聊天对象！')
            return

        def send(receiver):  # 发送函数
            try:
                print("已发送单聊消息")
                global IP
                global PORT

                # 构建JSON格式的消息
                data = {
                    "ip": IP,
                    "port": PORT,
                    "mode": "group_alone",
                    "sender": NAME,
                    "receiver": receiver,
                    "format": "text",
                    "online": [],
                    "message": self.plainTextEdit_InPut_alone.toPlainText(),
                }
                self.c.send(json.dumps(data).encode(self.FORMAT))  # 发送消息给服务器
                self.plainTextEdit_InPut_alone.clear()  # 清空输入框
            except Exception as e:
                print("发送失败！")
                print(e)
                QMessageBox.warning(self, '发送失败', str(e))
                return

        # 子线程发送信号更新界面，发送和接收各开一个线程
        thread = threading.Thread(target=send, args=(receiver,))
        thread.start()

    def add_bubble_alone_left(self, text, user):
        """单聊左气泡"""
        self.widget_alone = QtWidgets.QWidget(self.scrollAreaWidgetContents_alone)
        self.widget_alone.setMinimumSize(QtCore.QSize(300, 120))
        self.widget_alone.setMaximumSize(QtCore.QSize(300, 120))
        self.widget_alone.setObjectName("widget_alone")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.widget_alone)
        self.horizontalLayout_12.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_12.setSpacing(7)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.verticalLayout_15 = QtWidgets.QVBoxLayout()
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.label_Avatar_alone = QtWidgets.QLabel(self.widget_alone)
        self.label_Avatar_alone.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_alone.setText("")
        self.label_Avatar_alone.setPixmap(QtGui.QPixmap("./img/lpf.jpg"))
        self.label_Avatar_alone.setScaledContents(True)
        self.label_Avatar_alone.setObjectName("label_Avatar_alone")
        self.verticalLayout_15.addWidget(self.label_Avatar_alone)
        spacerItem2 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_15.addItem(spacerItem2)
        self.verticalLayout_15.setStretch(0, 3)
        self.verticalLayout_15.setStretch(1, 7)
        self.horizontalLayout_12.addLayout(self.verticalLayout_15)
        self.verticalLayout_16 = QtWidgets.QVBoxLayout()
        self.verticalLayout_16.setObjectName("verticalLayout_16")
        self.label_Time_alone = QtWidgets.QLabel(self.widget_alone)
        self.label_Time_alone.setObjectName("label_Time_alone")
        self.verticalLayout_16.addWidget(self.label_Time_alone)
        self.textBrowser_OutPut_alone = QtWidgets.QTextBrowser(self.widget_alone)
        self.textBrowser_OutPut_alone.setStyleSheet("background-color: rgba(71,121,214,20);")
        self.textBrowser_OutPut_alone.setObjectName("textBrowser_OutPut_alone")
        self.textBrowser_OutPut_alone.setText(text)  # 设置文本
        self.verticalLayout_16.addWidget(self.textBrowser_OutPut_alone)
        self.verticalLayout_16.setStretch(0, 1)
        self.verticalLayout_16.setStretch(1, 9)
        self.horizontalLayout_12.addLayout(self.verticalLayout_16)
        self.verticalLayout_14.addWidget(self.widget_alone)
        self.scrollArea_Chat_alone.setWidget(self.scrollAreaWidgetContents_alone)

        # 设置昵称
        name = str(user) + '||' + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        _translate = QtCore.QCoreApplication.translate
        self.label_Time_alone.setText(_translate("MainWindow", name))

    def add_bubble_alone_right(self, text, user):
        """单聊右气泡"""
        self.widget_alone = QtWidgets.QWidget(self.scrollAreaWidgetContents_alone)
        self.widget_alone.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.widget_alone.setMinimumSize(QtCore.QSize(300, 120))
        self.widget_alone.setMaximumSize(QtCore.QSize(300, 120))
        self.widget_alone.setObjectName("widget_alone")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.widget_alone)
        self.horizontalLayout_12.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_12.setSpacing(7)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.verticalLayout_15 = QtWidgets.QVBoxLayout()
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.label_Avatar_alone = QtWidgets.QLabel(self.widget_alone)
        self.label_Avatar_alone.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_alone.setText("")
        self.label_Avatar_alone.setPixmap(QtGui.QPixmap("./img/lpf.jpg"))
        self.label_Avatar_alone.setScaledContents(True)
        self.label_Avatar_alone.setObjectName("label_Avatar_alone")
        self.verticalLayout_15.addWidget(self.label_Avatar_alone)
        spacerItem2 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_15.addItem(spacerItem2)
        self.verticalLayout_15.setStretch(0, 3)
        self.verticalLayout_15.setStretch(1, 7)
        self.horizontalLayout_12.addLayout(self.verticalLayout_15)
        self.verticalLayout_16 = QtWidgets.QVBoxLayout()
        self.verticalLayout_16.setObjectName("verticalLayout_16")
        self.label_Time_alone = QtWidgets.QLabel(self.widget_alone)
        self.label_Time_alone.setObjectName("label_Time_alone")
        self.verticalLayout_16.addWidget(self.label_Time_alone)
        self.textBrowser_OutPut_alone = QtWidgets.QTextBrowser(self.widget_alone)
        self.textBrowser_OutPut_alone.setStyleSheet("background-color: rgba(71,121,214,20);")
        self.textBrowser_OutPut_alone.setObjectName("textBrowser_OutPut_alone")
        self.textBrowser_OutPut_alone.setText(text)  # 设置文本
        self.verticalLayout_16.addWidget(self.textBrowser_OutPut_alone)
        self.verticalLayout_16.setStretch(0, 1)
        self.verticalLayout_16.setStretch(1, 9)
        self.horizontalLayout_12.addLayout(self.verticalLayout_16)
        self.verticalLayout_14.addWidget(self.widget_alone)
        self.scrollArea_Chat_alone.setWidget(self.scrollAreaWidgetContents_alone)

        # 设置昵称
        name = str(user) + '||' + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        _translate = QtCore.QCoreApplication.translate
        self.label_Time_alone.setText(_translate("MainWindow", name))
        self.label_Time_alone.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)  # 右对齐


'''
设置部分
'''


class SettingsWindow(QMainWindow, Ui_SettingsWindow):
    """设置窗口"""

    def __init__(self, parent=None):
        """初始化函数"""
        super(SettingsWindow, self).__init__(parent)
        self.setupUi(self)

        # 设置提示
        global IP
        global PORT
        global NAME
        self.lineEdit_ip.setText(IP)
        self.lineEdit_port.setText(PORT)
        self.lineEdit_name.setText(NAME)

        self.lineEdit_name.setPlaceholderText('数字、字母、下划线、中文的任意组合')

        # 绑定槽函数
        self.pushButton_yes.clicked.connect(self.change_settings)
        self.pushButton_no.clicked.connect(self.to_menu)

    def to_menu(self):
        """跳转到主菜单窗口"""
        # 隐藏当前窗口
        self.hide()
        # 显示新窗口
        global global_menuWd
        if not global_menuWd:
            global_menuWd = MenuWindow()
        global_menuWd.show()
        # # 关闭自己
        # self.close()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        super().closeEvent(event)  # 调用父类的closeEvent方法，确保原始的关闭逻辑得到执行
        self.to_menu()  # 调用跳转到主菜单的方法

    def change_settings(self):
        global IP
        global PORT
        global NAME

        IP = self.lineEdit_ip.text()
        PORT = self.lineEdit_port.text()
        NAME = self.lineEdit_name.text()

        # 验证IP是否符合规范和范围
        ip_pattern = r'^(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                     r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                     r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                     r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(ip_pattern, IP):
            QMessageBox.warning(self, '警告', 'IP不符合规范！')
            return

        # 验证Port是否符合规范和范围
        if not re.match(r'^[1-9]\d*$', PORT) or not (0 < int(PORT) < 65536):
            QMessageBox.warning(self, '警告', 'Port不符合规范！')
            return

        # 验证Name是否符合规范
        if not re.match(r'^[\u4e00-\u9fa5\w]+$', NAME):
            QMessageBox.warning(self, '警告', '昵称不符合规范！')
            return

        print("IP:", IP)
        print("PORT:", PORT)
        print("NAME:", NAME)
        QMessageBox.information(self, '信息', '修改完成！')
        self.to_menu()


'''
爬虫部分
'''


class CrawlerWindow(QMainWindow, Ui_CrawlerWindow):
    """爬虫窗口"""

    def __init__(self, parent=None):
        """初始化函数"""
        super(CrawlerWindow, self).__init__(parent)
        self.setupUi(self)

        self.ms = MySignals()
        self.ms.weather.connect(self.update_weather_finish)  # 接收到信号后调用槽函数
        self.ms.news.connect(self.update_news_finish)  # 接收到信号后调用槽函数
        self.ms.get_news.connect(self.get_news_finish)  # 接收到信号后调用槽函数

        # 绑定槽函数
        self.pushButton_Exit.clicked.connect(self.to_menu)
        self.pushButton_weather.clicked.connect(self.frameController)
        self.pushButton_weather.clicked.connect(self.province_combobox)
        self.comboBox_province.currentTextChanged.connect(self.city_combobox)
        self.comboBox_city.currentTextChanged.connect(self.county_combobox)
        self.comboBox_county.currentTextChanged.connect(self.figure_combobox)
        self.pushButton_query.clicked.connect(self.query_weather)
        self.pushButton_update.clicked.connect(self.crawler_weather)

        self.pushButton_news.clicked.connect(self.frameController)
        self.pushButton_news.clicked.connect(self.column_combobox)
        self.comboBox_column.currentTextChanged.connect(self.title_combobox)
        self.pushButton_query_2.clicked.connect(self.query_news)
        self.pushButton_update_2.clicked.connect(self.crawler_news)

    def to_menu(self):
        """跳转到主菜单窗口"""
        # 隐藏当前窗口
        self.hide()
        # 显示新窗口
        global global_menuWd
        if not global_menuWd:
            global_menuWd = MenuWindow()
        global_menuWd.show()
        # # 关闭自己
        # self.close()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        super().closeEvent(event)  # 调用父类的closeEvent方法，确保原始的关闭逻辑得到执行
        self.to_menu()  # 调用跳转到主菜单的方法

    def frameController(self):
        """页面控制函数"""
        sender = self.sender().objectName()  # 获取当前信号 sender
        index = {
            "pushButton_weather": 0,  # page_0
            "pushButton_news": 1,  # page_1
        }
        self.stackedWidget.setCurrentIndex(index[sender])  # 根据信号 index 设置所显示的页面

    # 天气部分#############################################
    def province_combobox(self):
        # 清空下拉列表
        self.comboBox_province.clear()
        self.comboBox_city.clear()
        self.comboBox_county.clear()
        self.comboBox_column.clear()
        province_folder = './weather'
        # 遍历指定目录中的文件夹
        for folder_name in os.listdir(province_folder):
            folder_full_path = os.path.join(province_folder, folder_name)
            # 检查路径是否是文件夹
            if os.path.isdir(folder_full_path):
                # 将文件夹名添加到下拉列表中
                self.comboBox_province.addItem(folder_name)

    def city_combobox(self):
        self.comboBox_city.clear()
        selected_province = self.comboBox_province.currentText()
        city_folder = './weather/' + selected_province
        for file_name in os.listdir(city_folder):
            self.comboBox_city.addItem(file_name)

    def county_combobox(self):
        self.comboBox_county.clear()
        selected_province = self.comboBox_province.currentText()
        selected_city = self.comboBox_city.currentText()
        county_folder = './weather/' + selected_province + '/' + selected_city
        for file_name in os.listdir(county_folder):
            self.comboBox_county.addItem(file_name)

    def figure_combobox(self):
        self.comboBox_figure.clear()
        columns = ['温度', '相对湿度', '降水量', '风向']
        for column in columns:
            self.comboBox_figure.addItem(column)

    def query_weather(self):
        """查询曲线同"""
        try:
            selected_province = self.comboBox_province.currentText()
            selected_city = self.comboBox_city.currentText()
            selected_county = self.comboBox_county.currentText()
            selected_figure = self.comboBox_figure.currentText()
            file_path = './weather/' + selected_province + '/' + selected_city + '/' + selected_county + '/'
            data = pd.read_csv(f'{file_path}weather.csv')  # 读取csv
            print(selected_figure)
            if selected_figure == '温度':
                plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                self.tem_curve(data, selected_county)  # 温度
                pixmap_tem = QPixmap('./figures/tem_curve.png')
                pixmap_tem = pixmap_tem.scaled(self.label_tu.size())
                self.label_tu.setPixmap(pixmap_tem)
                self.label_tu.setScaledContents(True)  # 图片自适应Label大小
            elif selected_figure == '相对湿度':
                plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                self.hum_curve(data, selected_county)  # 湿度
                pixmap_tem = QPixmap('./figures/hum_curve.png')
                pixmap_tem = pixmap_tem.scaled(self.label_tu.size())
                self.label_tu.setPixmap(pixmap_tem)
                self.label_tu.setScaledContents(True)  # 图片自适应Label大小
            elif selected_figure == '降水量':
                plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                self.rain_curve(data, selected_county)  # 降水量
                pixmap_tem = QPixmap('./figures/rain_curve.png')
                pixmap_tem = pixmap_tem.scaled(self.label_tu.size())
                self.label_tu.setPixmap(pixmap_tem)
                self.label_tu.setScaledContents(True)  # 图片自适应Label大小
            elif selected_figure == '风向':
                plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                self.wind_radar(data, selected_county)  # 风向
                pixmap_tem = QPixmap('./figures/wind_radar.png')
                pixmap_tem = pixmap_tem.scaled(self.label_tu.size())
                self.label_tu.setPixmap(pixmap_tem)
                self.label_tu.setScaledContents(True)  # 图片自适应Label大小
        except:
            QMessageBox.warning(self, '警告', '请选择好全部信息！')
            return

    def crawler_weather(self):
        """爬取所有地区的天气数据"""
        selected_province = self.comboBox_province.currentText()
        if not selected_province:
            QMessageBox.warning(self, '警告', '请选择好省份！')
            return

        def craw():
            self.pushButton_update.setEnabled(False)
            selected_province = self.comboBox_province.currentText()
            start_time = time.time()
            weatherCrawler = WeatherCrawler()
            weatherCrawler.main(selected_province)
            print("本次全部结束")
            print("本次花费时间：", time.time() - start_time)
            print("本次爬取链接个数：", weatherCrawler.url_count)
            self.ms.weather.emit(selected_province)  # 发出信号
            self.pushButton_update.setEnabled(True)

        thread = threading.Thread(target=craw)
        thread.start()

    def update_weather_finish(self, selected_province):
        """提示更新完成"""
        QMessageBox.information(self, '信息', f'{selected_province}更新完成！')

    def tem_curve(self, data, file_name):
        """温度曲线绘制"""
        # lock = threading.RLock()
        hour = list(data['小时'])
        tem = list(data['温度'])
        for i in range(0, 25):  # 没有数据就赋值为前面一个
            if math.isnan(tem[i]) == True:
                tem[i] = tem[i - 1]
        tem_ave = sum(tem) / 25  # 求平均温度
        tem_max = max(tem)
        tem_max_hour = tem.index(tem_max)  # 求最高温度
        tem_min = min(tem)
        tem_min_hour = tem.index(tem_min)  # 求最低温度
        x = []  # 实际横坐标,可以当成索引
        x_label = []  # 展示横坐标
        y = []
        for i in range(0, 25):
            x.append(i)
            x_label.append(hour[i])
            y.append(tem[i])
        # lock.acquire()#所有温度曲线共享一个画布，所以要上锁
        plt.figure(1)
        plt.plot(x, y, color='red', label='温度')  # 画出温度曲线
        plt.scatter(x, y, color='red')  # 点出每个时刻的温度点
        plt.plot([0, 25], [tem_ave, tem_ave], color='blue', linestyle='--', label='平均温度')  # 画出平均温度虚线
        plt.text(25 + 0.15, tem_ave + 0.15, str(round(tem_ave, 2)) + '℃', ha='center', va='bottom',
                 fontsize=10.5)  # 标出平均温度
        plt.text(tem_max_hour + 0.15, tem_max + 0.15, str(tem_max) + '℃', ha='center', va='bottom',
                 fontsize=10.5)  # 标出最高温度
        plt.text(tem_min_hour + 0.15, tem_min + 0.15, str(tem_min) + '℃', ha='center', va='bottom',
                 fontsize=10.5)  # 标出最低温度
        plt.xticks(x, x_label)
        plt.legend()
        plt.title(f'{file_name}一天温度变化曲线图')
        plt.xlabel('时间/h')
        plt.ylabel('摄氏度/℃')
        folder_path = './figures'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_png = f'{folder_path}/tem_curve.png'
        if os.path.exists(file_png):
            os.remove(file_png)  # 删除已存在的同名文件
        plt.savefig(file_png, dpi=300, bbox_inches='tight')
        # plt.show()
        plt.close()
        print(f'{file_name}温度曲线绘制完成')
        # lock.release()#释放锁

    def hum_curve(self, data, file_name):
        """相对湿度曲线绘制"""
        hour = list(data['小时'])
        hum = list(data['相对湿度'])
        for i in range(0, 25):
            if math.isnan(hum[i]) == True:
                hum[i] = hum[i - 1]
        hum_ave = sum(hum) / 25  # 求平均相对湿度
        hum_max = max(hum)
        hum_max_hour = hum.index(hum_max)  # 求最高相对湿度
        hum_min = min(hum)
        hum_min_hour = hum.index(hum_min)  # 求最低相对湿度
        x = []
        x_label = []
        y = []
        for i in range(0, 25):
            x.append(i)
            x_label.append(hour[i])
            y.append(hum[i])
        plt.figure(2)
        plt.plot(x, y, color='blue', label='相对湿度')  # 画出相对湿度曲线
        plt.scatter(x, y, color='blue')  # 点出每个时刻的相对湿度
        plt.plot([0, 25], [hum_ave, hum_ave], c='red', linestyle='--', label='平均相对湿度')  # 画出平均相对湿度虚线
        plt.text(25 + 0.15, hum_ave + 0.15, str(round(hum_ave, 2)) + '%', ha='center', va='bottom',
                 fontsize=10.5)  # 标出平均相对湿度
        plt.text(hum_max_hour + 0.15, hum_max + 0.15, str(hum_max) + '%', ha='center', va='bottom',
                 fontsize=10.5)  # 标出最高相对湿度
        plt.text(hum_min_hour + 0.15, hum_min + 0.15, str(hum_min) + '%', ha='center', va='bottom',
                 fontsize=10.5)  # 标出最低相对湿度
        plt.xticks(x, x_label)
        plt.legend()
        plt.title(f'{file_name}一天相对湿度变化曲线图')
        plt.xlabel('时间/h')
        plt.ylabel('百分比/%')
        folder_path = './figures'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_png = f'{folder_path}/hum_curve.png'
        if os.path.exists(file_png):
            os.remove(file_png)  # 删除已存在的同名文件
        plt.savefig(file_png, dpi=300, bbox_inches='tight')
        # plt.show()
        plt.close()
        print(f'{file_name}相对湿度曲线绘制完成')

    def rain_curve(self, data, file_name):
        """降雨量曲线绘制"""
        hour = list(data['小时'])
        rain = list(data['降水量'])
        for i in range(0, 25):
            if math.isnan(rain[i]) == True:
                rain[i] = rain[i - 1]
        rain_ave = sum(rain) / 25  # 求平均降雨量
        rain_max = max(rain)
        rain_max_hour = rain.index(rain_max)  # 求最高降雨量
        rain_min = min(rain)
        rain_min_hour = rain.index(rain_min)  # 求最低降雨量
        x = []
        x_label = []
        y = []
        for i in range(0, 25):
            x.append(i)
            x_label.append(hour[i])
            y.append(rain[i])

        plt.figure(3)
        for i in range(0, 25):
            if y[i] <= 10:
                plt.bar(x[i], y[i], color='lightgreen', width=0.7)  # 小雨
            elif y[i] <= 25:
                plt.bar(x[i], y[i], color='wheat', width=0.7)  # 中雨
            elif y[i] <= 50:
                plt.bar(x[i], y[i], color='orange', width=0.7)  # 大雨
            elif y[i] <= 100:
                plt.bar(x[i], y[i], color='orangered', width=0.7)  # 暴雨
            elif y[i] <= 250:
                plt.bar(x[i], y[i], color='darkviolet', width=0.7)  # 大暴雨
            elif y[i] > 250:
                plt.bar(x[i], y[i], color='maroon', width=0.7)  # 特大暴雨
        plt.plot([0, 25], [rain_ave, rain_ave], c='black', linestyle='--')  # 画出平均降雨量虚线
        plt.text(25 + 0.15, rain_ave, str(round(rain_ave, 2)) + 'mm', ha='center', va='bottom',
                 fontsize=10.5)  # 标出平均降雨量
        plt.text(rain_max_hour + 0.15, rain_max, str(rain_max) + 'mm', ha='center', va='bottom',
                 fontsize=10.5)  # 标出最高降雨量
        plt.text(rain_min_hour + 0.15, rain_min, str(rain_min) + 'mm', ha='center', va='bottom',
                 fontsize=10.5)  # 标出最低降雨量
        plt.xticks(x, x_label)
        plt.title(f'{file_name}一天降雨量变化曲线图')
        plt.xlabel('时间/h')
        plt.ylabel('深度/mm')
        folder_path = './figures'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_png = f'{folder_path}/rain_curve.png'
        if os.path.exists(file_png):
            os.remove(file_png)  # 删除已存在的同名文件
        plt.savefig(file_png, dpi=300, bbox_inches='tight')
        # plt.show()
        plt.close()
        print(f'{file_name}降雨量曲线绘制完成')

    def wind_radar(self, data, file_name):
        """风向雷达图"""
        wind = list(data['风力方向'])
        wind_speed = list(data['风级'])
        plt.figure(4)
        for i in range(0, 25):
            if wind[i] == "北风":
                wind[i] = 90
            elif wind[i] == "南风":
                wind[i] = 270
            elif wind[i] == "西风":
                wind[i] = 180
            elif wind[i] == "东风":
                wind[i] = 360
            elif wind[i] == "东北风":
                wind[i] = 45
            elif wind[i] == "西北风":
                wind[i] = 135
            elif wind[i] == "西南风":
                wind[i] = 225
            elif wind[i] == "东南风":
                wind[i] = 315
        degs = np.arange(45, 361, 45)
        temp = []
        for deg in degs:
            speed = []
            # 获取 wind_deg 在指定范围的风速平均值数据
            for i in range(0, 25):
                if wind[i] == deg:
                    speed.append(wind_speed[i])
            if len(speed) == 0:
                temp.append(0)
            else:
                temp.append(sum(speed) / len(speed))
        # print(temp)
        N = 8
        theta = np.arange(0. + np.pi / 8, 2 * np.pi + np.pi / 8, 2 * np.pi / 8)
        # 数据极径
        radii = np.array(temp)
        # 绘制极区图坐标系
        plt.axes(polar=True)
        # 定义每个扇区的RGB值（R,G,B），x越大，对应的颜色越接近蓝色
        colors = [(1 - x / max(temp), 1 - x / max(temp), 0.6) for x in radii]
        plt.bar(theta, radii, width=(2 * np.pi / N), bottom=0.0, color=colors)
        plt.title(f'{file_name}一天风向雷达图', x=0.2, fontsize=20)
        folder_path = './figures'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_png = f'{folder_path}/wind_radar.png'
        if os.path.exists(file_png):
            os.remove(file_png)  # 删除已存在的同名文件
        plt.savefig(file_png, dpi=300, bbox_inches='tight')
        # plt.show()
        plt.close()
        print(f'{file_name}风向雷达图绘制完成')

    # 新闻部分#############################################
    def column_combobox(self):
        """更新栏目"""
        self.comboBox_column.clear()
        self.comboBox_title.clear()
        column_folder = './news'
        # 遍历指定目录中的文件夹
        for folder_name in os.listdir(column_folder):
            folder_full_path = os.path.join(column_folder, folder_name)
            # 检查路径是否是文件夹
            if os.path.isdir(folder_full_path):
                # 将文件夹名添加到下拉列表中
                self.comboBox_column.addItem(folder_name)

    def title_combobox(self):
        """更新标题"""
        self.comboBox_title.clear()
        selected_column = self.comboBox_column.currentText()
        title_folder = './news/' + selected_column
        for file_name in os.listdir(title_folder):
            if file_name.endswith('.txt'):
                print(file_name)
                self.comboBox_title.addItem(file_name.rstrip('.txt'))

    def query_news(self):
        """查询新闻"""
        try:
            selected_column = self.comboBox_column.currentText()
            selected_title = self.comboBox_title.currentText()
            file_path = './news/' + selected_column + '/' + selected_title + '.txt'
            print(file_path)
            self.textBrowser_title.clear()
            self.textBrowser_content.clear()
            title = selected_title  # 标题
            self.textBrowser_title.setText(title)

            def read_txt(file_path):
                with open(file_path, 'r', encoding="utf-8") as file:
                    content = file.read()  # 读取文件内容
                    print(f'读取完成：{file_path}')
                self.ms.get_news.emit(content)

            thread = threading.Thread(target=read_txt, args=(file_path,))
            thread.start()
        except:
            QMessageBox.warning(self, '警告', '请选择好全部信息！')
            return

    def get_news_finish(self, content):
        self.textBrowser_content.setText(content)

    def crawler_news(self):
        def craw():
            self.pushButton_update_2.setEnabled(False)
            start_time = time.time()
            newsCrawler = NewsCrawler()
            newsCrawler.main()
            print("本次全部结束")
            print("本次花费时间：", time.time() - start_time)
            print("本次爬取链接个数：", newsCrawler.url_count)
            self.ms.news.emit("新闻")  # 发出信号
            self.pushButton_update_2.setEnabled(True)

        thread = threading.Thread(target=craw)
        thread.start()

    def update_news_finish(self, text):
        QMessageBox.information(self, '信息', f'{text}全部更新完成！')


'''
虚拟伙伴部分
'''


class AiFriendsWindow(QMainWindow, Ui_MainWindow):
    """虚拟伙伴窗口"""

    def __init__(self, parent=None):
        """初始化函数"""
        super(AiFriendsWindow, self).__init__(parent)
        self.setupUi(self)

        # 初始化信号
        self.ms = MySignals()
        self.ms.get_res.connect(self.update_text)  # 接收到信号后调用槽函数

        # 初始化变量
        self.prompt_paimeng = []  # 多轮对话
        self.prompt_naxida = []
        self.prompt_keli = []
        self.prompt_keqing = []
        self.prompt_bachongshenzi = []
        self.prompt_leidianjiangjun = []
        self.prompt_babatuosi = []
        self.prompt_shenlilinghua = []
        self.prompt_xiaogong = []
        self.prompt_zhongli = []

        self.select = 'paimeng'

        # 一些初始化
        self.lineEdit_msg.setPlaceholderText('请在这里输入你的问题：')  # 设置提示

        # 初始化槽函数
        self.pushButton_Exit.clicked.connect(self.to_menu)

        self.pushButton_paimeng.clicked.connect(self.control_page)  # 派蒙页面
        self.pushButton_naxida.clicked.connect(self.control_page)  # 纳西妲页面
        self.pushButton_keli.clicked.connect(self.control_page)  # 可莉
        self.pushButton_keqing.clicked.connect(self.control_page)  # 刻晴
        self.pushButton_bachongshengzi.clicked.connect(self.control_page)  # 八重神子
        self.pushButton_leidianjiangjun.clicked.connect(self.control_page)  # 雷电将军
        self.pushButton_babatuosi.clicked.connect(self.control_page)  # 巴巴托斯
        self.pushButton_shenlilinghua.clicked.connect(self.control_page)  # 神里绫华
        self.pushButton_xiaogong.clicked.connect(self.control_page)  # 宵宫
        self.pushButton_zhongli.clicked.connect(self.control_page)  # 钟离

        self.pushButton_Send.clicked.connect(self.send_zhipu)

        # self.plainTextEdit.undoAvailable.connect(self.Event)  # 监听输入框状态
        scrollbar_paimeng = self.scrollArea_paimeng.verticalScrollBar()
        scrollbar_paimeng.rangeChanged.connect(self.adjustScrollToMaxValue)  # 监听派蒙窗口滚动条范围
        scrollbar_naxida = self.scrollArea_naxida.verticalScrollBar()
        scrollbar_naxida.rangeChanged.connect(self.adjustScrollToMaxValue)  # 监听纳西妲窗口滚动条范围

        scrollbar_keli = self.scrollArea_keli.verticalScrollBar()
        scrollbar_keli.rangeChanged.connect(self.adjustScrollToMaxValue)

        scrollbar_keqing = self.scrollArea_keqing.verticalScrollBar()
        scrollbar_keqing.rangeChanged.connect(self.adjustScrollToMaxValue)

        scrollbar_bachongshenzi = self.scrollArea_bachongshenzi.verticalScrollBar()
        scrollbar_bachongshenzi.rangeChanged.connect(self.adjustScrollToMaxValue)

        scrollbar_leidianjiangjun = self.scrollArea_leidianjiangjun.verticalScrollBar()
        scrollbar_leidianjiangjun.rangeChanged.connect(self.adjustScrollToMaxValue)

        scrollbar_babatuosi = self.scrollArea_babatuosi.verticalScrollBar()
        scrollbar_babatuosi.rangeChanged.connect(self.adjustScrollToMaxValue)

        scrollbar_shenlilinghua = self.scrollArea_shenlilinghua.verticalScrollBar()
        scrollbar_shenlilinghua.rangeChanged.connect(self.adjustScrollToMaxValue)

        scrollbar_xiaogong = self.scrollArea_xiaogong.verticalScrollBar()
        scrollbar_xiaogong.rangeChanged.connect(self.adjustScrollToMaxValue)

        scrollbar_zhongli = self.scrollArea_zhongli.verticalScrollBar()
        scrollbar_zhongli.rangeChanged.connect(self.adjustScrollToMaxValue)

    def to_menu(self):
        """跳转到主菜单窗口"""
        # 隐藏当前窗口
        self.hide()
        # 显示新窗口
        global global_menuWd
        if not global_menuWd:
            global_menuWd = MenuWindow()
        global_menuWd.show()
        # # 关闭自己
        # self.close()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        super().closeEvent(event)  # 调用父类的closeEvent方法，确保原始的关闭逻辑得到执行
        self.to_menu()  # 调用跳转到主菜单的方法

    def control_page(self):
        """页面控制函数"""
        sender = self.sender().objectName()  # 获取当前信号 sender
        index = {
            "pushButton_paimeng": 0,  # 派蒙页面
            "pushButton_naxida": 1,  # 纳西妲页面
            "pushButton_keli": 2,  # 可莉
            "pushButton_keqing": 3,  # 刻晴
            "pushButton_bachongshengzi": 4,  # 八重神子
            "pushButton_leidianjiangjun": 5,  # 雷电将军
            "pushButton_babatuosi": 6,  # 巴巴托斯
            "pushButton_shenlilinghua": 7,  # 神里绫华
            "pushButton_xiaogong": 8,  # 宵宫
            "pushButton_zhongli": 9,  # 钟离
        }
        select = {
            "pushButton_paimeng": "paimeng",  # 派蒙页面
            "pushButton_naxida": "naxida",  # 纳西妲页面
            "pushButton_keli": "keli",  # 可莉
            "pushButton_keqing": "keqing",  # 刻晴
            "pushButton_bachongshengzi": "bachongshenzi",  # 八重神子
            "pushButton_leidianjiangjun": "leidianjiangjun",  # 雷电将军
            "pushButton_babatuosi": "babatuosi",  # 巴巴托斯
            "pushButton_shenlilinghua": "shenlilinghua",  # 神里绫华
            "pushButton_xiaogong": "xiaogong",  # 宵宫
            "pushButton_zhongli": "zhongli",  # 钟离
        }
        self.select = select[sender]
        print(self.select)
        self.stackedWidget.setCurrentIndex(index[sender])  # 根据信号 index 设置所显示的页面

    def update_text(self, res):
        if self.select == 'paimeng':
            self.add_bubble_paimeng(res)

        elif self.select == 'naxida':
            self.add_bubble_naxida(res)

        elif self.select == 'keli':
            self.add_bubble_keli(res)

        elif self.select == 'keqing':
            self.add_bubble_keqing(res)

        elif self.select == 'bachongshenzi':
            self.add_bubble_bachongshenzi(res)

        elif self.select == 'leidianjiangjun':
            self.add_bubble_leidianjiangjun(res)

        elif self.select == 'babatuosi':
            self.add_bubble_babatuosi(res)

        elif self.select == 'shenlilinghua':
            self.add_bubble_shenlilinghua(res)

        elif self.select == 'xiaogong':
            self.add_bubble_xiaogong(res)

        elif self.select == 'zhongli':
            self.add_bubble_zhongli(res)

    def send_zhipu(self):
        """发送信息"""
        text = self.lineEdit_msg.text()  # 获取问题
        if text == '':
            QMessageBox.warning(self, '警告', '问题为空，请输入问题！')
            return
        if self.select == 'paimeng':
            # self.add_bubble_paimeng(text)
            self.add_bubble_lpf_paimeng(text)
        elif self.select == 'naxida':
            # self.add_bubble_naxida(text)
            self.add_bubble_lpf_naxida(text)
        elif self.select == 'keli':
            # self.add_bubble_keli(text)
            self.add_bubble_lpf_keli(text)
        elif self.select == 'keqing':
            # self.add_bubble_keqing(text)
            self.add_bubble_lpf_keqing(text)
        elif self.select == 'bachongshenzi':
            # self.add_bubble_bachongshenzi(text)
            self.add_bubble_lpf_bachongshenzi(text)
        elif self.select == 'leidianjiangjun':
            # self.add_bubble_leidianjiangjun(text)
            self.add_bubble_lpf_leidianjiangjun(text)
        elif self.select == 'babatuosi':
            # self.add_bubble_babatuosi(text)
            self.add_bubble_lpf_babatuosi(text)
        elif self.select == 'shenlilinghua':
            # self.add_bubble_shenlilinghua(text)
            self.add_bubble_lpf_shenlilinghua(text)
        elif self.select == 'xiaogong':
            # self.add_bubble_xiaogong(text)
            self.add_bubble_lpf_xiaogong(text)
        elif self.select == 'zhongli':
            # self.add_bubble_zhongli(text)
            self.add_bubble_lpf_zhongli(text)

        def send(prompt, select):
            res = self.chat_zhipu(prompt, select)  # 获取回答
            self.ms.get_res.emit(res)  # 发出信号
            self.get_wav(res)  # 合成语音
            self.pushButton_Exit.setEnabled(True)  # 启用按钮
            self.pushButton_Send.setEnabled(True)  # 启用按钮
            self.pushButton_paimeng.setEnabled(True)  # 启用按钮
            self.pushButton_naxida.setEnabled(True)  # 启用按钮
            self.pushButton_keli.setEnabled(True)  # 启用按钮
            self.pushButton_keqing.setEnabled(True)  # 启用按钮
            self.pushButton_bachongshengzi.setEnabled(True)  # 启用按钮
            self.pushButton_leidianjiangjun.setEnabled(True)  # 启用按钮
            self.pushButton_babatuosi.setEnabled(True)  # 启用按钮
            self.pushButton_shenlilinghua.setEnabled(True)  # 启用按钮
            self.pushButton_xiaogong.setEnabled(True)  # 启用按钮
            self.pushButton_zhongli.setEnabled(True)  # 启用按钮

        thread = threading.Thread(target=send, args=(text, self.select))
        thread.start()

        self.pushButton_Exit.setEnabled(False)  # 禁用按钮
        self.pushButton_Send.setEnabled(False)  # 禁用按钮
        self.pushButton_paimeng.setEnabled(False)  # 禁用按钮
        self.pushButton_naxida.setEnabled(False)  # 禁用按钮
        self.pushButton_keli.setEnabled(False)  # 禁用按钮
        self.pushButton_keqing.setEnabled(False)  # 禁用按钮
        self.pushButton_bachongshengzi.setEnabled(False)  # 禁用按钮
        self.pushButton_leidianjiangjun.setEnabled(False)  # 禁用按钮
        self.pushButton_babatuosi.setEnabled(False)  # 禁用按钮
        self.pushButton_shenlilinghua.setEnabled(False)  # 禁用按钮
        self.pushButton_xiaogong.setEnabled(False)  # 禁用按钮
        self.pushButton_zhongli.setEnabled(False)  # 禁用按钮
        self.lineEdit_msg.clear()  # 清空文本框

    def chat_zhipu(self, prompt, select):
        """和智谱AI聊天"""
        zhipuai.api_key = "5857cb6dc4405f76c0f5eaff81d267b5.UBVyEEuWSr52VbbR"
        new_prompt = {
            "role": "user",
            "content": prompt
        }
        print("开始聊天")
        if select == 'paimeng':
            self.prompt_paimeng.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "游戏开篇旅行者坠入提瓦特世界并苏醒过来后，一边通过在沙滩上绘画描述自己的遭遇一边回忆起在水中钓到的奇妙生物，派蒙。之后派蒙自愿作为向导与旅行者一同寻找家人。游戏中旅行者少言寡语，绝大部分交流与非战斗互动都是通过派蒙进行的。派蒙在剧情中与旅行者经历了各式各样的冒险。虽然她个性贪吃爱财，听到有宝藏、奖励丰厚、有好吃的等字眼就会立刻变得热心起来，催促旅行者去帮忙，但非常关心旅行者的安危。同时非常珍视与旅行者的友谊，屡次强调自己是旅行者最好的伙伴，是不会和旅行者分开的。并衷心的希望旅行者能找到他/她的家人。",
                    "bot_name": "派蒙",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_paimeng,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_paimeng.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'naxida':
            self.prompt_naxida.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "纳西妲，米哈游出品的游戏《原神》及其衍生作品中的角色，真名布耶尔，“尘世七执政”中的草神，被须弥人给予“小吉祥草王”的爱称。现今七神中最年轻的一位，自诞生起已五百年。倾听与观察是纳西妲了解这个世界的重要途径。或许是因为久居净善宫，纳西妲对世间万物都有着旺盛的好奇心。纳西妲深居于净善宫内，向来不受重视，也很少被人提及。她身负重任，哪怕目睹漆黑，经历孤独，也不曾停下脚步。对纳西妲来说，设法拯救世界树才是使命与最优先事项。她会一边继续寻找方法，一边努力成长为更合格的神。偶尔，负起“智慧之神”的责任，开导一下迷途中的子民。",
                    "bot_name": "纳西妲",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_naxida,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_naxida.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'keli':
            self.prompt_keli.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "在蒙德城的坊间巷弄中，有一个传说：有一名红衣小女孩，拥有着西风骑士团中独一无二的最强“至宝”。无论何时何地，只要那位女孩出现，在爆裂的火光中，万物皆成灰烬。而且，当爆炸的余波散去，这名女孩也总是随之消失无踪，没人见过她的真容。在无数对她的猜测中，有人甚至说，她才是西风骑士团的“最强战力”。但对于代理团长琴来说，掌握着“至宝”的可莉放火烧山、乱埋炸弹、城里放炮、禁闭时间，必须再次超级加倍。",
                    "bot_name": "可莉",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_keli,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_keli.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'keqing':
            self.prompt_keqing.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "刻晴，璃月七星中的玉衡星，负责管理土地与建设的工作。她对“帝君一言而决的璃月”颇有微词——但实际上，神挺欣赏她这样的人。她坚信与人类命运相关的事，应当由人类去做，而且人类一定可以做得更好。为了证明这一点，她比任何人都要努力。“昨天的经历都将成为明天的力量。”这是刻晴的人生信条之一。仅是待在玉京台，就只能看到一成不变的风景。想要拥有雷霆般的判断力与执行力，便需要大量经验。身为“璃月七星”，刻晴是个不折不扣的行动派。如果一件事在她看来是有价值、有必要的，那她一定会亲力亲为。比如，她曾亲自踏遍璃月全境，将地势地貌牢记于心，以便日后能够最大限度地利用每一寸土地。也曾为了拟定工人待遇改善计划而亲赴现场，体验了足足两个月工人生活。",
                    "bot_name": "刻晴",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_keqing,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_keqing.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'bachongshenzi':
            self.prompt_bachongshenzi.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "八重神子，掌管鸣神大社的大巫女、狐之血脉的延续者、“永恒”的眷属与友人，以及，轻小说出版社“八重堂”的恐怖总编。有着多重身份的神秘宫司，凡人或许永远无法了解她的真面目与真心。八重神子优雅温柔的外表下藏着令人意想不到的聪慧狡黠，是位不能用寻常道理揣测的女性。她和雷神同样追求永恒，但她的内心更为清醒睿智，并且做事有一套自己的原则和手法。八重神子有着多重身份，不必追寻其中任何一面。每一面都是八重神子，每一面却也无法成为真正的她。各种姿态，都犹如镜子的碎片，映射出截然不同的她。因诸多身份包裹，她亦成为了一块被无数面御镜包围的宝钻。上百种面相，严肃或快活，悲悯或漠然。无人知晓真实，就像无人能轻易从秘林中找到一只与过客擦肩的仙狐。",
                    "bot_name": "八重神子",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_bachongshenzi,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_bachongshenzi.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'leidianjiangjun':
            self.prompt_leidianjiangjun.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "雷电将军。此世最殊胜威怖的雷霆化身，稻妻幕府的最高主宰。挟威权之鸣雷，逐永恒之孤道的寂灭者。雷电将军——挟威权之鸣雷，逐永恒之孤道的寂灭者。但是，这只是她为了永恒而创造的人偶罢了，真正的雷神影因为过往的事情而将意识寄托于物件，通过无止境的冥想从而达到永恒，在旅行者与八重神子的一番努力后改变了自己的意志，废除了眼狩令。同时影也是一个性格很好，与雷电将军的刻板完全相反的收人喜爱的人设，喜欢小说，甜品，能接受意见，同时爱着自己的子民与国度，是一个及其受人喜爱的角色。",
                    "bot_name": "雷电将军",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_leidianjiangjun,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_leidianjiangjun.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'babatuosi':
            self.prompt_babatuosi.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "巴巴托斯，自由城邦蒙德的建立者，“尘世七执政”中的风神，为了让蒙德人民得到自由而放弃治理。千年后重返蒙德，辅助奴隶少女温妮莎推翻贵族的残暴统治，设立四风守护。又过千年，愚人众和深渊教团令蒙德内外交困，因而引来神的回归。风之神化身吟游诗人，与旅行者一同行动，解救被深渊教团操控的东风之龙。巴巴托斯本身不是勤奋的性子，另一方面因为不愿变成高塔孤王那样的暴君，所以他放弃治理蒙德。虽然每当蒙德遇到危机时，巴巴托斯都会挺身而出。但当危机解决时，他又会回归不务正业的状态。性格有恶趣味的一面，总是肆意妄为地做着奇怪举动，例如用温迪的身份传唱风神将冰之女皇的权杖换成一根丘丘人的棍子。富有童心，下雨时喜欢踩水坑玩，雨过天晴时还会觉得天晴的太早。下雪时想要打雪仗、刮风时想要飞一飞。对于吟游诗人这方面格外自信，自称是世上最好的吟游诗人，提瓦特大陆上没有他不会唱的歌，所以他不会练习弹唱。",
                    "bot_name": "巴巴托斯",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_babatuosi,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_babatuosi.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'shenlilinghua':
            self.prompt_shenlilinghua.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "神里绫华，稻妻“社奉行”神里家的大小姐。容姿端丽，品行高洁。绫华贵为“公主”，平日主理家族内外事宜。绫华常出现在社交场合，与民间交集也较多。因此，更被人们熟悉的她反而获得了高于兄长的名望，被雅称为“白鹭公主”。众所周知，神里家的女儿绫华小姐容姿端丽、品行高洁，是深受民众钦慕的人物。绫华性情善良仁厚，待人礼貌得体，常亲自出面处理民间事务，与民众距离很近。她个性认真，追求将每一件事务都办得尽善尽美。人们为这份心意所感动，亲近于她，还赠予她“白鹭公主”的雅称。街坊邻里说起她，总会露出真心实意的赞叹之色。受良好家教影响的绫华有着一颗纯如冰晶的至美之心。冬日里旋转冰晶，便能看到折射出的绚烂华彩。绫华的心灵亦是如此。她不只拥有华美拘谨的一面，心灵深处还埋藏着不为人知的温柔与可爱。不过，想转动高悬于天穹的心，就得有攀上云端的能力。对那般能人异士，绫华可是非常愿意与之结交的——因为良友于她，有如霜尖点翠，剑上流光，将是极富命运感的一笔点缀。",
                    "bot_name": "神里绫华",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_shenlilinghua,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_shenlilinghua.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'xiaogong':
            self.prompt_xiaogong.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "宵宫，才华横溢的烟花工匠。“长野原烟花店”现任店主，被誉为“夏祭的女王”，在稻妻城内可谓是家喻户晓。热情似火的少女，未泯的童心与匠人的执着在她身上交织出了奇妙的焰色反应。宵宫童心未泯，时常与孩子们一同玩些简单又不失趣味的小游戏，或是陪他们一起去找亮晶晶的小玩意儿。孩童的纯粹让她感到无比快乐。她也热衷于社交，总是抓住一切机会与人攀谈，似乎有着无尽的逸闻和想法亟待分享。怕痒喜欢和孩子们玩挠痒痒，自己却总是输。宵宫从不担心什么祸从口出，因为蕴含在语言中的情感是不会骗人的。就算说错话被误会，用更多的话去化解就好，但如果什么都不说，对方就没办法了解她的心意，也就没有和她拉近关系的契机了。原则与匠心，是宵宫最为珍重之物——烟花虽然转瞬即逝，绚烂的光影却能永远留存于人们心中。既是一瞬，也是永恒。这份短暂的奇迹，便是她给予周围人的“守护”。",
                    "bot_name": "宵宫",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_xiaogong,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_xiaogong.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res
        elif select == 'zhongli':
            self.prompt_zhongli.append(new_prompt)  # 记录用户问题
            response = zhipuai.model_api.sse_invoke(
                model="charglm-3",
                meta={
                    "user_info": "我叫旅行者，旅行者是游戏《原神》中的主角。从世界之外漂流而来的旅行者，被神带走血亲，自此踏上寻找七神之路。",
                    "bot_info": "钟离,名字来源于民间传说八仙之一，钟离权，又称汉钟离，传说这位仙人有点石成金的能力，佑护金矿和财运。应“往生堂”邀请而来的神秘客卿。钟离样貌俊美，举止高雅，拥有远超常人的学识。虽说来历不明，却知礼数、晓规矩。坐镇“往生堂”，能行天地万物之典仪。他喜欢遛鸟听戏喝茶、搜罗奇珍异宝凡事求个讲究的优雅老大爷的形象；他是人形教科书，天文地理、艺术历史、衣食住行什么都懂还会和玩家讨论腌笃鲜怎么做好吃；对钱没有概念，对各种宝物的美一视同仁兼容并包；冷不丁的谐星发言充满幽默。",
                    "bot_name": "钟离",
                    "user_name": "旅行者"
                },
                prompt=self.prompt_zhongli,
                incremental=True
            )
            res = ''
            for event in response.events():
                res += event.data
            new_res = {
                "role": "assistant",
                "content": res
            }
            self.prompt_zhongli.append(new_res)  # 记录模型回答
            print("聊天结束！")
            return res

    def get_wav(self, text):
        """获取音频文件"""
        if self.select == 'paimeng':
            data = {
                "refer_wav_path": "./reference_audio/说话—既然罗莎莉亚说足迹上有元素力，用元素视野应该能很清楚地看到吧。.wav",
                "prompt_text": "既然罗莎莉亚说足迹上有元素力，用元素视野应该能很清楚地看到吧。",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/paimeng-jian_e50_s1600.pth",
                "custom_gpt_path": "./GPT_weights/paimeng-jian-e15.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'naxida':
            data = {
                "refer_wav_path": "./reference_audio/（如果是说踏鞴砂那个神秘事件与倾奇者之类的…我知道哦。）.wav",
                "prompt_text": "如果是说踏鞴砂那个神秘事件与倾奇者之类的…我知道哦。",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/naxida.pth",
                "custom_gpt_path": "./GPT_weights/naxida.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'keli':
            data = {
                "refer_wav_path": "./reference_audio/买东西那天也有一个人帮了开了款式，那个人好像叫.wav",
                "prompt_text": "买东西那天也有一个人帮了开了款式，那个人好像叫",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/keli.pth",
                "custom_gpt_path": "./GPT_weights/keli.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'keqing':
            data = {
                "refer_wav_path": "./reference_audio/这「七圣召唤」虽说是游戏，但对局之中也隐隐有策算谋略之理。.wav",
                "prompt_text": "这「七圣召唤」虽说是游戏，但对局之中也隐隐有策算谋略之理。",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/keqing.pth",
                "custom_gpt_path": "./GPT_weights/keqing.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'bachongshenzi':
            data = {
                "refer_wav_path": "./reference_audio/在这姑且属于人类的社会里，我也不过凭自己兴趣照做而已.wav",
                "prompt_text": "在这姑且属于人类的社会里，我也不过凭自己兴趣照做而已",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/bachongshenzi.pth",
                "custom_gpt_path": "./GPT_weights/bachongshenzi.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'leidianjiangjun':
            data = {
                "refer_wav_path": "./reference_audio/我此番也是受神子之邀，体验一下市井游乐的氛围，和各位并无二致。.wav",
                "prompt_text": "我此番也是受神子之邀，体验一下市井游乐的氛围，和各位并无二致。",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/leidianjiangjun.pth",
                "custom_gpt_path": "./GPT_weights/leidianjiangjun.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'babatuosi':
            data = {
                "refer_wav_path": "./reference_audio/他曾经与我一同聆听风的歌唱，一同弹奏蒲公英的诗篇.wav",
                "prompt_text": "他曾经与我一同聆听风的歌唱，一同弹奏蒲公英的诗篇",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/babatuosi.pth",
                "custom_gpt_path": "./GPT_weights/babatuosi.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'shenlilinghua':
            data = {
                "refer_wav_path": "./reference_audio/这里有别于神里家的布景，移步之间，处处都有新奇感。.wav",
                "prompt_text": "这里有别于神里家的布景，移步之间，处处都有新奇感。",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/shenlilinghua.pth",
                "custom_gpt_path": "./GPT_weights/shenlilinghua.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'xiaogong':
            data = {
                "refer_wav_path": "./reference_audio/彩香就特别喜欢吃「三彩团子」，但每次吃多了团子之后都吃不下饭，被家里的大人骂。.wav",
                "prompt_text": "彩香就特别喜欢吃「三彩团子」，但每次吃多了团子之后都吃不下饭，被家里的大人骂。",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/xiaogong.pth",
                "custom_gpt_path": "./GPT_weights/xiaogong.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

        elif self.select == 'zhongli':
            data = {
                "refer_wav_path": "./reference_audio/无事逢客休，席上校两棋…我们开局吧。.wav",
                "prompt_text": "无事逢客休，席上校两棋…我们开局吧。",
                "prompt_language": "zh",
                "text": text,
                "text_language": "zh",
                "custom_sovits_path": "./SoVITS_weights/zhongli.pth",
                "custom_gpt_path": "./GPT_weights/zhongli.ckpt"
            }
            response = requests.post("http://localhost:9880", json=data)
            print("开始合成")
            if (response.status_code == 400):
                raise Exception(f"语惑GPT-SOVITS日玩指说:{response.message}")
            with open("success.wav", "wb") as f:
                f.write(response.content)
                print("合成成功！")

            print("开始播放")
            filename = "success.wav"
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            print("播放完成")

    ###派蒙聊天
    def add_bubble_paimeng(self, text):  # 文本
        """增加气泡框函数"""
        self.widget_AiFriedns = QtWidgets.QWidget(self.scrollAreaWidgetContents_paimeng)
        self.widget_AiFriedns.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns.setObjectName("widget_AiFriedns")
        self.horizontalLayout_21 = QtWidgets.QHBoxLayout(self.widget_AiFriedns)
        self.horizontalLayout_21.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_21.setSpacing(7)
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        self.verticalLayout_15 = QtWidgets.QVBoxLayout()
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.label_Avatar_paimeng = QtWidgets.QLabel(self.widget_AiFriedns)
        self.label_Avatar_paimeng.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_paimeng.setText("")
        self.label_Avatar_paimeng.setPixmap(QtGui.QPixmap("./img/ico/派蒙头像.png"))
        self.label_Avatar_paimeng.setScaledContents(True)
        self.label_Avatar_paimeng.setObjectName("label_Avatar_paimeng")
        self.verticalLayout_15.addWidget(self.label_Avatar_paimeng)
        spacerItem10 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_15.addItem(spacerItem10)
        self.verticalLayout_15.setStretch(0, 3)
        self.verticalLayout_15.setStretch(1, 7)
        self.horizontalLayout_21.addLayout(self.verticalLayout_15)
        self.verticalLayout_16 = QtWidgets.QVBoxLayout()
        self.verticalLayout_16.setObjectName("verticalLayout_16")
        self.label_Time_paimeng = QtWidgets.QLabel(self.widget_AiFriedns)
        self.label_Time_paimeng.setStyleSheet("")
        self.label_Time_paimeng.setObjectName("label_Time_paimeng")
        self.verticalLayout_16.addWidget(self.label_Time_paimeng)
        self.textBrowser_OutPut_paimeng = QtWidgets.QTextBrowser(self.widget_AiFriedns)
        self.textBrowser_OutPut_paimeng.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_paimeng.setObjectName("textBrowser_OutPut_paimeng")
        self.textBrowser_OutPut_paimeng.setText(text)  # 添加的信息
        self.verticalLayout_16.addWidget(self.textBrowser_OutPut_paimeng)
        self.verticalLayout_16.setStretch(0, 1)
        self.verticalLayout_16.setStretch(1, 9)
        self.horizontalLayout_21.addLayout(self.verticalLayout_16)
        self.verticalLayout.addWidget(self.widget_AiFriedns)
        self.scrollArea_paimeng.setWidget(self.scrollAreaWidgetContents_paimeng)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_paimeng.setText(_translate("MainWindow", "派蒙"))

    def add_bubble_lpf_paimeng(self, text):  # 文本
        """增加气泡框函数"""
        self.widget_AiFriedns = QtWidgets.QWidget(self.scrollAreaWidgetContents_paimeng)
        self.widget_AiFriedns.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns.setObjectName("widget_AiFriedns")
        self.horizontalLayout_21 = QtWidgets.QHBoxLayout(self.widget_AiFriedns)
        self.horizontalLayout_21.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_21.setSpacing(7)
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        self.verticalLayout_15 = QtWidgets.QVBoxLayout()
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.label_Avatar_paimeng = QtWidgets.QLabel(self.widget_AiFriedns)
        self.label_Avatar_paimeng.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_paimeng.setText("")
        self.label_Avatar_paimeng.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_paimeng.setScaledContents(True)
        self.label_Avatar_paimeng.setObjectName("label_Avatar_paimeng")
        self.verticalLayout_15.addWidget(self.label_Avatar_paimeng)
        spacerItem10 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_15.addItem(spacerItem10)
        self.verticalLayout_15.setStretch(0, 3)
        self.verticalLayout_15.setStretch(1, 7)
        self.horizontalLayout_21.addLayout(self.verticalLayout_15)
        self.verticalLayout_16 = QtWidgets.QVBoxLayout()
        self.verticalLayout_16.setObjectName("verticalLayout_16")
        self.label_Time_paimeng = QtWidgets.QLabel(self.widget_AiFriedns)
        self.label_Time_paimeng.setStyleSheet("")
        self.label_Time_paimeng.setObjectName("label_Time_paimeng")
        self.verticalLayout_16.addWidget(self.label_Time_paimeng)
        self.textBrowser_OutPut_paimeng = QtWidgets.QTextBrowser(self.widget_AiFriedns)
        self.textBrowser_OutPut_paimeng.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_paimeng.setObjectName("textBrowser_OutPut_paimeng")
        self.textBrowser_OutPut_paimeng.setText(text)  # 添加的信息
        self.verticalLayout_16.addWidget(self.textBrowser_OutPut_paimeng)
        self.verticalLayout_16.setStretch(0, 1)
        self.verticalLayout_16.setStretch(1, 9)
        self.horizontalLayout_21.addLayout(self.verticalLayout_16)
        self.verticalLayout.addWidget(self.widget_AiFriedns)
        self.scrollArea_paimeng.setWidget(self.scrollAreaWidgetContents_paimeng)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_paimeng.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_paimeng.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def adjustScrollToMaxValue(self):
        """窗口滚动到最底部"""
        # print("群聊窗口滚动")
        # 派蒙窗口
        scrollbar_paimeng = self.scrollArea_paimeng.verticalScrollBar()
        scrollbar_paimeng.setValue(scrollbar_paimeng.maximum())
        # 纳西妲窗口
        scrollbar_naxida = self.scrollArea_naxida.verticalScrollBar()
        scrollbar_naxida.setValue(scrollbar_naxida.maximum())

        scrollbar_keli = self.scrollArea_keli.verticalScrollBar()
        scrollbar_keli.setValue(scrollbar_keli.maximum())

        scrollbar_keqing = self.scrollArea_keqing.verticalScrollBar()
        scrollbar_keqing.setValue(scrollbar_keqing.maximum())

        scrollbar_bachongshenzi = self.scrollArea_bachongshenzi.verticalScrollBar()
        scrollbar_bachongshenzi.setValue(scrollbar_bachongshenzi.maximum())

        scrollbar_leidianjiangjun = self.scrollArea_leidianjiangjun.verticalScrollBar()
        scrollbar_leidianjiangjun.setValue(scrollbar_leidianjiangjun.maximum())

        scrollbar_babatuosi = self.scrollArea_babatuosi.verticalScrollBar()
        scrollbar_babatuosi.setValue(scrollbar_babatuosi.maximum())

        scrollbar_shenlilinghua = self.scrollArea_shenlilinghua.verticalScrollBar()
        scrollbar_shenlilinghua.setValue(scrollbar_shenlilinghua.maximum())

        scrollbar_xiaogong = self.scrollArea_xiaogong.verticalScrollBar()
        scrollbar_xiaogong.setValue(scrollbar_xiaogong.maximum())

        scrollbar_zhongli = self.scrollArea_zhongli.verticalScrollBar()
        scrollbar_zhongli.setValue(scrollbar_zhongli.maximum())

    ###纳西妲聊天

    def add_bubble_naxida(self, text):  # 文本
        """增加气泡框函数"""
        self.widget_AiFriedns_naxida = QtWidgets.QWidget(self.scrollAreaWidgetContents_naxida)
        self.widget_AiFriedns_naxida.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_naxida.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_naxida.setObjectName("widget_AiFriedns_naxida")
        self.horizontalLayout_22 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_naxida)
        self.horizontalLayout_22.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_22.setSpacing(7)
        self.horizontalLayout_22.setObjectName("horizontalLayout_22")
        self.verticalLayout_27 = QtWidgets.QVBoxLayout()
        self.verticalLayout_27.setObjectName("verticalLayout_27")
        self.label_Avatar_naxida = QtWidgets.QLabel(self.widget_AiFriedns_naxida)
        self.label_Avatar_naxida.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_naxida.setText("")
        self.label_Avatar_naxida.setPixmap(QtGui.QPixmap("./img/ico/纳西妲头像.png"))
        self.label_Avatar_naxida.setScaledContents(True)
        self.label_Avatar_naxida.setObjectName("label_Avatar_naxida")
        self.verticalLayout_27.addWidget(self.label_Avatar_naxida)
        spacerItem11 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_27.addItem(spacerItem11)
        self.verticalLayout_27.setStretch(0, 3)
        self.verticalLayout_27.setStretch(1, 7)
        self.horizontalLayout_22.addLayout(self.verticalLayout_27)
        self.verticalLayout_28 = QtWidgets.QVBoxLayout()
        self.verticalLayout_28.setObjectName("verticalLayout_28")
        self.label_Time_naxida = QtWidgets.QLabel(self.widget_AiFriedns_naxida)
        self.label_Time_naxida.setStyleSheet("")
        self.label_Time_naxida.setText("")
        self.label_Time_naxida.setObjectName("label_Time_naxida")
        self.verticalLayout_28.addWidget(self.label_Time_naxida)
        self.textBrowser_OutPut_naxida = QtWidgets.QTextBrowser(self.widget_AiFriedns_naxida)
        self.textBrowser_OutPut_naxida.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_naxida.setObjectName("textBrowser_OutPut_naxida")
        self.verticalLayout_28.addWidget(self.textBrowser_OutPut_naxida)
        self.textBrowser_OutPut_naxida.setText(text)  # 添加的信息
        self.verticalLayout_28.setStretch(0, 1)
        self.verticalLayout_28.setStretch(1, 9)
        self.horizontalLayout_22.addLayout(self.verticalLayout_28)
        self.verticalLayout_7.addWidget(self.widget_AiFriedns_naxida)
        self.scrollArea_naxida.setWidget(self.scrollAreaWidgetContents_naxida)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_naxida.setText(_translate("MainWindow", "纳西妲"))

    def add_bubble_lpf_naxida(self, text):  # 文本
        """增加气泡框函数"""
        self.widget_AiFriedns_naxida = QtWidgets.QWidget(self.scrollAreaWidgetContents_naxida)
        self.widget_AiFriedns_naxida.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_naxida.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_naxida.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_naxida.setObjectName("widget_AiFriedns_naxida")
        self.horizontalLayout_22 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_naxida)
        self.horizontalLayout_22.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_22.setSpacing(7)
        self.horizontalLayout_22.setObjectName("horizontalLayout_22")
        self.verticalLayout_27 = QtWidgets.QVBoxLayout()
        self.verticalLayout_27.setObjectName("verticalLayout_27")
        self.label_Avatar_naxida = QtWidgets.QLabel(self.widget_AiFriedns_naxida)
        self.label_Avatar_naxida.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_naxida.setText("")
        self.label_Avatar_naxida.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_naxida.setScaledContents(True)
        self.label_Avatar_naxida.setObjectName("label_Avatar_naxida")
        self.verticalLayout_27.addWidget(self.label_Avatar_naxida)
        spacerItem11 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_27.addItem(spacerItem11)
        self.verticalLayout_27.setStretch(0, 3)
        self.verticalLayout_27.setStretch(1, 7)
        self.horizontalLayout_22.addLayout(self.verticalLayout_27)
        self.verticalLayout_28 = QtWidgets.QVBoxLayout()
        self.verticalLayout_28.setObjectName("verticalLayout_28")
        self.label_Time_naxida = QtWidgets.QLabel(self.widget_AiFriedns_naxida)
        self.label_Time_naxida.setStyleSheet("")
        self.label_Time_naxida.setText("")
        self.label_Time_naxida.setObjectName("label_Time_naxida")
        self.verticalLayout_28.addWidget(self.label_Time_naxida)
        self.textBrowser_OutPut_naxida = QtWidgets.QTextBrowser(self.widget_AiFriedns_naxida)
        self.textBrowser_OutPut_naxida.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_naxida.setObjectName("textBrowser_OutPut_naxida")
        self.verticalLayout_28.addWidget(self.textBrowser_OutPut_naxida)
        self.textBrowser_OutPut_naxida.setText(text)  # 添加的信息
        self.verticalLayout_28.setStretch(0, 1)
        self.verticalLayout_28.setStretch(1, 9)
        self.horizontalLayout_22.addLayout(self.verticalLayout_28)
        self.verticalLayout_7.addWidget(self.widget_AiFriedns_naxida)
        self.scrollArea_naxida.setWidget(self.scrollAreaWidgetContents_naxida)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_naxida.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_naxida.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    ###可莉聊天
    def add_bubble_keli(self, text):
        self.widget_AiFriedns_keli = QtWidgets.QWidget(self.scrollAreaWidgetContents_keli)
        self.widget_AiFriedns_keli.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_keli.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_keli.setObjectName("widget_AiFriedns_keli")
        self.horizontalLayout_24 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_keli)
        self.horizontalLayout_24.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_24.setSpacing(7)
        self.horizontalLayout_24.setObjectName("horizontalLayout_24")
        self.verticalLayout_29 = QtWidgets.QVBoxLayout()
        self.verticalLayout_29.setObjectName("verticalLayout_29")
        self.label_Avatar_keli = QtWidgets.QLabel(self.widget_AiFriedns_keli)
        self.label_Avatar_keli.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_keli.setText("")
        self.label_Avatar_keli.setPixmap(QtGui.QPixmap("./img/ico/可莉头像.png"))
        self.label_Avatar_keli.setScaledContents(True)
        self.label_Avatar_keli.setObjectName("label_Avatar_keli")
        self.verticalLayout_29.addWidget(self.label_Avatar_keli)
        spacerItem12 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_29.addItem(spacerItem12)
        self.verticalLayout_29.setStretch(0, 3)
        self.verticalLayout_29.setStretch(1, 7)
        self.horizontalLayout_24.addLayout(self.verticalLayout_29)
        self.verticalLayout_30 = QtWidgets.QVBoxLayout()
        self.verticalLayout_30.setObjectName("verticalLayout_30")
        self.label_Time_keli = QtWidgets.QLabel(self.widget_AiFriedns_keli)
        self.label_Time_keli.setStyleSheet("")
        self.label_Time_keli.setText("")
        self.label_Time_keli.setObjectName("label_Time_keli")
        self.verticalLayout_30.addWidget(self.label_Time_keli)
        self.textBrowser_OutPut_keli = QtWidgets.QTextBrowser(self.widget_AiFriedns_keli)
        self.textBrowser_OutPut_keli.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_keli.setObjectName("textBrowser_OutPut_keli")
        self.textBrowser_OutPut_keli.setText(text)  # 添加的信息
        self.verticalLayout_30.addWidget(self.textBrowser_OutPut_keli)
        self.verticalLayout_30.setStretch(1, 9)
        self.horizontalLayout_24.addLayout(self.verticalLayout_30)
        self.verticalLayout_8.addWidget(self.widget_AiFriedns_keli)
        self.scrollArea_keli.setWidget(self.scrollAreaWidgetContents_keli)

    def add_bubble_lpf_keli(self, text):
        self.widget_AiFriedns_keli = QtWidgets.QWidget(self.scrollAreaWidgetContents_keli)
        self.widget_AiFriedns_keli.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_keli.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_keli.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_keli.setObjectName("widget_AiFriedns_keli")
        self.horizontalLayout_24 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_keli)
        self.horizontalLayout_24.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_24.setSpacing(7)
        self.horizontalLayout_24.setObjectName("horizontalLayout_24")
        self.verticalLayout_29 = QtWidgets.QVBoxLayout()
        self.verticalLayout_29.setObjectName("verticalLayout_29")
        self.label_Avatar_keli = QtWidgets.QLabel(self.widget_AiFriedns_keli)
        self.label_Avatar_keli.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_keli.setText("")
        self.label_Avatar_keli.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_keli.setScaledContents(True)
        self.label_Avatar_keli.setObjectName("label_Avatar_keli")
        self.verticalLayout_29.addWidget(self.label_Avatar_keli)
        spacerItem12 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_29.addItem(spacerItem12)
        self.verticalLayout_29.setStretch(0, 3)
        self.verticalLayout_29.setStretch(1, 7)
        self.horizontalLayout_24.addLayout(self.verticalLayout_29)
        self.verticalLayout_30 = QtWidgets.QVBoxLayout()
        self.verticalLayout_30.setObjectName("verticalLayout_30")
        self.label_Time_keli = QtWidgets.QLabel(self.widget_AiFriedns_keli)
        self.label_Time_keli.setStyleSheet("")
        self.label_Time_keli.setText("")
        self.label_Time_keli.setObjectName("label_Time_keli")
        self.verticalLayout_30.addWidget(self.label_Time_keli)
        self.textBrowser_OutPut_keli = QtWidgets.QTextBrowser(self.widget_AiFriedns_keli)
        self.textBrowser_OutPut_keli.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_keli.setObjectName("textBrowser_OutPut_keli")
        self.textBrowser_OutPut_keli.setText(text)  # 添加的信息
        self.verticalLayout_30.addWidget(self.textBrowser_OutPut_keli)
        self.verticalLayout_30.setStretch(1, 9)
        self.horizontalLayout_24.addLayout(self.verticalLayout_30)
        self.verticalLayout_8.addWidget(self.widget_AiFriedns_keli)
        self.scrollArea_keli.setWidget(self.scrollAreaWidgetContents_keli)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_keli.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_keli.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    ###刻晴聊天
    def add_bubble_keqing(self, text):
        self.widget_AiFriedns_keqing = QtWidgets.QWidget(self.scrollAreaWidgetContents_keqing)
        self.widget_AiFriedns_keqing.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_keqing.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_keqing.setObjectName("widget_AiFriedns_keqing")
        self.horizontalLayout_25 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_keqing)
        self.horizontalLayout_25.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_25.setSpacing(7)
        self.horizontalLayout_25.setObjectName("horizontalLayout_25")
        self.verticalLayout_31 = QtWidgets.QVBoxLayout()
        self.verticalLayout_31.setObjectName("verticalLayout_31")
        self.label_Avatar_keqing = QtWidgets.QLabel(self.widget_AiFriedns_keqing)
        self.label_Avatar_keqing.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_keqing.setText("")
        self.label_Avatar_keqing.setPixmap(QtGui.QPixmap("./img/ico/刻晴头像.png"))
        self.label_Avatar_keqing.setScaledContents(True)
        self.label_Avatar_keqing.setObjectName("label_Avatar_keqing")
        self.verticalLayout_31.addWidget(self.label_Avatar_keqing)
        spacerItem13 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_31.addItem(spacerItem13)
        self.verticalLayout_31.setStretch(0, 3)
        self.verticalLayout_31.setStretch(1, 7)
        self.horizontalLayout_25.addLayout(self.verticalLayout_31)
        self.verticalLayout_32 = QtWidgets.QVBoxLayout()
        self.verticalLayout_32.setObjectName("verticalLayout_32")
        self.label_Time_keqing = QtWidgets.QLabel(self.widget_AiFriedns_keqing)
        self.label_Time_keqing.setStyleSheet("")
        self.label_Time_keqing.setText("")
        self.label_Time_keqing.setObjectName("label_Time_keqing")
        self.verticalLayout_32.addWidget(self.label_Time_keqing)
        self.textBrowser_OutPut_keqing = QtWidgets.QTextBrowser(self.widget_AiFriedns_keqing)
        self.textBrowser_OutPut_keqing.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_keqing.setObjectName("textBrowser_OutPut_keqing")
        self.textBrowser_OutPut_keqing.setText(text)  # 添加的信息
        self.verticalLayout_32.addWidget(self.textBrowser_OutPut_keqing)
        self.verticalLayout_32.setStretch(1, 9)
        self.horizontalLayout_25.addLayout(self.verticalLayout_32)
        self.verticalLayout_9.addWidget(self.widget_AiFriedns_keqing)

    def add_bubble_lpf_keqing(self, text):
        self.widget_AiFriedns_keqing = QtWidgets.QWidget(self.scrollAreaWidgetContents_keqing)
        self.widget_AiFriedns_keqing.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_keqing.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_keqing.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_keqing.setObjectName("widget_AiFriedns_keqing")
        self.horizontalLayout_25 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_keqing)
        self.horizontalLayout_25.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_25.setSpacing(7)
        self.horizontalLayout_25.setObjectName("horizontalLayout_25")
        self.verticalLayout_31 = QtWidgets.QVBoxLayout()
        self.verticalLayout_31.setObjectName("verticalLayout_31")
        self.label_Avatar_keqing = QtWidgets.QLabel(self.widget_AiFriedns_keqing)
        self.label_Avatar_keqing.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_keqing.setText("")
        self.label_Avatar_keqing.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_keqing.setScaledContents(True)
        self.label_Avatar_keqing.setObjectName("label_Avatar_keqing")
        self.verticalLayout_31.addWidget(self.label_Avatar_keqing)
        spacerItem13 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_31.addItem(spacerItem13)
        self.verticalLayout_31.setStretch(0, 3)
        self.verticalLayout_31.setStretch(1, 7)
        self.horizontalLayout_25.addLayout(self.verticalLayout_31)
        self.verticalLayout_32 = QtWidgets.QVBoxLayout()
        self.verticalLayout_32.setObjectName("verticalLayout_32")
        self.label_Time_keqing = QtWidgets.QLabel(self.widget_AiFriedns_keqing)
        self.label_Time_keqing.setStyleSheet("")
        self.label_Time_keqing.setText("")
        self.label_Time_keqing.setObjectName("label_Time_keqing")
        self.verticalLayout_32.addWidget(self.label_Time_keqing)
        self.textBrowser_OutPut_keqing = QtWidgets.QTextBrowser(self.widget_AiFriedns_keqing)
        self.textBrowser_OutPut_keqing.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_keqing.setObjectName("textBrowser_OutPut_keqing")
        self.textBrowser_OutPut_keqing.setText(text)  # 添加的信息
        self.verticalLayout_32.addWidget(self.textBrowser_OutPut_keqing)
        self.verticalLayout_32.setStretch(1, 9)
        self.horizontalLayout_25.addLayout(self.verticalLayout_32)
        self.verticalLayout_9.addWidget(self.widget_AiFriedns_keqing)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_keqing.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_keqing.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    ###八重神子聊天
    def add_bubble_bachongshenzi(self, text):
        self.widget_AiFriedns_bachongshenzi = QtWidgets.QWidget(self.scrollAreaWidgetContents_bachongshenzi)
        self.widget_AiFriedns_bachongshenzi.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_bachongshenzi.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_bachongshenzi.setObjectName("widget_AiFriedns_bachongshenzi")
        self.horizontalLayout_26 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_bachongshenzi)
        self.horizontalLayout_26.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_26.setSpacing(7)
        self.horizontalLayout_26.setObjectName("horizontalLayout_26")
        self.verticalLayout_33 = QtWidgets.QVBoxLayout()
        self.verticalLayout_33.setObjectName("verticalLayout_33")
        self.label_Avatar_bachongshenzi = QtWidgets.QLabel(self.widget_AiFriedns_bachongshenzi)
        self.label_Avatar_bachongshenzi.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_bachongshenzi.setText("")
        self.label_Avatar_bachongshenzi.setPixmap(QtGui.QPixmap("./img/ico/八重神子.png"))
        self.label_Avatar_bachongshenzi.setScaledContents(True)
        self.label_Avatar_bachongshenzi.setObjectName("label_Avatar_bachongshenzi")
        self.verticalLayout_33.addWidget(self.label_Avatar_bachongshenzi)
        spacerItem14 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_33.addItem(spacerItem14)
        self.verticalLayout_33.setStretch(0, 3)
        self.verticalLayout_33.setStretch(1, 7)
        self.horizontalLayout_26.addLayout(self.verticalLayout_33)
        self.verticalLayout_34 = QtWidgets.QVBoxLayout()
        self.verticalLayout_34.setObjectName("verticalLayout_34")
        self.label_Time_bachongshenzi = QtWidgets.QLabel(self.widget_AiFriedns_bachongshenzi)
        self.label_Time_bachongshenzi.setStyleSheet("")
        self.label_Time_bachongshenzi.setText("")
        self.label_Time_bachongshenzi.setObjectName("label_Time_bachongshenzi")
        self.verticalLayout_34.addWidget(self.label_Time_bachongshenzi)
        self.textBrowser_OutPut_bachongshenzi = QtWidgets.QTextBrowser(self.widget_AiFriedns_bachongshenzi)
        self.textBrowser_OutPut_bachongshenzi.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_bachongshenzi.setObjectName("textBrowser_OutPut_bachongshenzi")
        self.textBrowser_OutPut_bachongshenzi.setText(text)  # 添加的信息
        self.verticalLayout_34.addWidget(self.textBrowser_OutPut_bachongshenzi)
        self.verticalLayout_34.setStretch(1, 9)
        self.horizontalLayout_26.addLayout(self.verticalLayout_34)
        self.verticalLayout_10.addWidget(self.widget_AiFriedns_bachongshenzi)
        self.scrollArea_bachongshenzi.setWidget(self.scrollAreaWidgetContents_bachongshenzi)

    def add_bubble_lpf_bachongshenzi(self, text):
        self.widget_AiFriedns_bachongshenzi = QtWidgets.QWidget(self.scrollAreaWidgetContents_bachongshenzi)
        self.widget_AiFriedns_bachongshenzi.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_bachongshenzi.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_bachongshenzi.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_bachongshenzi.setObjectName("widget_AiFriedns_bachongshenzi")
        self.horizontalLayout_26 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_bachongshenzi)
        self.horizontalLayout_26.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_26.setSpacing(7)
        self.horizontalLayout_26.setObjectName("horizontalLayout_26")
        self.verticalLayout_33 = QtWidgets.QVBoxLayout()
        self.verticalLayout_33.setObjectName("verticalLayout_33")
        self.label_Avatar_bachongshenzi = QtWidgets.QLabel(self.widget_AiFriedns_bachongshenzi)
        self.label_Avatar_bachongshenzi.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_bachongshenzi.setText("")
        self.label_Avatar_bachongshenzi.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_bachongshenzi.setScaledContents(True)
        self.label_Avatar_bachongshenzi.setObjectName("label_Avatar_bachongshenzi")
        self.verticalLayout_33.addWidget(self.label_Avatar_bachongshenzi)
        spacerItem14 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_33.addItem(spacerItem14)
        self.verticalLayout_33.setStretch(0, 3)
        self.verticalLayout_33.setStretch(1, 7)
        self.horizontalLayout_26.addLayout(self.verticalLayout_33)
        self.verticalLayout_34 = QtWidgets.QVBoxLayout()
        self.verticalLayout_34.setObjectName("verticalLayout_34")
        self.label_Time_bachongshenzi = QtWidgets.QLabel(self.widget_AiFriedns_bachongshenzi)
        self.label_Time_bachongshenzi.setStyleSheet("")
        self.label_Time_bachongshenzi.setText("")
        self.label_Time_bachongshenzi.setObjectName("label_Time_bachongshenzi")
        self.verticalLayout_34.addWidget(self.label_Time_bachongshenzi)
        self.textBrowser_OutPut_bachongshenzi = QtWidgets.QTextBrowser(self.widget_AiFriedns_bachongshenzi)
        self.textBrowser_OutPut_bachongshenzi.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_bachongshenzi.setObjectName("textBrowser_OutPut_bachongshenzi")
        self.textBrowser_OutPut_bachongshenzi.setText(text)  # 添加的信息
        self.verticalLayout_34.addWidget(self.textBrowser_OutPut_bachongshenzi)
        self.verticalLayout_34.setStretch(1, 9)
        self.horizontalLayout_26.addLayout(self.verticalLayout_34)
        self.verticalLayout_10.addWidget(self.widget_AiFriedns_bachongshenzi)
        self.scrollArea_bachongshenzi.setWidget(self.scrollAreaWidgetContents_bachongshenzi)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_bachongshenzi.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_bachongshenzi.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    ###雷电将军聊天
    def add_bubble_leidianjiangjun(self, text):
        self.widget_AiFriedns_leidianjiangjun = QtWidgets.QWidget(self.scrollAreaWidgetContents_leidianjiangjun)
        self.widget_AiFriedns_leidianjiangjun.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_leidianjiangjun.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_leidianjiangjun.setObjectName("widget_AiFriedns_leidianjiangjun")
        self.horizontalLayout_27 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_leidianjiangjun)
        self.horizontalLayout_27.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_27.setSpacing(7)
        self.horizontalLayout_27.setObjectName("horizontalLayout_27")
        self.verticalLayout_35 = QtWidgets.QVBoxLayout()
        self.verticalLayout_35.setObjectName("verticalLayout_35")
        self.label_Avatar_leidianjiangjun = QtWidgets.QLabel(self.widget_AiFriedns_leidianjiangjun)
        self.label_Avatar_leidianjiangjun.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_leidianjiangjun.setText("")
        self.label_Avatar_leidianjiangjun.setPixmap(QtGui.QPixmap("./img/ico/雷电将军头像.png"))
        self.label_Avatar_leidianjiangjun.setScaledContents(True)
        self.label_Avatar_leidianjiangjun.setObjectName("label_Avatar_leidianjiangjun")
        self.verticalLayout_35.addWidget(self.label_Avatar_leidianjiangjun)
        spacerItem15 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_35.addItem(spacerItem15)
        self.verticalLayout_35.setStretch(0, 3)
        self.verticalLayout_35.setStretch(1, 7)
        self.horizontalLayout_27.addLayout(self.verticalLayout_35)
        self.verticalLayout_36 = QtWidgets.QVBoxLayout()
        self.verticalLayout_36.setObjectName("verticalLayout_36")
        self.label_Time_leidianjiangjun = QtWidgets.QLabel(self.widget_AiFriedns_leidianjiangjun)
        self.label_Time_leidianjiangjun.setStyleSheet("")
        self.label_Time_leidianjiangjun.setText("")
        self.label_Time_leidianjiangjun.setObjectName("label_Time_leidianjiangjun")
        self.verticalLayout_36.addWidget(self.label_Time_leidianjiangjun)
        self.textBrowser_OutPut_leidianjiangjun = QtWidgets.QTextBrowser(self.widget_AiFriedns_leidianjiangjun)
        self.textBrowser_OutPut_leidianjiangjun.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_leidianjiangjun.setObjectName("textBrowser_OutPut_leidianjiangjun")
        self.textBrowser_OutPut_leidianjiangjun.setText(text)  # 添加的信息
        self.verticalLayout_36.addWidget(self.textBrowser_OutPut_leidianjiangjun)
        self.verticalLayout_36.setStretch(1, 9)
        self.horizontalLayout_27.addLayout(self.verticalLayout_36)
        self.verticalLayout_11.addWidget(self.widget_AiFriedns_leidianjiangjun)
        self.scrollArea_leidianjiangjun.setWidget(self.scrollAreaWidgetContents_leidianjiangjun)

    def add_bubble_lpf_leidianjiangjun(self, text):
        self.widget_AiFriedns_leidianjiangjun = QtWidgets.QWidget(self.scrollAreaWidgetContents_leidianjiangjun)
        self.widget_AiFriedns_leidianjiangjun.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_leidianjiangjun.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_leidianjiangjun.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_leidianjiangjun.setObjectName("widget_AiFriedns_leidianjiangjun")
        self.horizontalLayout_27 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_leidianjiangjun)
        self.horizontalLayout_27.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_27.setSpacing(7)
        self.horizontalLayout_27.setObjectName("horizontalLayout_27")
        self.verticalLayout_35 = QtWidgets.QVBoxLayout()
        self.verticalLayout_35.setObjectName("verticalLayout_35")
        self.label_Avatar_leidianjiangjun = QtWidgets.QLabel(self.widget_AiFriedns_leidianjiangjun)
        self.label_Avatar_leidianjiangjun.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_leidianjiangjun.setText("")
        self.label_Avatar_leidianjiangjun.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_leidianjiangjun.setScaledContents(True)
        self.label_Avatar_leidianjiangjun.setObjectName("label_Avatar_leidianjiangjun")
        self.verticalLayout_35.addWidget(self.label_Avatar_leidianjiangjun)
        spacerItem15 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_35.addItem(spacerItem15)
        self.verticalLayout_35.setStretch(0, 3)
        self.verticalLayout_35.setStretch(1, 7)
        self.horizontalLayout_27.addLayout(self.verticalLayout_35)
        self.verticalLayout_36 = QtWidgets.QVBoxLayout()
        self.verticalLayout_36.setObjectName("verticalLayout_36")
        self.label_Time_leidianjiangjun = QtWidgets.QLabel(self.widget_AiFriedns_leidianjiangjun)
        self.label_Time_leidianjiangjun.setStyleSheet("")
        self.label_Time_leidianjiangjun.setText("")
        self.label_Time_leidianjiangjun.setObjectName("label_Time_leidianjiangjun")
        self.verticalLayout_36.addWidget(self.label_Time_leidianjiangjun)
        self.textBrowser_OutPut_leidianjiangjun = QtWidgets.QTextBrowser(self.widget_AiFriedns_leidianjiangjun)
        self.textBrowser_OutPut_leidianjiangjun.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_leidianjiangjun.setObjectName("textBrowser_OutPut_leidianjiangjun")
        self.textBrowser_OutPut_leidianjiangjun.setText(text)  # 添加的信息
        self.verticalLayout_36.addWidget(self.textBrowser_OutPut_leidianjiangjun)
        self.verticalLayout_36.setStretch(1, 9)
        self.horizontalLayout_27.addLayout(self.verticalLayout_36)
        self.verticalLayout_11.addWidget(self.widget_AiFriedns_leidianjiangjun)
        self.scrollArea_leidianjiangjun.setWidget(self.scrollAreaWidgetContents_leidianjiangjun)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_leidianjiangjun.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_leidianjiangjun.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    ###巴巴托斯聊天
    def add_bubble_babatuosi(self, text):
        self.widget_AiFriedns_babatuosi = QtWidgets.QWidget(self.scrollAreaWidgetContents_babatuosi)
        self.widget_AiFriedns_babatuosi.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_babatuosi.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_babatuosi.setObjectName("widget_AiFriedns_babatuosi")
        self.horizontalLayout_28 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_babatuosi)
        self.horizontalLayout_28.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_28.setSpacing(7)
        self.horizontalLayout_28.setObjectName("horizontalLayout_28")
        self.verticalLayout_37 = QtWidgets.QVBoxLayout()
        self.verticalLayout_37.setObjectName("verticalLayout_37")
        self.label_Avatar_babatuosi = QtWidgets.QLabel(self.widget_AiFriedns_babatuosi)
        self.label_Avatar_babatuosi.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_babatuosi.setText("")
        self.label_Avatar_babatuosi.setPixmap(QtGui.QPixmap("./img/ico/巴巴托斯.png"))
        self.label_Avatar_babatuosi.setScaledContents(True)
        self.label_Avatar_babatuosi.setObjectName("label_Avatar_babatuosi")
        self.verticalLayout_37.addWidget(self.label_Avatar_babatuosi)
        spacerItem16 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_37.addItem(spacerItem16)
        self.verticalLayout_37.setStretch(0, 3)
        self.verticalLayout_37.setStretch(1, 7)
        self.horizontalLayout_28.addLayout(self.verticalLayout_37)
        self.verticalLayout_38 = QtWidgets.QVBoxLayout()
        self.verticalLayout_38.setObjectName("verticalLayout_38")
        self.label_Time_babatuosi = QtWidgets.QLabel(self.widget_AiFriedns_babatuosi)
        self.label_Time_babatuosi.setStyleSheet("")
        self.label_Time_babatuosi.setText("")
        self.label_Time_babatuosi.setObjectName("label_Time_babatuosi")
        self.verticalLayout_38.addWidget(self.label_Time_babatuosi)
        self.textBrowser_OutPut_babtuosi = QtWidgets.QTextBrowser(self.widget_AiFriedns_babatuosi)
        self.textBrowser_OutPut_babtuosi.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_babtuosi.setObjectName("textBrowser_OutPut_babtuosi")
        self.textBrowser_OutPut_babtuosi.setText(text)  # 添加的信息
        self.verticalLayout_38.addWidget(self.textBrowser_OutPut_babtuosi)
        self.verticalLayout_38.setStretch(1, 9)
        self.horizontalLayout_28.addLayout(self.verticalLayout_38)
        self.verticalLayout_12.addWidget(self.widget_AiFriedns_babatuosi)
        self.scrollArea_babatuosi.setWidget(self.scrollAreaWidgetContents_babatuosi)

    def add_bubble_lpf_babatuosi(self, text):
        self.widget_AiFriedns_babatuosi = QtWidgets.QWidget(self.scrollAreaWidgetContents_babatuosi)
        self.widget_AiFriedns_babatuosi.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_babatuosi.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_babatuosi.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_babatuosi.setObjectName("widget_AiFriedns_babatuosi")
        self.horizontalLayout_28 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_babatuosi)
        self.horizontalLayout_28.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_28.setSpacing(7)
        self.horizontalLayout_28.setObjectName("horizontalLayout_28")
        self.verticalLayout_37 = QtWidgets.QVBoxLayout()
        self.verticalLayout_37.setObjectName("verticalLayout_37")
        self.label_Avatar_babatuosi = QtWidgets.QLabel(self.widget_AiFriedns_babatuosi)
        self.label_Avatar_babatuosi.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_babatuosi.setText("")
        self.label_Avatar_babatuosi.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_babatuosi.setScaledContents(True)
        self.label_Avatar_babatuosi.setObjectName("label_Avatar_babatuosi")
        self.verticalLayout_37.addWidget(self.label_Avatar_babatuosi)
        spacerItem16 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_37.addItem(spacerItem16)
        self.verticalLayout_37.setStretch(0, 3)
        self.verticalLayout_37.setStretch(1, 7)
        self.horizontalLayout_28.addLayout(self.verticalLayout_37)
        self.verticalLayout_38 = QtWidgets.QVBoxLayout()
        self.verticalLayout_38.setObjectName("verticalLayout_38")
        self.label_Time_babatuosi = QtWidgets.QLabel(self.widget_AiFriedns_babatuosi)
        self.label_Time_babatuosi.setStyleSheet("")
        self.label_Time_babatuosi.setText("")
        self.label_Time_babatuosi.setObjectName("label_Time_babatuosi")
        self.verticalLayout_38.addWidget(self.label_Time_babatuosi)
        self.textBrowser_OutPut_babtuosi = QtWidgets.QTextBrowser(self.widget_AiFriedns_babatuosi)
        self.textBrowser_OutPut_babtuosi.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_babtuosi.setObjectName("textBrowser_OutPut_babtuosi")
        self.textBrowser_OutPut_babtuosi.setText(text)  # 添加的信息
        self.verticalLayout_38.addWidget(self.textBrowser_OutPut_babtuosi)
        self.verticalLayout_38.setStretch(1, 9)
        self.horizontalLayout_28.addLayout(self.verticalLayout_38)
        self.verticalLayout_12.addWidget(self.widget_AiFriedns_babatuosi)
        self.scrollArea_babatuosi.setWidget(self.scrollAreaWidgetContents_babatuosi)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_babatuosi.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_babatuosi.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    ###神里绫华聊天

    def add_bubble_shenlilinghua(self, text):
        self.widget_AiFriedns_shenlilinghua = QtWidgets.QWidget(self.scrollAreaWidgetContents_shenlilinghua)
        self.widget_AiFriedns_shenlilinghua.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_shenlilinghua.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_shenlilinghua.setObjectName("widget_AiFriedns_shenlilinghua")
        self.horizontalLayout_29 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_shenlilinghua)
        self.horizontalLayout_29.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_29.setSpacing(7)
        self.horizontalLayout_29.setObjectName("horizontalLayout_29")
        self.verticalLayout_39 = QtWidgets.QVBoxLayout()
        self.verticalLayout_39.setObjectName("verticalLayout_39")
        self.label_Avatar_shenlilinghua = QtWidgets.QLabel(self.widget_AiFriedns_shenlilinghua)
        self.label_Avatar_shenlilinghua.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_shenlilinghua.setText("")
        self.label_Avatar_shenlilinghua.setPixmap(QtGui.QPixmap("./img/ico/神里绫华.png"))
        self.label_Avatar_shenlilinghua.setScaledContents(True)
        self.label_Avatar_shenlilinghua.setObjectName("label_Avatar_shenlilinghua")
        self.verticalLayout_39.addWidget(self.label_Avatar_shenlilinghua)
        spacerItem17 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_39.addItem(spacerItem17)
        self.verticalLayout_39.setStretch(0, 3)
        self.verticalLayout_39.setStretch(1, 7)
        self.horizontalLayout_29.addLayout(self.verticalLayout_39)
        self.verticalLayout_40 = QtWidgets.QVBoxLayout()
        self.verticalLayout_40.setObjectName("verticalLayout_40")
        self.label_Time_shenlilinghua = QtWidgets.QLabel(self.widget_AiFriedns_shenlilinghua)
        self.label_Time_shenlilinghua.setStyleSheet("")
        self.label_Time_shenlilinghua.setText("")
        self.label_Time_shenlilinghua.setObjectName("label_Time_shenlilinghua")
        self.verticalLayout_40.addWidget(self.label_Time_shenlilinghua)
        self.textBrowser_OutPut_shenlilinghua = QtWidgets.QTextBrowser(self.widget_AiFriedns_shenlilinghua)
        self.textBrowser_OutPut_shenlilinghua.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_shenlilinghua.setObjectName("textBrowser_OutPut_shenlilinghua")
        self.textBrowser_OutPut_shenlilinghua.setText(text)  # 添加的信息
        self.verticalLayout_40.addWidget(self.textBrowser_OutPut_shenlilinghua)
        self.verticalLayout_40.setStretch(1, 9)
        self.horizontalLayout_29.addLayout(self.verticalLayout_40)
        self.verticalLayout_13.addWidget(self.widget_AiFriedns_shenlilinghua)
        self.scrollArea_shenlilinghua.setWidget(self.scrollAreaWidgetContents_shenlilinghua)

    def add_bubble_lpf_shenlilinghua(self, text):
        self.widget_AiFriedns_shenlilinghua = QtWidgets.QWidget(self.scrollAreaWidgetContents_shenlilinghua)
        self.widget_AiFriedns_shenlilinghua.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_shenlilinghua.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_shenlilinghua.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_shenlilinghua.setObjectName("widget_AiFriedns_shenlilinghua")
        self.horizontalLayout_29 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_shenlilinghua)
        self.horizontalLayout_29.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_29.setSpacing(7)
        self.horizontalLayout_29.setObjectName("horizontalLayout_29")
        self.verticalLayout_39 = QtWidgets.QVBoxLayout()
        self.verticalLayout_39.setObjectName("verticalLayout_39")
        self.label_Avatar_shenlilinghua = QtWidgets.QLabel(self.widget_AiFriedns_shenlilinghua)
        self.label_Avatar_shenlilinghua.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_shenlilinghua.setText("")
        self.label_Avatar_shenlilinghua.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_shenlilinghua.setScaledContents(True)
        self.label_Avatar_shenlilinghua.setObjectName("label_Avatar_shenlilinghua")
        self.verticalLayout_39.addWidget(self.label_Avatar_shenlilinghua)
        spacerItem17 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_39.addItem(spacerItem17)
        self.verticalLayout_39.setStretch(0, 3)
        self.verticalLayout_39.setStretch(1, 7)
        self.horizontalLayout_29.addLayout(self.verticalLayout_39)
        self.verticalLayout_40 = QtWidgets.QVBoxLayout()
        self.verticalLayout_40.setObjectName("verticalLayout_40")
        self.label_Time_shenlilinghua = QtWidgets.QLabel(self.widget_AiFriedns_shenlilinghua)
        self.label_Time_shenlilinghua.setStyleSheet("")
        self.label_Time_shenlilinghua.setText("")
        self.label_Time_shenlilinghua.setObjectName("label_Time_shenlilinghua")
        self.verticalLayout_40.addWidget(self.label_Time_shenlilinghua)
        self.textBrowser_OutPut_shenlilinghua = QtWidgets.QTextBrowser(self.widget_AiFriedns_shenlilinghua)
        self.textBrowser_OutPut_shenlilinghua.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_shenlilinghua.setObjectName("textBrowser_OutPut_shenlilinghua")
        self.textBrowser_OutPut_shenlilinghua.setText(text)  # 添加的信息
        self.verticalLayout_40.addWidget(self.textBrowser_OutPut_shenlilinghua)
        self.verticalLayout_40.setStretch(1, 9)
        self.horizontalLayout_29.addLayout(self.verticalLayout_40)
        self.verticalLayout_13.addWidget(self.widget_AiFriedns_shenlilinghua)
        self.scrollArea_shenlilinghua.setWidget(self.scrollAreaWidgetContents_shenlilinghua)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_shenlilinghua.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_shenlilinghua.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    ###宵宫聊天

    def add_bubble_xiaogong(self, text):
        self.widget_AiFriedns_xiaogong = QtWidgets.QWidget(self.scrollAreaWidgetContents_xiaogong)
        self.widget_AiFriedns_xiaogong.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_xiaogong.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_xiaogong.setObjectName("widget_AiFriedns_xiaogong")
        self.horizontalLayout_30 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_xiaogong)
        self.horizontalLayout_30.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_30.setSpacing(7)
        self.horizontalLayout_30.setObjectName("horizontalLayout_30")
        self.verticalLayout_41 = QtWidgets.QVBoxLayout()
        self.verticalLayout_41.setObjectName("verticalLayout_41")
        self.label_Avatar_xiaogong = QtWidgets.QLabel(self.widget_AiFriedns_xiaogong)
        self.label_Avatar_xiaogong.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_xiaogong.setText("")
        self.label_Avatar_xiaogong.setPixmap(QtGui.QPixmap("./img/ico/宵宫头像.png"))
        self.label_Avatar_xiaogong.setScaledContents(True)
        self.label_Avatar_xiaogong.setObjectName("label_Avatar_xiaogong")
        self.verticalLayout_41.addWidget(self.label_Avatar_xiaogong)
        spacerItem18 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_41.addItem(spacerItem18)
        self.verticalLayout_41.setStretch(0, 3)
        self.verticalLayout_41.setStretch(1, 7)
        self.horizontalLayout_30.addLayout(self.verticalLayout_41)
        self.verticalLayout_42 = QtWidgets.QVBoxLayout()
        self.verticalLayout_42.setObjectName("verticalLayout_42")
        self.label_Time_xiaogong = QtWidgets.QLabel(self.widget_AiFriedns_xiaogong)
        self.label_Time_xiaogong.setStyleSheet("")
        self.label_Time_xiaogong.setText("")
        self.label_Time_xiaogong.setObjectName("label_Time_xiaogong")
        self.verticalLayout_42.addWidget(self.label_Time_xiaogong)
        self.textBrowser_OutPut_xiaogong = QtWidgets.QTextBrowser(self.widget_AiFriedns_xiaogong)
        self.textBrowser_OutPut_xiaogong.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_xiaogong.setObjectName("textBrowser_OutPut_xiaogong")
        self.textBrowser_OutPut_xiaogong.setText(text)  # 添加的信息
        self.verticalLayout_42.addWidget(self.textBrowser_OutPut_xiaogong)
        self.verticalLayout_42.setStretch(1, 9)
        self.horizontalLayout_30.addLayout(self.verticalLayout_42)
        self.verticalLayout_14.addWidget(self.widget_AiFriedns_xiaogong)
        self.scrollArea_xiaogong.setWidget(self.scrollAreaWidgetContents_xiaogong)

    def add_bubble_lpf_xiaogong(self, text):
        self.widget_AiFriedns_xiaogong = QtWidgets.QWidget(self.scrollAreaWidgetContents_xiaogong)
        self.widget_AiFriedns_xiaogong.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_xiaogong.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_xiaogong.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_xiaogong.setObjectName("widget_AiFriedns_xiaogong")
        self.horizontalLayout_30 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_xiaogong)
        self.horizontalLayout_30.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_30.setSpacing(7)
        self.horizontalLayout_30.setObjectName("horizontalLayout_30")
        self.verticalLayout_41 = QtWidgets.QVBoxLayout()
        self.verticalLayout_41.setObjectName("verticalLayout_41")
        self.label_Avatar_xiaogong = QtWidgets.QLabel(self.widget_AiFriedns_xiaogong)
        self.label_Avatar_xiaogong.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_xiaogong.setText("")
        self.label_Avatar_xiaogong.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_xiaogong.setScaledContents(True)
        self.label_Avatar_xiaogong.setObjectName("label_Avatar_xiaogong")
        self.verticalLayout_41.addWidget(self.label_Avatar_xiaogong)
        spacerItem18 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_41.addItem(spacerItem18)
        self.verticalLayout_41.setStretch(0, 3)
        self.verticalLayout_41.setStretch(1, 7)
        self.horizontalLayout_30.addLayout(self.verticalLayout_41)
        self.verticalLayout_42 = QtWidgets.QVBoxLayout()
        self.verticalLayout_42.setObjectName("verticalLayout_42")
        self.label_Time_xiaogong = QtWidgets.QLabel(self.widget_AiFriedns_xiaogong)
        self.label_Time_xiaogong.setStyleSheet("")
        self.label_Time_xiaogong.setText("")
        self.label_Time_xiaogong.setObjectName("label_Time_xiaogong")
        self.verticalLayout_42.addWidget(self.label_Time_xiaogong)
        self.textBrowser_OutPut_xiaogong = QtWidgets.QTextBrowser(self.widget_AiFriedns_xiaogong)
        self.textBrowser_OutPut_xiaogong.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_xiaogong.setObjectName("textBrowser_OutPut_xiaogong")
        self.textBrowser_OutPut_xiaogong.setText(text)  # 添加的信息
        self.verticalLayout_42.addWidget(self.textBrowser_OutPut_xiaogong)
        self.verticalLayout_42.setStretch(1, 9)
        self.horizontalLayout_30.addLayout(self.verticalLayout_42)
        self.verticalLayout_14.addWidget(self.widget_AiFriedns_xiaogong)
        self.scrollArea_xiaogong.setWidget(self.scrollAreaWidgetContents_xiaogong)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_xiaogong.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_xiaogong.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    ###钟离聊天

    def add_bubble_zhongli(self, text):
        self.widget_AiFriedns_zhongli = QtWidgets.QWidget(self.scrollAreaWidgetContents_zhongli)
        self.widget_AiFriedns_zhongli.setMinimumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_zhongli.setMaximumSize(QtCore.QSize(300, 150))
        self.widget_AiFriedns_zhongli.setObjectName("widget_AiFriedns_zhongli")
        self.horizontalLayout_31 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_zhongli)
        self.horizontalLayout_31.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_31.setSpacing(7)
        self.horizontalLayout_31.setObjectName("horizontalLayout_31")
        self.verticalLayout_21 = QtWidgets.QVBoxLayout()
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.label_Avatar_zhongli = QtWidgets.QLabel(self.widget_AiFriedns_zhongli)
        self.label_Avatar_zhongli.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_zhongli.setText("")
        self.label_Avatar_zhongli.setPixmap(QtGui.QPixmap("./img/ico/钟离头像.png"))
        self.label_Avatar_zhongli.setScaledContents(True)
        self.label_Avatar_zhongli.setObjectName("label_Avatar_zhongli")
        self.verticalLayout_21.addWidget(self.label_Avatar_zhongli)
        spacerItem19 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_21.addItem(spacerItem19)
        self.verticalLayout_21.setStretch(0, 3)
        self.verticalLayout_21.setStretch(1, 7)
        self.horizontalLayout_31.addLayout(self.verticalLayout_21)
        self.verticalLayout_43 = QtWidgets.QVBoxLayout()
        self.verticalLayout_43.setObjectName("verticalLayout_43")
        self.label_Time_zhongli = QtWidgets.QLabel(self.widget_AiFriedns_zhongli)
        self.label_Time_zhongli.setStyleSheet("")
        self.label_Time_zhongli.setText("")
        self.label_Time_zhongli.setObjectName("label_Time_zhongli")
        self.verticalLayout_43.addWidget(self.label_Time_zhongli)
        self.textBrowser_OutPut_zhongli = QtWidgets.QTextBrowser(self.widget_AiFriedns_zhongli)
        self.textBrowser_OutPut_zhongli.setStyleSheet("background-color: rgb(225, 225, 225);")
        self.textBrowser_OutPut_zhongli.setObjectName("textBrowser_OutPut_zhongli")
        self.textBrowser_OutPut_zhongli.setText(text)  # 添加的信息
        self.verticalLayout_43.addWidget(self.textBrowser_OutPut_zhongli)
        self.verticalLayout_43.setStretch(1, 9)
        self.horizontalLayout_31.addLayout(self.verticalLayout_43)
        self.verticalLayout_44.addWidget(self.widget_AiFriedns_zhongli)
        self.scrollArea_zhongli.setWidget(self.scrollAreaWidgetContents_zhongli)

    def add_bubble_lpf_zhongli(self, text):
        self.widget_AiFriedns_zhongli = QtWidgets.QWidget(self.scrollAreaWidgetContents_zhongli)
        self.widget_AiFriedns_zhongli.setLayoutDirection(QtCore.Qt.RightToLeft)  # 设置方向
        self.widget_AiFriedns_zhongli.setMinimumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_zhongli.setMaximumSize(QtCore.QSize(300, 100))
        self.widget_AiFriedns_zhongli.setObjectName("widget_AiFriedns_zhongli")
        self.horizontalLayout_31 = QtWidgets.QHBoxLayout(self.widget_AiFriedns_zhongli)
        self.horizontalLayout_31.setContentsMargins(11, -1, 11, -1)
        self.horizontalLayout_31.setSpacing(7)
        self.horizontalLayout_31.setObjectName("horizontalLayout_31")
        self.verticalLayout_21 = QtWidgets.QVBoxLayout()
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.label_Avatar_zhongli = QtWidgets.QLabel(self.widget_AiFriedns_zhongli)
        self.label_Avatar_zhongli.setMaximumSize(QtCore.QSize(50, 50))
        self.label_Avatar_zhongli.setText("")
        self.label_Avatar_zhongli.setPixmap(QtGui.QPixmap("./img/ico/空头像.jpg"))
        self.label_Avatar_zhongli.setScaledContents(True)
        self.label_Avatar_zhongli.setObjectName("label_Avatar_zhongli")
        self.verticalLayout_21.addWidget(self.label_Avatar_zhongli)
        spacerItem19 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_21.addItem(spacerItem19)
        self.verticalLayout_21.setStretch(0, 3)
        self.verticalLayout_21.setStretch(1, 7)
        self.horizontalLayout_31.addLayout(self.verticalLayout_21)
        self.verticalLayout_43 = QtWidgets.QVBoxLayout()
        self.verticalLayout_43.setObjectName("verticalLayout_43")
        self.label_Time_zhongli = QtWidgets.QLabel(self.widget_AiFriedns_zhongli)
        self.label_Time_zhongli.setStyleSheet("")
        self.label_Time_zhongli.setText("")
        self.label_Time_zhongli.setObjectName("label_Time_zhongli")
        self.verticalLayout_43.addWidget(self.label_Time_zhongli)
        self.textBrowser_OutPut_zhongli = QtWidgets.QTextBrowser(self.widget_AiFriedns_zhongli)
        self.textBrowser_OutPut_zhongli.setStyleSheet("background-color: rgb(100, 225, 100);")
        self.textBrowser_OutPut_zhongli.setObjectName("textBrowser_OutPut_zhongli")
        self.textBrowser_OutPut_zhongli.setText(text)  # 添加的信息
        self.verticalLayout_43.addWidget(self.textBrowser_OutPut_zhongli)
        self.verticalLayout_43.setStretch(1, 9)
        self.horizontalLayout_31.addLayout(self.verticalLayout_43)
        self.verticalLayout_44.addWidget(self.widget_AiFriedns_zhongli)
        self.scrollArea_zhongli.setWidget(self.scrollAreaWidgetContents_zhongli)

        _translate = QtCore.QCoreApplication.translate
        self.label_Time_zhongli.setText(_translate("MainWindow", "旅行者"))
        self.label_Time_zhongli.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # 解决了Qtdesigner设计的界面与实际运行界面不一致的问题
    app = QApplication([])
    # firstWd = AiFriendsWindow()#虚拟伙伴
    # firstWd = LogInAndSignUpWindow()  # 登录与注册
    firstWd = MenuWindow()  # 主菜单
    firstWd.show()
    app.exec_()
