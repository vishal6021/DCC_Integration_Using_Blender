import sys
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QLineEdit, QMessageBox
)

API_URL = "http://127.0.0.1:8000"

class InventoryWorker(QThread):
    finished = pyqtSignal(list) 
    error = pyqtSignal(str)  

    def run(self):
        try:
            response = requests.get(f"{API_URL}/list-items")
            data = response.json().get("items", [])
            self.finished.emit(data)  
        except Exception as e:
            self.error.emit(str(e))  


class InventoryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Manager")
        self.setGeometry(100, 100, 500, 400)

        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Item", "Quantity"])

        self.refresh_button = QPushButton("Refresh Inventory")
        self.refresh_button.clicked.connect(self.load_inventory)  
        
        self.add_name_input = QLineEdit()
        self.add_name_input.setPlaceholderText("Item Name")
        self.add_quantity_input = QLineEdit()
        self.add_quantity_input.setPlaceholderText("Quantity")
        self.add_button = QPushButton("Add Item")
        self.add_button.clicked.connect(self.add_item)

        self.update_name_input = QLineEdit()
        self.update_name_input.setPlaceholderText("Item Name")
        self.update_quantity_input = QLineEdit()
        self.update_quantity_input.setPlaceholderText("New Quantity")
        self.update_button = QPushButton("Update Quantity")
        self.update_button.clicked.connect(self.update_quantity)

        self.delete_name_input = QLineEdit()
        self.delete_name_input.setPlaceholderText("Item Name to Delete")
        self.delete_button = QPushButton("Delete Item")
        self.delete_button.clicked.connect(self.delete_item)

        self.layout.addWidget(self.table)
        self.layout.addWidget(self.refresh_button)
        self.layout.addWidget(QLabel("Add New Item"))
        self.layout.addWidget(self.add_name_input)
        self.layout.addWidget(self.add_quantity_input)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(QLabel("Update Quantity"))
        self.layout.addWidget(self.update_name_input)
        self.layout.addWidget(self.update_quantity_input)
        self.layout.addWidget(self.update_button)
        self.layout.addWidget(QLabel("Delete Item"))
        self.layout.addWidget(self.delete_name_input)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)
        self.load_inventory()

    def load_inventory(self):
        """Start a worker thread to fetch inventory data."""
        self.worker = InventoryWorker()
        self.worker.finished.connect(self.update_inventory_table)
        self.worker.error.connect(self.show_error)
        self.worker.start()  

    def update_inventory_table(self, data):
        """Update UI table with inventory data."""
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(item["quantity"])))

    def show_error(self, message):
        """Show an error message if API call fails."""
        QMessageBox.critical(self, "Error", f"Failed to load inventory: {message}")

    def add_item(self):
        """Add an item to the inventory."""
        name = self.add_name_input.text().strip()
        quantity = self.add_quantity_input.text().strip()
        if not name or not quantity.isdigit():
            QMessageBox.warning(self, "Input Error", "Please enter valid item details.")
            return

        try:
            response = requests.post(f"{API_URL}/add-item", json={"name": name, "quantity": int(quantity)})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Item added successfully!")
                self.load_inventory()
            else:
                QMessageBox.warning(self, "Error", response.json().get("detail", "Failed to add item"))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add item: {e}")

    def update_quantity(self):
        """Update the quantity of an existing item."""
        name = self.update_name_input.text().strip()
        new_quantity = self.update_quantity_input.text().strip()
        if not name or not new_quantity.isdigit():
            QMessageBox.warning(self, "Input Error", "Please enter valid item details.")
            return

        try:
            response = requests.put(f"{API_URL}/update-quantity", json={"name": name, "new_quantity": int(new_quantity)})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Quantity updated successfully!")
                self.load_inventory()
            else:
                QMessageBox.warning(self, "Error", response.json().get("detail", "Failed to update quantity"))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update quantity: {e}")

    def delete_item(self):
        """Delete an item from the inventory."""
        name = self.delete_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please enter a valid item name.")
            return

        try:
            response = requests.delete(f"{API_URL}/remove-item", params={"name": name})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Item deleted successfully!")
                self.load_inventory()
            else:
                QMessageBox.warning(self, "Error", response.json().get("detail", "Failed to delete item"))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete item: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryApp()
    window.show()
    sys.exit(app.exec_())
