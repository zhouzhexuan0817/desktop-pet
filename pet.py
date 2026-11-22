# -*- coding: utf-8 -*-
"""透明桌面小狗：PyQt5 + QtWebEngine 实现。"""

import json
import os
import random
import sys
from pathlib import Path

# 让 Qt WebEngine 在 Windows 上稳定地呈现透明背景。
# 这两个参数必须在导入 QtWebEngine 之前设置。
_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
for _flag in ("--enable-transparent-visuals", "--disable-gpu"):
    if _flag not in _flags.split():
        _flags = f"{_flags} {_flag}".strip()
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = _flags

from PyQt5.QtCore import QPoint, Qt, QUrl
from PyQt5.QtGui import QCursor
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMenu, QVBoxLayout, QWidget


class InputOverlay(QWidget):
    """覆盖在网页上方，专门接管鼠标，避免 WebEngine 吞掉拖拽事件。"""

    DRAG_THRESHOLD = 4

    def __init__(self, pet_window):
        super().__init__(pet_window)
        self.pet_window = pet_window

        self._left_down = False
        self._dragging = False
        self._press_global = QPoint()
        self._window_offset = QPoint()

        # 自己不绘制任何东西，只负责接收鼠标。
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._left_down = True
            self._dragging = False
            self._press_global = event.globalPos()
            self._window_offset = event.globalPos() - self.pet_window.frameGeometry().topLeft()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._left_down and (event.buttons() & Qt.LeftButton):
            moved = event.globalPos() - self._press_global

            if not self._dragging and moved.manhattanLength() >= self.DRAG_THRESHOLD:
                self._dragging = True
                self.pet_window.set_hover(False)
                self.setCursor(Qt.ClosedHandCursor)

            if self._dragging:
                # 用按下时的偏移量移动整个窗口，避免窗口跳动。
                self.pet_window.move(event.globalPos() - self._window_offset)

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._left_down:
            was_dragging = self._dragging

            self._left_down = False
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)

            # 没有发生拖动，才视为一次“点击”。
            if not was_dragging:
                self.pet_window.jump()

            self.pet_window.set_hover(self.rect().contains(event.pos()))
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.pet_window.set_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._dragging:
            self.pet_window.set_hover(False)
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        self.pet_window.show_context_menu(event.globalPos())
        event.accept()


class PetWindow(QWidget):
    WINDOW_WIDTH = 240
    WINDOW_HEIGHT = 240

    GREETINGS = (
        "汪！你好呀～",
        "嗨，今天也要开心鸭！",
        "摇摇尾巴，很高兴见到你！",
        "要不要一起出去玩？",
    )

    def __init__(self):
        super().__init__()

        self._page_ready = False
        self._hovered = False

        self.setWindowTitle("桌面小狗")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        self.view = QWebEngineView(self)
        self.view.setAttribute(Qt.WA_TranslucentBackground, True)
        self.view.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.view.setFocusPolicy(Qt.NoFocus)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)
        self.view.page().setBackgroundColor(Qt.transparent)
        self.view.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)

        # 鼠标事件全部交给这一层处理。
        self.overlay = InputOverlay(self)
        self.overlay.setGeometry(self.rect())
        self.overlay.raise_()

        self.view.loadFinished.connect(self._on_load_finished)

        html_path = Path(__file__).resolve().with_name("index.html")
        self.view.load(QUrl.fromLocalFile(str(html_path)))

        self._move_to_default_position()

    def _on_load_finished(self, ok):
        self._page_ready = bool(ok)
        if not ok:
            print("index.html 加载失败，请检查文件是否与 pet.py 位于同一目录。",
                  file=sys.stderr)
            return

        # 页面加载完成前可能已经有鼠标悬停状态，这里同步一次。
        self._run_js("window.petSetHover(%s);" %
                     ("true" if self._hovered else "false"))

    def _run_js(self, code):
        if self._page_ready:
            self.view.page().runJavaScript(code)

    def set_hover(self, hovered):
        hovered = bool(hovered)
        if self._hovered == hovered:
            return

        self._hovered = hovered
        self._run_js("window.petSetHover(%s);" %
                     ("true" if hovered else "false"))

    def jump(self):
        self._run_js("window.petJump();")

    def greet(self):
        message = random.choice(self.GREETINGS)
        # json.dumps 可以安全地把中文和引号放进 JS 字符串里。
        self._run_js(f"window.showBubble({json.dumps(message)});")

    def show_context_menu(self, global_pos):
        self.set_hover(False)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dedede;
                border-radius: 8px;
                padding: 5px;
                font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                min-width: 104px;
                padding: 7px 18px;
                border-radius: 5px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #f2f2f2;
                color: #111111;
            }
            QMenu::separator {
                height: 1px;
                margin: 4px 8px;
                background-color: #ececec;
            }
        """)

        greet_action = menu.addAction("打个招呼")
        greet_action.triggered.connect(self.greet)
        menu.addSeparator()
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self.quit_app)

        menu.exec_(global_pos)
        menu.deleteLater()

        # 菜单关闭后，如果鼠标仍在小狗窗口上，恢复悬停放大效果。
        cursor_over_window = self.overlay.rect().contains(
            self.overlay.mapFromGlobal(QCursor.pos())
        )
        self.set_hover(cursor_over_window)

    def quit_app(self):
        self._page_ready = False
        QApplication.instance().quit()

    def _move_to_default_position(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return

        area = screen.availableGeometry()
        margin_right = 40
        margin_bottom = 20

        x = area.x() + area.width() - self.width() - margin_right
        y = area.y() + area.height() - self.height() - margin_bottom
        self.move(max(area.x(), x), max(area.y(), y))

    # 某些平台/渲染后端可能把事件交给顶层窗口而不是覆盖层，这里兜底转发。
    def mousePressEvent(self, event):
        self.overlay.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.overlay.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.overlay.mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self.show_context_menu(event.globalPos())

    def enterEvent(self, event):
        self.set_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.set_hover(False)
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 构造函数中第一次 resize 时 overlay 可能还不存在。
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.rect())
            self.overlay.raise_()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.rect())
            self.overlay.raise_()

    def closeEvent(self, event):
        event.accept()
        QApplication.instance().quit()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    app = QApplication(sys.argv)
    app.setApplicationName("桌面小狗")
    app.setQuitOnLastWindowClosed(True)

    pet = PetWindow()
    pet.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
