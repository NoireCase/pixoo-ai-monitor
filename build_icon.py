from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap,QPainter
from PySide6.QtCore import Qt
from PIL import Image
app=QApplication([]);pix=QPixmap(256,256);pix.fill(Qt.GlobalColor.transparent);p=QPainter(pix);QSvgRenderer('assets/app.svg').render(p);p.end();pix.save('assets/app.png')
im=Image.open('assets/app.png');im.save('assets/app.ico',sizes=[(16,16),(20,20),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
