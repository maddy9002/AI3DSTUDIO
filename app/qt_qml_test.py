import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtQml import qmlRegisterType

from ui.webcam_view import WebcamView


qmlRegisterType(
    WebcamView,
    "AI3D",
    1,
    0,
    "WebcamView"
)


app = QApplication(sys.argv)

window = QQuickWidget()
window.resize(1400, 900)
window.setWindowTitle("AI3D QML Test")

qml_path = r"C:\Users\dell\OneDrive\Desktop\AI3DSTUDIO\app\ui\qml\Main.qml"

window.setSource(
    QUrl.fromLocalFile(qml_path)
)

if window.status() == QQuickWidget.Error:
    print("QML ERRORS:")
    for error in window.errors():
        print(error)

window.show()

sys.exit(app.exec())