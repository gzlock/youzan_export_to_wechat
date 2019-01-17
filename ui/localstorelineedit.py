from PyQt5.QtWidgets import QLineEdit

from services.localstore import LocalStore


class LocalStoreLineEdit(QLineEdit):
    def __init__(self, key: str):
        super(LocalStoreLineEdit, self).__init__()
        self.store_key = key
        self.store_value = LocalStore.Get(key)
        self.setText(self.store_value)

    def focusOutEvent(self, event):
        super(LocalStoreLineEdit, self).focusOutEvent(event)

        if self.text() != self.store_value:
            LocalStore.Set(self.store_key, self.text())

        self.store_value = self.text()
