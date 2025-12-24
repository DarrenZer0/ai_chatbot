import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QPushButton,
    QTextEdit, QLineEdit, QLabel, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QDialog, QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPainterPath

from persona import Persona
from persona_storage import load_persona, save_persona
from backend import chat_with_ai, set_persona


PERSONA_DIR = "personas"
AVATAR_DIR = "avatars"

SIDEBAR_ITEM_HEIGHT = 56
AVATAR_SIZE = 36


# =============================
# Avatar utilities
# =============================
def make_circular_pixmap(image_path: str, size: int) -> QPixmap:
    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        return QPixmap()

    pixmap = pixmap.scaled(
        size,
        size,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation
    )

    result = QPixmap(size, size)
    result.fill(Qt.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)

    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)

    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    return result


# =============================
# Sidebar character widget
# =============================
class CharacterItemWidget(QWidget):
    def __init__(self, persona: Persona):
        super().__init__()

        avatar_label = QLabel()
        avatar_label.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)

        if persona.avatar_path and os.path.exists(persona.avatar_path):
            avatar_label.setPixmap(
                make_circular_pixmap(persona.avatar_path, AVATAR_SIZE)
            )

        name_label = QLabel(persona.name)
        name_label.setStyleSheet("font-weight: 600;")

        subtitle = QLabel("Click to chat")
        subtitle.setStyleSheet(
            "color: #8b949e; font-size: 11px;"
        )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.addWidget(name_label)
        text_layout.addWidget(subtitle)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)
        layout.addWidget(avatar_label)
        layout.addLayout(text_layout)


# =============================
# Persona Editor Dialog
# =============================
class PersonaEditor(QDialog):
    def __init__(self, parent=None, persona=None):
        super().__init__(parent)
        self.setWindowTitle("Character Editor")
        self.setMinimumWidth(420)

        self.avatar_path = persona.avatar_path if persona else ""

        self.name_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.avatar_label = QLabel("No avatar selected")

        avatar_btn = QPushButton("Choose Avatar")
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        avatar_btn.clicked.connect(self.choose_avatar)
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Character Name"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Personality / System Prompt"))
        layout.addWidget(self.desc_input)
        layout.addWidget(self.avatar_label)

        btns = QHBoxLayout()
        btns.addWidget(avatar_btn)
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)

        layout.addLayout(btns)

        if persona:
            self.name_input.setText(persona.name)
            self.desc_input.setText(persona.description)
            self.avatar_label.setText(persona.avatar_path or "No avatar selected")

    def choose_avatar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Avatar", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            os.makedirs(AVATAR_DIR, exist_ok=True)
            dest = os.path.join(AVATAR_DIR, os.path.basename(path))
            if path != dest:
                with open(path, "rb") as s, open(dest, "wb") as d:
                    d.write(s.read())
            self.avatar_path = dest
            self.avatar_label.setText(dest)

    def get_persona(self):
        return Persona(
            name=self.name_input.text().strip(),
            description=self.desc_input.toPlainText().strip(),
            avatar_path=self.avatar_path
        )


