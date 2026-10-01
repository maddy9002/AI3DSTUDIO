from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtQuick import QQuickPaintedItem


class WebcamView(QQuickPaintedItem):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._image = QImage()

        self.setAntialiasing(False)
        self.setOpaquePainting(True)

    def set_image(self, image):
        if image is None or image.isNull():
            return

        self._image = image
        self.update()

    def paint(self, painter):
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)

        painter.fillRect(
            self.boundingRect(),
            Qt.black
        )

        if self._image.isNull():
            return

        painter.drawImage(
            self.boundingRect(),
            self._image
        )