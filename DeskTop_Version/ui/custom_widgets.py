from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

def make_input_group(label_text, widget, label_width=130):
    group = QFrame()
    group.setStyleSheet("""
        QFrame {
            background-color: #f9f9f9;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        QFrame:focus-within {
            border: 1px solid #4CAF50;
            background-color: #ffffff;
        }
    """)
    layout = QHBoxLayout(group)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    lbl = QLabel(label_text)
    lbl.setFixedWidth(label_width)
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    lbl.setStyleSheet("""
        QLabel {
            background-color: #eeeeee;
            border: none;
            border-right: 1px solid #cccccc;
            border-top-left-radius: 4px;
            border-bottom-left-radius: 4px;
            padding-right: 15px;
            color: #555555;
            font-weight: 600;
            font-size: 13px;
        }
    """)
    
    # We strip the native border from the inner widget so it blends seamlessly
    # Ensure background is transparent so the group box color shows
    widget_type = widget.metaObject().className()
    widget.setStyleSheet(f"""
        {widget_type} {{
            border: none;
            background-color: transparent;
            padding: 8px;
            color: #333333;
            font-size: 13px;
        }}
        {widget_type}:focus {{
            border: none;
            background-color: transparent;
        }}
    """)
    
    layout.addWidget(lbl)
    layout.addWidget(widget)
    # For ComboBox/SpinBox, we may want to stretch if they have native limit constraints
    layout.setStretch(1, 1)
    
    return group
