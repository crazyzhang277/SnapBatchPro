import os
import sys
import webbrowser
import cv2
import numpy as np

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QPropertyAnimation,
    QEasingCurve, QPoint, QEvent, QTimer, QRect,
    QObject
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QDialog
)
from PySide6.QtGui import QDoubleValidator, QFont, QIcon, QPixmap, QPainter, QCursor, QGuiApplication


class LogTextWidget(QTextEdit):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.is_auto_scroll = True  # 默认开启自动跟随

        # 监听垂直滚动条的位置变化
        self.verticalScrollBar().valueChanged.connect(self.on_scroll_value_changed)

    # 💡 优化：已删除原本此处的 mousePressEvent。
    # 现在界面的点击收回逻辑已经由主窗口的全局 eventFilter 统一接管，保留此方法会导致事件冲突。

    def wheelEvent(self, event):
        """核心交互 1：监听鼠标滚轮事件（动作判定，零延迟）"""
        if event.angleDelta().y() > 0:
            self.is_auto_scroll = False
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        """核心交互 2：监听键盘按键事件（防护判定）"""
        if event.key() in (Qt.Key_Up, Qt.Key_PageUp, Qt.Key_Home):
            self.is_auto_scroll = False
        super().keyPressEvent(event)

    def on_scroll_value_changed(self, value):
        """核心交互 3：精准控制绝对位置。彻底解决日志拉长后，临界点漂移到中间的 Bug"""
        scrollbar = self.verticalScrollBar()
        max_pos = scrollbar.maximum()
        distance_to_bottom = max_pos - value

        if distance_to_bottom <= 10:
            self.is_auto_scroll = True
        else:
            if scrollbar.isSliderDown():
                self.is_auto_scroll = False


