import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QTextEdit, QLineEdit, QPushButton,
)
from PySide6.QtCore import Qt, QObject, Signal, QThread
from PySide6.QtGui import QTextCursor
from backend import chat_with_ai

# ---------- Worker ----------
class Worker(QObject):
    finished = Signal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        reply = chat_with_ai(self.prompt)
        self.finished.emit(reply)


# ---------- UI ----------
class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local AI Chatbot")
        self.resize(700, 550)

        layout = QVBoxLayout(self)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message...")
        self.input.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        layout.addWidget(self.chat_area)
        layout.addWidget(self.input)
        layout.addWidget(self.send_btn)

    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return

        self.input.clear()
        self.chat_area.append(f"<b>You:</b> {text}")
        self.chat_area.append("<i>Bot is thinking...</i>")

        self.thread = QThread()
        self.worker = Worker(text)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.display_response)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def display_response(self, reply):
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)

        # delete last line ("Bot is thinking...")
        cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()

        self.chat_area.append(f"<b>Bot:</b> {reply}\n")


# ---------- Dark Theme ----------
def apply_dark_theme(app):
    app.setStyle("Fusion")
    app.setStyleSheet("""
        /* Base */
        QWidget {
            background-color: #0f172a;       /* deep blue-black */
            color: #e5e7eb;
            font-size: 14px;
            font-family: Segoe UI, Inter, Arial;
        }

        /* Chat area */
        QTextEdit {
            background-color: #020617;       /* near-black */
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 10px;
            selection-background-color: #2563eb;
        }

        /* Input box */
        QLineEdit {
            background-color: #020617;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 8px;
        }

        QLineEdit:focus {
            border: 1px solid #3b82f6;       /* blue focus ring */
        }

        /* Buttons */
        QPushButton {
            background-color: #1e40af;       /* muted blue */
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            color: #e5e7eb;
        }

        QPushButton:hover {
            background-color: #2563eb;
        }

        QPushButton:pressed {
            background-color: #1d4ed8;
        }

        /* Scrollbar */
        QScrollBar:vertical {
            background: #020617;
            width: 10px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #334155;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover {
            background: #475569;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """)



# ---------- Main ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    window = ChatWindow()
    window.show()

    sys.exit(app.exec())