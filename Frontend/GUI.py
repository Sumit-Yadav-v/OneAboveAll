from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve
from dotenv import dotenv_values
import sys
import os

# ------------------------------
# Environment + Paths (unchanged)
# ------------------------------
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname") or "jarvis"
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

# ------------------------------
# Helper / Backend functions (UNCHANGED logic)
# ------------------------------
def AnswerModifier(Answer):
    # remove empty lines
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["what", "who", "where", "when", "why", "how", "whose", "which",
                      "can you", "could you", "would you", "what's", "who's", "where's",
                      "when's", "why's", "how's"]
    if any(word + " " in new_query for word in question_words):
        if query_words and query_words[0] and query_words[0][0] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words and query_words[0] and query_words[0][0] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    try:
        with open(rf'{TempDirPath}\Mic.data', "w", encoding='utf-8') as file:
            file.write(Command)
    except Exception:
        pass

def GetMicrophoneStatus():
    try:
        with open(rf'{TempDirPath}\Mic.data', "r", encoding='utf-8') as file:
            return file.read()
    except Exception:
        return ""

def SetAssistantStatus(Status):
    try:
        with open(rf'{TempDirPath}\Status.data', "w", encoding='utf-8') as file:
            file.write(Status)
    except Exception:
        pass

def GetAssistantStatus():
    try:
        with open(rf'{TempDirPath}\Status.data', "r", encoding='utf-8') as file:
            return file.read()
    except Exception:
        return ""

def MicButtonInitialed():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def GraphicsDirectoryPath(Filename):
    return rf'{GraphicsDirPath}\{Filename}'

def TempDirectoryPath(Filename):
    return rf'{TempDirPath}\{Filename}'

def ShowTextToScreen(Text):
    try:
        with open(rf'{TempDirPath}\Responses.data', "w", encoding='utf-8') as file:
            file.write(Text)
    except Exception:
        pass

