from PyQt6.QtWidgets import QWidget
from csv import DictWriter
from addacc import Ui_Form as Ui_AddAccountWindow
from PyQt6 import QtCore


class AddAccountWindow(QWidget, Ui_AddAccountWindow):
    closed = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn.clicked.connect(self.add_account)

    def add_account(self):
        with open("accounts.csv", "a") as f:
            w = DictWriter(f, fieldnames=["addr", "name", "smtpserv", "smtpport", "smtpsec",
                                          "smtpauth", "smtpuname", "smtppass", "imapserv", "imapport",
                                          "imapsec", "imapauth", "imapuname", "imappass"])
            w.writerow({
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
            })
        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.closed.emit()
