import asyncio
import os
import threading
import time
import webbrowser

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import config
from async_services.threads import Pool
from services.localstore import LocalStore
from services.wechat import WeChat
from services.youzan import YouZanItem
from ui.book_dialog import BookDialog
from ui.item_window import ItemWindow
from ui.line import QHLine
from ui.localstorelineedit import LocalStoreLineEdit
from ui.new_process_dialog import ProcessDialog
from youzan.yzclient import YZClient

WeChatItemCategories = ['图书', '女装', '男装', '美妆个护', '母婴', '食品生鲜', '数码家电', '珠宝配饰', '鞋靴箱包', '运动户外', '家居百货', '汽车用品']

Style = '''
    QListWidget{
        background: rgba(255,255,255,0.3);
    }
'''


class EditorWindowSignals:
    Close = pyqtSignal()


class Loader(QThread):
    when_start = pyqtSignal()
    callback = pyqtSignal(list)


# 读取 微信商品 工作线程
class WeChatItemsLoader(Loader):
    def run(self):
        self.when_start.emit()
        self.callback.emit(self.Load())

    @staticmethod
    def Load():
        items = []
        page = 1
        page_size = 100
        while True:
            has_next_page = WeChatItemsLoader.LoadByPage(items=items, page=page, page_size=page_size)
            page += 1
            if not has_next_page:
                break
        return items

    @staticmethod
    def LoadByPage(items: list, page: int, page_size: int):
        res = WeChat.GetItemByPage(page_num=page, page_size=page_size)
        items.extend(res)
        return len(res) > 0


# 读取 有赞商品 工作线程
class YouZanItemsLoader(Loader):
    __loop = asyncio.new_event_loop()

    def run(self):
        self.when_start.emit()
        self.callback.emit(self.load())

    def load(self):
        items = []
        page_size = 100

        # 先获取商品总数，计算页数
        data = YZClient.exec(apiName='youzan.items.onsale.get', version='3.0.0', method='GET',
                             params={'page_size': 1, 'page_no': 1})
        count = data['response']['count']
        page = count / page_size
        page_int = int(page)
        total_page = page_int + 1
        if page > page_int:
            total_page += 1

        tasks = [YouZanItemsLoader.LoadByPage(items=items, page=page, page_size=page_size) for page in
                 range(1, total_page)]
        self.__loop.run_until_complete(asyncio.wait(tasks))
        return items

    @staticmethod
    async def LoadByPage(items: list, page: int, page_size: int):
        params = {'page_no': page, 'page_size': page_size}
        res = YouZanItem.ParseList(
            YZClient.exec(apiName='youzan.items.onsale.get', version='3.0.0', method='GET', params=params))
        items.extend(res)


