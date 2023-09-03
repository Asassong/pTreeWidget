import sys
from typing import Tuple

from PyQt5 import QtCore
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QLabel, QMainWindow, \
    QApplication, QAbstractItemView, QToolButton
from PyQt5.QtCore import Qt, QPoint, QSize, QRect
from PyQt5.QtGui import QIcon, QFont


class Map:
    def __init__(self):
        self.key = []
        self.value = []

    def __getitem__(self, item):
        for key, value in zip(self.key, self.value):
            if key == item:
                return value
        raise KeyError(f"{item}")

    def __setitem__(self, key, value):
        exist = False
        for i, k in enumerate(self.key):
            if key == k:
                self.value[i] = value
                exist = True
                break
        if not exist:
            self.key.append(key)
            self.value.append(value)

    def pop(self, item):
        if item in self.key:
            index = self.key.index(item)
            self.key.remove(item)
            self.value.pop(index)

    def match_value(self, value):
        keys = []
        for key, v in zip(self.key, self.value):
            if v == value:
                keys.append(key)
        return keys

class Block(QWidget):
    size_change = QtCore.pyqtSignal(tuple)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.type_label = QLabel("显示", self)
        self.type_label.resize(120, 25)
        font = QFont()
        font.setPointSize(8)
        self.type_label.setFont(font)
        self.stretch_button = QToolButton(self)
        self.stretch_button.setCheckable(True)
        self.stretch_button.move(150, 0)
        self.stretch_button.setIcon(QIcon("up.png"))
        self.stretch_button.setStyleSheet("QToolButton { border: none; }")
        self.stretch_button.toggled.connect(self.stretch)
        self.test_label = QLabel(data, self)
        self.test_label.setGeometry(0, 25, 120, 25)

    def stretch(self):
        if self.stretch_button.isChecked():
            self.stretch_button.setIcon(QIcon("down.png"))
            self.test_label.setVisible(False)
            self.size_change.emit((self.pos(), 25))
        else:
            self.stretch_button.setIcon(QIcon("up.png"))
            self.test_label.setVisible(True)
            self.size_change.emit((self.pos(), 50))

class Directory(QListWidgetItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon("right.png"))
        self.setText("新建文件夹")

