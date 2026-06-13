from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QTransform

class CustomGraphicsView(QGraphicsView):
    """自定义GraphicsView支持拖放形状和Ctrl+滚轮缩放"""
    dropReceived = pyqtSignal(str, QPointF)
    
    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        self.zoom_factor = 1.0  # 当前缩放比例
        self.zoom_changed_callback = None  # 缩放回调函数
        self.min_zoom = 0.1  # 最小缩放10%
        self.max_zoom = 10.0  # 最大缩放1000%

    def setZoom(self, factor):
        """设置缩放比例"""
        self.zoom_factor = factor
        transform = QTransform()
        transform.scale(factor, factor)
        self.setTransform(transform)

    def wheelEvent(self, event):
        """处理滚轮事件，Ctrl+滚轮缩放"""
        if event.modifiers() == Qt.ControlModifier:
            # 计算缩放增量
            delta = event.angleDelta().y()
            zoom_delta = 0.1 if delta > 0 else -0.1
            
            # 计算新的缩放比例
            new_zoom = self.zoom_factor + zoom_delta
            new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
            
            # 应用缩放
            self.setZoom(new_zoom)
            
            # 回调更新显示
            if self.zoom_changed_callback:
                self.zoom_changed_callback(new_zoom)
            
            event.accept()
        else:
            # 普通滚轮事件，交给父类处理（滚动视图）
            super().wheelEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("shape:"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("shape:"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("shape:"):
            shape_type = event.mimeData().text().split(":")[1]
            scene_pos = self.mapToScene(event.pos())
            self.dropReceived.emit(shape_type, scene_pos)
            event.acceptProposedAction()

    def drawBackground(self, painter, rect):
        """背景绘制，删除网格功能"""
        super().drawBackground(painter, rect)