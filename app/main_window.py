import os
from PyQt5.QtWidgets import (
    QMainWindow, QGraphicsScene, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSpinBox, QLabel, QLineEdit, QCheckBox,
    QDialog, QMessageBox, QApplication, QGraphicsView, QSlider, QFileDialog
)
from PyQt5.QtGui import QIcon, QColor, QBrush, QPainter, QPen
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, QPropertyAnimation, QEasingCurve, QSize
import sip

from config import Config, APP_NAME, SHAPE_TYPES, MIN_SHAPE_SIZE, DEFAULT_FILE_PREFIX
from shape_manager import ShapeManager
from shape_item import ShapePreview
from image_processor import ImageProcessor
from custom_view import CustomGraphicsView

class ImageCropperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        # 固定快捷键设置
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._confirm_exit)
        QShortcut(QKeySequence("Ctrl+O"), self, self._open_image)
        QShortcut(QKeySequence("Ctrl+Shift+V"), self, self._paste_image)
        QShortcut(QKeySequence("Ctrl+Q"), self, self._clear_image)
        QShortcut(QKeySequence("Ctrl+S"), self, self._export_all)
        # 尺寸预览快捷键：Ctrl+1正方形，Ctrl+2矩形，Ctrl+3圆形
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._toggle_preview_by_shortcut("正方形"))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._toggle_preview_by_shortcut("矩形"))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self._toggle_preview_by_shortcut("圆形"))
        # 位置微调快捷键：WSAD
        QShortcut(QKeySequence("W"), self, lambda: self._move_selected_shape(0, -1))
        QShortcut(QKeySequence("S"), self, lambda: self._move_selected_shape(0, 1))
        QShortcut(QKeySequence("A"), self, lambda: self._move_selected_shape(-1, 0))
        QShortcut(QKeySequence("D"), self, lambda: self._move_selected_shape(1, 0))

        # 设置窗口标题
        self.setWindowTitle(f"{APP_NAME} Version:1.4 v：cqxq05")
        # 禁用系统默认声音提示
        QApplication.setQuitOnLastWindowClosed(True)
        self.setWindowFlags(self.windowFlags())
        
        # 设置窗口图标
        import sys
        # 优先从打包后的临时目录读取内嵌的图标
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "ico.png")
        elif getattr(sys, 'frozen', False):
            # 如果临时目录没有，再从exe所在目录找
            icon_path = os.path.join(os.path.dirname(sys.executable), "ico.png")
        else:
            # 开发环境从当前目录找
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            QApplication.instance().setWindowIcon(QIcon(icon_path))
            
        self.resize(1200, 800)


        # 初始化核心组件
        self.shape_manager = ShapeManager()
        self.image_processor = ImageProcessor()
        self.scene = QGraphicsScene()
        self.shape_previews = {}
        self.copied_shape_data = None
        
        # 气泡提示管理
        self.active_tooltips = []  # 存储当前显示的气泡列表
        self.tooltip_spacing = 15  # 气泡之间的间距

        # 拖放支持
        self.setAcceptDrops(True)
        
        # 构建UI
        self._build_ui()
        
        # 构建顶部功能工具栏
        self._build_tool_bar()
        
        # 程序启动时默认将焦点设置到画布
        QTimer.singleShot(0, self.view.setFocus)


    def _build_ui(self):
        """构建UI界面"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 左侧形状面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)

        self.shape_list = QWidget()
        shape_list_layout = QVBoxLayout(self.shape_list)
        shape_list_layout.setSpacing(20)
        shape_list_layout.setContentsMargins(0, 0, 0, 0)
        
        # 设置左侧面板样式
        left_panel.setStyleSheet("""
            QWidget#left_panel {
                background-color: #f5f7fa;
                border-right: 1px solid #e4e7ed;
            }
            QWidget#shape_container {
                background-color: white;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid #e4e7ed;
            }
            QLabel {
                color: #000000;
                font-size: 12px;
            }
            QSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
                min-width: 60px;
            }
            QSpinBox:focus {
                border-color: #409eff;
            }
            QCheckBox {
                color: #000000;
                font-size: 12px;
            }
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #409eff;
            }
        """)
        left_panel.setObjectName("left_panel")
        
        # 初始化所有spinbox引用字典
        self.shape_size_spins = {}
        self.shape_width_spins = {}
        self.shape_height_spins = {}
        self.shape_corner_spins = {}
        self.preview_checkboxes = {}
        self.preview_shapes = {}

        for shape_type in SHAPE_TYPES:
            # 每个形状独立的容器
            shape_container = QWidget()
            shape_container.setObjectName("shape_container")
            shape_container_layout = QVBoxLayout(shape_container)
            shape_container_layout.setContentsMargins(12, 12, 12, 12)
            shape_container_layout.setSpacing(10)
            
            # 创建形状预览控件支持拖动
            preview = ShapePreview(shape_type,
                                  self.shape_manager.shape_configs[shape_type]["width"],
                                  self.shape_manager.shape_configs[shape_type]["height"])
            shape_container_layout.addWidget(preview, alignment=Qt.AlignCenter)
            self.shape_previews[shape_type] = preview
            
            # 尺寸设置
            if shape_type in ["正方形", "圆形"]:
                # 正方形和圆形只有一个尺寸输入
                size_layout = QHBoxLayout()
                size_layout.addWidget(QLabel("尺寸:"))
                size_spin = QSpinBox()
                size_spin.setRange(MIN_SHAPE_SIZE, 99999)  # 设置很大的上限，允许用户任意输入
                size_spin.setValue(self.shape_manager.shape_configs[shape_type]["width"])
                size_spin.setSuffix(" px")
                size_spin.valueChanged.connect(lambda val, st=shape_type: self._on_shape_size_changed(st, val, val))
                size_layout.addWidget(size_spin)
                size_layout.addStretch()
                shape_container_layout.addLayout(size_layout)
                self.shape_size_spins[shape_type] = size_spin
            else:
                # 矩形和圆角矩形有宽高两个输入
                width_layout = QHBoxLayout()
                width_layout.addWidget(QLabel("宽度:"))
                width_spin = QSpinBox()
                width_spin.setRange(MIN_SHAPE_SIZE, 99999)  # 设置很大的上限，允许用户任意输入
                width_spin.setValue(self.shape_manager.shape_configs[shape_type]["width"])
                width_spin.setSuffix(" px")
                width_spin.valueChanged.connect(lambda val, st=shape_type: self._on_shape_width_changed(st, val))
                width_layout.addWidget(width_spin)
                width_layout.addStretch()
                shape_container_layout.addLayout(width_layout)
                self.shape_width_spins[shape_type] = width_spin
                
                height_layout = QHBoxLayout()
                height_layout.addWidget(QLabel("高度:"))
                height_spin = QSpinBox()
                height_spin.setRange(MIN_SHAPE_SIZE, 99999)  # 设置很大的上限，允许用户任意输入
                height_spin.setValue(self.shape_manager.shape_configs[shape_type]["height"])
                height_spin.setSuffix(" px")
                height_spin.valueChanged.connect(lambda val, st=shape_type: self._on_shape_height_changed(st, val))
                height_layout.addWidget(height_spin)
                height_layout.addStretch()
                shape_container_layout.addLayout(height_layout)
                self.shape_height_spins[shape_type] = height_spin
            
            # 圆角设置（矩形和正方形）
            if shape_type in ["矩形", "正方形"]:
                corner_layout = QHBoxLayout()
                corner_layout.addWidget(QLabel("圆角:"))
                corner_spin = QSpinBox()
                corner_spin.setRange(0, 100)
                corner_spin.setValue(self.shape_manager.shape_configs[shape_type]["corner_radius"])
                corner_spin.setSuffix(" px")
                corner_spin.valueChanged.connect(lambda val, st=shape_type: self._on_shape_corner_changed(st, val))
                corner_layout.addWidget(corner_spin)
                corner_layout.addStretch()
                shape_container_layout.addLayout(corner_layout)
                self.shape_corner_spins[shape_type] = corner_spin
            
            # 预览复选框（所有形状都有）
            preview_check = QCheckBox("尺寸预览")
            preview_check.setChecked(False)
            preview_check.stateChanged.connect(lambda state, st=shape_type: self._toggle_shape_preview(st, state))
            shape_container_layout.addWidget(preview_check)
            self.preview_checkboxes[shape_type] = preview_check
            
            shape_list_layout.addWidget(shape_container)
            
        # 文件名前缀设置，放在形状区域下方
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("前缀:"))
        self.prefix_input = QLineEdit(self.config.file_prefix)
        self.prefix_input.setPlaceholderText("输入文件名前缀")
        # 实时更新前缀
        import re
        forbidden_chars = r'[\\/:*?"<>|\x00-\x1F]'
        def update_prefix(text):
            # 验证是否包含非法字符
            if re.search(forbidden_chars, text):
                self._show_error_tip("文件名前缀不能包含 \\ / : * ? \" < > | 等特殊字符")
                # 移除非法字符
                cleaned_text = re.sub(forbidden_chars, '', text)
                self.prefix_input.blockSignals(True)
                self.prefix_input.setText(cleaned_text)
                self.prefix_input.blockSignals(False)
                self.config.file_prefix = cleaned_text.strip() or DEFAULT_FILE_PREFIX
            else:
                self.config.file_prefix = text.strip() or DEFAULT_FILE_PREFIX
        self.prefix_input.textChanged.connect(update_prefix)
        prefix_layout.addWidget(self.prefix_input)
        shape_list_layout.addLayout(prefix_layout)

        left_layout.addWidget(self.shape_list)
        left_layout.addStretch()

        # 左侧面板固定宽度
        left_panel.setFixedWidth(200)
        main_layout.addWidget(left_panel)

        # 右侧内容区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        # 缩放控制区域
        zoom_panel = QWidget()
        zoom_panel.setFixedHeight(35)
        zoom_layout = QHBoxLayout(zoom_panel)
        zoom_layout.setContentsMargins(10, 5, 10, 5)
        zoom_layout.setSpacing(8)
        
        zoom_label = QLabel("缩放:")
        zoom_label.setStyleSheet("font-size: 12px; color: #333;")
        zoom_layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 1000)  # 10% - 1000%
        self.zoom_slider.setValue(100)  # 默认100%
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        self.zoom_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #dcdfe6;
                height: 6px;
                background: #e4e7ed;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #909399;
                border: 1px solid #909399;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #606266;
                border: 1px solid #606266;
            }
            QSlider::sub-page:horizontal {
                background: #909399;
                border-radius: 3px;
            }
        """)
        zoom_layout.addWidget(self.zoom_slider)
        
        self.zoom_value_label = QLabel("100%")
        self.zoom_value_label.setFixedWidth(45)
        self.zoom_value_label.setStyleSheet("font-size: 12px; color: #333;")
        zoom_layout.addWidget(self.zoom_value_label)
        
        # 还原按钮
        reset_zoom_btn = QPushButton("还原")
        reset_zoom_btn.setFixedSize(45, 22)
        reset_zoom_btn.clicked.connect(self._reset_zoom)
        reset_zoom_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                font-size: 12px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #f5f7fa;
                border-color: #c0c4cc;
            }
        """)
        zoom_layout.addWidget(reset_zoom_btn)
        
        # 快捷键标签
        shortcut_label = QLabel("快捷键: ESC 退出 | Ctrl + C/V 复制粘贴选区 | Ctrl+滚轮/0 缩放/还原画板 | Ctrl + 1/2/3 预览尺寸 | WSAD 微调选区")
        shortcut_label.setStyleSheet("font-size: 12px; color: #111;")
        zoom_layout.addWidget(shortcut_label)
        
        zoom_layout.addStretch()
        
        # 设置缩放面板样式（删除横线）
        zoom_panel.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
            }
        """)
        right_layout.addWidget(zoom_panel)

        # 图片显示区域
        self.view = CustomGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setAcceptDrops(True)
        self.view.dropReceived.connect(self._handle_shape_drop)
        self.view.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.zoom_changed_callback = self._update_zoom_display
        # 添加复制粘贴快捷键
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self.view)
        copy_shortcut.activated.connect(self._copy_selected_shape)
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self.view)
        paste_shortcut.activated.connect(self._paste_copied_shape)
        # Ctrl+0 还原缩放快捷键
        reset_zoom_shortcut = QShortcut(QKeySequence("Ctrl+0"), self.view)
        reset_zoom_shortcut.activated.connect(self._reset_zoom)
        # 初始禁用所有形状控件（没有图片时）
        for spin in getattr(self, 'shape_size_spins', {}).values():
            spin.setEnabled(False)
        for spin in getattr(self, 'shape_width_spins', {}).values():
            spin.setEnabled(False)
        for spin in getattr(self, 'shape_height_spins', {}).values():
            spin.setEnabled(False)
        for spin in getattr(self, 'shape_corner_spins', {}).values():
            spin.setEnabled(False)
        for checkbox in getattr(self, 'preview_checkboxes', {}).values():
            checkbox.setEnabled(False)
        right_layout.addWidget(self.view)

        main_layout.addWidget(right_panel)

    def _build_tool_bar(self):
        """构建顶部功能工具栏，直接显示所有功能按钮"""
        tool_bar = self.addToolBar("功能工具栏")
        tool_bar.setMovable(False)  # 禁止拖动
        tool_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # 文字在图标旁边
        tool_bar.setIconSize(QSize(16, 16))
        
        # 设置工具栏样式与左侧形状区域保持一致
        tool_bar.setStyleSheet("""
            QToolBar {
                background-color: #f5f7fa;
                border-bottom: 1px solid #e4e7ed;
                spacing: 8px;
                padding: 6px 12px;
            }
            QToolBar QToolButton {
                background-color: white;
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
                color: #000000;
            }
            QToolBar QToolButton:hover {
                border-color: #c0c4cc;
                background-color: white;
            }
            QToolBar QToolButton:pressed {
                background-color: #f5f7fa;
                border-color: #dcdfe6;
            }
            QToolBar QToolButton:checked {
                background-color: #ecf5ff;
                border-color: #409eff;
                color: #409eff;
            }
            QToolBar QSeparator {
                background-color: #e4e7ed;
                width: 1px;
                margin: 0 8px;
            }
        """)

        # 文件操作按钮
        open_action = tool_bar.addAction("打开图片 (Ctrl+O)")
        open_action.triggered.connect(self._open_image)
        
        paste_action = tool_bar.addAction("粘贴图片 (Ctrl+Shift+V)")
        paste_action.triggered.connect(self._paste_image)
        
        export_action = tool_bar.addAction("全部导出 (Ctrl+S)")
        export_action.triggered.connect(self._export_all)
        
        tool_bar.addSeparator()

        # 编辑操作按钮
        undo_action = tool_bar.addAction("撤销 (Ctrl+Z)")
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self._undo_last_shape)
        
        clear_shapes_action = tool_bar.addAction("清除所有选区")
        clear_shapes_action.triggered.connect(self._clear_all_shapes)
        
        clear_selected_action = tool_bar.addAction("清除选中选区 (Delete)")
        clear_selected_action.setShortcut("Delete")
        clear_selected_action.triggered.connect(self._clear_selected_shape)
        
        clear_image_action = tool_bar.addAction("清除图片 (Ctrl+Q)")
        clear_image_action.triggered.connect(self._clear_image)

    def _on_shape_size_changed(self, shape_type, width, height):
        """形状尺寸调整"""
        # 验证尺寸不超过图片大小，超过则自动调整
        adjusted_width = width
        adjusted_height = height
        if self.image_processor and self.image_processor.image:
            max_size = min(self.image_processor.image.width, self.image_processor.image.height)
            if width > max_size or height > max_size:
                adjusted_width = max_size
                adjusted_height = max_size
                self._show_error_tip(f"尺寸已自动调整为图片最大尺寸{max_size}px")
                # 更新spinbox的值
                if shape_type in self.shape_size_spins:
                    self.shape_size_spins[shape_type].blockSignals(True)
                    self.shape_size_spins[shape_type].setValue(adjusted_width)
                    self.shape_size_spins[shape_type].blockSignals(False)
                
        self.shape_manager.shape_configs[shape_type]["width"] = adjusted_width
        self.shape_manager.shape_configs[shape_type]["height"] = adjusted_height
        # 更新预览控件
        preview = self.shape_previews[shape_type]
        preview.preview_width = adjusted_width
        preview.preview_height = adjusted_height
        preview.update()

        # 更新预览形状
        if shape_type in self.preview_shapes:
            preview_shape = self.preview_shapes[shape_type]
            if not sip.isdeleted(preview_shape):
                preview_shape.width = adjusted_width
                preview_shape.height = adjusted_height
                preview_shape.setRect(0, 0, preview_shape.width, preview_shape.height)
        
    def _on_shape_width_changed(self, shape_type, width):
        """形状宽度调整"""
        # 验证宽度不超过图片大小，超过则自动调整
        adjusted_width = width
        if self.image_processor and self.image_processor.image:
            max_width = self.image_processor.image.width
            if width > max_width:
                adjusted_width = max_width
                self._show_error_tip(f"宽度已自动调整为图片最大宽度{max_width}px")
                # 更新spinbox的值
                if shape_type in self.shape_width_spins:
                    self.shape_width_spins[shape_type].blockSignals(True)
                    self.shape_width_spins[shape_type].setValue(adjusted_width)
                    self.shape_width_spins[shape_type].blockSignals(False)
                
        self.shape_manager.shape_configs[shape_type]["width"] = adjusted_width
        # 更新预览控件
        preview = self.shape_previews[shape_type]
        preview.preview_width = adjusted_width
        preview.preview_height = self.shape_manager.shape_configs[shape_type]["height"]
        preview.update()

        # 更新预览形状
        if shape_type in self.preview_shapes:
            preview_shape = self.preview_shapes[shape_type]
            if not sip.isdeleted(preview_shape):
                preview_shape.width = adjusted_width
                if shape_type in ["正方形", "圆形"]:
                    preview_shape.height = adjusted_width
                preview_shape.setRect(0, 0, preview_shape.width, preview_shape.height)
        
    def _on_shape_height_changed(self, shape_type, height):
        """形状高度调整"""
        # 验证高度不超过图片大小，超过则自动调整
        adjusted_height = height
        if self.image_processor and self.image_processor.image:
            max_height = self.image_processor.image.height
            if height > max_height:
                adjusted_height = max_height
                self._show_error_tip(f"高度已自动调整为图片最大高度{max_height}px")
                # 更新spinbox的值
                if shape_type in self.shape_height_spins:
                    self.shape_height_spins[shape_type].blockSignals(True)
                    self.shape_height_spins[shape_type].setValue(adjusted_height)
                    self.shape_height_spins[shape_type].blockSignals(False)
                
        self.shape_manager.shape_configs[shape_type]["height"] = adjusted_height
        # 更新预览控件
        preview = self.shape_previews[shape_type]
        preview.preview_width = self.shape_manager.shape_configs[shape_type]["width"]
        preview.preview_height = adjusted_height
        preview.update()

        # 更新预览形状
        if shape_type in self.preview_shapes:
            preview_shape = self.preview_shapes[shape_type]
            if not sip.isdeleted(preview_shape):
                preview_shape.height = adjusted_height
                preview_shape.setRect(0, 0, preview_shape.width, preview_shape.height)
        
    def _on_shape_corner_changed(self, shape_type, radius):
        """形状圆角调整"""
        # 验证圆角不超过最小边长的一半
        config = self.shape_manager.shape_configs[shape_type]
        min_side = min(config["width"], config["height"])
        max_radius = min_side // 2
        if radius > max_radius:
            self._show_error_tip(f"圆角不能超过最小边长的一半，最大支持{max_radius}px")
            # 自动修正到最大值
            radius = max_radius
            # 更新spinbox的值
            if shape_type in self.shape_corner_spins:
                self.shape_corner_spins[shape_type].blockSignals(True)
                self.shape_corner_spins[shape_type].setValue(radius)
                self.shape_corner_spins[shape_type].blockSignals(False)
                
        self.shape_manager.shape_configs[shape_type]["corner_radius"] = radius
        # 更新预览控件
        preview = self.shape_previews[shape_type]
        preview.update()

        # 更新预览形状
        if shape_type in self.preview_shapes:
            preview_shape = self.preview_shapes[shape_type]
            if not sip.isdeleted(preview_shape):
                preview_shape.corner_radius = radius
                preview_shape.update()

    def _show_tooltip(self, message, bg_color):
        """通用气泡提示方法"""
        # 创建新的气泡标签
        tooltip = QLabel(self.view.viewport())
        tooltip.setText(message)
        tooltip.setStyleSheet(f"""
            background-color: {bg_color};
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
        """)
        tooltip.adjustSize()
        
        # 计算位置：顶部居中，在已有气泡下方排列
        view_rect = self.view.viewport().rect()
        label_rect = tooltip.rect()
        x = (view_rect.width() - label_rect.width()) // 2
        y = 20  # 第一个气泡距离顶部20px
        
        # 加上已有气泡的高度和间距
        for existing_tooltip in self.active_tooltips:
            y += existing_tooltip.height() + self.tooltip_spacing
        
        tooltip.move(x, y)
        tooltip.show()
        
        # 添加到活跃列表
        self.active_tooltips.append(tooltip)
        
        # 设置定时隐藏和消失动画
        def hide_tooltip():
            if tooltip in self.active_tooltips:
                index = self.active_tooltips.index(tooltip)
                # 添加透明度渐变消失动画
                opacity_effect = QGraphicsOpacityEffect()
                tooltip.setGraphicsEffect(opacity_effect)
                animation = QPropertyAnimation(opacity_effect, b"opacity")
                animation.setDuration(300)  # 300ms动画时间
                animation.setStartValue(1.0)
                animation.setEndValue(0.0)
                animation.setEasingCurve(QEasingCurve.OutQuad)
                
                def animation_finished():
                    tooltip.hide()
                    self.active_tooltips.remove(tooltip)
                    # 下面的气泡向上移动
                    for i in range(index, len(self.active_tooltips)):
                        current_pos = self.active_tooltips[i].pos()
                        self.active_tooltips[i].move(current_pos.x(), current_pos.y() - label_rect.height() - self.tooltip_spacing)
                
                animation.finished.connect(animation_finished)
                animation.start()
                # 保存动画引用防止被回收
                tooltip.animation = animation

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(hide_tooltip)
        timer.start(1000)  # 1秒后开始消失动画
        # 保存timer引用防止被回收
        tooltip.timer = timer

    def _show_error_tip(self, message):
        """显示错误提示气泡"""
        self._show_tooltip(message, "rgba(255, 0, 0, 0.8)")

    def _show_exit_dialog(self):
        """显示自定义退出确认对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle("退出确认")
        dialog.setFixedSize(280, 120)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QPushButton {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 6px 20px;
                font-size: 13px;
            }
            QPushButton#yesBtn {
                background-color: #909399;
                color: white;
                border: none;
            }
            QPushButton#yesBtn:hover {
                background-color: #606266;
            }
            QPushButton#noBtn {
                background-color: white;
                color: #606266;
            }
            QPushButton#noBtn:hover {
                border-color: #c0c4cc;
                background-color: #f5f7fa;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 15)
        layout.setSpacing(15)
        
        # 提示文字
        label = QLabel("确定要退出程序吗？")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        yes_btn = QPushButton("确定")
        yes_btn.setObjectName("yesBtn")
        yes_btn.clicked.connect(dialog.accept)
        
        no_btn = QPushButton("取消")
        no_btn.setObjectName("noBtn")
        no_btn.clicked.connect(dialog.reject)
        no_btn.setDefault(True)
        
        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)
        layout.addLayout(btn_layout)
        
        return dialog.exec_() == QDialog.Accepted

    def _confirm_exit(self):
        """退出确认"""
        if self._show_exit_dialog():
            self.close()

    def _show_success_tip(self, message):
        """显示成功提示气泡"""
        self._show_tooltip(message, "rgba(0, 128, 0, 0.8)")

    def _on_zoom_changed(self, value):
        """缩放滑块值改变时更新视图"""
        zoom_factor = value / 100.0
        self.view.setZoom(zoom_factor)
        self.zoom_value_label.setText(f"{value}%")

    def _update_zoom_display(self, zoom_factor):
        """更新缩放显示（从滚轮缩放回调）"""
        value = int(zoom_factor * 100)
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(value)
        self.zoom_slider.blockSignals(False)
        self.zoom_value_label.setText(f"{value}%")

    def _reset_zoom(self):
        """还原缩放到100%"""
        self.zoom_slider.setValue(100)
        self.view.setZoom(1.0)
        self.zoom_value_label.setText("100%")

    def _toggle_preview_by_shortcut(self, shape_type):
        """通过快捷键切换尺寸预览"""
        if shape_type in self.preview_checkboxes:
            checkbox = self.preview_checkboxes[shape_type]
            # 切换选中状态
            checkbox.setChecked(Qt.Unchecked if checkbox.isChecked() else Qt.Checked)
    
    def _move_selected_shape(self, dx, dy):
        """微调选中形状的位置"""
        from shape_item import ShapeItem
        selected_items = self.scene.selectedItems()
        selected_shapes = [item for item in selected_items if isinstance(item, ShapeItem)]
        for shape in selected_shapes:
            shape.moveBy(dx, dy)
    
    def _toggle_shape_preview(self, shape_type, state):
        """切换形状实时预览"""
        if state == Qt.Checked:
            # 互斥逻辑：关闭其他所有形状的预览
            for st, checkbox in self.preview_checkboxes.items():
                if st != shape_type and checkbox.isChecked():
                    checkbox.setChecked(Qt.Unchecked)
            # 创建预览形状
            config = self.shape_manager.shape_configs[shape_type]
            from shape_item import ShapeItem
            preview_shape = ShapeItem(shape_type, config["width"], config["height"], is_preview=True)
            preview_shape.corner_radius = config["corner_radius"]
            # 预览形状使用蓝色样式，和普通形状区分
            preview_shape.normal_pen = QPen(QColor(0, 120, 215))
            preview_shape.normal_pen.setStyle(Qt.SolidLine)
            preview_shape.normal_pen.setWidth(2)
            preview_shape.selected_pen = QPen(QColor(0, 80, 150))
            preview_shape.selected_pen.setStyle(Qt.SolidLine)
            preview_shape.selected_pen.setWidth(2)
            preview_shape.setPen(preview_shape.normal_pen)
            preview_shape.setBrush(QBrush(QColor(0, 120, 215, 60)))
            
            # 默认放在场景可见区域的中间位置，方便用户看到
            view_rect = self.view.viewport().rect()
            center_view = self.view.mapToScene(view_rect.center())
            # 让形状中心对齐视图中心
            pos_x = center_view.x() - preview_shape.width / 2
            pos_y = center_view.y() - preview_shape.height / 2
            preview_shape.setPos(pos_x, pos_y)
                
            self.scene.addItem(preview_shape)
            # 取消所有其他选区的选中状态，只选中预览形状
            self.scene.clearSelection()
            preview_shape.setSelected(True)  # 预览形状默认选中，直接可以缩放
            self.preview_shapes[shape_type] = preview_shape
        else:
            # 移除预览形状
            if shape_type in self.preview_shapes:
                preview_shape = self.preview_shapes[shape_type]
                if preview_shape and not sip.isdeleted(preview_shape) and preview_shape.scene() == self.scene:
                    self.scene.removeItem(preview_shape)
                del self.preview_shapes[shape_type]

    def _handle_shape_drop(self, shape_type, pos):
        """处理拖放的形状"""
        try:
            if self.image_processor.pixmap is None:
                self._show_error_tip("请先加载图片")
                return
            
            shape = self.shape_manager.create_shape(shape_type)
            # 调整位置使形状中心在鼠标落点
            w = shape.rect().width()
            h = shape.rect().height()
            shape.setPos(pos.x() - w/2, pos.y() - h/2)
            self.scene.addItem(shape)
            self.shape_manager.add_shape(shape)
            # 清除其他选区的选中状态，只选中新添加的形状
            self.scene.clearSelection()
            shape.setSelected(True)
        except Exception as e:
            pass

    def _copy_selected_shape(self):
        """复制选中的形状"""
        from shape_item import ShapeItem
        selected_items = self.scene.selectedItems()
        selected_shapes = [item for item in selected_items if isinstance(item, ShapeItem)]
        if not selected_shapes:
            self._show_error_tip("请先选中要复制的选区")
            return
        # 复制第一个选中的形状
        shape = selected_shapes[0]
        self.copied_shape_data = {
            "type": shape.shape_type,
            "width": shape.width,
            "height": shape.height,
            "corner_radius": shape.corner_radius,
            "pos": shape.pos()
        }
        self._show_success_tip("选区已复制")

    def _paste_copied_shape(self):
        """粘贴形状，优先粘贴当前预览形状，其次粘贴复制的形状"""
        # 优先粘贴当前预览形状
        preview_shape = None
        for shape in self.preview_shapes.values():
            if shape and not sip.isdeleted(shape) and shape.scene() == self.scene:
                preview_shape = shape
                break
        
        if preview_shape:
            # 创建普通选区
            from shape_item import ShapeItem
            from PyQt5.QtGui import QCursor
            new_shape = ShapeItem(
                preview_shape.shape_type,
                preview_shape.width,
                preview_shape.height
            )
            new_shape.corner_radius = preview_shape.corner_radius
            # 位置在鼠标当前位置，左上角对齐
            cursor_pos = self.view.mapFromGlobal(QCursor.pos())
            scene_pos = self.view.mapToScene(cursor_pos)
            new_shape.setPos(scene_pos)
            # 添加到场景和管理器
            self.scene.addItem(new_shape)
            self.shape_manager.add_shape(new_shape)
            # 自动选中新粘贴的形状
            self.scene.clearSelection()
            new_shape.setSelected(True)
            self._show_success_tip("预览形状已粘贴为选区")
            return
        
        # 没有预览形状时，粘贴复制的形状
        if self.copied_shape_data:
            # 创建新形状
            from shape_item import ShapeItem
            from PyQt5.QtGui import QCursor
            new_shape = ShapeItem(
                self.copied_shape_data["type"],
                self.copied_shape_data["width"],
                self.copied_shape_data["height"]
            )
            new_shape.corner_radius = self.copied_shape_data["corner_radius"]
            # 位置在鼠标当前位置，左上角对齐
            cursor_pos = self.view.mapFromGlobal(QCursor.pos())
            scene_pos = self.view.mapToScene(cursor_pos)
            new_shape.setPos(scene_pos)
            # 添加到场景和管理器
            self.scene.addItem(new_shape)
            self.shape_manager.add_shape(new_shape)
            # 自动选中新粘贴的形状
            self.scene.clearSelection()
            new_shape.setSelected(True)
            self._show_success_tip("选区已粘贴")
            return
        
        # 既没有预览形状也没有复制的形状
        self._show_error_tip("没有可粘贴的选区或预览形状")

    def _clear_image(self):
        """清除当前图片和所有形状"""
        self.scene.clear()
        self.image_processor.image = None
        self.image_processor.pixmap = None
        self.shape_manager.clear_shapes()
        # 清除剪贴板的复制选区数据
        self.copied_shape_data = None
        # 禁用所有形状控件
        for spin in getattr(self, 'shape_size_spins', {}).values():
            spin.setEnabled(False)
        for spin in getattr(self, 'shape_width_spins', {}).values():
            spin.setEnabled(False)
        for spin in getattr(self, 'shape_height_spins', {}).values():
            spin.setEnabled(False)
        for spin in getattr(self, 'shape_corner_spins', {}).values():
            spin.setEnabled(False)
        for checkbox in getattr(self, 'preview_checkboxes', {}).values():
            checkbox.setEnabled(False)
            checkbox.setChecked(False)
        # 清除所有预览形状
        for preview_shape in getattr(self, 'preview_shapes', {}).values():
            if preview_shape and not sip.isdeleted(preview_shape) and preview_shape.scene() == self.scene:
                self.scene.removeItem(preview_shape)
        self.preview_shapes = {}

    def _delete_selected_shapes(self):
        """删除选中的选区"""
        selected_items = [item for item in self.scene.selectedItems() if hasattr(item, 'shape_type') and not getattr(item, 'is_preview', False)]
        if selected_items:
            for item in selected_items:
                self.scene.removeItem(item)
            self._show_success_tip(f"已删除 {len(selected_items)} 个选区")
        else:
            self._show_error_tip("请先选择要删除的选区")

    def _open_image(self):
        """打开图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self._load_image(file_path)

    def _paste_image(self):
        """从剪贴板粘贴图片"""
        try:
            pixmap = self.image_processor.load_from_clipboard()
            if pixmap:
                self._set_image_to_scene(pixmap)
                self._show_success_tip("图片粘贴成功")
            else:
                self._show_error_tip("剪贴板中无图片")
        except Exception as e:
            self._show_error_tip("粘贴失败")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self._load_image(file_path)

    def _load_image(self, file_path):
        """加载并显示图片"""
        try:
            pixmap = self.image_processor.load_from_file(file_path)
            self._set_image_to_scene(pixmap)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"图片加载失败: {str(e)}")

    def _set_image_to_scene(self, pixmap):
        """设置图片到场景"""
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.shape_manager.clear_shapes()
        # 场景范围和图片大小一致
        self.view.setSceneRect(QRectF(pixmap.rect()))
        # 启用所有形状控件
        for spin in getattr(self, 'shape_size_spins', {}).values():
            spin.setEnabled(True)
        for spin in getattr(self, 'shape_width_spins', {}).values():
            spin.setEnabled(True)
        for spin in getattr(self, 'shape_height_spins', {}).values():
            spin.setEnabled(True)
        for spin in getattr(self, 'shape_corner_spins', {}).values():
            spin.setEnabled(True)
        for checkbox in getattr(self, 'preview_checkboxes', {}).values():
            checkbox.setEnabled(True)
        # 加载完图片后将焦点设置到画布
        self.view.setFocus()

    def _export_all(self):
        """导出所有选区"""
        try:
            if not self.image_processor.image or not self.shape_manager.shapes:
                self._show_error_tip("导出失败：无图片或选区")
                return

            save_dir = self.config.save_path
            if not os.path.exists(save_dir):
                self._show_error_tip("导出失败：保存路径不存在")
                return
                
            prefix = self.config.file_prefix
            naming_mode = self.config.naming_mode
                
            success_count = self.image_processor.export_all_shapes(self.shape_manager.shapes, save_dir, prefix, naming_mode)
            self._show_success_tip(f"导出完成：已成功导出 {success_count} 张图片到 {save_dir}")
        except Exception as e:
            self._show_error_tip(f"导出失败：{str(e)}")

    def _undo_last_shape(self):
        """撤销最后一次操作"""
        op_type, data = self.shape_manager.undo_last()
        if op_type == 'add':
            # 撤销添加：从场景移除形状
            self.scene.removeItem(data)
            self._show_success_tip("已撤销添加选区")
        elif op_type == 'delete':
            # 撤销删除：重新添加到场景
            self.scene.addItem(data)
            self._show_success_tip("已恢复删除的选区")
        elif op_type == 'clear_all':
            # 撤销清除所有：重新添加所有形状到场景
            for shape in data:
                self.scene.addItem(shape)
            self._show_success_tip(f"已恢复{len(data)}个选区")
        else:
            self._show_error_tip("没有可撤销的操作")

    def _clear_all_shapes(self):
        """清除所有形状"""
        if not self.shape_manager.shapes:
            self._show_error_tip("没有可清除的选区")
            return
        
        self.shape_manager.clear_shapes()
        for shape in self.scene.items():
            from shape_item import ShapeItem
            if isinstance(shape, ShapeItem) and not shape.is_preview:
                self.scene.removeItem(shape)
        self._show_success_tip("已清除所有选区")

    def _clear_selected_shape(self):
        """清除选中的形状"""
        from shape_item import ShapeItem
        selected_items = self.scene.selectedItems()
        selected_shapes = [item for item in selected_items if isinstance(item, ShapeItem) and not item.is_preview]
        if not selected_shapes:
            self._show_error_tip("请先选中要清除的选区")
            return
        
        for shape in selected_shapes:
            self.scene.removeItem(shape)
            self.shape_manager.remove_shape(shape)
        self._show_success_tip(f"已清除{len(selected_shapes)}个选区")

    def closeEvent(self, event):
        """窗口关闭事件 - 点击X按钮时二次确认"""
        if self._show_exit_dialog():
            event.accept()
            # 强制立即退出，避免延迟
            import sys
            from PyQt5.QtWidgets import QApplication
            QApplication.quit()
            sys.exit(0)
        else:
            event.ignore()
