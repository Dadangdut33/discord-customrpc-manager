"""
RPC form widget for editing presence fields.

Provides input fields for all Discord RPC parameters.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QPushButton, QGroupBox, QHBoxLayout, QTextEdit,
    QLabel, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any, Optional
import time
from customrpc.utils.validators import (
    validate_app_id, validate_text_field, validate_party_size,
    validate_button_label, validate_url
)


class RPCForm(QWidget):
    """Form widget for RPC field editing."""
    
    # Signal emitted when form data changes
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize RPC form."""
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        
        # Application ID
        app_id_group = QGroupBox("Application")
        app_id_layout = QFormLayout()
        self.app_id_input = QLineEdit()
        self.app_id_input.setPlaceholderText("Enter Discord Application ID (numeric)")
        self.app_id_input.textChanged.connect(self.data_changed.emit)
        app_id_layout.addRow("Application ID:", self.app_id_input)
        app_id_group.setLayout(app_id_layout)
        layout.addWidget(app_id_group)
        
        # Text fields
        text_group = QGroupBox("Details")
        text_layout = QFormLayout()

        self.game_name_input = QLineEdit()
        self.game_name_input.setPlaceholderText("Name of the game (max 128 chars)")
        self.game_name_input.textChanged.connect(self.data_changed.emit)
        text_layout.addRow("Name:", self.game_name_input)
        
        self.details_input = QLineEdit()
        self.details_input.setPlaceholderText("What you're doing (max 128 chars)")
        self.details_input.textChanged.connect(self.data_changed.emit)
        text_layout.addRow("Details:", self.details_input)
        
        self.state_input = QLineEdit()
        self.state_input.setPlaceholderText("Current state (max 128 chars)")
        self.state_input.textChanged.connect(self.data_changed.emit)
        text_layout.addRow("State:", self.state_input)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)
        
        # Images
        image_group = QGroupBox("Images")
        image_layout = QFormLayout()
        
        self.large_image_key = QLineEdit()
        self.large_image_key.setPlaceholderText("Image key or URL")
        self.large_image_key.textChanged.connect(self.data_changed.emit)
        image_layout.addRow("Large Image Key:", self.large_image_key)
        
        self.large_image_text = QLineEdit()
        self.large_image_text.setPlaceholderText("Hover text (max 128 chars)")
        self.large_image_text.textChanged.connect(self.data_changed.emit)
        image_layout.addRow("Large Image Text:", self.large_image_text)
        
        self.small_image_key = QLineEdit()
        self.small_image_key.setPlaceholderText("Image key or URL")
        self.small_image_key.textChanged.connect(self.data_changed.emit)
        image_layout.addRow("Small Image Key:", self.small_image_key)
        
        self.small_image_text = QLineEdit()
        self.small_image_text.setPlaceholderText("Hover text (max 128 chars)")
        self.small_image_text.textChanged.connect(self.data_changed.emit)
        image_layout.addRow("Small Image Text:", self.small_image_text)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # Timestamps
        timestamp_group = QGroupBox("Timestamps")
        timestamp_layout = QVBoxLayout()
        
        # Start timestamp
        start_layout = QHBoxLayout()
        self.start_timestamp_check = QCheckBox("Start Timestamp")
        self.start_timestamp_check.toggled.connect(self._on_start_timestamp_toggled)
        self.start_timestamp_check.toggled.connect(self.data_changed.emit)
        start_layout.addWidget(self.start_timestamp_check)
        
        self.start_now_btn = QPushButton("Use Now")
        self.start_now_btn.clicked.connect(self._set_start_now)
        self.start_now_btn.setEnabled(False)
        start_layout.addWidget(self.start_now_btn)
        start_layout.addStretch()
        
        timestamp_layout.addLayout(start_layout)
        
        # End timestamp
        end_layout = QHBoxLayout()
        self.end_timestamp_check = QCheckBox("End Timestamp")
        self.end_timestamp_check.toggled.connect(self._on_end_timestamp_toggled)
        self.end_timestamp_check.toggled.connect(self.data_changed.emit)
        end_layout.addWidget(self.end_timestamp_check)
        
        self.end_now_btn = QPushButton("Use Now")
        self.end_now_btn.clicked.connect(self._set_end_now)
        self.end_now_btn.setEnabled(False)
        end_layout.addWidget(self.end_now_btn)
        end_layout.addStretch()
        
        timestamp_layout.addLayout(end_layout)
        
        timestamp_group.setLayout(timestamp_layout)
        layout.addWidget(timestamp_group)
        
        # Party
        party_group = QGroupBox("Party")
        party_layout = QFormLayout()
        
        self.party_size = QSpinBox()
        self.party_size.setMinimum(0)
        self.party_size.setMaximum(999)
        self.party_size.valueChanged.connect(self.data_changed.emit)
        party_layout.addRow("Current Size:", self.party_size)
        
        self.party_max = QSpinBox()
        self.party_max.setMinimum(0)
        self.party_max.setMaximum(999)
        self.party_max.valueChanged.connect(self.data_changed.emit)
        party_layout.addRow("Max Size:", self.party_max)
        
        party_group.setLayout(party_layout)
        layout.addWidget(party_group)
        
        # Buttons
        buttons_group = QGroupBox("Buttons (max 2)")
        buttons_layout = QVBoxLayout()
        
        # Button 1
        btn1_layout = QFormLayout()
        self.button1_label = QLineEdit()
        self.button1_label.setPlaceholderText("Button label (max 32 chars)")
        self.button1_label.textChanged.connect(self.data_changed.emit)
        btn1_layout.addRow("Button 1 Label:", self.button1_label)
        
        self.button1_url = QLineEdit()
        self.button1_url.setPlaceholderText("https://example.com")
        self.button1_url.textChanged.connect(self.data_changed.emit)
        btn1_layout.addRow("Button 1 URL:", self.button1_url)
        buttons_layout.addLayout(btn1_layout)
        
        # Button 2
        btn2_layout = QFormLayout()
        self.button2_label = QLineEdit()
        self.button2_label.setPlaceholderText("Button label (max 32 chars)")
        self.button2_label.textChanged.connect(self.data_changed.emit)
        btn2_layout.addRow("Button 2 Label:", self.button2_label)
        
        self.button2_url = QLineEdit()
        self.button2_url.setPlaceholderText("https://example.com")
        self.button2_url.textChanged.connect(self.data_changed.emit)
        btn2_layout.addRow("Button 2 URL:", self.button2_url)
        buttons_layout.addLayout(btn2_layout)
        
        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)
        
        # Instance
        self.instance_check = QCheckBox("Instance")
        self.instance_check.setToolTip("Marks the presence as a game instance")
        self.instance_check.toggled.connect(self.data_changed.emit)
        layout.addWidget(self.instance_check)
        
        layout.addStretch()
        
        # Store timestamp values
        self._start_timestamp: Optional[int] = None
        self._end_timestamp: Optional[int] = None
    
    def _on_start_timestamp_toggled(self, checked: bool) -> None:
        """Handle start timestamp checkbox toggle."""
        self.start_now_btn.setEnabled(checked)
        if checked and self._start_timestamp is None:
            self._set_start_now()
    
    def _on_end_timestamp_toggled(self, checked: bool) -> None:
        """Handle end timestamp checkbox toggle."""
        self.end_now_btn.setEnabled(checked)
        if checked and self._end_timestamp is None:
            self._set_end_now()
    
    def _set_start_now(self) -> None:
        """Set start timestamp to current time."""
        self._start_timestamp = int(time.time())
        self.data_changed.emit()
    
    def _set_end_now(self) -> None:
        """Set end timestamp to current time."""
        self._end_timestamp = int(time.time())
        self.data_changed.emit()
    
    def get_data(self) -> Dict[str, Any]:
        """
        Get form data as dictionary.
        
        Returns:
            Dictionary with all form data
        """
        data = {
            'app_id': self.app_id_input.text().strip(),
            'game_name': self.game_name_input.text().strip() or None,
            'details': self.details_input.text().strip() or None,
            'state': self.state_input.text().strip() or None,
            'large_image_key': self.large_image_key.text().strip() or None,
            'large_image_text': self.large_image_text.text().strip() or None,
            'small_image_key': self.small_image_key.text().strip() or None,
            'small_image_text': self.small_image_text.text().strip() or None,
            'start_timestamp': self._start_timestamp if self.start_timestamp_check.isChecked() else None,
            'end_timestamp': self._end_timestamp if self.end_timestamp_check.isChecked() else None,
            'party_size': self.party_size.value() if self.party_size.value() > 0 else None,
            'party_max': self.party_max.value() if self.party_max.value() > 0 else None,
            'instance': self.instance_check.isChecked() if self.instance_check.isChecked() else None,
        }
        
        # Build buttons array
        buttons = []
        if self.button1_label.text().strip() and self.button1_url.text().strip():
            buttons.append({
                'label': self.button1_label.text().strip(),
                'url': self.button1_url.text().strip()
            })
        if self.button2_label.text().strip() and self.button2_url.text().strip():
            buttons.append({
                'label': self.button2_label.text().strip(),
                'url': self.button2_url.text().strip()
            })
        
        data['buttons'] = buttons if buttons else None
        
        return data
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        Load data into form.
        
        Args:
            data: Dictionary with form data
        """
        self.app_id_input.setText(data.get('app_id', ''))
        self.game_name_input.setText(data.get('game_name', ''))
        self.details_input.setText(data.get('details', ''))
        self.state_input.setText(data.get('state', ''))
        self.large_image_key.setText(data.get('large_image_key', ''))
        self.large_image_text.setText(data.get('large_image_text', ''))
        self.small_image_key.setText(data.get('small_image_key', ''))
        self.small_image_text.setText(data.get('small_image_text', ''))
        
        # Timestamps
        self._start_timestamp = data.get('start_timestamp')
        self.start_timestamp_check.setChecked(self._start_timestamp is not None)
        
        self._end_timestamp = data.get('end_timestamp')
        self.end_timestamp_check.setChecked(self._end_timestamp is not None)
        
        # Party
        self.party_size.setValue(data.get('party_size', 0) or 0)
        self.party_max.setValue(data.get('party_max', 0) or 0)
        
        # Buttons
        buttons = data.get('buttons', [])
        if buttons is None:
            buttons = []
        if len(buttons) > 0:
            self.button1_label.setText(buttons[0].get('label', ''))
            self.button1_url.setText(buttons[0].get('url', ''))
        if len(buttons) > 1:
            self.button2_label.setText(buttons[1].get('label', ''))
            self.button2_url.setText(buttons[1].get('url', ''))
        
        # Instance
        self.instance_check.setChecked(data.get('instance', False) or False)
    
    def clear(self) -> None:
        """Clear all form fields."""
        self.app_id_input.clear()
        self.game_name_input.clear()
        self.details_input.clear()
        self.state_input.clear()
        self.large_image_key.clear()
        self.large_image_text.clear()
        self.small_image_key.clear()
        self.small_image_text.clear()
        self.start_timestamp_check.setChecked(False)
        self.end_timestamp_check.setChecked(False)
        self.party_size.setValue(0)
        self.party_max.setValue(0)
        self.button1_label.clear()
        self.button1_url.clear()
        self.button2_label.clear()
        self.button2_url.clear()
        self.instance_check.setChecked(False)
        self._start_timestamp = None
        self._end_timestamp = None
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate form data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        data = self.get_data()
        
        # Validate app ID
        valid, error = validate_app_id(data['app_id'])
        if not valid:
            return False, error
        
        # Validate text fields
        for field, max_len in [
            ('details', 128), ('state', 128),
            ('large_image_text', 128), ('small_image_text', 128)
        ]:
            if data.get(field):
                valid, error = validate_text_field(data[field], field.replace('_', ' ').title(), max_len)
                if not valid:
                    return False, error
        
        # Validate party size
        valid, error = validate_party_size(data.get('party_size'), data.get('party_max'))
        if not valid:
            return False, error
        
        # Validate buttons
        buttons = data.get('buttons', [])
        if buttons is None:
            buttons = []

        for i, button in enumerate(buttons, 1):
            valid, error = validate_button_label(button['label'])
            if not valid:
                return False, f"Button {i}: {error}"
            
            valid, error = validate_url(button['url'])
            if not valid:
                return False, f"Button {i}: {error}"
        
        return True, None
