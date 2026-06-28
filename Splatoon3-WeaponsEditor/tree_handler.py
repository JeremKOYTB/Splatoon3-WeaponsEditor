from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtGui import QFont, QBrush, QColor
from PyQt6.QtCore import Qt
import byml

class TreeHandler:
    @staticmethod
    def populate_tree(tree_w, data, auto_expand=False):
        tree_w.clear()
        TreeHandler.add_items(tree_w.invisibleRootItem(), data)
        
        if auto_expand:
            tree_w.expandAll()
        else:
            for i in range(tree_w.topLevelItemCount()):
                root_item = tree_w.topLevelItem(i)
                root_item.setExpanded(True)
                if root_item.text(0) == "GameParameters":
                    for j in range(root_item.childCount()):
                        root_item.child(j).setExpanded(True)

    @staticmethod
    def _set_item_value(it, v):
        if v is None:
            it.setText(1, "None")
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
            it.setData(1, Qt.ItemDataRole.UserRole, "none")
            it.setData(1, Qt.ItemDataRole.UserRole + 1, "none")
            return

        python_val = v.value if hasattr(v, 'value') else v
        original_type = type(v).__name__

        it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
        
        if isinstance(python_val, bool) or original_type == 'Bool':
            it.setData(1, Qt.ItemDataRole.UserRole, "bool")
            it.setText(1, str(python_val))
        elif isinstance(python_val, int) or original_type in ['Int', 'UInt', 'Int64', 'UInt64']:
            it.setData(1, Qt.ItemDataRole.UserRole, "int")
            it.setText(1, str(python_val))
        elif isinstance(python_val, float) or original_type in ['Float', 'Double']:
            it.setData(1, Qt.ItemDataRole.UserRole, "float")
            it.setText(1, str(python_val))
        else:
            it.setData(1, Qt.ItemDataRole.UserRole, "str")
            it.setText(1, str(python_val))

        it.setData(1, Qt.ItemDataRole.UserRole + 1, original_type)

    @staticmethod
    def add_items(parent, value):
        if isinstance(value, dict):
            for k, v in value.items():
                it = QTreeWidgetItem(parent)
                it.setText(0, str(k))
                
                if isinstance(v, (dict, list)):
                    font = it.font(0)
                    font.setBold(True)
                    it.setFont(0, font)
                    it.setForeground(0, QBrush(QColor("#ff9f43")))
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    if not v:
                        it.setText(1, "{}" if isinstance(v, dict) else "[]")
                        it.setForeground(1, QBrush(QColor("gray")))
                        it.setData(1, Qt.ItemDataRole.UserRole, "empty_dict" if isinstance(v, dict) else "empty_list") 
                    else:
                        TreeHandler.add_items(it, v)
                else:
                    TreeHandler._set_item_value(it, v)
                    
        elif isinstance(value, list):
            for i, v in enumerate(value):
                it = QTreeWidgetItem(parent)
                it.setText(0, f"[{i}]")
                
                if isinstance(v, (dict, list)):
                    font = it.font(0)
                    font.setBold(True)
                    it.setFont(0, font)
                    it.setForeground(0, QBrush(QColor("#ff9f43")))
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    if not v:
                        it.setText(1, "{}" if isinstance(v, dict) else "[]")
                        it.setForeground(1, QBrush(QColor("gray")))
                        it.setData(1, Qt.ItemDataRole.UserRole, "empty_dict" if isinstance(v, dict) else "empty_list")
                    else:
                        TreeHandler.add_items(it, v)
                else:
                    TreeHandler._set_item_value(it, v)

    @staticmethod
    def build_dict(item):
        is_array = (item.childCount() > 0 and item.child(0).text(0).startswith("["))
        res = [] if is_array else {}

        for i in range(item.childCount()):
            c = item.child(i)
            key = c.text(0)
            
            if c.childCount() > 0:
                val = TreeHandler.build_dict(c)
            else:
                val_type = c.data(1, Qt.ItemDataRole.UserRole)
                orig_type = c.data(1, Qt.ItemDataRole.UserRole + 1)
                val_str = c.text(1)
                
                if val_type == "empty_dict": val = {}
                elif val_type == "empty_list": val = []
                elif val_type == "none": val = None
                elif val_type == "int":
                    int_val = int(val_str)
                    if orig_type == 'UInt' and hasattr(byml, 'UInt'): val = byml.UInt(int_val)
                    elif orig_type == 'Int64' and hasattr(byml, 'Int64'): val = byml.Int64(int_val)
                    elif orig_type == 'UInt64' and hasattr(byml, 'UInt64'): val = byml.UInt64(int_val)
                    elif hasattr(byml, 'Int'): val = byml.Int(int_val)
                    else: val = int_val
                elif val_type == "float":
                    float_val = float(val_str.replace(' ', '').replace(',', '.'))
                    if orig_type == 'Double' and hasattr(byml, 'Double'): val = byml.Double(float_val)
                    elif hasattr(byml, 'Float'): val = byml.Float(float_val)
                    else: val = float_val
                elif val_type == "bool":
                    bool_val = (val_str == "True")
                    if hasattr(byml, 'Bool'): val = byml.Bool(bool_val)
                    else: val = bool_val
                else:
                    if hasattr(byml, 'String'): val = byml.String(val_str)
                    else: val = val_str

            if is_array: res.append(val)
            else: res[key] = val
        return res