# ------------------------------
# UI - Styled, functionality kept
# ------------------------------
class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()

        # layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(8)

        # QTextEdit: console style
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)

        font = QFont("Consolas", 13)
        self.chat_text_edit.setFont(font)

        # Subtle, dark console stylesheet
        self.chat_text_edit.setStyleSheet("""
            QTextEdit {
                background: rgba(10,12,14,240);
                color: #cfeff4;               /* soft cyan-ish text */
                border-radius: 10px;
                padding: 12px;
                selection-background-color: rgba(100,150,170,120);
            }
        """)

        layout.addWidget(self.chat_text_edit)

        # Jarvis gif on bottom-right inside a glass panel
        gif_panel = QWidget()
        gif_layout = QHBoxLayout(gif_panel)
        gif_layout.setContentsMargins(0, 0, 0, 0)
        gif_layout.addStretch(1)

        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        movie.setScaledSize(QSize(220, 220))
        self.gif_label.setMovie(movie)
        movie.start()

        # subtle glass background for gif area
        self.gif_label.setFixedSize(220, 220)
        gif_container = QWidget()
        gif_container_layout = QVBoxLayout(gif_container)
        gif_container_layout.setContentsMargins(8, 8, 8, 8)
        gif_container_layout.addWidget(self.gif_label, alignment=Qt.AlignRight | Qt.AlignBottom)
        gif_container.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,6);
                border: 1px solid rgba(100,140,160,20);
                border-radius: 8px;
            }
        """)
        gif_layout.addWidget(gif_container, alignment=Qt.AlignRight | Qt.AlignBottom)
        layout.addWidget(gif_panel)

        # status label (right aligned)
        self.label = QLabel("")
        self.label.setStyleSheet("color: #9fcad9; font-size:15px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        # custom scrollbar style (soft, muted blue)
        self.chat_text_edit.setStyleSheet(self.chat_text_edit.styleSheet() + """
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(120,160,180,150);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: transparent;
            }
        """)

        # Timer to read files (keeps logic same)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(120)  # slightly relaxed

    def loadMessages(self):
        global old_chat_message
        try:
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as file:
                messages = file.read()
        except Exception:
            messages = ""

        if not messages:
            return

        if str(old_chat_message) == str(messages):
            return

        self.addMessage(message=messages, color='#cfeff4')
        old_chat_message = messages

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
                messages = file.read()
        except Exception:
            messages = ""
        self.label.setText(messages)

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        fmt = QTextCharFormat()
        block_fmt = QTextBlockFormat()
        block_fmt.setTopMargin(8)
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.setBlockFormat(block_fmt)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)
        # autoscroll to bottom
        self.chat_text_edit.verticalScrollBar().setValue(self.chat_text_edit.verticalScrollBar().maximum())


class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 6, 0, 40)
        content_layout.setSpacing(12)

        # Jarvis gif
        gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        movie.setScaledSize(QSize(520, 520))
        gif_label.setMovie(movie)
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()

        # Mic button (round with glow)
        self.icon_label = QLabel()
        try:
            pixmap = QPixmap(GraphicsDirectoryPath('Mic_on.png'))
        except Exception:
            pixmap = QPixmap()

        new_pixmap = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(120, 120)
        self.icon_label.setAlignment(Qt.AlignCenter)

        # make it round
        self.icon_label.setStyleSheet("""
            QLabel {
                border-radius: 60px;            /* half of 120px */
                background-color: rgba(20, 30, 35, 180);
            }
        """)

        # glow effect
        self.mic_glow = QGraphicsDropShadowEffect(self.icon_label)
        self.mic_glow.setColor(QColor(80, 120, 140, 160))  # muted dull blue
        self.mic_glow.setBlurRadius(0)
        self.mic_glow.setOffset(0, 0)
        self.icon_label.setGraphicsEffect(self.mic_glow)

        # breathing glow animation
        self.glow_anim = QPropertyAnimation(self.mic_glow, b"blurRadius")
        self.glow_anim.setStartValue(0)
        self.glow_anim.setEndValue(25)
        self.glow_anim.setDuration(1400)
        self.glow_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.glow_anim.setLoopCount(-1)

        # mic toggle state
        self.toggled = True
        try:
            status = GetMicrophoneStatus()
            if status.strip().lower() in ["true", "1", "on"]:
                self.toggled = False
            else:
                self.toggled = True
        except Exception:
            self.toggled = True

        self.apply_mic_state(start=True)
        self.icon_label.mousePressEvent = self.toggled_icon

        # Status label
        self.label = QLabel("")
        self.label.setStyleSheet("color: #9fcad9; font-size:16px;")
        self.label.setAlignment(Qt.AlignCenter)

        content_layout.addStretch(1)
        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        content_layout.addStretch(2)

        self.setLayout(content_layout)
        self.setStyleSheet("background-color: rgba(6,8,10,255);")

        # timer to update speech text
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(180)

    def apply_mic_state(self, start=False):
        if self.toggled:
            self.mic_glow.setColor(QColor(80, 120, 140, 170))
            if start or self.glow_anim.state() != QPropertyAnimation.Running:
                self.glow_anim.start()
            try:
                pix = QPixmap(GraphicsDirectoryPath('Mic_on.png')).scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                if not pix.isNull():
                    self.icon_label.setPixmap(pix)
            except Exception:
                pass
            MicButtonInitialed()
        else:
            try:
                self.glow_anim.stop()
            except Exception:
                pass
            self.mic_glow.setBlurRadius(0)
            try:
                pix = QPixmap(GraphicsDirectoryPath('Mic_off.png')).scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                if not pix.isNull():
                    self.icon_label.setPixmap(pix)
            except Exception:
                pass
            MicButtonClosed()


    def apply_mic_state(self, start=False):
        # when mic is active (listening) show glow animation
        if self.toggled:
            # ON -> start glow
            self.mic_glow.setColor(QColor(80, 120, 140, 170))
            if start:
                self.glow_anim.start()
            else:
                if self.glow_anim.state() != QPropertyAnimation.Running:
                    self.glow_anim.start()
            # load 'on' icon if exists
            try:
                pix = QPixmap(GraphicsDirectoryPath('Mic_on.png')).scaled(110, 110)
                if not pix.isNull():
                    self.icon_label.setPixmap(pix)
            except Exception:
                pass
            MicButtonInitialed()
        else:
            # OFF -> stop glow
            try:
                self.glow_anim.stop()
            except Exception:
                pass
            self.mic_glow.setBlurRadius(0)
            try:
                pix = QPixmap(GraphicsDirectoryPath('Mic_off.png')).scaled(110, 110)
                if not pix.isNull():
                    self.icon_label.setPixmap(pix)
            except Exception:
                pass
            MicButtonClosed()

    def toggled_icon(self, event=None):
        self.toggled = not self.toggled
        self.apply_mic_state()

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
                message = file.read()
        except Exception:
            message = ""
        self.label.setText(message)


class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        layout = QVBoxLayout()
        # placeholder label (kept from original)
        label = QLabel("")
        layout.addWidget(label)
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        self.setLayout(layout)
        self.setStyleSheet('background-color: rgba(6,8,10,255);')
        # keep full-screen sizing behaviour similar to original
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)


class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget

    def initUI(self):
        self.setFixedHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Title (muted blue glow)
        title_label = QLabel(f"{(Assistantname).capitalize()} AI")
        title_label.setStyleSheet("""
            QLabel {
                color: #bfe6ee;
                font-size: 18px;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        layout.addWidget(title_label)

        layout.addStretch(1)

        # Home & Chat with glass buttons
        home_button = QPushButton()
        home_icon = QIcon(GraphicsDirectoryPath('Home.png')) if os.path.exists(GraphicsDirectoryPath('Home.png')) else QIcon()
        home_button.setIcon(home_icon)
        home_button.setText(" Home ")
        message_button = QPushButton()
        message_icon = QIcon(GraphicsDirectoryPath("Chats.png")) if os.path.exists(GraphicsDirectoryPath("Chats.png")) else QIcon()
        message_button.setIcon(message_icon)
        message_button.setText(" Chat ")

        for btn in [home_button, message_button]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,6);
                    color: #d8eef3;
                    border: 1px solid rgba(120,160,180,40);
                    padding: 6px 12px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: rgba(100,140,160,24);
                }
            """)

        minimize_button = QPushButton()
        minimize_button.setIcon(QIcon(GraphicsDirectoryPath('Minimize2.png')) if os.path.exists(GraphicsDirectoryPath('Minimize2.png')) else QIcon())
        minimize_button.setFixedSize(36, 36)
        maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath('Maximize.png')) if os.path.exists(GraphicsDirectoryPath('Maximize.png')) else QIcon()
        self.restore_icon = QIcon(GraphicsDirectoryPath('Minimize.png')) if os.path.exists(GraphicsDirectoryPath('Minimize.png')) else QIcon()
        maximize_button.setIcon(self.maximize_icon)
        maximize_button.setFixedSize(36, 36)
        close_button = QPushButton()
        close_button.setIcon(QIcon(GraphicsDirectoryPath('Close.png')) if os.path.exists(GraphicsDirectoryPath('Close.png')) else QIcon())
        close_button.setFixedSize(36, 36)

        for btn in [minimize_button, maximize_button, close_button]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background: rgba(200,40,40,18);
                    border-radius: 6px;
                }
            """)

        # wire up basic actions (keeps original behaviour)
        minimize_button.clicked.connect(self.minimizeWindow)
        maximize_button.clicked.connect(self.maximizeWindow)
        close_button.clicked.connect(self.closeWindow)
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addWidget(minimize_button)
        layout.addWidget(maximize_button)
        layout.addWidget(close_button)

        # draggable
        self.draggable = True
        self.offset = None

        # subtle background
        self.setStyleSheet("background-color: rgba(8,10,12,230);")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(10, 14, 16))
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
        else:
            self.parent().showMaximized()

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    # kept original convenience methods (not used but preserved)
    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
            self.current_screen = message_screen

    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        initial_screen = InitialScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(initial_screen)
            self.current_screen = initial_screen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # keep frameless as original, but retain minimize/maximize/drag in topbar
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)

        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: rgba(6,8,10,255);")

        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)


def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    GraphicalUserInterface()
