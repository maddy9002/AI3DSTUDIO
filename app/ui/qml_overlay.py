from PySide6.QtCore import Qt, QUrl
from PySide6.QtQuickWidgets import QQuickWidget


class QMLOverlay(QQuickWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setResizeMode(
            QQuickWidget.SizeRootObjectToView
        )

        self.setClearColor(
            Qt.transparent
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True
        )

        self.setAttribute(
            Qt.WA_AlwaysStackOnTop,
            True
        )

        self.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True
        )

        self.setSource(
            QUrl.fromLocalFile(
                "app/ui/qml/Main.qml"
            )
        )