"""
Known issue: 
If you drag an item without changing its relative position, 
at some special position, the item will be deleted by default dropEvent.
"""
class PTreeWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.NoFocus)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.currentItem = QListWidgetItem()
        self.belongMap = Map()
        self.isHideMap = Map()

    def add_directory(self):
        newItem = Directory()
        newItem.setSizeHint(QSize(self.width(), 25))
        self.addItem(newItem)
        self.belongMap[newItem] = newItem
        self.isHideMap[newItem] = True
        self.currentItem = newItem

    def add_block(self, data):
        block = Block(data)
        block.size_change.connect(self.change_size_hint)
        newItem = QListWidgetItem()
        newItem.setSizeHint(QSize(self.width(), 50))
        self.insertItem(self.row(self.currentItem) + len(self.belongMap.match_value(self.currentItem)), newItem)
        self.setItemWidget(newItem, block)
        self.belongMap[newItem] = self.currentItem
        if self.isHideMap[self.currentItem]:
            newItem.setHidden(True)
        else:
            newItem.setHidden(False)

    def set_hide(self, item: QListWidgetItem, hide:bool, top_level):
        if not hide:
            for subItem in self.belongMap.match_value(item):
                if subItem != item:
                    subItem.setHidden(False)
                    if isinstance(subItem, Directory) and self.isHideMap[subItem] == False:
                        self.set_hide(subItem, False, False)
            if top_level:
                self.isHideMap[item] = False
                item.setIcon(QIcon("down.png"))
        else:
            for subItem in self.belongMap.match_value(item):
                if subItem != item:
                    subItem.setHidden(True)
                    if isinstance(subItem, Directory) and self.isHideMap[subItem] == False:
                        self.set_hide(subItem, True, False)
            if top_level:
                self.isHideMap[item] = True
                item.setIcon(QIcon("right.png"))

    def select_sub_item(self, directory: Directory):
        for subItem in self.belongMap.match_value(directory):
            if subItem != directory:
                subItem.setSelected(True)
                if isinstance(subItem, Directory):
                    self.select_sub_item(subItem)

    def change_size_hint(self, data: Tuple[QPoint, int]):
        item = self.itemAt(data[0])
        item.setSizeHint(QSize(self.width(), data[1]))
        self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.currentItem = self.itemAt(event.pos())
        if event.button() == Qt.LeftButton and isinstance(self.currentItem, Directory):
            if self.isHideMap[self.currentItem]:
                self.set_hide(self.currentItem, False, True)
            else:
                self.set_hide(self.currentItem, True, True)

    def dropEvent(self, event):
        target_pos = event.pos()
        rect = QRect(target_pos.x() + self.horizontalOffset(), target_pos.y() + self.verticalOffset(), 1, 1)
        rect.adjust(-self.spacing(), -self.spacing(), self.spacing(), self.spacing())
        intersects = []
        for i in range(self.count()):
            item = self.item(i)
            item_rect = self.visualItemRect(item)
            if item_rect.intersects(rect):
                intersects.append(i)
        target_item = None
        if intersects:
            target_item = self.item(intersects[-1])
            if isinstance(target_item, Directory):
                pass
            elif isinstance(self.belongMap[target_item], Directory):
                target_item = self.belongMap[target_item]

        items = self.selectedItems()
        for item in items:
            if self.belongMap[item] == item:
                self.belongMap[item] = target_item if target_item is not None else item
            elif self.belongMap[item] not in items:
                self.belongMap[item] = target_item if target_item is not None else item
            if isinstance(item, Directory):
                self.select_sub_item(item)
        last_item = self.item(self.count()-1)
        if len(items) == 1 and not intersects and last_item in items:
            # 当只有最后一个item被选中且拖动到空白处时，该item会被默认dropEvent异常删除
            return
        super().dropEvent(event)
        # dropEventMoved = True
        # if (event.source() == self
        #         and (event.dropAction() == Qt.MoveAction or self.dragDropMode() == QAbstractItemView.InternalMove)):
        #     row = -1
        #     target_pos = event.pos()
        #     rect = QRect(target_pos.x()+self.horizontalOffset(), target_pos.y()+self.verticalOffset(), 1, 1)
        #     rect.adjust(-self.spacing(), -self.spacing(), self.spacing(), self.spacing())
        #     intersects = []
        #     for i in range(self.count()):
        #         item = self.item(i)
        #         item_rect = self.visualItemRect(item)
        #         if item_rect.intersects(rect):
        #             intersects.append(i)
        #     if intersects:
        #         item = self.item(intersects[-1])
        #         item_rect = self.visualItemRect(item)
        #         margin = 2
        #         if target_pos.y() - item_rect.top() < margin:
        #             row = intersects[-1] - 1
        #         elif item_rect.top() - target_pos.y()  < margin:
        #             row = intersects[-1]
        #         elif item_rect.contains(target_pos):
        #             row = intersects[-1] if target_pos.y() < item_rect.center().y() else intersects[-1] + 1
        #     topIndexDropped = False
        #     selIndexes = self.selectedIndexes()
        #     persIndexes = []
        #
        #     for index in selIndexes:
        #         persIndexes.append(QPersistentModelIndex(index))
        #         if index.row() == row:
        #             topIndexDropped = True
        #             break
        #     if not topIndexDropped:
        #         persIndexes.sort()  # The dropped items will remain in the same visual order.
        #         r = row if row != -1 else self.model().rowCount()-1
        #         dataMoved = False
        #         for i in range(len(persIndexes)):
        #             pIndex = persIndexes[i]
        #             # only generate a move when not same row or behind itself
        #             if r != pIndex.row() and r != pIndex.row() + 1:
        #                 # try to move (preserves selection)
        #                 dataMoved |= self.model().moveRow(QModelIndex(), pIndex.row(), QModelIndex(), r)
        #                 if not dataMoved:  # can't move - abort and let QAbstractItemView handle this
        #                     break
        #             else:
        #                 # move onto itself is blocked, don't delete anything
        #                 dataMoved = True
        #
        #             r = pIndex.row() + 1  # Dropped items are inserted contiguously and in the right order.
        #
        #         if dataMoved:
        #             event.accept()
        #
        #     if event.isAccepted():
        #         dropEventMoved = False
        #
        # if not dropEventMoved:
        #     event.ignore()
        #     super().dropEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(400, 300)
        self.tree = PTreeWidget()
        self.setCentralWidget(self.tree)
        self.tree.add_directory()
        self.tree.add_block("test1")
        self.tree.add_block("test2")
        self.tree.add_directory()
        self.tree.add_block("test3")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())