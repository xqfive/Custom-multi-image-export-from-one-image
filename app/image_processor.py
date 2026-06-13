import os
from datetime import datetime
from PIL import Image, ImageDraw
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication

class ImageProcessor:
    """图片处理器，负责图片加载、裁剪、导出"""
    def __init__(self):
        self.image = None
        self.pixmap = None

    def load_from_file(self, file_path):
        """从文件加载图片"""
        self.image = Image.open(file_path).convert("RGBA")
        qimage = QImage(
            self.image.tobytes(),
            self.image.width,
            self.image.height,
            QImage.Format_RGBA8888
        )
        self.pixmap = QPixmap.fromImage(qimage)
        return self.pixmap

    def load_from_clipboard(self):
        """从剪贴板加载图片"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            qimage = QImage(mime_data.imageData())
            if not qimage.isNull():
                qimage = qimage.convertToFormat(QImage.Format_RGBA8888)
                width = qimage.width()
                height = qimage.height()
                ptr = qimage.bits()
                ptr.setsize(height * width * 4)
                self.image = Image.frombuffer("RGBA", (width, height), ptr.asstring(), "raw", "RGBA", 0, 1)
                self.pixmap = QPixmap.fromImage(qimage)
                return self.pixmap
        return None

    def crop_shape(self, shape):
        """裁剪形状区域"""
        pos = shape.pos()
        rect = shape.rect()
        x = int(pos.x())
        y = int(pos.y())
        w = int(rect.width())
        h = int(rect.height())

        crop_box = (x, y, x+w, y+h)
        cropped = self.image.crop(crop_box)

        # 处理形状蒙版
        if shape.shape_type == "圆形":
            mask = Image.new("L", (w, h), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, w, h), fill=255)
            cropped.putalpha(mask)
        else:
            # 处理所有形状的圆角
            corner_radius = getattr(shape, 'corner_radius', 0)
            if corner_radius > 0:
                mask = Image.new("L", (w, h), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle((0, 0, w, h), corner_radius, fill=255)
                cropped.putalpha(mask)
        
        return cropped

    def export_all_shapes(self, shapes, save_dir, prefix="首测", naming_mode="prefix_with_datetime"):
        """导出所有形状选区"""
        success_count = 0
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        for i, shape in enumerate(shapes):
            try:
                cropped = self.crop_shape(shape)
                if naming_mode == "prefix_only":
                    save_path = os.path.join(save_dir, f"{prefix}_{i+1}.png")
                else:
                    save_path = os.path.join(save_dir, f"{prefix}_{timestamp}_{i+1}.png")
                cropped.save(save_path)
                success_count += 1
            except Exception as e:
                pass
        return success_count