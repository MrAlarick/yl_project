from PyQt6.QtWidgets import QWidget, QListWidgetItem
from acc import Ui_Form as Ui_AccountWindow
from PyQt6 import QtCore
from csv import DictReader


class AccountWindow(QWidget, Ui_AccountWindow):
    closed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Настройки аккаунтов")
        with open("accounts.csv", "r") as f:
            self.r = list(DictReader(f, fieldnames=["addr", "name", "smtpserv", "smtpport", "smtpsec",
                                                    "smtpauth", "smtpuname", "smtppass", "imapserv", "imapport",
                                                    "imapsec", "imapauth", "imapuname", "imappass"]))
        if not self.r:
            self.show_add_account()
            self.close()
            return
        for i in self.r:
            item = QListWidgetItem(i["addr"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole, i)
            self.listWidget.addItem(item)
        self.listWidget.itemClicked.connect(self.show_acc)
        self.btn.clicked.connect(self.save)
        self.delete_btn.clicked.connect(self.delete_acc)
        self.show_acc(self.listWidget.item(0))

    def delete_acc(self):
        row = self.listWidget.currentRow()
        del self.r[row]
        with open("accounts.csv", "w") as f:
            w = DictWriter(f, fieldnames=["addr", "name", "smtpserv", "smtpport", "smtpsec",
                                          "smtpauth", "smtpuname", "smtppass", "imapserv", "imapport",
                                          "imapsec", "imapauth", "imapuname", "imappass"])
            w.writerows(self.r)

    def save(self):
        row = self.listWidget.currentRow()
        self.r[row] = {
            "addr": self.address_line.text(),
            "name": self.name_line.text(),
            "smtpserv": self.smtp_server_line.text(),
            "smtpport": self.smtp_port_line.text(),
            "smtpsec": self.smtp_connection_security_box.currentText(),
            "smtpauth": self.smtp_auth_method_box.currentText(),
            "smtpuname": self.smtp_username_line.text(),
            "smtppass": self.smtp_pass_line.text(),
            "imapserv": self.imap_server_line.text(),
            "imapport": self.imap_port_line.text(),
            "imapsec": self.imap_connection_security_box.currentText(),
            "imapauth": self.imap_auth_method_box.currentText(),
            "imapuname": self.imap_username_line.text(),
            "imappass": self.imap_pass_line.text()
        }
        with open("accounts.csv", "w") as f:
            w = DictWriter(f, fieldnames=ACCOUNT_FIELDNAMES)
            w.writerows(self.r)
        self.listWidget.takeItem(row)

    def show_acc(self, item):
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.address_line.setText(data["addr"])
        self.name_line.setText(data["name"])
        self.smtp_server_line.setText(data["smtpserv"])
        self.smtp_port_line.setText(data["smtpport"])
        self.smtp_connection_security_box.setCurrentText(data["smtpsec"])
        self.smtp_auth_method_box.setCurrentText(data["smtpauth"])
        self.smtp_username_line.setText(data["smtpuname"])
        self.smtp_pass_line.setText(data["smtppass"])
        self.imap_server_line.setText(data["imapserv"])
        self.imap_port_line.setText(data["imapport"])
        self.imap_connection_security_box.setCurrentText(data["imapsec"])
        self.imap_auth_method_box.setCurrentText(data["imapauth"])
        self.imap_username_line.setText(data["imapuname"])
        self.imap_pass_line.setText(data["imappass"])

    def closeEvent(self, event):
        super().closeEvent(event)
        self.closed.emit()