# =============================
# Main Window
# =============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Character Chat")
        self.resize(1100, 650)

        self.current_persona = None

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(260)
        self.sidebar.itemClicked.connect(self.select_persona)
        self.sidebar.setSpacing(4)

        add_btn = QPushButton("+ Add Character")
        edit_btn = QPushButton("Edit")
        del_btn = QPushButton("Delete")

        add_btn.clicked.connect(self.add_persona)
        edit_btn.clicked.connect(self.edit_persona)
        del_btn.clicked.connect(self.delete_persona)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("CHARACTERS")
        title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #8b949e;
        """)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.sidebar)
        sidebar_layout.addWidget(add_btn)
        sidebar_layout.addWidget(edit_btn)
        sidebar_layout.addWidget(del_btn)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)

        # Chat area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)

        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_area)
        chat_layout.addLayout(input_layout)

        chat_widget = QWidget()
        chat_widget.setLayout(chat_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar_widget)
        splitter.addWidget(chat_widget)
        splitter.setSizes([240, 860])

        self.setCentralWidget(splitter)

        self.load_personas()

    # =========================
    # Personas
    # =========================
    def load_personas(self):
        self.sidebar.clear()
        os.makedirs(PERSONA_DIR, exist_ok=True)

        for filename in os.listdir(PERSONA_DIR):
            if not filename.endswith(".json"):
                continue

            path = os.path.join(PERSONA_DIR, filename)
            persona = load_persona(path)

            item = QListWidgetItem()
            item.setSizeHint(QSize(0, SIDEBAR_ITEM_HEIGHT))
            item.setData(Qt.UserRole, persona.name)

            widget = CharacterItemWidget(persona)

            self.sidebar.addItem(item)
            self.sidebar.setItemWidget(item, widget)

    def select_persona(self, item):
        name = item.data(Qt.UserRole)
        path = os.path.join(PERSONA_DIR, f"{name}.json")

        self.current_persona = load_persona(path)
        set_persona(self.current_persona)

        self.chat_area.clear()
        self.append_message(
            self.current_persona.name,
            "Ready to chat.",
            self.current_persona.avatar_path
        )

    def add_persona(self):
        dlg = PersonaEditor(self)
        if dlg.exec():
            persona = dlg.get_persona()
            if not persona.name:
                return
            save_persona(persona, os.path.join(PERSONA_DIR, f"{persona.name}.json"))
            self.load_personas()

    def edit_persona(self):
        item = self.sidebar.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        path = os.path.join(PERSONA_DIR, f"{name}.json")
        persona = load_persona(path)
        dlg = PersonaEditor(self, persona)
        if dlg.exec():
            save_persona(dlg.get_persona(), path)
            self.load_personas()

    def delete_persona(self):
        item = self.sidebar.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        os.remove(os.path.join(PERSONA_DIR, f"{name}.json"))
        self.load_personas()
        self.chat_area.clear()

    # =========================
    # Chat
    # =========================
    def append_message(self, sender, text, avatar_path=None, is_user=False):
        avatar_html = ""
        if avatar_path and os.path.exists(avatar_path):
            avatar_html = f"""
        <img src="{avatar_path}" width="32" height="32"
             style="border-radius:16px;">
        """

        if is_user:
            html = f"""
        <table width="100%" cellspacing="0" cellpadding="6">
            <tr>
                <td align="right" width="100%">
                    <div style="color:#58a6ff; font-weight:600;">You</div>
                    <div>{text}</div>
                </td>
                <td align="right">
                    {avatar_html}
                </td>
            </tr>
        </table>
        """
        else:
            html = f"""
        <table width="100%" cellspacing="0" cellpadding="6">
            <tr>
                <td align="left" width="40">
                    {avatar_html}
                </td>
                <td align="left" width="100%">
                    <div style="color:#7ee787; font-weight:600;">{sender}</div>
                    <div>{text}</div>
                </td>
            </tr>
        </table>
        """

        self.chat_area.append(html)


    def send_message(self):
        if not self.current_persona:
            QMessageBox.warning(self, "No character", "Select a character first.")
            return

        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.append_message("You", text, is_user=True)

        reply = chat_with_ai(text)
        self.append_message(
            self.current_persona.name,
            reply,
            avatar_path=self.current_persona.avatar_path
        )


# =============================
# Theme
# =============================
def apply_theme(app):
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget {
            background-color: #0d1117;
            color: #c9d1d9;
            font-size: 14px;
        }

        QListWidget {
            background-color: #0b0f14;
            border: none;
        }

        QListWidget::item:selected {
            background-color: #161b22;
        }

        QTextEdit {
            background-color: #0b0f14;
            border: none;
            padding: 10px;
        }

        QLineEdit {
            background-color: #161b22;
            border: 1px solid #30363d;
            padding: 8px;
            border-radius: 6px;
        }

        QPushButton {
            background-color: #1f6feb;
            border-radius: 6px;
            padding: 6px 10px;
        }

        QPushButton:hover {
            background-color: #388bfd;
        }
    """)


# =============================
# Entry
# =============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())