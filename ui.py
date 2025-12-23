import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QPushButton,
    QTextEdit, QLineEdit, QLabel, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QDialog, QListWidgetItem
)
from PySide6.QtCore import Qt

from persona import Persona
from persona_storage import load_persona, save_persona
from backend import chat_with_ai, set_persona


PERSONA_DIR = "personas"
AVATAR_DIR = "avatars"


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
        self.messages = []

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(260)
        self.sidebar.itemClicked.connect(self.select_persona)

        add_btn = QPushButton("+ Add Character")
        edit_btn = QPushButton("Edit")
        del_btn = QPushButton("Delete")

        add_btn.clicked.connect(self.add_persona)
        edit_btn.clicked.connect(self.edit_persona)
        del_btn.clicked.connect(self.delete_persona)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.addWidget(QLabel("Characters"))
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

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(chat_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.load_personas()

    # =========================
    # Personas
    # =========================
    def load_personas(self):
        self.sidebar.clear()
        os.makedirs(PERSONA_DIR, exist_ok=True)

        for file in os.listdir(PERSONA_DIR):
            if file.endswith(".json"):
                self.sidebar.addItem(QListWidgetItem(file[:-5]))

    def select_persona(self, item):
        path = os.path.join(PERSONA_DIR, f"{item.text()}.json")
        self.current_persona = load_persona(path)
        set_persona(self.current_persona)

        self.chat_area.clear()
        self.chat_area.append(
            f"<i>Now chatting as <b>{self.current_persona.name}</b></i>"
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
        path = os.path.join(PERSONA_DIR, f"{item.text()}.json")
        persona = load_persona(path)
        dlg = PersonaEditor(self, persona)
        if dlg.exec():
            save_persona(dlg.get_persona(), path)
            self.load_personas()

    def delete_persona(self):
        item = self.sidebar.currentItem()
        if not item:
            return
        os.remove(os.path.join(PERSONA_DIR, f"{item.text()}.json"))
        self.load_personas()
        self.chat_area.clear()

    # =========================
    # Chat
    # =========================
    def send_message(self):
        if not self.current_persona:
            QMessageBox.warning(self, "No character", "Select a character first.")
            return

        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.chat_area.append(f"<b>You:</b> {text}")

        reply = chat_with_ai(text)

        self.chat_area.append(
            f"<b>{self.current_persona.name}:</b> {reply}"
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
            background-color: #161b22;
            border: 1px solid #30363d;
        }
        QTextEdit {
            background-color: #0d1117;
            border: 1px solid #30363d;
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
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #388bfd;
        }
        QLabel {
            font-weight: bold;
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