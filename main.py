from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget,
                             QTreeWidgetItem, QListWidget, QListWidgetItem)
from PyQt6 import QtCore, QtGui
import sys
from csv import DictReader
from os import path
import imaplib
import ssl
from ui import Ui_MainWindow
from PyQt6.QtWebEngineCore import QWebEngineSettings
from sqlite3 import connect
from email.utils import make_msgid
from parse_email import parse_email
from folder_widget import FolderWidget
from message_list import MessageList, MessageListItem
from attachment_list import AttachmentList, AttachmentListItem
from add_account_window import AddAccountWindow
from account_window import AccountWindow
from message_editor import MessageEditor


ACCOUNT_FIELDNAMES = ["addr", "name", "smtpserv", "smtpport", "smtpsec",
                      "smtpauth", "smtpuname", "smtppass", "imapserv", "imapport",
                      "imapsec", "imapauth", "imapuname", "imappass"]

CON = connect("attachments.db")
CUR = CON.cursor()


class MailClient(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.attachment_list = AttachmentList()
        self.verticalLayout.addWidget(self.attachment_list)
        self.setWindowTitle("Alarick mail")
        settings = self.viewer.settings()
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, True)
        self.action_2.triggered.connect(self.show_account)
        self.action_3.triggered.connect(self.show_add_account)
        self.pushButton_5.clicked.connect(self.update_window)
        self.pushButton_4.clicked.connect(self.show_message_editor)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #ddd;
                border: none;
            }
            QTreeWidget::item {
                padding: 4px 6px;
            }
            QTreeWidget::item:selected {
                background-color: #3a3f4b;
                border-radius: 3px;
            }
        """)
        self.viewer.setHtml("""
        <html>
        <head>
        <style>
            body {
                background-color: #121212;
                color: #e0e0e0;
                font-family: "Segoe UI", sans-serif;
                margin: 0;
                padding: 1em;
            }
            a {
                color: #64b5f6;
            }
            /* Hide scrollbar but keep scrolling */
            ::-webkit-scrollbar {
                width: 0px;
                background: transparent;
            }
        </style>
        </head>
        <body></body>
        </html>
        """)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setIndentation(20)
        self.treeWidget.setColumnCount(1)
        self.treeWidget.itemClicked.connect(self.folder_clicked)

        self.messages = []
        self.empty_list = QListWidget()
        self.stack.addWidget(self.empty_list)
        CUR.execute("create table if not exists attachments (id integer primary key autoincrement, data blob, hash text not null, content_type text);")
        CON.commit()
        self.update_window()

    def show_account(self):
        self.setEnabled(False)
        self.account_settings_window = AccountWindow()
        self.account_settings_window.closed.connect(self.update_window)
        self.account_settings_window.show()

    def show_add_account(self):
        self.setEnabled(False)
        self.add_account_window = AddAccountWindow()
        self.add_account_window.closed.connect(self.update_window)
        self.add_account_window.show()

    def show_message_editor(self):
        try:
            self.edit = MessageEditor()
            self.edit.show()
        except Exception as e:
            print(type(e), e)

    def update_window(self):
        self.setEnabled(True)
        if not path.exists("accounts.csv"):
            self.show_add_account()
            return
        with open("accounts.csv", "r") as f:
            r = list(DictReader(f, fieldnames=ACCOUNT_FIELDNAMES))
        if not r:
            self.show_add_account()
            return
        self.treeWidget.clear()
        self.clear_stack()
        self.stack.setCurrentWidget(self.empty_list)
        self.viewer.setHtml("""
        <html>
        <head>
        <style>
            body {
                font-family: "Segoe UI", sans-serif;
                margin: 0;
                padding: 1em;
                background-color: #121212;
                color: #e0e0e0;
            }
            ::-webkit-scrollbar {
                width: 0px;
                background: transparent;
            }
        </style>
        </head>
        <body></body>
        </html>
        """)
        self.label.setText("")
        self.subject_label.setText("")
        self.attachment_list.update_list([])
        self.messages = {}
        for i in r: # account
            port = int(i["imapport"])
            if i["imapsec"] == "SSL/TLS":
                s = 1
            elif i["imapsec"] == "STARTTLS":
                s = 2
            else:
                s = 0
            if i["imapauth"] == "PLAIN":
                a = False
            else:
                a = True
            m = self.fetch(i["addr"], i["imapserv"], port, i["imapuname"],
                           i["imappass"], s, a)
            self.messages[i["addr"]] = {}
            account = QTreeWidgetItem()
            account.setIcon(0, QtGui.QIcon.fromTheme("mail-unread"))
            self.treeWidget.addTopLevelItem(account)
            self.treeWidget.setItemWidget(account, 0, FolderWidget(i["addr"]))
            con = connect("attachments.db")
            if "INBOX" in m:
                inbox = QTreeWidgetItem()
                inbox.setData(0, QtCore.Qt.ItemDataRole.UserRole,
                              (i["addr"], "INBOX"))
                inbox.setIcon(0, QtGui.QIcon.fromTheme("mail-folder-inbox"))
                account.addChild(inbox)
                self.treeWidget.setItemWidget(inbox, 0, FolderWidget("Inbox", len(m["INBOX"])))
            for j in m: # folder
                self.messages[i["addr"]][j] = MessageList()
                for k in m[j]: # message
                    item = QListWidgetItem()
                    item.setSizeHint(QtCore.QSize(250, 75))
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, k)
                    self.messages[i["addr"]][j].addItem(item)
                    self.messages[i["addr"]][j].setItemWidget(item,
                                                              MessageListItem(k, con))
                self.messages[i["addr"]][j].itemClicked.connect(self.show_message)
                self.stack.addWidget(self.messages[i["addr"]][j])
                if j == "INBOX":
                    continue
                elif j.lower() == "trash":
                    trash = QTreeWidgetItem()
                    trash.setData(0, QtCore.Qt.ItemDataRole.UserRole,
                                  (i["addr"], j))
                    trash.setIcon(0, QtGui.QIcon.fromTheme("user-trash"))
                    account.addChild(trash)
                    self.treeWidget.setItemWidget(trash, 0, FolderWidget("Trash"))
                else:
                    folder = QTreeWidgetItem()
                    folder.setData(0, QtCore.Qt.ItemDataRole.UserRole,
                                  (i["addr"], j))
                    account.addChild(folder)
                    self.treeWidget.setItemWidget(folder, 0, FolderWidget(j))
            self.treeWidget.expandAll()

    def folder_clicked(self, item, _):
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if data:
            self.stack.setCurrentWidget(self.messages[data[0]][data[1]])
        else:
            self.stack.setCurrentWidget(self.empty_list)
        self.viewer.setHtml("""
        <html>
        <head>
        <style>
            body {
                font-family: "Segoe UI", sans-serif;
                margin: 0;
                padding: 1em;
                background-color: #121212;
                color: #e0e0e0;
            }
            ::-webkit-scrollbar {
                width: 0px;
                background: transparent;
            }
        </style>
        </head>
        <body></body>
        </html>
        """)
        self.label.setText("")
        self.subject_label.setText("")
        self.attachment_list.update_list([])

    def show_message(self, item):
        message = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.viewer.setHtml(f"""
        <html>
        <head>
        <style>
            body {{
                font-family: "Segoe UI", sans-serif;
                margin: 0;
                padding: 1em;
            }}
            ::-webkit-scrollbar {{
                width: 0px;
                background: transparent;
            }}
        </style>
        </head>
        <body>{message["body"]}</body>
        </html>
        """, QtCore.QUrl.fromLocalFile(path.abspath("") + "/"))
        self.label.setText(f"""<p><b>От: {message["name"]}</b> {message["from"]}</p>
        <p><b>Кому: {message["to"]}</b></p>""")
        self.subject_label.setText(message["subject"])
        self.attachment_list.update_list(message["attachments"])

    def fetch(self, addr, server, port, username, password, encryption, auth_method):
        imap = None
        results = {}
        try:
            print(f"Connecting to {server}")
            self.statusbar.showMessage(f"Connecting to {server}")
            if encryption == 1:
                imap = imaplib.IMAP4_SSL(server, port)
            else:
                imap = imaplib.IMAP4(server, port)
                if encryption == 2:
                    imap.starttls(ssl_context=ssl.create_default_context())
            print(f"Logging in to {addr}")
            self.statusbar.showMessage(f"Logging in to {addr}")
            if auth_method:
                imap.login(username, password)
            else:
                def plain_auth(_):
                    return f"\0{username}\0{password}".encode()
                imap.authenticate("PLAIN", plain_auth)
            print(f"Fetching messages for {addr}")
            self.statusbar.showMessage(f"Fetching messages for {addr}")
            status, mailboxes = imap.list()
            if status != "OK":
                print(f"Failed to fetch messages for {addr}")
                self.statusbar.showMessage(f"Failed to fetch messages for {addr}")
                return
            print(f"Decoding messages for {addr}")
            self.statusbar.showMessage(f"Decoding messages for {addr}")
            for box in mailboxes:
                parts = box.decode().split(' "/" ')
                if len(parts) == 2:
                    folder = parts[1].strip('"')
                else:
                    folder = box.decode().split()[-1].strip('"')
                try:
                    imap.select(f'"{folder}"', readonly=True)
                    status, data = imap.search(None, "ALL")
                    if status != "OK":
                        continue
                    ids = data[0].split()
                    if not ids:
                        continue
                    folder_messages = []
                    for msg_id in ids:
                        status, msg_data = imap.fetch(msg_id, "(RFC822)")
                        if status == "OK":
                            folder_messages.append(parse_email(msg_data[0][1]))
                        results[folder] = folder_messages[::-1]
                except Exception as e:
                    print(f"Error reading {folder} at {addr}", type(e), e)
                    self.statusbar.showMessage(f"Error reading {folder} at {addr}")
            self.statusbar.showMessage(f"")
            return results
        except Exception as e:
            print(f"IMAP error: {e}")
            self.statusbar.showMessage(f"IMAP error: {e}")
            return results
        finally:
            if imap:
                try:
                    imap.logout()
                except:
                    pass

    def clear_stack(self):
        c = True
        while self.stack.count() > 1 or c:
            widget = self.stack.widget(0)
            if widget == self.empty_list:
                c = False
                widget = self.stack.widget(1)
            self.stack.removeWidget(widget)


if __name__ == '__main__':
    def except_hook(exc_type, exc_value, exc_traceback):
        # Print full traceback to console
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        
        # Optional: show a dialog
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        msg.setText("An unexpected error occurred:")
        msg.setDetailedText(tb_str)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()

    # Override the default excepthook
    sys.excepthook = exec
    app = QApplication(sys.argv)
    ex = MailClient()
    ex.show()
    exit_code = app.exec()
    CON.close()
    sys.exit(exit_code)
