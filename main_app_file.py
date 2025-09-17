# ПРОСТО ТЕСТОВЫЙ КОД

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
import sys


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Мое первое приложение PySide6')
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        button = QPushButton('Нажми меня')
        button.clicked.connect(self.on_click)
        layout.addWidget(button)

        self.setLayout(layout)

    def on_click(self):
        print("Кнопка нажата!")


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