def get_integrated_icon():
    """自绘极简影视图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    font = QFont("Segoe UI Emoji", 42)
    font.setStyleStrategy(QFont.PreferAntialias)
    painter.setFont(font)
    painter.setPen(Qt.black)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "🎬")
    painter.end()

    return QIcon(pixmap)


class VideoWorker(QThread):
    """后台核心业务处理线程"""
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, video_dir, output_dir, target_time):
        super().__init__()
        self.video_dir = video_dir
        self.output_dir = output_dir
        self.target_time = target_time

    def run(self):
        valid_extensions = (".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".webm")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        try:
            video_files = [f for f in os.listdir(self.video_dir) if f.lower().endswith(valid_extensions)]
        except Exception as e:
            self.log_signal.emit(f"❌ 读取文件夹失败: {str(e)}")
            self.finished_signal.emit()
            return

        if not video_files:
            self.log_signal.emit("❌ 错误：未在指定目录中找到任何支持的视频文件！")
            self.finished_signal.emit()
            return

        self.log_signal.emit(f"🚀 找到 {len(video_files)} 个视频，目标截取点: 第 {self.target_time} 秒...")
        self.log_signal.emit("=" * 70)

        success_count = 0
        for video_file in video_files:
            video_path = os.path.join(self.video_dir, video_file)
            base_name = os.path.splitext(video_file)[0]
            output_image_path = os.path.join(self.output_dir, f"{base_name}.jpg")

            cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                self.log_signal.emit(f"[失败] 无法打开: {video_file}")
                continue

            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = cap.get(cv2.CAP_PROP_FPS)

            if fps > 0:
                duration_ms = (total_frames / fps) * 1000
                target_ms = self.target_time * 1000
                if target_ms >= duration_ms:
                    target_ms = max(0.0, duration_ms - 100.0)
                cap.set(cv2.CAP_PROP_POS_MSEC, target_ms)

            ret, frame = cap.read()
            if ret:
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
                res, img_encode = cv2.imencode('.jpg', frame, encode_param)
                # 💡 使用 Python 原生文件流进行“无损写入”，彻底摆脱对 NumPy 特有方法的显式依赖
                with open(output_image_path, 'wb') as f:
                    f.write(img_encode.tobytes())
                self.log_signal.emit(f"[成功] 已提取: {base_name}.jpg")
                success_count += 1
            else:
                self.log_signal.emit(f"[失败] 无法读取指定帧: {video_file}")
            cap.release()

        self.log_signal.emit("=" * 70)
        self.log_signal.emit(f"🎉 全部处理完成！成功提取 {success_count}/{len(video_files)} 个视频。")
        self.log_signal.emit(f"📁 截图已保存至: {self.output_dir}")
        self.finished_signal.emit()


class ModernLineEdit(QLineEdit):
    """支持智能拖拽的固态不透明输入框"""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            local_path = urls[0].toLocalFile()
            self.setText(local_path)


class LuxuryVideoExtractor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.is_dragging = False
        self.is_snapped_left = False
        self.is_snapped_right = False
        self.normal_geometry = None

        self.resize(800, 660)
        self.setMinimumSize(800, 660)
        self.setWindowIcon(get_integrated_icon())
        self.drag_position = QPoint()

        self.init_ui()
        self.update_theme_styles(is_maximized=False)

        self._resize_dir = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self._cursor_overridden = False
        self.BORDER_WIDTH = 13

        # 💡 核心修改：不仅为自身安装，还为所有子控件强制安装事件过滤器，确信不漏掉任何一个点击操作
        self.installEventFilter(self)
        self.setMouseTracking(True)
        for child in self.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)

        # Windows 风格边缘吸附预览
        self.snap_preview = QWidget()
        self.snap_preview.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.snap_preview.setAttribute(Qt.WA_TranslucentBackground)
        self.snap_preview.setAttribute(Qt.WA_ShowWithoutActivating)
        self.snap_preview.setAttribute(Qt.WA_StyledBackground, True)
        self.snap_preview.setStyleSheet("""
            background-color: rgba(6, 182, 212, 50);
            border: 2px solid rgba(34, 211, 238, 220);
            border-radius: 10px;
        """)
        self.snap_preview.hide()

        self.edge_preview_timer = QTimer(self)
        self.edge_preview_timer.setInterval(16)
        self.edge_preview_timer.timeout.connect(self.update_snap_preview)

        self.current_snap_mode = None

        self.preview_geo_anim = QPropertyAnimation(self.snap_preview, b"geometry")
        self.preview_geo_anim.setDuration(180)
        self.preview_geo_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.preview_opacity_anim = QPropertyAnimation(self.snap_preview, b"windowOpacity")
        self.preview_opacity_anim.setDuration(150)

    def get_current_screen_geo(self):
        screen = QGuiApplication.screenAt(QCursor.pos())
        if not screen:
            screen = self.screen()
        return screen.availableGeometry() if screen else None

    def build_snap_preview_geometry(self, screen_geo, mode):
        margin = 8
        if mode == "left":
            return screen_geo.adjusted(margin, margin, -(screen_geo.width() // 2 + margin), -margin)
        elif mode == "right":
            return screen_geo.adjusted(screen_geo.width() // 2 + margin, margin, -margin, -margin)
        elif mode == "top":
            return screen_geo.adjusted(margin, margin, -margin, -margin)
        return None

    def update_snap_preview(self):
        if not self.is_dragging or self.isMaximized():
            if self.current_snap_mode is not None:
                self.current_snap_mode = None
                self.preview_opacity_anim.setStartValue(self.snap_preview.windowOpacity())
                self.preview_opacity_anim.setEndValue(0.0)
                self.preview_opacity_anim.start()
                QTimer.singleShot(150, lambda: self.snap_preview.hide() if self.current_snap_mode is None else None)
            return

        screen_geo = self.get_current_screen_geo()
        if not screen_geo: return

        global_pos = QCursor.pos()
        snap_margin = 40
        mode = None

        if global_pos.x() <= screen_geo.left() + snap_margin:
            mode = "left"
        elif global_pos.x() >= screen_geo.right() - snap_margin:
            mode = "right"
        elif global_pos.y() <= screen_geo.top() + snap_margin:
            mode = "top"

        if mode != self.current_snap_mode:
            self.current_snap_mode = mode

            if mode:
                target_geo = self.build_snap_preview_geometry(screen_geo, mode)
                if target_geo:
                    start_geo = target_geo
                    if mode == "left":
                        start_geo = target_geo.adjusted(0, 50, -target_geo.width() // 4, -50)
                    elif mode == "right":
                        start_geo = target_geo.adjusted(target_geo.width() // 4, 50, 0, -50)
                    elif mode == "top":
                        start_geo = target_geo.adjusted(80, 0, -80, -target_geo.height() // 4)

                    self.snap_preview.setGeometry(start_geo)
                    self.snap_preview.setWindowOpacity(0.0)
                    self.snap_preview.show()
                    self.snap_preview.raise_()

                    self.preview_geo_anim.setStartValue(start_geo)
                    self.preview_geo_anim.setEndValue(target_geo)
                    self.preview_opacity_anim.setStartValue(0.0)
                    self.preview_opacity_anim.setEndValue(1.0)

                    self.preview_geo_anim.start()
                    self.preview_opacity_anim.start()
            else:
                self.preview_opacity_anim.setStartValue(self.snap_preview.windowOpacity())
                self.preview_opacity_anim.setEndValue(0.0)
                self.preview_opacity_anim.start()
                QTimer.singleShot(150, lambda: self.snap_preview.hide() if self.current_snap_mode is None else None)

    def eventFilter(self, obj, event):
        # 💡 核心修复：全局判断鼠标点击，处理“点击空白处收回侧边栏”
        if event.type() == QEvent.MouseButtonPress:
            # 判断是否有折叠动画正在播放（防止事件冒泡导致子控件和父控件同一瞬间触发两次，陷入死循环）
            is_animating = hasattr(self, 'animation') and self.animation.state() == QPropertyAnimation.Running

            if self.side_panel.width() > 0 and not is_animating:
                # 获取屏幕全局绝对坐标
                global_pos = event.globalPosition().toPoint()

                # 获取“豁免区域”的全局矩形边框 (MapToGlobal 转换父组件相对坐标系为全局坐标系)
                side_rect = QRect(self.side_panel.mapToGlobal(QPoint(0, 0)), self.side_panel.size())
                btn_menu_rect = QRect(self.btn_menu.mapToGlobal(QPoint(0, 0)), self.btn_menu.size())
                input_rect1 = QRect(self.entry_input.mapToGlobal(QPoint(0, 0)), self.entry_input.size())
                input_rect2 = QRect(self.entry_output.mapToGlobal(QPoint(0, 0)), self.entry_output.size())

                # 如果点击位置既不在侧边栏内，也不在菜单按钮和两个输入框上，自动折叠它！
                if not side_rect.contains(global_pos) and \
                        not btn_menu_rect.contains(global_pos) and \
                        not input_rect1.contains(global_pos) and \
                        not input_rect2.contains(global_pos):
                    self.toggle_side_panel()

        # 原本的 Resize 拖拽改变窗口大小及鼠标样式变动逻辑保持不变
        if event.type() in (QEvent.MouseMove, QEvent.HoverMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            if self.isActiveWindow() and not self.isMaximized():
                global_pos = QCursor.pos()
                if event.type() in (QEvent.MouseMove, QEvent.HoverMove):
                    if self._resize_dir is None:
                        zone = self.get_resize_zone(global_pos)
                        if zone:
                            self._set_resize_cursor(zone)
                            self._cursor_overridden = True
                        elif self._cursor_overridden:
                            self.unsetCursor()
                            self._cursor_overridden = False
                    else:
                        self.do_resize(global_pos)
                        return True
                elif event.type() == QEvent.MouseButtonPress:
                    if hasattr(event, 'button') and event.button() == Qt.LeftButton:
                        zone = self.get_resize_zone(global_pos)
                        if zone:
                            self._resize_dir = zone
                            self._resize_start_pos = global_pos
                            self._resize_start_geometry = self.geometry()
                            return True
                elif event.type() == QEvent.MouseButtonRelease:
                    if hasattr(event, 'button') and event.button() == Qt.LeftButton:
                        if self._resize_dir is not None:
                            self._resize_dir = None
                            self.unsetCursor()
                            self._cursor_overridden = False
                            return True
        return super().eventFilter(obj, event)

    def get_resize_zone(self, global_pos):
        local_pos = self.mapFromGlobal(global_pos)

        if self.btn_min.geometry().contains(local_pos) or \
                self.btn_max.geometry().contains(local_pos) or \
                self.btn_close.geometry().contains(local_pos):
            return None

        rect = self.geometry()
        x = global_pos.x() - rect.x()
        y = global_pos.y() - rect.y()
        w, h = rect.width(), rect.height()
        b = self.BORDER_WIDTH

        on_left = x <= b
        on_right = x >= w - b
        on_top = y <= b
        on_bottom = y >= h - b

        if on_top and on_left: return 'top_left'
        if on_top and on_right: return 'top_right'
        if on_bottom and on_left: return 'bottom_left'
        if on_bottom and on_right: return 'bottom_right'
        if on_left: return 'left'
        if on_right: return 'right'
        if on_bottom: return 'bottom'

        return None

    def _set_resize_cursor(self, zone):
        if zone in ('top_left', 'bottom_right'):
            self.setCursor(Qt.SizeFDiagCursor)
        elif zone in ('top_right', 'bottom_left'):
            self.setCursor(Qt.SizeBDiagCursor)
        elif zone in ('left', 'right'):
            self.setCursor(Qt.SizeHorCursor)
        elif zone in ('top', 'bottom'):
            self.setCursor(Qt.SizeVerCursor)

    def do_resize(self, global_pos):
        rect = self._resize_start_geometry
        dx = global_pos.x() - self._resize_start_pos.x()
        dy = global_pos.y() - self._resize_start_pos.y()
        new_rect = rect.adjusted(0, 0, 0, 0)
        min_w, min_h = self.minimumWidth(), self.minimumHeight()
        if 'left' in self._resize_dir:
            new_rect.setLeft(min(rect.left() + dx, rect.right() - min_w))
        elif 'right' in self._resize_dir:
            new_rect.setRight(max(rect.right() + dx, rect.left() + min_w))
        if 'top' in self._resize_dir:
            new_rect.setTop(min(rect.top() + dy, rect.bottom() - min_h))
        elif 'bottom' in self._resize_dir:
            new_rect.setBottom(max(rect.bottom() + dy, rect.top() + min_h))
        self.setGeometry(new_rect)

    def update_theme_styles(self, is_maximized=False):
        window_radius = "0px" if is_maximized else "16px"
        title_radius = "0px" if is_maximized else "15px"
        style_qss = f"""
            #WindowContainer {{ background-color: #1e293b; border: {"none" if is_maximized else "1px solid #334155"}; border-radius: {window_radius}; }}
            #CustomTitleBar {{ background-color: #0f172a; border-bottom: 1px solid #1e293b; border-top-left-radius: {title_radius}; border-top-right-radius: {title_radius}; }}
            #AppTitle {{ color: #94a3b8; font-family: 'Microsoft YaHei'; font-size: 13px; font-weight: bold; }}
            #WinMinButton, #WinMaxButton {{ background: transparent; color: #64748b; font-size: 14px; border: none; }}
            #WinMinButton:hover, #WinMaxButton:hover {{ background-color: #1e293b; color: #ffffff; }}
            #WinCloseButton {{ background: transparent; color: #64748b; font-size: 14px; border: none; border-top-right-radius: {title_radius}; }}
            #WinCloseButton:hover {{ background-color: #ef4444; color: #ffffff; }}
            #MainTitle {{ color: #ffffff; font-family: 'Microsoft YaHei'; font-size: 26px; font-weight: 800; }}
            #MenuButton {{ background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #cbd5e1; font-size: 13px; padding: 7px 16px; font-weight: bold; }}
            #MenuButton:hover {{ background-color: #1e293b; color: #ffffff; border-color: #475569; }}
            #FormCard {{ background-color: #0f172a; border-radius: 14px; border: 1px solid #334155; }}
            #FieldLabel {{ color: #f1f5f9; font-family: 'Microsoft YaHei'; font-size: 14px; font-weight: bold; }}
            #TipLabel {{ color: #94a3b8; font-family: 'Microsoft YaHei'; font-size: 12px; line-height: 1.4; }}
            QLineEdit {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; color: #ffffff; padding: 10px 14px; font-size: 13px; }}
            QLineEdit:focus {{ background-color: #0f172a; border: 2px solid #06b6d4; }}
            #TimeEntry {{ font-weight: 900; color: #22d3ee; font-size: 18px; background-color: #0c4a6e; border: 1.5px solid #0284c7; }}
            #TimeEntry:focus {{ background-color: #0f172a; border: 2px solid #22d3ee; }}
            #NormalButton {{ background-color: #334155; border: 1px solid #475569; border-radius: 8px; color: #f1f5f9; padding: 9px 22px; font-weight: bold; }}
            #NormalButton:hover {{ background-color: #475569; border-color: #64748b; }}
            #StartButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #06b6d4, stop:1 #3b82f6); border: none; border-radius: 10px; color: #ffffff; font-size: 16px; font-weight: bold; padding: 14px; }}
            #StartButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #22d3ee, stop:1 #2563eb); }}
            #StartButton:disabled {{ background: #475569; color: #94a3b8; }}
            #SidePanel {{ background-color: #0f172a; border-left: 1px solid #1e293b; border-bottom-right-radius: {"0px" if is_maximized else "15px"}; }}
            #SideTitle {{ color: #ffffff; font-family: 'Microsoft YaHei'; font-size: 15px; font-weight: bold; }}
            #SeparatorLine {{ background-color: #1e293b; }}
            #AboutButton {{ background-color: #eab308; border: none; border-radius: 8px; color: #000000; padding: 10px; font-weight: bold; }}
            #AboutButton:hover {{ background-color: #ca8a04; color: #ffffff; }}
            QTextEdit#LogConsole {{ background-color: #0f172a; border: 1px solid #334155; border-radius: 12px; color: #e2e8f0; font-family: 'Consolas', 'Microsoft YaHei'; font-size: 13px; padding: 14px; }}

            /* ====== 新增滚动条优化样式 ====== */
            QTextEdit#LogConsole QScrollBar:vertical {{
                background-color: #0f172a;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }}
            QTextEdit#LogConsole QScrollBar::handle:vertical {{
                background-color: #334155;
                min-height: 30px;
                border-radius: 5px;
            }}
            QTextEdit#LogConsole QScrollBar::handle:vertical:hover,
            QTextEdit#LogConsole QScrollBar::handle:vertical:pressed {{
                background-color: #06b6d4;
            }}
            QTextEdit#LogConsole QScrollBar::sub-line:vertical,
            QTextEdit#LogConsole QScrollBar::add-line:vertical {{
                height: 0px;
                background: none;
            }}
            QTextEdit#LogConsole QScrollBar::up-arrow:vertical,
            QTextEdit#LogConsole QScrollBar::down-arrow:vertical {{
                background: none;
            }}
            QTextEdit#LogConsole QScrollBar::add-page:vertical,
            QTextEdit#LogConsole QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
        self.setStyleSheet(style_qss)

    def init_ui(self):
        self.window_container = QWidget(self)
        self.window_container.setObjectName("WindowContainer")
        self.setCentralWidget(self.window_container)
        self.base_v_layout = QVBoxLayout(self.window_container)
        self.base_v_layout.setContentsMargins(0, 0, 0, 0)
        self.base_v_layout.setSpacing(0)

        self.title_bar = QWidget()
        self.title_bar.setObjectName("CustomTitleBar")
        self.title_bar.setFixedHeight(45)

        self.title_bar.mousePressEvent = self.title_bar_mousePressEvent
        self.title_bar.mouseMoveEvent = self.title_bar_mouseMoveEvent
        self.title_bar.mouseDoubleClickEvent = self.title_bar_mouseDoubleClickEvent
        self.title_bar.mouseReleaseEvent = self.title_bar_mouseReleaseEvent

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(18, 0, 0, 0)
        title_layout.setSpacing(10)
        icon_label = QLabel()
        icon_label.setPixmap(get_integrated_icon().pixmap(18, 18))
        app_title_text = QLabel("视频帧批量提取工具 Pro")
        app_title_text.setObjectName("AppTitle")
        title_layout.addWidget(icon_label)
        title_layout.addWidget(app_title_text)
        title_layout.addStretch()

        self.btn_min = QPushButton("—")
        self.btn_min.setObjectName("WinMinButton")
        self.btn_min.setFixedSize(45, 45)
        self.btn_min.clicked.connect(self.showMinimized)

        self.btn_max = QPushButton("❑")
        self.btn_max.setObjectName("WinMaxButton")
        self.btn_max.setFixedSize(45, 45)
        self.btn_max.clicked.connect(self.toggle_maximized)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("WinCloseButton")
        self.btn_close.setFixedSize(45, 45)
        self.btn_close.clicked.connect(self.close)

        title_layout.addWidget(self.btn_min)
        title_layout.addWidget(self.btn_max)
        title_layout.addWidget(self.btn_close)
        self.base_v_layout.addWidget(self.title_bar)

        self.workspace_widget = QWidget()
        self.layout_wrapper = QHBoxLayout(self.workspace_widget)
        self.layout_wrapper.setContentsMargins(0, 0, 0, 0)
        self.layout_wrapper.setSpacing(0)
        self.left_workarea = QWidget()
        self.left_layout = QVBoxLayout(self.left_workarea)
        self.left_layout.setContentsMargins(40, 30, 40, 40)
        self.left_layout.setSpacing(20)
        self.top_bar_layout = QHBoxLayout()
        title = QLabel("视频帧批量提取")
        title.setObjectName("MainTitle")
        self.btn_menu = QPushButton("⚙️ 参数与配置")
        self.btn_menu.setObjectName("MenuButton")
        self.btn_menu.setCheckable(True)
        self.btn_menu.clicked.connect(self.toggle_side_panel)
        self.top_bar_layout.addWidget(title)
        self.top_bar_layout.addStretch()
        self.top_bar_layout.addWidget(self.btn_menu)
        self.left_layout.addLayout(self.top_bar_layout)
        form_widget = QWidget()
        form_widget.setObjectName("FormCard")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(28, 28, 28, 28)
        form_layout.setSpacing(16)
        lbl_in = QLabel("视频文件夹路径")
        lbl_in.setObjectName("FieldLabel")
        h_layout1 = QHBoxLayout()
        self.entry_input = ModernLineEdit("点击右侧浏览，或直接拖拽文件夹至此处...")
        # 💡 已删除了自动联动的 callback，实现路径完全独立
        btn_browse_in = QPushButton("浏览")
        btn_browse_in.setObjectName("NormalButton")
        btn_browse_in.clicked.connect(self.browse_input)
        h_layout1.addWidget(self.entry_input)
        h_layout1.addWidget(btn_browse_in)
        form_layout.addWidget(lbl_in)
        form_layout.addLayout(h_layout1)
        lbl_out = QLabel("图片保存路径")
        lbl_out.setObjectName("FieldLabel")
        h_layout2 = QHBoxLayout()
        self.entry_output = ModernLineEdit("点击右侧浏览，或直接拖拽文件夹至此处...")
        btn_browse_out = QPushButton("浏览")
        btn_browse_out.setObjectName("NormalButton")
        btn_browse_out.clicked.connect(self.browse_output)
        h_layout2.addWidget(self.entry_output)
        h_layout2.addWidget(btn_browse_out)
        form_layout.addWidget(lbl_out)
        form_layout.addLayout(h_layout2)
        self.left_layout.addWidget(form_widget)
        self.btn_start = QPushButton("🚀 开始批量提取")
        self.btn_start.setObjectName("StartButton")
        self.btn_start.clicked.connect(self.start_processing)
        self.left_layout.addWidget(self.btn_start)

        self.log_text = LogTextWidget(self)
        self.log_text.setObjectName("LogConsole")
        self.log_text.setReadOnly(True)
        self.left_layout.addWidget(self.log_text)

        self.layout_wrapper.addWidget(self.left_workarea)
        self.side_panel = QWidget()
        self.side_panel.setObjectName("SidePanel")
        self.side_panel.setFixedWidth(0)
        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setContentsMargins(22, 25, 22, 25)
        self.side_layout.setSpacing(15)
        lbl_side_title = QLabel("核心参数设置")
        lbl_side_title.setObjectName("SideTitle")
        self.side_layout.addWidget(lbl_side_title)
        lbl_time = QLabel("提取特定时间点 (秒)")
        lbl_time.setObjectName("FieldLabel")
        self.entry_time = QLineEdit("0.0")
        self.entry_time.setObjectName("TimeEntry")
        self.entry_time.setAlignment(Qt.AlignCenter)
        validator = QDoubleValidator(0.0, 9999.0, 2, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.entry_time.setValidator(validator)
        lbl_tip = QLabel("提示：设为 0.0 代表提取视频第一帧。支持精确小数（如输入 2.5 提取第 2.5 秒的画面）。")
        lbl_tip.setObjectName("TipLabel")
        lbl_tip.setWordWrap(True)
        self.side_layout.addWidget(lbl_time)
        self.side_layout.addWidget(self.entry_time)
        self.side_layout.addWidget(lbl_tip)
        line = QWidget()
        line.setObjectName("SeparatorLine")
        line.setFixedHeight(1)
        self.side_layout.addWidget(line)
        lbl_info_title = QLabel("关于")
        lbl_info_title.setObjectName("SideTitle")
        self.side_layout.addWidget(lbl_info_title)
        self.btn_about = QPushButton("💡 此项目已完全开源")
        self.btn_about.setObjectName("AboutButton")
        self.btn_about.clicked.connect(self.show_about_dialog)
        self.side_layout.addWidget(self.btn_about)
        self.side_layout.addStretch()
        self.layout_wrapper.addWidget(self.side_panel)
        self.base_v_layout.addWidget(self.workspace_widget)

    def animate_main_window(self, target_geo):
        self.win_anim = QPropertyAnimation(self, b"geometry")
        self.win_anim.setDuration(250)
        self.win_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.win_anim.setStartValue(self.geometry())
        self.win_anim.setEndValue(target_geo)
        self.win_anim.start()

    def title_bar_mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            if self.btn_min.geometry().contains(pos) or \
                    self.btn_max.geometry().contains(pos) or \
                    self.btn_close.geometry().contains(pos):
                event.ignore()
                return

            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.edge_preview_timer.start()
            event.accept()

    def title_bar_mouseMoveEvent(self, event):
        if self.is_dragging and (event.buttons() & Qt.LeftButton):
            if self.is_snapped_left or self.is_snapped_right:
                self.is_snapped_left = False
                self.is_snapped_right = False
                if self.normal_geometry:
                    self.setGeometry(self.normal_geometry)
                    self.drag_position = QPoint(self.width() // 2, 15)

            elif self.isMaximized():
                ratio = event.globalPosition().toPoint().x() / max(1, self.width())
                self.showNormal()
                if self.normal_geometry:
                    self.setGeometry(self.normal_geometry)
                self.drag_position = QPoint(int(self.width() * ratio), 15)

            self.move(event.globalPosition().toPoint() - self.drag_position)
            self.update_snap_preview()
            event.accept()

    def title_bar_mouseReleaseEvent(self, event):
        if self.is_dragging and event.button() == Qt.LeftButton:
            drag_distance = (event.globalPosition().toPoint() - self.drag_position).manhattanLength()
            self.is_dragging = False
            self.edge_preview_timer.stop()

            self.current_snap_mode = None
            if self.snap_preview.isVisible():
                self.preview_opacity_anim.setStartValue(self.snap_preview.windowOpacity())
                self.preview_opacity_anim.setEndValue(0.0)
                self.preview_opacity_anim.start()
                QTimer.singleShot(150, lambda: self.snap_preview.hide() if self.current_snap_mode is None else None)

            if drag_distance < 5:
                event.accept()
                return

            global_pos = event.globalPosition().toPoint()
            screen_geo = self.get_current_screen_geo()
            snap_margin = 40

            if not screen_geo:
                event.accept()
                return

            if not (self.is_snapped_left or self.is_snapped_right) and not self.isMaximized():
                self.normal_geometry = self.geometry()

            if global_pos.x() <= screen_geo.left() + snap_margin:
                self.is_snapped_left = True
                self.is_snapped_right = False
                self.showNormal()
                target_rect = QRect(screen_geo.left(), screen_geo.top(), screen_geo.width() // 2, screen_geo.height())
                self.animate_main_window(target_rect)

            elif global_pos.x() >= screen_geo.right() - snap_margin:
                self.is_snapped_left = False
                self.is_snapped_right = True
                self.showNormal()
                target_rect = QRect(screen_geo.left() + screen_geo.width() // 2, screen_geo.top(),
                                    screen_geo.width() // 2, screen_geo.height())
                self.animate_main_window(target_rect)

            elif global_pos.y() <= screen_geo.top() + snap_margin:
                self.is_snapped_left = False
                self.is_snapped_right = False
                self.showMaximized()

            event.accept()

    def title_bar_mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximized()

    def toggle_maximized(self):
        if hasattr(self, 'win_anim') and self.win_anim.state() == QPropertyAnimation.Running:
            self.win_anim.stop()

        if self.isMaximized():
            self.showNormal()
            self.is_snapped_left = False
            self.is_snapped_right = False
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)

        elif self.is_snapped_left or self.is_snapped_right:
            self.is_snapped_left = False
            self.is_snapped_right = False

            if self.normal_geometry:
                snapshot_pixmap = self.grab()
                self.flash_mask = QLabel(self)
                self.flash_mask.setPixmap(snapshot_pixmap)
                self.flash_mask.setGeometry(0, 0, self.width(), self.height())
                self.flash_mask.setScaledContents(True)
                self.flash_mask.show()
                self.flash_mask.raise_()

                self.win_anim = QPropertyAnimation(self, b"geometry")
                self.win_anim.setDuration(160)
                self.win_anim.setEasingCurve(QEasingCurve.OutCubic)
                self.win_anim.setStartValue(self.geometry())
                self.win_anim.setEndValue(self.normal_geometry)
                self.win_anim.finished.connect(self._cleanup_flash_mask)
                self.win_anim.start()
        else:
            self.normal_geometry = self.geometry()
            self.is_snapped_left = False
            self.is_snapped_right = False
            self.showMaximized()

    def _cleanup_flash_mask(self):
        if hasattr(self, 'flash_mask') and self.flash_mask:
            self.flash_mask.hide()
            self.flash_mask.deleteLater()
            self.flash_mask = None

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            is_max = self.isMaximized()
            self.update_theme_styles(is_maximized=is_max)
            self.btn_max.setText("🗗" if is_max else "❑")
        super().changeEvent(event)

    def toggle_side_panel(self):
        start_width = self.side_panel.width()
        end_width = 260 if start_width == 0 else 0
        self.animation = QPropertyAnimation(self.side_panel, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(start_width)
        self.animation.setEndValue(end_width)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.valueChanged.connect(self.side_panel.setFixedWidth)
        self.animation.start()

    def show_about_dialog(self):
        """✨ 自定义奢华暗黑无边框关于弹窗（带完全可拖拽和联动关闭）"""
        dlg = QDialog(self)
        dlg.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dlg.setAttribute(Qt.WA_TranslucentBackground)
        dlg.setFixedSize(550, 400)

        dialog_container = QWidget(dlg)
        dialog_container.setObjectName("DialogContainer")

        dlg.setStyleSheet("""
            #DialogContainer { 
                background-color: #0f172a; 
                border: 1.5px solid #334155; 
                border-radius: 16px; 
            }
            QLabel { color: #cbd5e1; font-family: 'Microsoft YaHei'; }
            QPushButton { 
                background-color: #334155; border: 1px solid #475569; 
                border-radius: 8px; color: #f3f4f6; padding: 9px 18px; font-weight: bold; 
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover { background-color: #06b6d4; color: #ffffff; border-color: #22d3ee; }
            #CloseBtn { background-color: transparent; border: none; color: #64748b; font-size: 16px; }
            #CloseBtn:hover { color: #ef4444; }
        """)

        container_layout = QVBoxLayout(dialog_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        custom_title_bar = QWidget()
        custom_title_bar.setFixedHeight(45)
        title_layout = QHBoxLayout(custom_title_bar)
        title_layout.setContentsMargins(20, 0, 10, 0)

        title_logo = QLabel("🎬  关于 SnapBatch")
        title_logo.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 13px;")
        btn_mini_close = QPushButton("✕")
        btn_mini_close.setObjectName("CloseBtn")
        btn_mini_close.setFixedSize(35, 35)
        btn_mini_close.clicked.connect(dlg.reject)

        title_layout.addWidget(title_logo)
        title_layout.addStretch()
        title_layout.addWidget(btn_mini_close)
        container_layout.addWidget(custom_title_bar)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(35, 10, 35, 30)
        layout.setSpacing(20)

        title_color = "#22d3ee"
        content_html = f"""
            <h3 style='font-family: "Microsoft YaHei"; color: {title_color}; margin-bottom: 8px;'>视频帧批量提取工具 Pro</h3>
            <p style='color: #cbd5e1; font-size: 13px; margin: 5px 0;'>
             📦 <b>当前版本:</b> v1.1.0  |  📜 <b>授权协议:</b> MIT <br>
             🧑‍🎄 <b>核心开发者:</b> 西瓜味的葡萄🍇
            </p>
            <hr style='border: 0; border-top: 1px solid #1e293b; margin: 10px 0;'>
            <p style='color: #e2e8f0; font-size: 13px; line-height: 1.6;'>
                一款极简、高效的自动化视频帧提取工具，专为视频创作者与开发者设计。✨<br><br>
                🔓 <b style='color: #facc15;'>关于开源：</b><br>
                <span style='color: #facc15; font-weight: 500;'>
                本项目完全开源，代码透明、无任何广告或捆绑。我们期待与您共同迭代，欢迎前往 GitHub 查看源码。
                </span>
            </p>
        """
        text_label = QLabel(content_html)
        text_label.setWordWrap(True)
        text_label.setTextFormat(Qt.RichText)
        layout.addWidget(text_label)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_github = QPushButton("🌐 查看开源仓库 (GitHub)")
        btn_close = QPushButton("关闭")

        btn_layout.addStretch()
        btn_layout.addWidget(btn_github)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        container_layout.addWidget(content_widget)

        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(0, 0, 0, 0)
        dlg_layout.addWidget(dialog_container)

        def on_github_clicked():
            webbrowser.open("https://github.com/crazyzhang277/SnapBatchPro.git")
            dlg.accept()

        btn_close.clicked.connect(dlg.reject)
        btn_github.clicked.connect(on_github_clicked)

        class DialogDragFilter(QObject):
            def __init__(self, target_dialog):
                super().__init__()
                self.target = target_dialog
                self.drag_position = QPoint()

            def eventFilter(self, obj, event):
                if event.type() == QEvent.MouseButtonPress:
                    if event.button() == Qt.LeftButton:
                        self.drag_position = event.globalPosition().toPoint() - self.target.frameGeometry().topLeft()
                        event.accept()
                        return True
                elif event.type() == QEvent.MouseMove:
                    if event.buttons() == Qt.LeftButton and not self.drag_position.isNull():
                        self.target.move(event.globalPosition().toPoint() - self.drag_position)
                        event.accept()
                        return True
                return super().eventFilter(obj, event)

        self.drag_filter = DialogDragFilter(dlg)
        dialog_container.installEventFilter(self.drag_filter)

        dlg.exec()

    def browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "选择视频文件夹")
        if folder:
            self.entry_input.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图片保存文件夹")
        if folder: self.entry_output.setText(folder)

    @Slot(str)
    def append_log(self, text):
        self.log_text.append(text)
        if self.log_text.is_auto_scroll:
            self.log_text.ensureCursorVisible()

    def start_processing(self):
        self.log_text.clear()
        video_dir = self.entry_input.text().strip()
        output_dir = self.entry_output.text().strip()
        time_str = self.entry_time.text().strip()
        if not video_dir or not output_dir:
            self.append_log("⚠️ 提示：请先选择或拖入视频文件夹和图片保存路径！")
            return
        if not os.path.isdir(video_dir):
            self.append_log(f"❌ 错误：指定的视频文件夹不存在，请核对！\n路径: {video_dir}")
            return
        target_time = float(time_str) if time_str and time_str != "." else 0.0
        self.btn_start.setEnabled(False)
        self.btn_start.setText("⏳ 正在全力处理中，请稍候...")
        self.worker = VideoWorker(video_dir, output_dir, target_time)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("🚀 开始批量提取")

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    window = LuxuryVideoExtractor()
    window.show()
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        sys.exit(0)