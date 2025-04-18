import os
import sys

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QFrame, QSizeGrip
)


class FramelessWindow(QWidget):
    def __init__(self, content_widget: QWidget):
        super().__init__()
        self.title_bar = None  # For navbar dragging
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setObjectName("MainWindow")
        self._old_pos = None

        self.init_ui(content_widget)
        self.load_styles()

    def load_styles(self):
        """Loads the app's CSS from gui_styles.qss."""
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled .exe
                base_path = sys._MEIPASS
            else:
                # Running from source
                base_path = os.path.dirname(os.path.abspath(__file__))

            qss_path = os.path.join(base_path, "gui_styles.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        except Exception as e:
            print(f"[Style Load Error] {e}")

    def init_ui(self, content_widget):
        # Title bar
        title_bar = QFrame()
        self.title_bar = title_bar
        self.title_bar.installEventFilter(self)
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(36)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(8, 4, 8, 4)
        title_layout.setSpacing(4)

        # App title
        self.title = QLabel("Software Updater")
        self.title.setObjectName("Title")
        self.title.setStyleSheet("color: white;")

        # Minimize button
        self.btn_minimize = QPushButton("–")
        self.btn_minimize.setFixedSize(24, 24)
        self.btn_minimize.clicked.connect(self.showMinimized)

        # Maximize button
        self.btn_maximize = QPushButton("⛶")
        self.btn_minimize.setFixedSize(24, 24)
        self.btn_maximize.clicked.connect(self.toggle_maximize_restore)

        # Close button
        self.btn_close = QPushButton("✕")
        self.btn_minimize.setFixedSize(24, 24)
        self.btn_close.clicked.connect(self.close)

        # Title layout setup
        title_layout.addWidget(self.title)
        title_layout.addStretch()
        title_layout.addWidget(self.btn_minimize)
        title_layout.addWidget(self.btn_maximize)
        title_layout.addWidget(self.btn_close)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_bar.setLayout(title_layout)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.addWidget(title_bar)
        content_widget.setObjectName("ContentArea")
        main_layout.addWidget(content_widget)

        self.setLayout(main_layout)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._old_pos:
            delta = event.globalPosition().toPoint() - self._old_pos
            self.move(self.pos() + delta)
            self._old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._old_pos = None

    def toggle_maximize_restore(self):
        """Switches the minimize/maximize button between its states."""
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("⛶")
        else:
            self.showMaximized()
            self.btn_maximize.setText("❐")

    def eventFilter(self, obj, event):
        """Handles the dragging of the app window."""
        if obj == self.title_bar:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._old_pos = event.globalPosition().toPoint()
            elif event.type() == QEvent.Type.MouseMove and self._old_pos:
                delta = event.globalPosition().toPoint() - self._old_pos
                self.move(self.pos() + delta)
                self._old_pos = event.globalPosition().toPoint()
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._old_pos = None
        return super().eventFilter(obj, event)
