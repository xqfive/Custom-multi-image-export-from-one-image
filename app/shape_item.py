from PyQt5.QtWidgets import QGraphicsRectItem, QFrame
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QDrag, QPixmap
from PyQt5.QtCore import Qt, QPointF, QMimeData, QRectF

class ShapeItem(QGraphicsRectItem):
    """可拖动、统一大小的形状选区"""
    def __init__(self, shape_type, width, height=None, parent=None, is_preview=False):
        if shape_type in ["正方形", "圆形"]:
            size = min(width, height if height is not None else width)
            w = h = size
        else:
            w = width
            h = height if height is not None else width
        super().__init__(0, 0, w, h, parent)
        self.shape_type = shape_type
        self.width = w
        self.height = h
        self.corner_radius = 0
        self.is_preview = is_preview  # 标记是否是尺寸预览形状
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        # 默认样式：灰色虚线边框，半透明灰色背景
        self.normal_pen = QPen(QColor(128, 128, 128))
        self.normal_pen.setStyle(Qt.DashLine)
        self.normal_pen.setWidth(2)
        
        # 选中样式：深灰色虚线边框，半透明深灰色背景
        self.selected_pen = QPen(QColor(64, 64, 64))
        self.selected_pen.setStyle(Qt.DashLine)
        self.selected_pen.setWidth(2)
        
        self.setPen(self.normal_pen)
        self.setBrush(QBrush(QColor(128, 128, 128, 30)))
        self.snap_threshold = 10  # 吸附阈值（像素）
        self.resize_handle_size = 8  # 调整手柄大小
        self.resizing = False
        self.resize_edge = None  # 正在调整的边缘: top, bottom, left, right, top_left, top_right, bottom_left, bottom_right
        self.resize_start_pos = None
        self.resize_start_rect = None

    def hoverMoveEvent(self, event):
        """处理悬停事件，改变鼠标光标样式"""
        if not self.isSelected():
            self.setCursor(Qt.ArrowCursor)
            return
            
        pos = event.pos()
        rect = self.rect()
        # 正方形和圆形扩大边缘识别范围，更容易拖动
        handle_size = self.resize_handle_size if self.shape_type not in ["正方形", "圆形"] else 15
        
        # 判断鼠标位置
        on_top = pos.y() <= rect.top() + handle_size
        on_bottom = pos.y() >= rect.bottom() - handle_size
        on_left = pos.x() <= rect.left() + handle_size
        on_right = pos.x() >= rect.right() - handle_size
        
        # 正方形和圆形任何边缘都显示对角调整光标，方便缩放
        if self.shape_type in ["正方形", "圆形"]:
            if on_top or on_bottom or on_left or on_right:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            return
            
        # 普通矩形的边缘判断
        if on_top and on_left:
            self.setCursor(Qt.SizeFDiagCursor)
        elif on_top and on_right:
            self.setCursor(Qt.SizeBDiagCursor)
        elif on_bottom and on_left:
            self.setCursor(Qt.SizeBDiagCursor)
        elif on_bottom and on_right:
            self.setCursor(Qt.SizeFDiagCursor)
        elif on_top:
            self.setCursor(Qt.SizeVerCursor)
        elif on_bottom:
            self.setCursor(Qt.SizeVerCursor)
        elif on_left:
            self.setCursor(Qt.SizeHorCursor)
        elif on_right:
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，判断是否开始调整大小"""
        if event.button() == Qt.LeftButton and self.isSelected():
            pos = event.pos()
            rect = self.rect()
            # 正方形和圆形扩大边缘识别范围
            handle_size = self.resize_handle_size if self.shape_type not in ["正方形", "圆形"] else 15
            
            on_top = pos.y() <= rect.top() + handle_size
            on_bottom = pos.y() >= rect.bottom() - handle_size
            on_left = pos.x() <= rect.left() + handle_size
            on_right = pos.x() >= rect.right() - handle_size
            
            # 正方形和圆形根据点击的边缘设置正确的调整方向
            if self.shape_type in ["正方形", "圆形"]:
                if on_top and on_left:
                    self.resize_edge = "top_left"
                elif on_top and on_right:
                    self.resize_edge = "top_right"
                elif on_bottom and on_left:
                    self.resize_edge = "bottom_left"
                elif on_bottom and on_right:
                    self.resize_edge = "bottom_right"
                elif on_top:
                    self.resize_edge = "top"
                elif on_bottom:
                    self.resize_edge = "bottom"
                elif on_left:
                    self.resize_edge = "left"
                elif on_right:
                    self.resize_edge = "right"
                else:
                    self.resize_edge = None
                    
                if self.resize_edge:
                    self.resizing = True
                    self.resize_start_pos = event.scenePos()
                    self.resize_start_rect = self.rect()
                    self.resize_start_scene_pos = self.scenePos()  # 记录形状初始位置
                    self.setFlag(QGraphicsRectItem.ItemIsMovable, False)
                    return
            else:
                # 普通矩形的边缘判断
                if on_top and on_left:
                    self.resize_edge = "top_left"
                elif on_top and on_right:
                    self.resize_edge = "top_right"
                elif on_bottom and on_left:
                    self.resize_edge = "bottom_left"
                elif on_bottom and on_right:
                    self.resize_edge = "bottom_right"
                elif on_top:
                    self.resize_edge = "top"
                elif on_bottom:
                    self.resize_edge = "bottom"
                elif on_left:
                    self.resize_edge = "left"
                elif on_right:
                    self.resize_edge = "right"
                else:
                    self.resize_edge = None
                
            if self.resize_edge:
                self.resizing = True
                self.resize_start_pos = event.scenePos()
                self.resize_start_rect = self.rect()
                self.setFlag(QGraphicsRectItem.ItemIsMovable, False)
                return
                
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，调整大小或移动"""
        if self.resizing and self.resize_edge:
            delta = event.scenePos() - self.resize_start_pos
            new_rect = QRectF(self.resize_start_rect)
            
            if self.resize_edge in ["left", "top_left", "bottom_left"]:
                new_width = self.resize_start_rect.width() - delta.x()
                if new_width > 10:
                    new_rect.setLeft(new_rect.left() + delta.x())
            if self.resize_edge in ["right", "top_right", "bottom_right"]:
                new_width = self.resize_start_rect.width() + delta.x()
                if new_width > 10:
                    new_rect.setRight(new_rect.right() + delta.x())
            if self.resize_edge in ["top", "top_left", "top_right"]:
                new_height = self.resize_start_rect.height() - delta.y()
                if new_height > 10:
                    new_rect.setTop(new_rect.top() + delta.y())
            if self.resize_edge in ["bottom", "bottom_left", "bottom_right"]:
                new_height = self.resize_start_rect.height() + delta.y()
                if new_height > 10:
                    new_rect.setBottom(new_rect.bottom() + delta.y())
            
            # 正方形和圆形保持宽高比
            if self.shape_type in ["正方形", "圆形"]:
                # 计算等比例缩放的尺寸
                delta_x = abs(delta.x())
                delta_y = abs(delta.y())
                max_delta = max(delta_x, delta_y)
                original_size = max(self.resize_start_rect.width(), self.resize_start_rect.height())
                
                # 根据拖动方向确定尺寸变化
                size_change = 0
                if self.resize_edge in ["right", "bottom_right", "top_right"]:
                    size_change = delta.x() if delta.x() > 0 else -delta_x
                elif self.resize_edge in ["left", "bottom_left", "top_left"]:
                    size_change = -delta.x() if delta.x() < 0 else delta_x
                elif self.resize_edge in ["bottom", ]:
                    size_change = delta.y() if delta.y() > 0 else -delta_y
                elif self.resize_edge in ["top"]:
                    size_change = -delta.y() if delta.y() < 0 else delta_y
                    
                new_size = max(10, original_size + size_change)
                new_rect.setWidth(new_size)
                new_rect.setHeight(new_size)
                
                # 根据调整的边缘保持相应的位置不变
                if self.resize_edge == "top_left":
                    # 左上角拖动，右下角位置不变
                    new_rect.moveBottomRight(self.resize_start_rect.bottomRight())
                elif self.resize_edge == "top_right":
                    # 右上角拖动，左下角位置不变
                    new_rect.moveBottomLeft(self.resize_start_rect.bottomLeft())
                elif self.resize_edge == "bottom_left":
                    # 左下角拖动，右上角位置不变
                    new_rect.moveTopRight(self.resize_start_rect.topRight())
                elif self.resize_edge == "bottom_right":
                    # 右下角拖动，左上角位置不变
                    new_rect.moveTopLeft(self.resize_start_rect.topLeft())
                elif self.resize_edge == "top":
                    # 顶部拖动，底部位置不变
                    new_rect.moveBottom(self.resize_start_rect.bottom())
                    # 水平居中
                    new_rect.moveLeft((self.resize_start_rect.width() - new_size) / 2)
                elif self.resize_edge == "bottom":
                    # 底部拖动，顶部位置不变
                    new_rect.moveTop(self.resize_start_rect.top())
                    # 水平居中
                    new_rect.moveLeft((self.resize_start_rect.width() - new_size) / 2)
                elif self.resize_edge == "left":
                    # 左侧拖动，右侧位置不变
                    new_rect.moveRight(self.resize_start_rect.right())
                    # 垂直居中
                    new_rect.moveTop((self.resize_start_rect.height() - new_size) / 2)
                elif self.resize_edge == "right":
                    # 右侧拖动，左侧位置不变
                    new_rect.moveLeft(self.resize_start_rect.left())
                    # 垂直居中
                    new_rect.moveTop((self.resize_start_rect.height() - new_size) / 2)
            
            self.setRect(new_rect)
            self.width = new_rect.width()
            self.height = new_rect.height()
            self.update()
            
            # 通知主窗口更新尺寸输入框
            from PyQt5.QtWidgets import qApp
            main_window = qApp.activeWindow()
            if main_window and hasattr(main_window, 'shape_manager'):
                if self in main_window.preview_shapes.values():
                    # 是预览形状，更新配置
                    main_window.shape_manager.shape_configs[self.shape_type]["width"] = int(self.width)
                    main_window.shape_manager.shape_configs[self.shape_type]["height"] = int(self.height)
                    # 更新输入框
                    if self.shape_type in ["正方形", "圆形"]:
                        if self.shape_type in main_window.shape_size_spins:
                            main_window.shape_size_spins[self.shape_type].setValue(int(self.width))
                    else:
                        if self.shape_type in main_window.shape_width_spins:
                            main_window.shape_width_spins[self.shape_type].setValue(int(self.width))
                        if self.shape_type in main_window.shape_height_spins:
                            main_window.shape_height_spins[self.shape_type].setValue(int(self.height))
            return
            
        # 普通移动，处理吸附
        super().mouseMoveEvent(event)
        scene = self.scene()
        if not scene:
            return
            
        # 获取当前形状的边界
        current_rect = self.sceneBoundingRect()
        current_left = current_rect.left()
        current_right = current_rect.right()
        current_top = current_rect.top()
        current_bottom = current_rect.bottom()
        
        # 获取场景边界（图片边界）
        scene_rect = scene.sceneRect()
        scene_left = scene_rect.left()
        scene_right = scene_rect.right()
        scene_top = scene_rect.top()
        scene_bottom = scene_rect.bottom()
        
        # 计算需要调整的偏移量
        dx, dy = 0, 0
        
        # 1. 吸附到图片边缘
        # 左边缘吸附
        if abs(current_left - scene_left) < self.snap_threshold:
            dx = scene_left - current_left
        # 右边缘吸附
        elif abs(current_right - scene_right) < self.snap_threshold:
            dx = scene_right - current_right
        # 上边缘吸附
        if abs(current_top - scene_top) < self.snap_threshold:
            dy = scene_top - current_top
        # 下边缘吸附
        elif abs(current_bottom - scene_bottom) < self.snap_threshold:
            dy = scene_bottom - current_bottom
        
        # 2. 吸附到其他选区
        for item in scene.items():
            if isinstance(item, ShapeItem) and item != self:
                # 尺寸预览形状拖动时，不吸附到任何其他形状
                if self.is_preview:
                    continue
                # 普通形状拖动时，可以吸附到所有形状（包括预览形状）
                other_rect = item.sceneBoundingRect()
                other_left = other_rect.left()
                other_right = other_rect.right()
                other_top = other_rect.top()
                other_bottom = other_rect.bottom()
                other_center_x = other_rect.center().x()
                other_center_y = other_rect.center().y()
                
                # 边缘对齐
                if abs(current_left - other_left) < self.snap_threshold:
                    dx = other_left - current_left
                elif abs(current_right - other_right) < self.snap_threshold:
                    dx = other_right - current_right
                elif abs(current_left - other_right) < self.snap_threshold:
                    dx = other_right - current_left
                elif abs(current_right - other_left) < self.snap_threshold:
                    dx = other_left - current_right
                    
                if abs(current_top - other_top) < self.snap_threshold:
                    dy = other_top - current_top
                elif abs(current_bottom - other_bottom) < self.snap_threshold:
                    dy = other_bottom - current_bottom
                elif abs(current_top - other_bottom) < self.snap_threshold:
                    dy = other_bottom - current_top
                elif abs(current_bottom - other_top) < self.snap_threshold:
                    dy = other_top - current_bottom
                
                # 中心线对齐
                current_center_x = current_rect.center().x()
                current_center_y = current_rect.center().y()
                if abs(current_center_x - other_center_x) < self.snap_threshold:
                    dx = other_center_x - current_center_x
                if abs(current_center_y - other_center_y) < self.snap_threshold:
                    dy = other_center_y - current_center_y
        
        # 应用吸附偏移
        if dx != 0 or dy != 0:
            self.moveBy(dx, dy)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，结束调整大小"""
        if event.button() == Qt.LeftButton and self.resizing:
            self.resizing = False
            self.resize_edge = None
            self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
            return
            
        super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget=None):
        """根据类型绘制不同形状"""
        # 直接设置painter的画笔和画刷，确保样式生效
        if self.isSelected():
            painter.setPen(self.selected_pen)
            painter.setBrush(QBrush(QColor(128, 128, 128, 50)))
        else:
            painter.setPen(self.normal_pen)
            painter.setBrush(QBrush(QColor(128, 128, 128, 30)))
            
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        adjusted_rect = rect.adjusted(0, 0, -1, -1)
        if self.shape_type == "矩形":
            if self.corner_radius > 0:
                painter.drawRoundedRect(adjusted_rect, self.corner_radius, self.corner_radius)
            else:
                painter.drawRect(adjusted_rect)
        elif self.shape_type == "正方形":
            if self.corner_radius > 0:
                painter.drawRoundedRect(adjusted_rect, self.corner_radius, self.corner_radius)
            else:
                painter.drawRect(adjusted_rect)
        elif self.shape_type == "圆角":
            painter.drawRoundedRect(adjusted_rect, 20, 20)
        elif self.shape_type == "圆形":
            painter.drawEllipse(adjusted_rect)

class ShapePreview(QFrame):
    """左侧形状预览项，支持拖动"""
    def __init__(self, shape_type, width=200, height=200, parent=None):
        super().__init__(parent)
        self.shape_type = shape_type
        self.preview_width = width
        self.preview_height = height
        self.setFixedSize(120, 100)
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("background-color: white;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(0, 0, 0))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(200, 200, 200, 30)))

        # 居中绘制预览，保持比例
        max_preview_size = 60
        ratio = 1.0
        if self.shape_type in ["正方形", "圆形"]:
            original_size = min(self.preview_width, self.preview_height)
            size = min(original_size, max_preview_size)
            w = h = size
            ratio = size / original_size if original_size > 0 else 1.0
        else:
            ratio = min(max_preview_size / self.preview_width, max_preview_size / self.preview_height)
            w = self.preview_width * ratio
            h = self.preview_height * ratio
        x = (self.width() - w) / 2
        y = (self.height() - h) / 2
        rect = QRectF(x, y, w, h)

        # 获取形状配置中的圆角值
        from PyQt5.QtWidgets import qApp
        main_window = qApp.activeWindow()
        corner_radius = 0
        if main_window and hasattr(main_window, 'shape_manager'):
            corner_radius = main_window.shape_manager.shape_configs[self.shape_type].get("corner_radius", 0)
        # 圆角也等比例缩放
        scaled_corner_radius = corner_radius * ratio
            
        if self.shape_type == "矩形":
            if scaled_corner_radius > 0:
                painter.drawRoundedRect(rect, scaled_corner_radius, scaled_corner_radius)
            else:
                painter.drawRect(rect)
        elif self.shape_type == "正方形":
            if scaled_corner_radius > 0:
                painter.drawRoundedRect(rect, scaled_corner_radius, scaled_corner_radius)
            else:
                painter.drawRect(rect)
        elif self.shape_type == "圆形":
            painter.drawEllipse(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(f"shape:{self.shape_type}")
            drag.setMimeData(mime_data)

            # 拖动时显示预览
            if self.shape_type in ["正方形", "圆形"]:
                size = min(self.preview_width, self.preview_height)
                w = h = size
            else:
                w = self.preview_width
                h = self.preview_height
                
            pixmap = QPixmap(w, h)
            pixmap.fill(Qt.transparent)
            p = QPainter(pixmap)
            p.setRenderHint(QPainter.Antialiasing)
            # 拖动预览样式和图片上的形状完全一致：灰色虚线边框+半透明灰色背景
            pen = QPen(QColor(128, 128, 128))
            pen.setStyle(Qt.DashLine)
            pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(QBrush(QColor(128, 128, 128, 30)))
            
            # 获取形状配置中的圆角值
            from PyQt5.QtWidgets import qApp
            main_window = qApp.activeWindow()
            corner_radius = 0
            if main_window and hasattr(main_window, 'shape_manager'):
                corner_radius = main_window.shape_manager.shape_configs[self.shape_type].get("corner_radius", 0)
            
            if self.shape_type == "矩形" or self.shape_type == "正方形":
                if corner_radius > 0:
                    p.drawRoundedRect(0, 0, pixmap.width()-1, pixmap.height()-1, corner_radius, corner_radius)
                else:
                    p.drawRect(0, 0, pixmap.width()-1, pixmap.height()-1)
            elif self.shape_type == "圆形":
                p.drawEllipse(0, 0, pixmap.width()-1, pixmap.height()-1)
            p.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPointF(pixmap.width()/2, pixmap.height()/2).toPoint())

            drag.exec_(Qt.CopyAction)
