import asyncio

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from services.item import Item
from services.wechat import WeChat, WeChatImportStatus
from services.youzan import YouZanItem
from youzan.yzclient import YZClient


class WorkThread(QThread):
    stop = False
    signal = pyqtSignal(bool, str, str)
    callback = pyqtSignal()
    loop = asyncio.new_event_loop()

    def __init__(self, app_id: str, load: list, ):
        super(WorkThread, self).__init__()
        self.load = load
        self.app_id = app_id

    def run(self):
        while True:
            if self.stop:
                break

            if len(self.load) > 0:
                items = self.load[:10]
                self.load = self.load[10:]
                tasks = [self.do(item=item) for item in items]
                print('任务数量', len(tasks))
                self.loop.run_until_complete(asyncio.wait(tasks))
            else:
                break
        print('任务完成')
        self.callback.emit()

    async def do(self, item):
        res = None
        if isinstance(item, YouZanItem):
            res = await asyncio.gather(
                WorkThread.LoadYouZanItemAndUploadToWeChat(app_id=self.app_id, item=item),
                return_exceptions=True)
        elif isinstance(item, Item):
            res = await asyncio.gather(WorkThread.UploadToWeChat(app_id=self.app_id, item=item),
                                       return_exceptions=True)
        if res and res[0]:
            success = isinstance(res[0], WeChatImportStatus)
            self.signal.emit(success, item.title, res[0].__str__())

    @staticmethod
    async def LoadYouZanItem(item: YouZanItem):
        data = YZClient.exec('youzan.item.get', '3.0.0', 'get', {'alias': item.alias, 'item_id': item.id})
        return Item.FromYouZan(data['response']['item'])

    @staticmethod
    async def LoadYouZanItemAndUploadToWeChat(app_id: str, item: YouZanItem):
        # print('load', item.id)

        try:
            loaded_item = await WorkThread.LoadYouZanItem(item)
        except:
            raise Exception('读取有赞商品信息 发生错误')
        loaded_item.setOfficialCategory(item.category)
        if item.category == '图书':
            if item.book is None:
                raise Exception('没有图书信息，上传失败')
            loaded_item.book = item.book
        return await WorkThread.UploadToWeChat(app_id=app_id, item=loaded_item)

    @staticmethod
    async def UploadToWeChat(app_id: str, item):
        params = {'product': [item.toWeChatItem(wechat_app_id=app_id)]}
        # print(params)
        try:
            res = WeChat.exec(command='add', params=params)
            if res['errmsg'] != 'ok':
                raise Exception(res['errmsg'])
            status_data = WeChat.exec(command='status', params={'status_ticket': res['status_ticket']})
            # print('微信结果', status_data)
        except Exception as e:
            print(e.__str__())
            raise Exception('提交到微信 发生错误')

        status = WeChatImportStatus(data=status_data)
        return status


class ProcessDialog(QDialog):

    def __init__(self, app_id: str, load: list, ignore: list, auto_close: bool = False, parent=None):
        QDialog.__init__(self, parent=parent, flags=Qt.Window | Qt.WindowTitleHint)

        self.__can_close = False
        self.__total = len(load)
        self.__current = 0
        self.__ignore_text = ignore
        self.__ignore = len(ignore)
        self.__success = 0
        self.__fail = 0
        self.__finish = False
        self.__close_timer = None

        self.__ui()

        self.worker = worker = WorkThread(app_id=app_id, load=load)

        self.worker.signal.connect(self.__update_ui)
        if auto_close:
            self.worker.callback.connect(self.__initCloseDialogTimer)

        worker.start()

    def __ui(self):
        self.setWindowTitle('请稍候')
        self.setMinimumSize(600, 400)
        hbox = QVBoxLayout()
        self.setLayout(hbox)

        self.bar = QProgressBar()
        hbox.addWidget(self.bar)
        self.bar.setTextVisible(True)
        self.bar.setAlignment(Qt.AlignCenter)

        grid = QGridLayout()
        hbox.addLayout(grid)
        stop_btn = QPushButton('停止')

        def stop():
            self.__current = 100
            self.__finish = True
            self.worker.stop = True
            self.__stop_close_timer()
            self.done(QDialog.Rejected)

        stop_btn.clicked.connect(stop)
        grid.addWidget(stop_btn, 0, 5)

        self.tree = QTreeWidget()
        hbox.addWidget(self.tree)
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(['商品', '结果'])

        self.success_item = QTreeWidgetItem(['成功', str(0)])
        self.tree.addTopLevelItem(self.success_item)

        self.fail_item = QTreeWidgetItem(['失败', str(0)])
        self.tree.addTopLevelItem(self.fail_item)

        self.ignore_item = QTreeWidgetItem(['跳过', str(self.__ignore)])
        self.ignore_item.addChildren([QTreeWidgetItem(text) for text in self.__ignore_text])

        self.tree.addTopLevelItem(self.ignore_item)

    def setTotal(self, total: int):
        self.__total = total
        self.__calc_current()

    def current(self):
        return self.__current

    def __calc_current(self):
        value = 1 if self.__ignore > 0 else 0
        current = self.__success + self.__fail
        if self.__total > 0 and current > 0:
            value = current / self.__total

        self.__current = int(value * 100)
        if self.__current > 100:
            self.__current = 100

        self.__finish = self.__current >= 100
        return self.__current

    def __update_ui(self, is_success: bool, item_title: str, message: str):
        # print('更新ui')

        if is_success:
            parent = self.success_item
            self.__success += 1
        else:
            parent = self.fail_item
            self.__fail += 1
        item = QTreeWidgetItem([item_title, message])
        parent.addChild(item)

        self.__calc_current()
        self.bar.setValue(self.__current)
        self.bar.setFormat('进度：{}%'.format(self.__current))
        self.setWindowTitle(str(self.__current) + '%')

        self.success_item.setText(1, str(self.__success))
        self.fail_item.setText(1, str(self.__fail))

    def __initCloseDialogTimer(self):
        self.__stop_close_timer()
        self.__close_timer = timer = QTimer()
        timer.setSingleShot(True)
        # 5秒后自动关闭
        timer.setInterval(5000)
        timer.timeout.connect(lambda: self.done(QDialog.Rejected))
        timer.start()

    def __stop_close_timer(self):
        if isinstance(self.__close_timer, QTimer) and self.__close_timer.isActive():
            self.__close_timer.stop()

    def __stop_ui_timer(self):
        return

    def done(self, p_int):
        print('done', self.__current, self.__current < 100)
        if self.__current < 100:
            return
        self.__stop_close_timer()
        self.__stop_ui_timer()
        QDialog.done(self, p_int)

    def closeEvent(self, eve: QCloseEvent):
        print('closeEvent', self.__current, self.__current < 100)
        if self.__current < 100:
            eve.ignore()
            return
        self.__stop_close_timer()
        self.__stop_ui_timer()
        QDialog.closeEvent(self, eve)
