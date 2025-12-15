from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6 import QtCore


class FolderWidget(QWidget):
    def __init__(self, name, count=None):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)
        label_name = QLabel(f"<b>{name}</b>")
        label_name.setTextFormat(QtCore.Qt.TextFormat.RichText)
        label_name.setStyleSheet("color: #e6e6e6;")
        layout.addWidget(label_name)
        if count is not None:
            label_count = QLabel(f"<span style='color: gray;'>({count})</span>")
            label_count.setTextFormat(QtCore.Qt.TextFormat.RichText)
            layout.addWidget(label_count)
        layout.addStretch(1)
