from PyQt6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QFileDialog
from PyQt6 import QtCore
from att import Ui_Form as Ui_AttachmentListItem
from sqlite3 import connect


class AttachmentList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("")
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(0)
        self.itemClicked.connect(self.select_message)
        self.scrollable = False
        
    def select_message(self, item):
        pass

    def update_list(self, attachments):
        self.clear()
        for i in attachments:
            item = QListWidgetItem()
            item.setSizeHint(QtCore.QSize(0, 44))
            self.addItem(item)
            self.setItemWidget(item, AttachmentListItem(i))
        if 44 * len(attachments) > 150:
            self.setFixedHeight(150)
            self.scrollable = True
        else:
            self.setFixedHeight(44 * len(attachments))
            self.scrollable = False

    def wheelEvent(self, event):
        if self.scrollable:
            try:
                super().wheelEvent(event)
            except Exception as e:
                print(type(e), e)

    def keyPressEvent(self, event):
        if self.scrollable:
            super().keyPressEvent(event)

    def scrollTo(self, index, hint):
        if self.scrollable:
            try:
                super().scrollTo(index, hint)
            except Exception as e:
                print(type(e), e)


class AttachmentListItem(QWidget, Ui_AttachmentListItem):
    def __init__(self, att):
        super().__init__()
        self.setupUi(self)
        self.label.setText(att["filename"])
        self.file_id = att["file_id"]
        self.pushButton.clicked.connect(self.download)

    def download(self):
        f = QFileDialog.getSaveFileName(self, "Save")[0]
        try:
            con = connect("attachments.db")
            cur = CON.cursor()
            with open(f, "wb") as w:
                w.write(CUR.execute(f"select data from attachments where id = '{self.file_id}'").fetchone()[0])
        except Exception as e:
            print(type(e), e)
