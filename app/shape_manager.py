from shape_item import ShapeItem
from config import DEFAULT_SHAPE_WIDTH, DEFAULT_SHAPE_HEIGHT

class ShapeManager:
    """形状管理器，负责形状创建、更新、管理"""
    def __init__(self):
        self.shapes = []
        self.operation_history = []
        self.lock_aspect = True
        # 每个形状的独立配置
        self.shape_configs = {
            "正方形": {"width": DEFAULT_SHAPE_WIDTH, "height": DEFAULT_SHAPE_WIDTH, "corner_radius": 0},
            "矩形": {"width": DEFAULT_SHAPE_WIDTH, "height": 100, "corner_radius": 0},
            "圆形": {"width": DEFAULT_SHAPE_WIDTH, "height": DEFAULT_SHAPE_WIDTH, "corner_radius": 0}
        }

    def create_shape(self, shape_type):
        """创建一个新形状"""
        config = self.shape_configs[shape_type]
        shape = ShapeItem(shape_type, config["width"], config["height"])
        # 设置圆角属性
        if shape_type in ["矩形", "正方形"]:
            shape.corner_radius = config["corner_radius"]
        return shape

    def update_all_shapes_size(self):
        """更新所有形状的尺寸"""
        for shape in self.shapes:
            config = self.shape_configs[shape.shape_type]
            if shape.shape_type in ["正方形", "圆形"]:
                size = min(config["width"], config["height"])
                shape.setRect(0, 0, size, size)
            else:
                shape.setRect(0, 0, config["width"], config["height"])

    def add_shape(self, shape):
        """添加形状到管理列表"""
        self.shapes.append(shape)
        self.operation_history.append(('add', shape))
        
    def remove_shape(self, shape):
        """移除形状"""
        if shape in self.shapes:
            self.shapes.remove(shape)
            self.operation_history.append(('delete', shape))
            return True
        return False
        
    def clear_shapes(self):
        """清除所有形状，记录操作历史"""
        if self.shapes:
            # 保存所有形状用于撤销
            self.operation_history.append(('clear_all', self.shapes.copy()))
            self.shapes.clear()

    def undo_last(self):
        """撤销最后一次操作"""
        if self.operation_history:
            op_type, data = self.operation_history.pop()
            if op_type == 'add':
                # 撤销添加：移除形状
                if data in self.shapes:
                    self.shapes.remove(data)
                return op_type, data
            elif op_type == 'delete':
                # 撤销删除：重新添加形状
                self.shapes.append(data)
                return op_type, data
            elif op_type == 'clear_all':
                # 撤销清除所有：恢复所有形状
                self.shapes.extend(data)
                return op_type, data
        return None, None
