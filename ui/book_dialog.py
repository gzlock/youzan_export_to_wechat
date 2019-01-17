from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from services.localstore import LocalStore


class BookDialog(QDialog):
    def __init__(self, item, parent=None):
        QDialog.__init__(self, parent=parent)
        self.item = item
        self.publisher = ''
        self.author = ''
        self.desc = ''
        self.load_db()
        self.ui()

    def load_db(self):
        print('item_' + self.item.id)
        data = LocalStore.Get('item_' + self.item.id)
        if data is not None:
            self.publisher = data['publisher']
            self.author = data['author']
            self.desc = data['desc']

    def accept(self):
        self.__toValue()
        LocalStore.Set('item_' + self.item.id, self.getValue())
        super(BookDialog, self).accept()

    def __toValue(self):
        self.publisher = self.__publisher.text()
        self.desc = self.__desc.toPlainText()
        self.author = self.__author.text()

    def ui(self):
        title = '输入 ' + self.item.title + ' 的图书信息'
        self.setWindowTitle(title)
        grid: QGridLayout = QGridLayout()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))
        layout.addLayout(grid)
        self.setLayout(layout)

        grid.addWidget(QLabel('出版社'), 0, 0)
        self.__publisher = QLineEdit(self.publisher)
        grid.addWidget(self.__publisher, 0, 1)

        grid.addWidget(QLabel('作者'), 1, 0)
        self.__author = QLineEdit(self.author)
        grid.addWidget(self.__author, 1, 1)

        grid.addWidget(QLabel('简介'), 2, 0)
        self.__desc = QTextEdit(self.desc)
        grid.addWidget(self.__desc, 2, 1)

        buttonBox = QDialogButtonBox()
        buttonBox.setOrientation(Qt.Horizontal)  # 设置为水平方向
        buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)  # 确定和取消两个按钮
        buttonBox.button(QDialogButtonBox.Ok).setText('确认')
        buttonBox.button(QDialogButtonBox.Cancel).setText('取消')

        buttonBox.accepted.connect(self.accept)  # 确定
        buttonBox.rejected.connect(self.reject)  # 取消
        layout.addWidget(buttonBox)
        layout.addWidget(QLabel('按取消将会跳过这本书，即不上传这本书'))

    def getValue(self):
        self.__toValue()
        return {'publisher': self.publisher, 'author': self.author, 'desc': self.desc}