class EditorWindow(QMainWindow):
    __IsDev__ = 'DEV' in os.environ and os.environ['DEV'] == '1'

    auto_update_signal = pyqtSignal()

    def __init__(self):
        super(EditorWindow, self).__init__()
        print('打开Editor Window')

        self.youzan_items = []
        self.youzan_search_items = []
        self.wechat_items = []
        self.wechat_search_items = []
        self.item_windows = {}
        self.signals = EditorWindowSignals()

        self.is_loading_youzan = True
        self.is_loading_wechat = True

        self.youzan_loader = YouZanItemsLoader()
        self.youzan_loader.when_start.connect(self.load_start_youzan)
        self.youzan_loader.callback.connect(self.loaded_youzan_items)

        self.wechat_loader = WeChatItemsLoader()
        self.wechat_loader.when_start.connect(self.load_start_wechat)
        self.wechat_loader.callback.connect(self.loaded_wechat_items)

        self.auto_update_signal.connect(lambda: self.oneKeyUpdateWeChat(is_auto=True))

        self.resize(800, 600)
        self.initUI()
        self.drawMenu()

        WeChat(AppID='wx0aded43ce76b4496', AppSecret='f9ee1c6b217dc7c6841d799688dc42ac')
        # self.loadYouZanItems()
        # self.loadWeChatItems()
        self.youzan_loader.start()
        self.wechat_loader.start()

    def load_start_youzan(self):
        self.is_loading_youzan = True
        self.refresh_youzan_btn.setDisabled(True)
        self.youzan_list.setDisabled(True)
        self.youzan_total_label.setText('读取中')

    def load_start_wechat(self):
        self.is_loading_wechat = True
        self.refresh_wechat_btn.setDisabled(True)
        self.wechat_list.setDisabled(True)
        self.wechat_total_label.setText('读取中')

    def loaded_youzan_items(self, items):
        self.youzan_list.clear()
        self.youzan_search_items.clear()
        self.youzan_items.clear()
        self.youzan_items.extend(items)
        self.searchItem('youzan')
        self.is_loading_youzan = False
        self.refresh_youzan_btn.setDisabled(False)
        self.youzan_list.setDisabled(False)

    def loaded_wechat_items(self, items):
        self.wechat_list.clear()
        self.wechat_items.clear()
        self.wechat_search_items.clear()
        self.wechat_items.extend(items)
        self.searchItem('wechat')
        self.is_loading_wechat = False
        self.refresh_wechat_btn.setDisabled(False)
        self.wechat_list.setDisabled(False)

    def initUI(self):
        self.setStyleSheet(Style)
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        self.setWindowTitle('商品导入' + config.Version)
        widget = QWidget()
        self.setCentralWidget(widget)
        vbox = QVBoxLayout()
        widget.setLayout(vbox)
        self.topUI(vbox)
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        self.leftUI(hbox)
        self.centerUI(hbox)
        self.rightUI(hbox)
        self.initAutoUpdateTimer()

    def drawMenu(self):
        menu: QMenuBar = self.menuBar()
        about: QMenu = menu.addMenu('关于')
        action: QAction = about.addAction('关于')
        action.triggered.connect(self.aboutMeAlert)

    def aboutMeAlert(self):
        QMessageBox.about(self, '联系信息', '微信ID：gzlock')

    def topUI(self, parentLayout: QVBoxLayout):
        layout = QHBoxLayout()
        parentLayout.addLayout(layout)

        self.wechat_app_id_input = LocalStoreLineEdit('wechat_tuiguang_app_id')
        layout.addWidget(QLabel('微信小程序ID'))
        layout.addWidget(self.wechat_app_id_input)
        button = QPushButton('在哪找')
        button.clicked.connect(lambda: webbrowser.open('http://wenda.youzan.com/question/8132'))
        layout.addWidget(button)

    def leftUI(self, parentLayout: QVBoxLayout):
        layout = QVBoxLayout()
        parentLayout.addLayout(layout)
        hbox = QHBoxLayout()
        layout.addLayout(hbox)
        hbox.addWidget(QLabel('有赞商品列表'))
        self.refresh_youzan_btn = refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(lambda: self.youzan_loader.start())
        hbox.addWidget(refresh_btn)

        self.youzan_list = QListWidget()
        self.youzan_list.doubleClicked.connect(
            lambda: self.openItemWindow(self.youzan_search_items[self.youzan_list.currentIndex().row()]))
        self.youzan_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.youzan_list)

        self.youzan_total_label = QLabel()
        layout.addWidget(self.youzan_total_label)

    def centerUI(self, parentLayout: QHBoxLayout):
        widget = QWidget()
        widget.setMaximumWidth(140)
        parentLayout.addWidget(widget)

        layout: QVBoxLayout = QVBoxLayout()
        widget.setLayout(layout)
        layout.setAlignment(Qt.AlignTop)
        # layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.searchItem)
        self.search_input.setPlaceholderText('输入搜索关键字')
        self.search_input.setFocus()
        clear_search_btn = QPushButton('清空')
        clear_search_btn.clicked.connect(lambda: self.search_input.setText(''))
        layout.addWidget(self.search_input)
        # layout.addWidget(clear_search_btn, 1, 0)
        layout.addWidget(QHLine())

        layout.addWidget(QLabel('双击商品列表\n查看详细信息'))
        layout.addWidget(QHLine())
        layout.addWidget(QLabel('微信商品分类'))
        self.wechat_categories_list = QListWidget()
        self.wechat_categories_list.setObjectName('wechat_item_type')
        # self.wechat_categories_list.setFixedHeight(160)
        for type in WeChatItemCategories:
            self.wechat_categories_list.addItem(type)

        layout.addWidget(self.wechat_categories_list)

        self.import_btn = QPushButton('执行导入')
        self.import_btn.setToolTip('将选择的有赞商品导入到微信商品')
        self.import_btn.clicked.connect(self.exportToWeChat)
        layout.addWidget(self.import_btn)

        self.update_btn = QPushButton('一键更新')
        self.update_btn.setToolTip('一键更新微信的商品信息')
        self.update_btn.clicked.connect(self.oneKeyUpdateWeChat)
        layout.addWidget(self.update_btn)

        timeout_list = QComboBox()
        timeout_list.addItem('不自动更新')
        timeout_list.addItem('每1小时')
        timeout_list.addItem('每2小时')
        timeout_list.addItem('每4小时')
        timeout_list.addItem('每8小时')
        timeout_list.addItem('每12小时')
        timeout_list.addItem('每24小时')
        layout.addWidget(timeout_list)
        self.__autoUpdate_index = LocalStore.Get(key='auto_update_selected', default=0)
        timeout_list.setCurrentIndex(self.__autoUpdate_index)
        timeout_list.currentIndexChanged.connect(self.changeAutoUpdate)

    def rightUI(self, parentLayout: QVBoxLayout):
        layout = QVBoxLayout()
        hbox = QHBoxLayout()
        layout.addLayout(hbox)
        parentLayout.addLayout(layout)
        hbox.addWidget(QLabel('微信商品列表'))
        self.refresh_wechat_btn = refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(lambda: self.wechat_loader.start())
        hbox.addWidget(refresh_btn)

        self.wechat_list = QListWidget()

        self.wechat_list.doubleClicked.connect(
            lambda: self.openItemWindow(self.wechat_search_items[self.wechat_list.currentIndex().row()]))
        layout.addWidget(self.wechat_list)

        self.wechat_total_label = QLabel()
        layout.addWidget(self.wechat_total_label)

    def changeAutoUpdate(self, index: int):
        LocalStore.Set(key='auto_update_selected', value=index)
        self.__autoUpdate_index = index

    def initAutoUpdateTimer(self):
        self.__last_update_time = 0
        self.timer = QTimer()

        def worker():
            is_loading = self.is_loading_youzan or self.is_loading_wechat
            hour = 1000 * 3600 * [0, 1, 2, 4, 8, 12, 24][self.__autoUpdate_index]
            last = time.time() - self.__last_update_time
            doit = not is_loading and 0 < hour <= last
            print('auto timer',
                  {'loading_youzan': self.is_loading_youzan, 'loading_wechat': self.is_loading_wechat, 'hour': hour,
                   'last': last, 'do it': doit})
            if not doit:
                return
            print('开始自动更新')

            self.auto_update_signal.emit()
            self.statusBar().showMessage('最后自动更新时间：' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            self.__last_update_time = time.time()

        self.timer.timeout.connect(worker)
        self.timer.setInterval(10000)
        self.timer.setSingleShot(False)
        print('timer start')
        self.timer.start()

    def searchItem(self, type: str = None):
        if type == 'youzan':
            list: QListWidget = self.youzan_list
            items = self.youzan_items
            search_items = self.youzan_search_items
            total_label = self.youzan_total_label
        elif type == 'wechat':
            list: QListWidget = self.wechat_list
            items = self.wechat_items
            search_items = self.wechat_search_items
            total_label = self.wechat_total_label
        else:
            self.searchItem('wechat')
            self.searchItem('youzan')
            return

        list.clear()
        search_items.clear()
        search_text = self.search_input.text().strip()
        # print('搜索', search_text)
        if len(search_text) == 0:
            search_items.extend(items)
        else:
            for item in items:
                if str.find(item.title, search_text) == -1:
                    continue
                search_items.append(item)

        search_items.sort(key=lambda item: item.title)

        for item in search_items:
            list.addItem(item.title)
        total_label.setText('总共：{}'.format(len(search_items)))

    def openItemWindow(self, item):
        if item in self.item_windows:
            window: QMainWindow = self.item_windows[item]
            window.show()
            window.raise_()
            window.setFocus()
            return

        window = ItemWindow(item=item)
        self.item_windows[item] = window
        window.show()

    # 选择商品导入到微信
    def exportToWeChat(self):
        if self.wechat_loader.isRunning() or self.youzan_loader.isRunning():
            return QMessageBox.information(None, '出现错误', '正在读取数据，请稍候再试')

        if len(self.youzan_list.selectedIndexes()) is 0:
            return QMessageBox.information(None, '出现错误', '请选择要导入到微信的有赞商品，可以多选')

        if len(self.wechat_categories_list.selectedIndexes()) is 0:
            return QMessageBox.information(None, '出现错误', '请选择微信商品分类，单选')
        app_id = self.wechat_app_id_input.text()

        if len(app_id) is 0:
            QMessageBox.information(None, '出现错误', '请填写小程序App ID')
            return self.wechat_app_id_input.setFocus()

        category = WeChatItemCategories[self.wechat_categories_list.currentRow()]
        isBookCategory = category == '图书'

        # 导入到微信的情况
        load = []
        ignore = []

        for index in self.youzan_list.selectedIndexes():
            item: YouZanItem = self.youzan_search_items[index.row()]
            item.category = category
            if isBookCategory:
                book_dialog = BookDialog(parent=self, item=item)
                res = book_dialog.exec()
                if res == QDialog.Rejected:
                    ignore.append([item.title, '取消输入图书信息，不上传这本书'])
                    continue
                book = book_dialog.getValue()
                item.book = book
            load.append(item)

        if len(load) == 0:
            QMessageBox.information(None, '没有任务', '没有任务')
            return

        dialog: ProcessDialog = ProcessDialog(app_id=app_id, load=load, ignore=ignore)
        dialog.exec()
        self.wechat_loader.start()

    # 一键更新 自动更新
    def oneKeyUpdateWeChat(self, is_auto: bool = False):

        if self.wechat_loader.isRunning() or self.youzan_loader.isRunning():
            return

        app_id = self.wechat_app_id_input.text()

        if is_auto:
            wechat_items = self.wechat_items
        else:
            wechat_items = self.wechat_search_items

        load = []
        ignore = []
        for wc_item in wechat_items:
            find_item: YouZanItem = None
            for yz_item in self.youzan_items:
                if wc_item.id == yz_item.id:
                    find_item = yz_item
                    break
            if find_item is None:  # 找不到有赞对应的商品，微信商品库存设置为0
                if wc_item.on_sale:
                    wc_item.stock = 0
                    wc_item.on_sale = False
                    load.append(wc_item)
                else:
                    ignore.append([wc_item.title, '有赞不存在对应的商品，微信已下架，不处理'])
            else:  # 读取 有赞商品信息 再 更新到 微信
                category = wc_item.official_category_list[0]['category_name']
                find_item.category = category
                # if category == '图书':
                #     find_item.book = wc_item.book
                load.append(find_item)
        # print('wait', {'微信商品总数': len(self.wechat_items), 'upload': upload, 'load': load})

        if len(load) == 0:
            QMessageBox.information(None, '没有任务', '没有任务')
            return

        dialog = ProcessDialog(app_id=app_id, load=load, ignore=ignore, auto_close=is_auto)
        if dialog.exec() == QDialog.Rejected:
            print('停止任务')

        self.wechat_loader.start()
