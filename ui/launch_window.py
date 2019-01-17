import logging
import os
import time
import webbrowser

import requests
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

import config
from services.wechat import WeChat
from services.youzan import YouZanCategories
from ui.editor_window import EditorWindow
from ui.localstorelineedit import LocalStoreLineEdit
from youzan import auth
from youzan.yzclient import YZClient


class LaunchWindow(QMainWindow):
    __IsDev__ = 'DEV' in os.environ and os.environ['DEV'] == '1'

    def __init__(self):
        super(LaunchWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('设置信息' + config.Version)
        self.setWindowIcon(QIcon('main.png'))
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setFixedSize(600, 400)
        widget = QWidget()
        self.setCentralWidget(widget)
        hbox = QHBoxLayout()
        widget.setLayout(layout)
        layout.addLayout(hbox)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint)
        label = QLabel('欢迎使用有赞商品导入到微信公众号商品程序\n请设置以下信息')
        hbox.addWidget(label)
        form = QFormLayout()
        layout.addLayout(form)

        wechat_btn = QPushButton('在哪看这些信息')
        wechat_btn.clicked.connect(
            lambda: webbrowser.open('https://mp.weixin.qq.com/wiki?t=resource/res_main&id=mp1472017492_58YV5'))
        form.addRow('微信公众号设置', wechat_btn)

        self.wechat_id = LocalStoreLineEdit('wechat_app_id')
        self.wechat_secret = LocalStoreLineEdit('wechat_app_secret')

        self.wechat_id.installEventFilter(self)
        self.wechat_secret.installEventFilter(self)

        form.addRow('App ID', self.wechat_id)
        form.addRow('App Secret', self.wechat_secret)

        wechat_ip_btn = QPushButton('微信官方教程')
        wechat_ip_btn.clicked.connect(
            lambda: webbrowser.open(
                'https://mp.weixin.qq.com/cgi-bin/announce?action=getannouncement&key=1495617578&version=1&lang=zh_CN&platform=2'))
        form.addRow('添加你电脑的IP到微信后台', wechat_ip_btn)

        youzan_btn = QPushButton('在哪看这些信息')
        youzan_btn.clicked.connect(
            lambda: webbrowser.open('https://open.youzan.com/v3/apicenter/doc-api-main/1/1/4369'))
        form.addRow('有赞设置', youzan_btn)
        self.youzan_id = LocalStoreLineEdit('youzan_app_id')
        self.youzan_secret = LocalStoreLineEdit('youzan_app_secret')
        self.youzan_kdt_id = LocalStoreLineEdit('youzan_kdt_id')

        self.youzan_id.installEventFilter(self)
        self.youzan_secret.installEventFilter(self)
        self.youzan_kdt_id.installEventFilter(self)

        form.addRow('Client ID', self.youzan_id)
        form.addRow('Client Secret', self.youzan_secret)
        form.addRow('授权店铺ID', self.youzan_kdt_id)
        next_btn = QPushButton('下一步')
        next_btn.clicked.connect(self.nextStep)
        form.addRow(None, next_btn)
        self.form_input = [self.wechat_id, self.wechat_secret, self.youzan_id, self.youzan_secret, self.youzan_kdt_id]

    def nextStep(self):
        ok = self.checkTimeTaoBao('2019-01-01')
        if not ok:
            return
        msg = ''
        go_next = 1

        wechat_app_id = self.wechat_id.text()
        wechat_app_secret = self.wechat_secret.text()

        youzan_app_id = self.youzan_id.text()
        youzan_app_secret = self.youzan_secret.text()
        youzan_kdt_id = self.youzan_kdt_id.text()

        if go_next and len(wechat_app_id) == 0:
            go_next = 0
            msg = '请填入微信App ID'
            self.wechat_id.setFocus()

        if go_next and len(wechat_app_secret) == 0:
            go_next = 0
            msg = '请填入微信App Secret'
            self.wechat_secret.setFocus()

        if go_next and len(youzan_app_id) == 0:
            go_next = 0
            msg = '请填入有赞开放接口的Client ID'
            self.youzan_id.setFocus()

        if go_next and len(youzan_app_secret) == 0:
            go_next = 0
            msg = '请填入有赞开放接口的Client Secret'
            self.youzan_secret.setFocus()

        if go_next and len(youzan_kdt_id) == 0:
            go_next = 0
            msg = '请填入有赞开放接口的授权店铺ID'
            self.youzan_kdt_id.setFocus()

        if go_next == 0:
            QMessageBox.about(self, '警告', msg)
            return

        go_next = self.checkYouZan()
        if go_next == 0:
            return
        go_next = self.checkWeChat()
        if go_next == 0:
            return

        self.editor = EditorWindow()
        # self.editor.signals.Close.connect(lambda: self.show())
        self.editor.show()
        self.hide()

    def checkYouZan(self):
        try:
            sign = auth.Sign(app_id=self.youzan_id.text(), app_secret=self.youzan_secret.text(),
                             kdt_id=self.youzan_kdt_id.text())
            print('有赞sign', sign)
            YZClient(sign)
        except Exception as e:
            logging.error(e)
            QMessageBox.information(None, '有赞检测', '有赞检测发生错误\n' + str(e))
            return 0
        YouZanCategories()
        return 1

    def checkWeChat(self):
        try:
            WeChat(AppID=self.wechat_id.text(), AppSecret=self.wechat_secret.text())
            return 1
        except Exception as e:
            QMessageBox.information(self, '微信检测', '微信检测发生错误\n' + str(e))
            return 0

    def checkTimeQQ(self, target):

        res = requests.get('https://cgi.im.qq.com/cgi-bin/cgi_svrtime')
        try:
            now = time.strptime(res.text.strip(), '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            QMessageBox.about(self, '联网失败', '请重试')
            return False

        targetTime = time.strptime(target, '%Y-%m-%d')
        if time.mktime(now) > time.mktime(targetTime):
            QMessageBox.about(self, '试用版', '试用版已到期\n{0} 后不能使用'.format(target))
            return False
        else:
            QMessageBox.about(self, '试用版', '试用版\n{0} 后不能使用'.format(target))
            return True

    def checkTimeTaoBao(self, target):
        try:
            res = requests.get('http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp', timeout=5)
        except:
            QMessageBox.about(self, '联网失败', '请重试')
            return False
        targetTime = time.strptime(target, '%Y-%m-%d')
        now = res.json()
        now = int(now['data']['t']) / 1000
        if now > time.mktime(targetTime):
            QMessageBox.about(self, '试用版', '试用版已到期：{0}'.format(target))
            return False
        else:
            QMessageBox.about(self, '试用版', '这是试用版\n{0} 后不能使用'.format(target))
            return True

    def eventFilter(self, widget, event):
        if (event.type() == QEvent.KeyPress and
                widget in self.form_input):
            key = event.key()
            if key == Qt.Key_Return or key == Qt.Key_Enter:
                index = self.form_input.index(widget)
                if index == len(self.form_input) - 1:
                    self.nextStep()
                    return True
                else:
                    self.form_input[index + 1].setFocus()
                    return True

        return QWidget.eventFilter(self, widget, event)
