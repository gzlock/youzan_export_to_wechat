from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import *

from services.item import Item
from services.youzan import *
from youzan.yzclient import YZClient

Style = '''
'''


class ItemWindow(QMainWindow):
    def __init__(self, item):
        super(ItemWindow, self).__init__()
        print('ItemWindow', item)
        self.__fromYouZan = True
        if isinstance(item, YouZanItem):
            self.item: Item = ItemWindow.loadYouZanItemDetail(item)
        else:
            self.item: Item = item
            self.__fromYouZan = False
        self.initUI()

    def initUI(self):
        self.setMinimumSize(400, 400)
        self.resize(400, 400)
        from_str = ['微信商品', '有赞商品'][self.__fromYouZan]

        self.setWindowTitle(['微信：', '有赞：'][self.__fromYouZan] + self.item.title)

        group_box = QGroupBox()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        form = QFormLayout()
        form.setAlignment(Qt.AlignLeft)
        group_box.setLayout(form)
        scroll.setWidget(group_box)
        form.addRow('正在查看' + from_str, None)

        form.addRow('商品ID', QLabel(self.item.id))
        form.addRow('商品名称', QLabel(self.item.title))
        form.addRow('商品销售状态', QLabel(['下架', '在售'][self.item.on_sale]))
        form.addRow('图片数量', QLabel(str(len(self.item.images))))

        # 分类
        if self.__fromYouZan:
            if len(self.item.category_list) == 0:
                form.addRow('有赞商品分类', '⚠️没有设置分类')
            else:
                form.addRow('有赞商品分类', QLabel('->'.join(e['category_name'] for e in self.item.category_list)))
        else:
            form.addRow('微信指定分类', QLabel('->'.join(e['category_name'] for e in self.item.official_category_list)))
            form.addRow('自定义分类', QLabel('->'.join(e['category_name'] for e in self.item.category_list)))

        desc = QLabel()
        desc.setTextFormat(Qt.PlainText)
        desc.setText(self.item.desc)
        desc.setWordWrap(True)
        form.addRow('商品简介', desc)

        form.addRow('商品价格', QLabel(str(self.item.price) + '（单位：分）'))
        form.addRow('商品原价', QLabel(str(self.item.ori_price) + '（单位：分）'))
        form.addRow('商品库存', QLabel(str(self.item.stock)))

        # 图书信息
        if not self.__fromYouZan and self.item.book is not None:
            form.addRow('微信图书 出版社', QLabel(self.item.book['publisher']))
            form.addRow('微信图书 作者', QLabel(self.item.book['author']))
            desc = QLabel()
            desc.setTextFormat(Qt.PlainText)
            desc.setText(self.item.book['desc'])
            desc.setWordWrap(True)
            form.addRow('微信图书 简介', desc)

        form.addRow(' ', None)

        if len(self.item.skus) > 0:
            form.addRow('Sku数据', None)
            i = 1
            for sku in self.item.skus:
                form.addRow('Sku ' + str(i), None)
                if self.__fromYouZan:
                    form.addRow('规格名', QLabel(sku.k_title))
                    form.addRow('规格值', QLabel(sku.v_title))
                else:
                    form.addRow(None, QLabel('微信商品没有Sku名称'))
                form.addRow('ID', QLabel(str(sku.id)))
                form.addRow('库存', QLabel(str(sku.stock)))
                form.addRow('价格', QLabel(str(sku.price) + '（单位：分）'))
                form.addRow('图片数量', QLabel(str(len(sku.images))))
                i += 1
        else:
            form.addRow('Sku数据', None)
            form.addRow(None, QLabel('无'))

    def keyPressEvent(self, e: QKeyEvent):
        key = e.key()
        modifiers = e.modifiers()

        if key == QtCore.Qt.Key_Escape or (modifiers == Qt.ControlModifier and key == Qt.Key_W):
            self.close()

    @staticmethod
    def loadYouZanItemDetail(item: YouZanItem):
        data = YZClient.exec('youzan.item.get', '3.0.0', 'get', {'alias': item.alias, 'item_id': item.id})
        return Item.FromYouZan(data['response']['item'])
