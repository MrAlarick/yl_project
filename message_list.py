from PyQt6.QtWidgets import QWidget, QListWidget
from PyQt6 import QtCore, QtGui
from msg import Ui_Form as Ui_MessageListItem


class MessageList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QListWidget::item:selected {background: transparent;color: inherit;}QListWidget::item:hover {background: transparent;}")
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.itemClicked.connect(self.select_message)

    def select_message(self, item):
        for i in range(self.count()):
            self.itemWidget(self.item(i)).set_selected(False)
        self.itemWidget(item).set_selected(True)


class MessageListItem(QWidget, Ui_MessageListItem):
    def __init__(self, message, con):
        super().__init__()
        self.setupUi(self)
        self.label_2.setText(message["date"])
        self.label_2.adjustSize()
        text = QtGui.QFontMetrics(self.label_3.font()).elidedText(message["subject"],
                                                       QtCore.Qt.TextElideMode.ElideRight,
                                                       230)
        self.label_3.adjustSize()
        self.label_3.setText(text)
        text = QtGui.QFontMetrics(self.label.font()).elidedText(f"{message['name']} <{message['from']}>",
                                         QtCore.Qt.TextElideMode.ElideRight, 130)
        self.label.setText(text)
        self.label.adjustSize()
        self.setStyleSheet("""
        #frame {
                border: 1px solid #606060;
                border-radius: 5px;
                background-color: #202020;
        }
        #frame:hover {
                background-color:rgb(95, 95, 95);
                border: 1px solid #606060;
                border-radius: 5px;
        }
        """)

    def set_selected(self, f):
        if f:
            self.setStyleSheet("""
            #frame {
                    border: 1px solid #606060;
                    border-radius: 5px;
                    background-color: #00aaff;
            }
            """)
        else:
            self.setStyleSheet("""
            #frame {
                    border: 1px solid #606060;
                    border-radius: 5px;
                    background-color: #202020;
            }
            #frame:hover {
                    background-color:rgb(95, 95, 95);
                    border: 1px solid #606060;
                    border-radius: 5px;
            }
            """)
