from PyQt6.QtWidgets import QMainWindow, QFileDialog, QWidget, QListWidgetItem
from att2 import Ui_Form as Ui_AttachmentListItem
from edit import Ui_MainWindow as Ui_MessageEditor
from csv import DictReader
from PyQt6 import QtCore, QtGui
from email.message import EmailMessage
from email.utils import formataddr
import smtplib
from mimetypes import guess_type
import ssl


class MessageEditor(QMainWindow, Ui_MessageEditor):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.send_button.clicked.connect(self.send)
        with open("accounts.csv", "r") as f:
            r = list(DictReader(f, fieldnames=["addr", "name", "smtpserv", "smtpport", "smtpsec",
                                               "smtpauth", "smtpuname", "smtppass", "imapserv", "imapport",
                                               "imapsec", "imapauth", "imapuname", "imappass"]))
        if not r:
            self.show_add_account()
            self.close()
            return
        for i in r:
            self.froma.addItem(f"{i['name']} ({i['addr']})", i)
        self.text.cursorPositionChanged.connect(self.update_tools)
        self.font.currentFontChanged.connect(self.set_font)
        self.font_weight.valueChanged.connect(self.set_font_weight)
        self.font_size.valueChanged.connect(self.set_font_size)
        self.italic.clicked.connect(self.text.setFontItalic)
        self.underline.clicked.connect(self.text.setFontUnderline)
        self.align_left.clicked.connect(self.set_align_left)
        self.align_center.clicked.connect(self.set_align_center)
        self.align_right.clicked.connect(self.set_align_right)
        self.align_justify.clicked.connect(self.set_align_justify)
        self.attachment.clicked.connect(self.add_attachment)

    def add_attachment(self):
        try:
            p = QFileDialog.getOpenFileName()[0]
            if not p:
                return
            item = QListWidgetItem(self.attachment_list)
            item.setSizeHint(QtCore.QSize(100, 32))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, p)
            self.attachment_list.addItem(item)
            self.attachment_list.setItemWidget(item, AttachmentListItem(self.attachment_list, item, p.rsplit("/", 1)[1]))
        except Exception as e:
            print(type(e), e)

    def set_font(self, font):
        self.text.setFontFamily(font.family())

    def set_font_weight(self):
        self.text.setFontWeight(self.font_weight.value())

    def set_font_size(self):
        self.text.setFontPointSize(self.font_size.value())

    def set_align_left(self, checked):
        try:
            if checked:
                self.text.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
                self.align_center.setChecked(False)
                self.align_right.setChecked(False)
                self.align_justify.setChecked(False)
        except Exception as e:
            print(type(e), e)

    def set_align_center(self, checked):
        try:
            if checked:
                self.text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.align_left.setChecked(False)
            else:
                self.text.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
                self.align_left.setChecked(True)
            self.align_right.setChecked(False)
            self.align_justify.setChecked(False)
        except Exception as e:
            print(type(e), e)

    def set_align_right(self, checked):
        try:
            if checked:
                self.text.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
                self.align_left.setChecked(False)
            else:
                self.text.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
                self.align_left.setChecked(True)
            self.align_center.setChecked(False)
            self.align_justify.setChecked(False)
        except Exception as e:
            print(type(e), e)

    def set_align_justify(self, checked):
        if checked:
            self.text.setAlignment(QtCore.Qt.AlignmentFlag.AlignJustify)
            self.align_left.setChecked(False)
        else:
            self.text.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            self.align_left.setChecked(True)
        self.align_center.setChecked(False)
        self.align_right.setChecked(False)

    def update_tools(self):
        self.italic.setChecked(self.text.fontItalic())
        self.underline.setChecked(self.text.fontUnderline())
        self.font_weight.setValue(self.text.fontWeight())
        self.font.setCurrentFont(QtGui.QFont(self.text.fontFamily()))
        
        mask = self.text.alignment() & QtCore.Qt.AlignmentFlag.AlignHorizontal_Mask
        self.align_left.setChecked(mask == QtCore.Qt.AlignmentFlag.AlignLeft)
        self.align_center.setChecked(mask == QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.align_right.setChecked(mask == QtCore.Qt.AlignmentFlag.AlignRight)
        self.align_justify.setChecked(mask == QtCore.Qt.AlignmentFlag.AlignJustify)

    def send(self):
        account = self.froma.currentData()
        message = EmailMessage()
        message["Subject"] = self.subject.text()
        message["From"] = formataddr((account["name"], account["addr"]))
        message["To"] = self.to.text()
        message.set_content(self.text.toPlainText())
        message.add_alternative(self.text.toHtml(), subtype="html")
        for i in range(self.attachment_list.count()):
            data = self.attachment_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole)
            mime_type = guess_type(data)[0]
            maintype, subtype = (mime_type.split("/", 1) if mime_type else ("application", "octet-stream"))
            filename = data.rsplit("/", 1)[1]
            with open(data, "rb") as f:
                message.add_attachment(
                    f.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=filename
                )
        if account["smtpsec"] == "SSL/TLS":
            server = smtplib.SMTP_SSL(account["smtpserv"], account["smtpport"], context=ssl.create_default_context())   
        elif account["smtpsec"] == "STARTTLS":
            server = smtplib.SMTP(account["smtpserv"], account["smtpport"])
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(account["smtpserv"], account["smtpport"])
        server.ehlo()
        server.login(account["smtpuname"], account["smtppass"])
        server.send_message(message)
        server.quit()
        self.close()


class AttachmentListItem(QWidget, Ui_AttachmentListItem):
    def __init__(self, list_widget, item, filename):
        super().__init__()
        self.setupUi(self)
        self.list_widget = list_widget
        self.item = item
        self.label.setText(filename)
        self.pushButton.clicked.connect(self.delete)

    def delete(self):
        self.list_widget.takeItem(self.list_widget.row(self.item))
