"""Screenshot and that kind of stuff."""
import io
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView

class Screenshot(QWebEngineView):
    def __init__(self):
        self.app = QApplication([])
        QWebEngineView.__init__(self)
        self._loaded = False
        self.loadFinished.connect(self._load_finished)

    def capture(self, url):
        self.load(QUrl(url))
        self.wait_load()
        frame = self.page().mainFrame()
        self.page().setViewportSize(frame.contentsSize())
        image = QImage(self.page().viewportSize(), QImage.Format_ARGB32)
        painter = QPainter(image)
        frame.render(painter)
        painter.end()
        print('Saving QImage')
        bio = io.BytesIO()
        image.save(bio)
        return bio

    def wait_load(self):
        while not self._loaded:
            self.app.processEvents()
        self._loaded = False

    def _load_finished(self, result):
        self._loaded = True
