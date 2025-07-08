import sys
import sqlite3
import shutil
import hashlib
import csv
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout,
    QMessageBox, QDialog, QHeaderView, QDialogButtonBox, QFormLayout, QSplitter, QComboBox, QFileDialog, QTabWidget, QScrollArea, QDateEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from classic_main_window import ClassicMainWindow, current_user, current_user_role

# --- Global Variable for Current User ---
current_user_role = None # Will be set after successful login

# --- Utility Functions ---
def run_query(query, params=(), fetch=None):
    try:
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch == "one":
            result = cursor.fetchone()
        elif fetch == "all":
            result = cursor.fetchall()
        else:
            result = None
        conn.commit()
        return result
    except sqlite3.Error as e:
        show_error_message(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def show_error_message(message):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setText(message)
    msg_box.setWindowTitle("Error")
    msg_box.exec()

def show_info_message(message):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setText(message)
    msg_box.setWindowTitle("Information")
    msg_box.exec()

def get_account_id(account_name):
    account = run_query("SELECT id FROM chart_of_accounts WHERE account_name = ?", (account_name,), fetch="one")
    if account: return account[0]
    return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Forms (QDialogs for pop-ups) ---
class ProductForm(QDialog):
    def __init__(self, product=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Product")
        self.layout = QFormLayout(self)
        self.name_input = QLineEdit(product[1] if product else "")
        self.barcode_input = QLineEdit(product[2] if product else "")
        self.price_input = QLineEdit(str(product[3]) if product else "")
        self.stock_input = QLineEdit(str(product[4]) if product else "")
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Barcode:", self.barcode_input)
        self.layout.addRow("Price:", self.price_input)
        self.layout.addRow("Stock:", self.stock_input)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "barcode": self.barcode_input.text(),
            "price": float(self.price_input.text()),
            "stock": int(self.stock_input.text())
        }

class SupplierForm(QDialog):
    def __init__(self, supplier=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Supplier")
        self.layout = QFormLayout(self)
        self.name_input = QLineEdit(supplier[1] if supplier else "")
        self.contact_input = QLineEdit(supplier[2] if supplier else "")
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Contact Info:", self.contact_input)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "contact": self.contact_input.text()
        }

class AccountForm(QDialog):
    def __init__(self, account=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Account")
        self.layout = QFormLayout(self)
        self.name_input = QLineEdit(account[1] if account else "")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Asset", "Liability", "Equity", "Revenue", "Expense"])
        if account: self.type_combo.setCurrentText(account[2])
        self.initial_balance_input = QLineEdit(str(account[3]) if account else "0.0")
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Type:", self.type_combo)
        self.layout.addRow("Initial Balance:", self.initial_balance_input)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "type": self.type_combo.currentText(),
            "initial_balance": float(self.initial_balance_input.text())
        }

class JournalEntryForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Journal Entry")
        self.setGeometry(200, 200, 600, 400)
        self.layout = QVBoxLayout(self)

        self.description_input = QLineEdit()
        self.layout.addWidget(QLabel("Description:"))
        self.layout.addWidget(self.description_input)

        self.entry_items_table = QTableWidget()
        self.entry_items_table.setColumnCount(3)
        self.entry_items_table.setHorizontalHeaderLabels(["Account", "Debit", "Credit"])
        self.entry_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.entry_items_table)

        add_row_button = QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_entry_row)
        self.layout.addWidget(add_row_button)

        self.total_debit_label = QLabel("Total Debit: $0.00")
        self.total_credit_label = QLabel("Total Credit: $0.00")
        self.layout.addWidget(self.total_debit_label)
        self.layout.addWidget(self.total_credit_label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.load_accounts_for_combo()
        self.add_entry_row() # Start with one row

    def load_accounts_for_combo(self):
        self.accounts = run_query("SELECT id, account_name FROM chart_of_accounts", fetch="all")
        self.account_names = {acc[0]: acc[1] for acc in self.accounts}
        self.account_ids = {acc[1]: acc[0] for acc in self.accounts}

    def add_entry_row(self):
        row_position = self.entry_items_table.rowCount()
        self.entry_items_table.insertRow(row_position)

        account_combo = QComboBox()
        for acc_id, acc_name in self.accounts:
            account_combo.addItem(acc_name, acc_id)
        self.entry_items_table.setCellWidget(row_position, 0, account_combo)

        debit_input = QLineEdit("0.00")
        debit_input.textChanged.connect(self.calculate_totals)
        self.entry_items_table.setCellWidget(row_position, 1, debit_input)

        credit_input = QLineEdit("0.00")
        credit_input.textChanged.connect(self.calculate_totals)
        self.entry_items_table.setCellWidget(row_position, 2, credit_input)

        self.calculate_totals()

    def calculate_totals(self):
        total_debit = 0.0
        total_credit = 0.0
        for row in range(self.entry_items_table.rowCount()):
            debit_input = self.entry_items_table.cellWidget(row, 1)
            credit_input = self.entry_items_table.cellWidget(row, 2)
            try:
                total_debit += float(debit_input.text())
            except ValueError: pass
            try:
                total_credit += float(credit_input.text())
            except ValueError: pass
        self.total_debit_label.setText(f"Total Debit: ${total_debit:.2f}")
        self.total_credit_label.setText(f"Total Credit: ${total_credit:.2f}")

    def validate_and_accept(self):
        total_debit = 0.0
        total_credit = 0.0
        for row in range(self.entry_items_table.rowCount()):
            debit_input = self.entry_items_table.cellWidget(row, 1)
            credit_input = self.entry_items_table.cellWidget(row, 2)
            try:
                total_debit += float(debit_input.text())
            except ValueError: pass
            try:
                total_credit += float(credit_input.text())
            except ValueError: pass

        if abs(total_debit - total_credit) > 0.001: # Allow for floating point inaccuracies
            show_error_message("Debits and Credits must balance!")
        else:
            self.accept()

    def get_entry_data(self):
        description = self.description_input.text()
        total_amount = float(self.total_debit_label.text().replace("Total Debit: $", ""))
        items = []
        for row in range(self.entry_items_table.rowCount()):
            account_combo = self.entry_items_table.cellWidget(row, 0)
            debit_input = self.entry_items_table.cellWidget(row, 1)
            credit_input = self.entry_items_table.cellWidget(row, 2)
            account_id = account_combo.currentData()
            debit = float(debit_input.text())
            credit = float(credit_input.text())
            items.append({"account_id": account_id, "debit": debit, "credit": credit})
        return description, total_amount, items

class CustomerForm(QDialog):
    def __init__(self, customer=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Customer")
        self.layout = QFormLayout(self)
        self.name_input = QLineEdit(customer[1] if customer else "")
        self.phone_input = QLineEdit(customer[2] if customer else "")
        self.email_input = QLineEdit(customer[3] if customer else "")
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Phone:", self.phone_input)
        self.layout.addRow("Email:", self.email_input)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "phone": self.phone_input.text(),
            "email": self.email_input.text()
        }

class UserForm(QDialog):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit User")
        self.layout = QFormLayout(self)
        self.username_input = QLineEdit(user[1] if user else "")
        self.password_input = QLineEdit("") # Never pre-fill passwords
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Admin", "Staff"])
        if user: self.role_combo.setCurrentText(user[3])

        self.layout.addRow("Username:", self.username_input)
        self.layout.addRow("Password:", self.password_input)
        self.layout.addRow("Role:", self.role_combo)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self):
        return {
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "role": self.role_combo.currentText()
        }

# --- Widgets (for tabs) ---
class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("Dashboard"))

        self.sales_today_label = QLabel("Sales Today: $0.00")
        self.layout.addWidget(self.sales_today_label)

        self.sales_week_label = QLabel("Sales This Week: $0.00")
        self.layout.addWidget(self.sales_week_label)

        self.sales_month_label = QLabel("Sales This Month: $0.00")
        self.layout.addWidget(self.sales_month_label)

        self.products_in_stock_label = QLabel("Products in Stock: 0")
        self.layout.addWidget(self.products_in_stock_label)

        self.low_stock_items_label = QLabel("Low Stock Items: 0")
        self.layout.addWidget(self.low_stock_items_label)

        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(3)
        self.recent_sales_table.setHorizontalHeaderLabels(["Sale ID", "Date", "Total Amount"])
        self.recent_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.recent_sales_table)

        self.load_dashboard_data()

    def load_dashboard_data(self):
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        sales_today = run_query("SELECT SUM(total_amount) FROM sales WHERE sale_date LIKE ?", (f"{today}%",), fetch="one")[0] or 0.0
        self.sales_today_label.setText(f"Sales Today: ${sales_today:.2f}")

        sales_week = run_query("SELECT SUM(total_amount) FROM sales WHERE sale_date BETWEEN ? AND ?", (week_ago, today), fetch="one")[0] or 0.0
        self.sales_week_label.setText(f"Sales This Week: ${sales_week:.2f}")

        sales_month = run_query("SELECT SUM(total_amount) FROM sales WHERE sale_date BETWEEN ? AND ?", (month_ago, today), fetch="one")[0] or 0.0
        self.sales_month_label.setText(f"Sales This Month: ${sales_month:.2f}")

        products_in_stock = run_query("SELECT COUNT(*) FROM products WHERE stock_quantity > 0", fetch="one")[0] or 0
        self.products_in_stock_label.setText(f"Products in Stock: {products_in_stock}")

        low_stock_items = run_query("SELECT COUNT(*) FROM products WHERE stock_quantity <= 10", fetch="one")[0] or 0
        self.low_stock_items_label.setText(f"Low Stock Items: {low_stock_items}")

        recent_sales = run_query("SELECT id, sale_date, total_amount FROM sales ORDER BY sale_date DESC LIMIT 5", fetch="all")
        self.recent_sales_table.setRowCount(0)
        if recent_sales:
            self.recent_sales_table.setRowCount(len(recent_sales))
            for row_num, sale in enumerate(recent_sales):
                self.recent_sales_table.setItem(row_num, 0, QTableWidgetItem(str(sale[0])))
                self.recent_sales_table.setItem(row_num, 1, QTableWidgetItem(sale[1]))
                self.recent_sales_table.setItem(row_num, 2, QTableWidgetItem(f"${sale[2]:.2f}"))

class POSWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sales_items = {}
        main_layout = QVBoxLayout(self)

        # Barcode, Description, Qty, Price, Add button row
        barcode_layout = QHBoxLayout()
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Enter barcode...")
        self.barcode_input.setMaximumWidth(180)
        self.barcode_input.returnPressed.connect(self.add_item_to_sale)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Description")
        self.description_input.setMaximumWidth(320)

        self.qty_input = QLineEdit("1")
        self.qty_input.setMaximumWidth(60)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price")
        self.price_input.setMaximumWidth(100)

        add_item_button = QPushButton("Add")
        add_item_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        add_item_button.setFixedWidth(100)
        add_item_button.clicked.connect(self.add_item_to_sale)

        barcode_layout.addWidget(QLabel("Part No./Barcode:"))
        barcode_layout.addWidget(self.barcode_input)
        barcode_layout.addWidget(QLabel("Description:"))
        barcode_layout.addWidget(self.description_input)
        barcode_layout.addWidget(QLabel("Qty:"))
        barcode_layout.addWidget(self.qty_input)
        barcode_layout.addWidget(QLabel("Price:"))
        barcode_layout.addWidget(self.price_input)
        barcode_layout.addWidget(add_item_button)
        main_layout.addLayout(barcode_layout)

        # Product search by name
        search_layout = QHBoxLayout()
        self.product_search_input = QLineEdit()
        self.product_search_input.setPlaceholderText("Search product by name...")
        self.product_search_input.returnPressed.connect(self.search_products)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_products)
        search_layout.addWidget(QLabel("Product Name:"))
        search_layout.addWidget(self.product_search_input)
        search_layout.addWidget(search_button)
        main_layout.addLayout(search_layout)

        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(4)
        self.search_results_table.setHorizontalHeaderLabels(["ID", "Name", "Barcode", "Price"])
        self.search_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.search_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.search_results_table.itemDoubleClicked.connect(self.add_selected_product_to_sale)
        main_layout.addWidget(self.search_results_table)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels(["Product Name", "Quantity", "Price", "Total"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.sales_table)

        bottom_layout = QHBoxLayout()
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        complete_sale_button = QPushButton("Complete Sale")
        complete_sale_button.clicked.connect(self.complete_sale)

        bottom_layout.addWidget(self.total_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(complete_sale_button)
        main_layout.addLayout(bottom_layout)

    def add_item_to_sale(self):
        barcode = self.barcode_input.text()
        if not barcode: return
        product = run_query("SELECT * FROM products WHERE barcode = ?", (barcode,), fetch="one")
        if product:
            if barcode in self.sales_items:
                self.update_item_quantity(barcode)
            else:
                self.add_new_item_to_table(product)
            self.update_total()
        else:
            show_error_message(f"Product with barcode '{barcode}' not found.")
        self.barcode_input.clear()
        self.barcode_input.setFocus()

    def search_products(self):
        search_term = self.product_search_input.text()
        if not search_term:
            self.search_results_table.setRowCount(0)
            return

        products = run_query("SELECT id, name, barcode, price FROM products WHERE name LIKE ?", (f"%{search_term}%",), fetch="all")
        
        self.search_results_table.setRowCount(0) # Clear previous results
        if products:
            self.search_results_table.setRowCount(len(products))
            for row_num, product in enumerate(products):
                for col_num, data in enumerate(product):
                    self.search_results_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))
        else:
            show_info_message(f"No products found matching '{search_term}'.")

    def add_selected_product_to_sale(self, item):
        # Get the barcode from the clicked row (assuming barcode is in column 2)
        barcode = self.search_results_table.item(item.row(), 2).text()
        self.barcode_input.setText(barcode) # Populate barcode input
        self.add_item_to_sale() # Add to sale
        self.search_results_table.setRowCount(0) # Clear search results
        self.product_search_input.clear() # Clear search input

    def add_new_item_to_table(self, product):
        product_id, product_name, _, price, _ = product
        quantity = 1
        row_position = self.sales_table.rowCount()
        self.sales_table.insertRow(row_position)
        self.sales_table.setItem(row_position, 0, QTableWidgetItem(product_name))
        self.sales_table.setItem(row_position, 1, QTableWidgetItem(str(quantity)))
        self.sales_table.setItem(row_position, 2, QTableWidgetItem(f"${price:.2f}"))
        self.sales_table.setItem(row_position, 3, QTableWidgetItem(f"${price * quantity:.2f}"))
        self.sales_items[product[2]] = {"row": row_position, "id": product_id, "name": product_name, "price": price, "quantity": quantity}

    def update_item_quantity(self, barcode):
        item_info = self.sales_items[barcode]
        item_info["quantity"] += 1
        row = item_info["row"]
        self.sales_table.item(row, 1).setText(str(item_info["quantity"]))
        total_price = item_info["price"] * item_info["quantity"]
        self.sales_table.item(row, 3).setText(f"${total_price:.2f}")

    def update_total(self):
        total = sum(item["price"] * item["quantity"] for item in self.sales_items.values())
        self.total_label.setText(f"Total: ${total:.2f}")

    def complete_sale(self):
        if not self.sales_items: return
        total_amount = sum(item["price"] * item["quantity"] for item in self.sales_items.values())
        sale_id = run_query("INSERT INTO sales (total_amount) VALUES (?)", (total_amount,), fetch="one")
        sale_id = run_query("SELECT last_insert_rowid()", fetch="one")[0]
        for item in self.sales_items.values():
            run_query("INSERT INTO sale_items (sale_id, product_id, quantity, price_per_unit) VALUES (?, ?, ?, ?)", (sale_id, item["id"], item["quantity"], item["price"]))
            run_query("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?", (item["quantity"], item["id"]))
        
        # Automated Journal Entry for Sale
        cash_account_id = get_account_id("Cash")
        sales_revenue_account_id = get_account_id("Sales Revenue")
        inventory_account_id = get_account_id("Inventory")
        cogs_account_id = get_account_id("Cost of Goods Sold")

        if cash_account_id and sales_revenue_account_id and inventory_account_id and cogs_account_id:
            # Entry for Cash and Sales Revenue
            entry_id = run_query("INSERT INTO journal_entries (description, total_amount) VALUES (?, ?)", (f"Sale #{sale_id}", total_amount), fetch="one")
            entry_id = run_query("SELECT last_insert_rowid()", fetch="one")[0]
            run_query("INSERT INTO journal_entry_items (journal_entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                      (entry_id, cash_account_id, total_amount, 0.0))
            run_query("INSERT INTO journal_entry_items (journal_entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                      (entry_id, sales_revenue_account_id, 0.0, total_amount))
            
            # Entry for Cost of Goods Sold and Inventory
            total_cogs = 0.0
            for item in self.sales_items.values():
                product_cost = run_query("SELECT price FROM products WHERE id = ?", (item["id"],), fetch="one")[0] # Assuming price is cost for simplicity
                total_cogs += product_cost * item["quantity"]

            entry_id_cogs = run_query("INSERT INTO journal_entries (description, total_amount) VALUES (?, ?)", (f"COGS for Sale #{sale_id}", total_cogs), fetch="one")
            entry_id_cogs = run_query("SELECT last_insert_rowid()", fetch="one")[0]
            run_query("INSERT INTO journal_entry_items (journal_entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                      (entry_id_cogs, cogs_account_id, total_cogs, 0.0))
            run_query("INSERT INTO journal_entry_items (journal_entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                      (entry_id_cogs, inventory_account_id, 0.0, total_cogs))
        else:
            show_error_message("Missing required accounts for automated journal entry (Sales).")

        QMessageBox.information(self, "Sale Complete", f"Sale #{sale_id} completed successfully!")
        self.reset_sale()

    def reset_sale(self):
        self.sales_table.setRowCount(0)
        self.sales_items = {}
        self.update_total()

class StockManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock Management")
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Stock List Tab
        self.stock_list_tab = QWidget()
        self.tabs.addTab(self.stock_list_tab, "Stock List")
        self.stock_list_layout = QVBoxLayout(self.stock_list_tab)
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(5)
        self.stock_table.setHorizontalHeaderLabels(["ID", "Name", "Barcode", "Price", "Stock"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stock_list_layout.addWidget(self.stock_table)
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Product")
        add_button.clicked.connect(self.add_product)
        update_button = QPushButton("Update Product")
        update_button.clicked.connect(self.update_product)
        delete_button = QPushButton("Delete Product")
        delete_button.clicked.connect(self.delete_product)
        button_layout.addWidget(add_button)
        button_layout.addWidget(update_button)
        button_layout.addWidget(delete_button)
        self.stock_list_layout.addLayout(button_layout)
        self.load_stock()

        # Stock Reports Tab
        self.stock_reports_tab = QWidget()
        self.tabs.addTab(self.stock_reports_tab, "Reports")
        self.stock_reports_layout = QVBoxLayout(self.stock_reports_tab)
        self.stock_reports_layout.addWidget(QLabel("Stock Reports"))
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(3)
        self.low_stock_table.setHorizontalHeaderLabels(["Product Name", "Barcode", "Stock Level"])
        self.low_stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stock_reports_layout.addWidget(self.low_stock_table)
        self.load_low_stock_report()

    def load_stock(self):
        products = run_query("SELECT * FROM products", fetch="all")
        if products is not None:
            self.stock_table.setRowCount(len(products))
            for row_num, product in enumerate(products):
                for col_num, data in enumerate(product):
                    self.stock_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))

    def load_low_stock_report(self, threshold=10):
        low_stock_products = run_query("SELECT name, barcode, stock_quantity FROM products WHERE stock_quantity <= ?", (threshold,), fetch="all")
        self.low_stock_table.setRowCount(0)
        if low_stock_products:
            self.low_stock_table.setRowCount(len(low_stock_products))
            for row_num, product in enumerate(low_stock_products):
                for col_num, data in enumerate(product):
                    self.low_stock_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))

    def add_product(self):
        form = ProductForm(parent=self)
        if form.exec() == QDialog.DialogCode.Accepted:
            data = form.get_data()
            run_query("INSERT INTO products (name, barcode, price, stock_quantity) VALUES (?, ?, ?, ?)", (data["name"], data["barcode"], data["price"], data["stock"]))
            self.load_stock()
            self.load_low_stock_report()

    def update_product(self):
        selected_row = self.stock_table.currentRow()
        if selected_row == -1:
            show_error_message("Please select a product to update.")
            return
        product_id = self.stock_table.item(selected_row, 0).text()
        product = run_query("SELECT * FROM products WHERE id = ?", (product_id,), fetch="one")
        if product:
            form = ProductForm(product=product, parent=self)
            if form.exec() == QDialog.DialogCode.Accepted:
                data = form.get_data()
                run_query("UPDATE products SET name=?, barcode=?, price=?, stock_quantity=? WHERE id=?", (data["name"], data["barcode"], data["price"], data["stock"], product_id))
                self.load_stock()
                self.load_low_stock_report()

    def delete_product(self):
        selected_row = self.stock_table.currentRow()
        if selected_row == -1:
            show_error_message("Please select a product to delete.")
            return
        product_id = self.stock_table.item(selected_row, 0).text()
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete product ID {product_id}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            run_query("DELETE FROM products WHERE id = ?", (product_id,))
            self.load_stock()
            self.load_low_stock_report()

class SalesHistoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Sales List Tab
        self.sales_list_tab = QWidget()
        self.tabs.addTab(self.sales_list_tab, "Sales List")
        self.sales_list_layout = QVBoxLayout(self.sales_list_tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(3)
        self.sales_table.setHorizontalHeaderLabels(["Sale ID", "Date", "Total Amount"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_table.selectionModel().selectionChanged.connect(self.load_sale_items)
        splitter.addWidget(self.sales_table)
        self.sale_items_table = QTableWidget()
        self.sale_items_table.setColumnCount(4)
        self.sale_items_table.setHorizontalHeaderLabels(["Product Name", "Quantity", "Price Per Unit", "Total"])
        self.sale_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        splitter.addWidget(self.sale_items_table)
        self.sales_list_layout.addWidget(splitter)
        self.load_sales()

        # Sales Reports Tab
        self.sales_reports_tab = QWidget()
        self.tabs.addTab(self.sales_reports_tab, "Reports")
        self.sales_reports_layout = QVBoxLayout(self.sales_reports_tab)

        # Date Range Selection
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1)) # Default to last month
        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_range_layout.addWidget(self.end_date)
        generate_report_button = QPushButton("Generate Sales Report")
        generate_report_button.clicked.connect(self.generate_sales_report)
        date_range_layout.addWidget(generate_report_button)
        self.sales_reports_layout.addLayout(date_range_layout)

        self.sales_summary_label = QLabel("Total Sales: $0.00")
        self.sales_reports_layout.addWidget(self.sales_summary_label)

        self.sales_by_product_table = QTableWidget()
        self.sales_by_product_table.setColumnCount(3)
        self.sales_by_product_table.setHorizontalHeaderLabels(["Product Name", "Quantity Sold", "Revenue"])
        self.sales_by_product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sales_reports_layout.addWidget(self.sales_by_product_table)

        export_sales_button = QPushButton("Export Sales Report to CSV")
        export_sales_button.clicked.connect(self.export_sales_report)
        self.sales_reports_layout.addWidget(export_sales_button)

    def load_sales(self):
        sales = run_query("SELECT id, sale_date, total_amount FROM sales ORDER BY sale_date DESC", fetch="all")
        if sales:
            self.sales_table.setRowCount(len(sales))
            for row_num, sale in enumerate(sales):
                self.sales_table.setItem(row_num, 0, QTableWidgetItem(str(sale[0])))
                self.sales_table.setItem(row_num, 1, QTableWidgetItem(sale[1]))
                self.sales_table.setItem(row_num, 2, QTableWidgetItem(f"${sale[2]:.2f}"))

    def load_sale_items(self, selected):
        self.sale_items_table.setRowCount(0)
        if not selected.indexes(): return
        selected_row = selected.indexes()[0].row()
        sale_id = self.sales_table.item(selected_row, 0).text()
        query = "SELECT p.name, si.quantity, si.price_per_unit, (si.quantity * si.price_per_unit) FROM sale_items si JOIN products p ON si.product_id = p.id WHERE si.sale_id = ?"
        items = run_query(query, (sale_id,), fetch="all")
        if items:
            self.sale_items_table.setRowCount(len(items))
            for row_num, item in enumerate(items):
                self.sale_items_table.setItem(row_num, 0, QTableWidgetItem(item[0]))
                self.sale_items_table.setItem(row_num, 1, QTableWidgetItem(str(item[1])))
                self.sale_items_table.setItem(row_num, 2, QTableWidgetItem(f"${item[2]:.2f}"))
                self.sale_items_table.setItem(row_num, 3, QTableWidgetItem(f"${item[3]:.2f}"))

    def generate_sales_report(self):
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)

        # Total Sales
        total_sales_query = "SELECT SUM(total_amount) FROM sales WHERE sale_date BETWEEN ? AND ?"
        total_sales = run_query(total_sales_query, (start_date, end_date), fetch="one")[0] or 0.0
        self.sales_summary_label.setText(f"Total Sales: ${total_sales:.2f}")

        # Sales by Product
        sales_by_product_query = """
        SELECT p.name, SUM(si.quantity), SUM(si.quantity * si.price_per_unit)
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        JOIN products p ON si.product_id = p.id
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY p.name
        ORDER BY SUM(si.quantity * si.price_per_unit) DESC
        """
        sales_by_product = run_query(sales_by_product_query, (start_date, end_date), fetch="all")

        self.sales_by_product_table.setRowCount(0)
        if sales_by_product:
            self.sales_by_product_table.setRowCount(len(sales_by_product))
            for row_num, data in enumerate(sales_by_product):
                self.sales_by_product_table.setItem(row_num, 0, QTableWidgetItem(data[0]))
                self.sales_by_product_table.setItem(row_num, 1, QTableWidgetItem(str(data[1])))
                self.sales_by_product_table.setItem(row_num, 2, QTableWidgetItem(f"${data[2]:.2f}"))

    def export_sales_report(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setNameFilter("CSV Files (*.csv)")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix("csv")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            try:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([self.sales_summary_label.text()])
                    writer.writerow(["Product Name", "Quantity Sold", "Revenue"])
                    for row in range(self.sales_by_product_table.rowCount()):
                        row_data = []
                        for col in range(self.sales_by_product_table.columnCount()):
                            row_data.append(self.sales_by_product_table.item(row, col).text())
                        writer.writerow(row_data)
                show_info_message("Sales report exported successfully!")
            except Exception as e:
                show_error_message(f"Error exporting sales report: {e}")

class PurchasingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Purchasing")
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Supplier Management Tab
        self.supplier_tab = QWidget()
        self.tabs.addTab(self.supplier_tab, "Suppliers")
        self.supplier_layout = QVBoxLayout(self.supplier_tab)
        self.supplier_layout.addWidget(QLabel("Suppliers"))
        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(3)
        self.supplier_table.setHorizontalHeaderLabels(["ID", "Name", "Contact"])
        self.supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.supplier_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.supplier_layout.addWidget(self.supplier_table)
        supplier_button_layout = QHBoxLayout()
        add_supplier_button = QPushButton("Add Supplier")
        add_supplier_button.clicked.connect(self.add_supplier)
        update_supplier_button = QPushButton("Update Supplier")
        update_supplier_button.clicked.connect(self.update_supplier)
        supplier_button_layout.addWidget(add_supplier_button)
        supplier_button_layout.addWidget(update_supplier_button)
        self.supplier_layout.addLayout(supplier_button_layout)
        self.load_suppliers()

        # Purchase Order Tab
        self.po_tab = QWidget()
        self.tabs.addTab(self.po_tab, "Purchase Orders")
        self.po_layout = QVBoxLayout(self.po_tab)
        self.po_layout.addWidget(QLabel("New Purchase Order"))
        self.supplier_combo = QComboBox()
        self.po_layout.addWidget(self.supplier_combo)
        self.po_table = QTableWidget()
        self.po_table.setColumnCount(4)
        self.po_table.setHorizontalHeaderLabels(["Product ID", "Name", "Quantity", "Cost Per Unit"])
        self.po_layout.addWidget(self.po_table)
        po_button_layout = QHBoxLayout()
        add_product_to_po_button = QPushButton("Add Product")
        add_product_to_po_button.clicked.connect(self.add_product_to_po)
        complete_po_button = QPushButton("Complete Purchase Order")
        complete_po_button.clicked.connect(self.complete_po)
        po_button_layout.addWidget(add_product_to_po_button)
        po_button_layout.addWidget(complete_po_button)
        self.po_layout.addLayout(po_button_layout)

        # Purchasing Reports Tab
        self.purchasing_reports_tab = QWidget()
        self.tabs.addTab(self.purchasing_reports_tab, "Reports")
        self.purchasing_reports_layout = QVBoxLayout(self.purchasing_reports_tab)

        # Date Range Selection
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("From:"))
        self.po_start_date = QDateEdit()
        self.po_start_date.setCalendarPopup(True)
        self.po_start_date.setDate(QDate.currentDate().addMonths(-1))
        date_range_layout.addWidget(self.po_start_date)
        date_range_layout.addWidget(QLabel("To:"))
        self.po_end_date = QDateEdit()
        self.po_end_date.setCalendarPopup(True)
        self.po_end_date.setDate(QDate.currentDate())
        date_range_layout.addWidget(self.po_end_date)
        generate_po_report_button = QPushButton("Generate PO Report")
        generate_po_report_button.clicked.connect(self.generate_po_report)
        date_range_layout.addWidget(generate_po_report_button)
        self.purchasing_reports_layout.addLayout(date_range_layout)

        self.po_summary_label = QLabel("Total Purchases: $0.00")
        self.purchasing_reports_layout.addWidget(self.po_summary_label)

        self.po_by_supplier_table = QTableWidget()
        self.po_by_supplier_table.setColumnCount(2)
        self.po_by_supplier_table.setHorizontalHeaderLabels(["Supplier", "Total Purchased"])
        self.po_by_supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.purchasing_reports_layout.addWidget(self.po_by_supplier_table)

        self.po_by_product_table = QTableWidget()
        self.po_by_product_table.setColumnCount(3)
        self.po_by_product_table.setHorizontalHeaderLabels(["Product Name", "Quantity Purchased", "Total Cost"])
        self.po_by_product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.purchasing_reports_layout.addWidget(self.po_by_product_table)

        export_po_button = QPushButton("Export Purchase Report to CSV")
        export_po_button.clicked.connect(self.export_po_report)
        self.purchasing_reports_layout.addWidget(export_po_button)

        self.load_suppliers()

    def load_suppliers(self):
        suppliers = run_query("SELECT * FROM suppliers", fetch="all")
        if suppliers:
            self.supplier_table.setRowCount(len(suppliers))
            self.supplier_combo.clear()
            for row_num, supplier in enumerate(suppliers):
                self.supplier_table.setItem(row_num, 0, QTableWidgetItem(str(supplier[0])))
                self.supplier_table.setItem(row_num, 1, QTableWidgetItem(supplier[1]))
                self.supplier_table.setItem(row_num, 2, QTableWidgetItem(supplier[2]))
                self.supplier_combo.addItem(supplier[1], supplier[0])

    def add_supplier(self):
        form = SupplierForm(parent=self)
        if form.exec() == QDialog.DialogCode.Accepted:
            data = form.get_data()
            run_query("INSERT INTO suppliers (name, contact_info) VALUES (?, ?)", (data["name"], data["contact"]))
            self.load_suppliers()

    def update_supplier(self):
        selected_row = self.supplier_table.currentRow()
        if selected_row == -1: return
        supplier_id = self.supplier_table.item(selected_row, 0).text()
        supplier = run_query("SELECT * FROM suppliers WHERE id = ?", (supplier_id,), fetch="one")
        if supplier:
            form = SupplierForm(supplier=supplier, parent=self)
            if form.exec() == QDialog.DialogCode.Accepted:
                data = form.get_data()
                run_query("UPDATE suppliers SET name=?, contact_info=? WHERE id=?", (data["name"], data["contact"], supplier_id))
                self.load_suppliers()

    def add_product_to_po(self):
        # In a real app, this would be a product selection dialog
        product_id, ok = QLineEdit.getText(self, 'Add Product', 'Enter Product ID:')
        if ok and product_id:
            product = run_query("SELECT * FROM products WHERE id = ?", (product_id,), fetch="one")
            if product:
                row_pos = self.po_table.rowCount()
                self.po_table.insertRow(row_pos)
                self.po_table.setItem(row_pos, 0, QTableWidgetItem(str(product[0])))
                self.po_table.setItem(row_pos, 1, QTableWidgetItem(product[1]))
                self.po_table.setItem(row_pos, 2, QTableWidgetItem("1")) # Default quantity
                self.po_table.setItem(row_pos, 3, QTableWidgetItem(f"{product[3]:.2f}")) # Use product price as default cost
            else:
                show_error_message("Product not found.")

    def complete_po(self):
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id: return
        
        total_cost = 0
        for row in range(self.po_table.rowCount()):
            total_cost += float(self.po_table.item(row, 3).text()) * int(self.po_table.item(row, 2).text())

        po_id = run_query("INSERT INTO purchase_orders (supplier_id, total_amount) VALUES (?, ?)", (supplier_id, total_cost), fetch="one")
        po_id = run_query("SELECT last_insert_rowid()", fetch="one")[0]

        for row in range(self.po_table.rowCount()):
            product_id = self.po_table.item(row, 0).text()
            quantity = int(self.po_table.item(row, 2).text())
            cost = float(self.po_table.item(row, 3).text())
            run_query("INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, cost_per_unit) VALUES (?, ?, ?, ?)", (po_id, product_id, quantity, cost))
            run_query("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?", (quantity, product_id))
        
        # Automated Journal Entry for Purchase
        inventory_account_id = get_account_id("Inventory")
        accounts_payable_account_id = get_account_id("Accounts Payable")

        if inventory_account_id and accounts_payable_account_id:
            entry_id = run_query("INSERT INTO journal_entries (description, total_amount) VALUES (?, ?)", (f"Purchase Order #{po_id}", total_cost), fetch="one")
            entry_id = run_query("SELECT last_insert_rowid()", fetch="one")[0]
            run_query("INSERT INTO journal_entry_items (journal_entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                      (entry_id, inventory_account_id, total_cost, 0.0))
            run_query("INSERT INTO journal_entry_items (journal_entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                      (entry_id, accounts_payable_account_id, 0.0, total_cost))
        else:
            show_error_message("Missing required accounts for automated journal entry (Purchase).")

        QMessageBox.information(self, "Success", "Purchase Order completed and stock updated.")
        self.po_table.setRowCount(0)

    def generate_po_report(self):
        start_date = self.po_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.po_end_date.date().toString(Qt.DateFormat.ISODate)

        # Total Purchases
        total_purchases_query = "SELECT SUM(total_amount) FROM purchase_orders WHERE order_date BETWEEN ? AND ?"
        total_purchases = run_query(total_purchases_query, (start_date, end_date), fetch="one")[0] or 0.0
        self.po_summary_label.setText(f"Total Purchases: ${total_purchases:.2f}")

        # Purchases by Supplier
        po_by_supplier_query = """
        SELECT s.name, SUM(po.total_amount)
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.order_date BETWEEN ? AND ?
        GROUP BY s.name
        ORDER BY SUM(po.total_amount) DESC
        """
        po_by_supplier = run_query(po_by_supplier_query, (start_date, end_date), fetch="all")

        self.po_by_supplier_table.setRowCount(0)
        if po_by_supplier:
            self.po_by_supplier_table.setRowCount(len(po_by_supplier))
            for row_num, data in enumerate(po_by_supplier):
                self.po_by_supplier_table.setItem(row_num, 0, QTableWidgetItem(data[0]))
                self.po_by_supplier_table.setItem(row_num, 1, QTableWidgetItem(f"${data[1]:.2f}"))

        # Purchases by Product
        po_by_product_query = """
        SELECT p.name, SUM(poi.quantity), SUM(poi.quantity * poi.cost_per_unit)
        FROM purchase_order_items poi
        JOIN purchase_orders po ON poi.purchase_order_id = po.id
        JOIN products p ON poi.product_id = p.id
        WHERE po.order_date BETWEEN ? AND ?
        GROUP BY p.name
        ORDER BY SUM(poi.quantity * poi.cost_per_unit) DESC
        """
        po_by_product = run_query(po_by_product_query, (start_date, end_date), fetch="all")

        self.po_by_product_table.setRowCount(0)
        if po_by_product:
            self.po_by_product_table.setRowCount(len(po_by_product))
            for row_num, data in enumerate(po_by_product):
                self.po_by_product_table.setItem(row_num, 0, QTableWidgetItem(data[0]))
                self.po_by_product_table.setItem(row_num, 1, QTableWidgetItem(str(data[1])))
                self.po_by_product_table.setItem(row_num, 2, QTableWidgetItem(f"${data[2]:.2f}"))

    def export_po_report(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setNameFilter("CSV Files (*.csv)")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix("csv")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            try:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([self.po_summary_label.text()])
                    writer.writerow(["Supplier", "Total Purchased"])
                    for row in range(self.po_by_supplier_table.rowCount()):
                        row_data = []
                        for col in range(self.po_by_supplier_table.columnCount()):
                            row_data.append(self.po_by_supplier_table.item(row, col).text())
                        writer.writerow(row_data)
                    writer.writerow([]) # Spacer
                    writer.writerow(["Product Name", "Quantity Purchased", "Total Cost"])
                    for row in range(self.po_by_product_table.rowCount()):
                        row_data = []
                        for col in range(self.po_by_product_table.columnCount()):
                            row_data.append(self.po_by_product_table.item(row, col).text())
                        writer.writerow(row_data)
                show_info_message("Purchase report exported successfully!")
            except Exception as e:
                show_error_message(f"Error exporting purchase report: {e}")

class AccountsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Accounts")
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Chart of Accounts Tab
        self.chart_of_accounts_tab = QWidget()
        self.tabs.addTab(self.chart_of_accounts_tab, "Chart of Accounts")
        self.chart_of_accounts_layout = QVBoxLayout(self.chart_of_accounts_tab)
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(4)
        self.accounts_table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Balance"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.chart_of_accounts_layout.addWidget(self.accounts_table)
        account_button_layout = QHBoxLayout()
        add_account_button = QPushButton("Add Account")
        add_account_button.clicked.connect(self.add_account)
        update_account_button = QPushButton("Update Account")
        update_account_button.clicked.connect(self.update_account)
        account_button_layout.addWidget(add_account_button)
        account_button_layout.addWidget(update_account_button)
        self.chart_of_accounts_layout.addLayout(account_button_layout)
        self.load_accounts()

        # Journal Entries Tab
        self.journal_entries_tab = QWidget()
        self.tabs.addTab(self.journal_entries_tab, "Journal Entries")
        self.journal_entries_layout = QVBoxLayout(self.journal_entries_tab)
        self.journal_table = QTableWidget()
        self.journal_table.setColumnCount(4)
        self.journal_table.setHorizontalHeaderLabels(["Entry ID", "Date", "Description", "Total Amount"])
        self.journal_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.journal_entries_layout.addWidget(self.journal_table)
        add_journal_entry_button = QPushButton("Add Journal Entry")
        add_journal_entry_button.clicked.connect(self.add_journal_entry)
        self.journal_entries_layout.addWidget(add_journal_entry_button)
        self.load_journal_entries()

        # Trial Balance Tab
        self.trial_balance_tab = QWidget()
        self.tabs.addTab(self.trial_balance_tab, "Trial Balance")
        self.trial_balance_layout = QVBoxLayout(self.trial_balance_tab)
        self.trial_balance_table = QTableWidget()
        self.trial_balance_table.setColumnCount(3)
        self.trial_balance_table.setHorizontalHeaderLabels(["Account", "Debit", "Credit"])
        self.trial_balance_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trial_balance_layout.addWidget(self.trial_balance_table)
        self.load_trial_balance()

        # Income Statement Tab
        self.income_statement_tab = QWidget()
        self.tabs.addTab(self.income_statement_tab, "Income Statement")
        self.income_statement_layout = QVBoxLayout(self.income_statement_tab)
        self.income_statement_layout.addWidget(QLabel("Income Statement"))
        self.income_statement_table = QTableWidget()
        self.income_statement_table.setColumnCount(2)
        self.income_statement_table.setHorizontalHeaderLabels(["Account", "Amount"])
        self.income_statement_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.income_statement_layout.addWidget(self.income_statement_table)
        self.load_income_statement()

        # Balance Sheet Tab
        self.balance_sheet_tab = QWidget()
        self.tabs.addTab(self.balance_sheet_tab, "Balance Sheet")
        self.balance_sheet_layout = QVBoxLayout(self.balance_sheet_tab)
        self.balance_sheet_layout.addWidget(QLabel("Balance Sheet"))
        self.balance_sheet_table = QTableWidget()
        self.balance_sheet_table.setColumnCount(2)
        self.balance_sheet_table.setHorizontalHeaderLabels(["Account", "Amount"])
        self.balance_sheet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.balance_sheet_layout.addWidget(self.balance_sheet_table)
        self.load_balance_sheet()

    def load_accounts(self):
        accounts = run_query("SELECT id, account_name, account_type, initial_balance FROM chart_of_accounts", fetch="all")
        if accounts:
            self.accounts_table.setRowCount(len(accounts))
            for row_num, account in enumerate(accounts):
                self.accounts_table.setItem(row_num, 0, QTableWidgetItem(str(account[0])))
                self.accounts_table.setItem(row_num, 1, QTableWidgetItem(account[1]))
                self.accounts_table.setItem(row_num, 2, QTableWidgetItem(account[2]))
                self.accounts_table.setItem(row_num, 3, QTableWidgetItem(f"${account[3]:.2f}"))

    def add_account(self):
        form = AccountForm(parent=self)
        if form.exec() == QDialog.DialogCode.Accepted:
            data = form.get_data()
            run_query("INSERT INTO chart_of_accounts (account_name, account_type, initial_balance) VALUES (?, ?, ?)", (data["name"], data["type"], data["initial_balance"]))
            self.load_accounts()

    def update_account(self):
        selected_row = self.accounts_table.currentRow()
        if selected_row == -1:
            show_error_message("Please select an account to update.")
            return
        account_id = self.accounts_table.item(selected_row, 0).text()
        account = run_query("SELECT id, account_name, account_type, initial_balance FROM chart_of_accounts WHERE id = ?", (account_id,), fetch="one")
        if account:
            form = AccountForm(account=account, parent=self)
            if form.exec() == QDialog.DialogCode.Accepted:
                data = form.get_data()
                run_query("UPDATE chart_of_accounts SET account_name=?, account_type=?, initial_balance=? WHERE id=?", (data["name"], data["type"], data["initial_balance"], account_id))
                self.load_accounts()

    def load_journal_entries(self):
        entries = run_query("SELECT id, entry_date, description, total_amount FROM journal_entries ORDER BY entry_date DESC", fetch="all")
        if entries:
            self.journal_table.setRowCount(len(entries))
            for row_num, entry in enumerate(entries):
                self.journal_table.setItem(row_num, 0, QTableWidgetItem(str(entry[0])))
                self.journal_table.setItem(row_num, 1, QTableWidgetItem(entry[1]))
                self.journal_table.setItem(row_num, 2, QTableWidgetItem(entry[2]))
                self.journal_table.setItem(row_num, 3, QTableWidgetItem(f"${entry[3]:.2f}"))

    def add_journal_entry(self):
        form = JournalEntryForm(parent=self)
        if form.exec() == QDialog.DialogCode.Accepted:
            description, total_amount, items = form.get_entry_data()
            entry_id = run_query("INSERT INTO journal_entries (description, total_amount) VALUES (?, ?)", (description, total_amount), fetch="one")
            entry_id = run_query("SELECT last_insert_rowid()", fetch="one")[0]
            for item in items:
                run_query("INSERT INTO journal_entry_items (journal_entry_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                          (entry_id, item["account_id"], item["debit"], item["credit"]))
            self.load_journal_entries()
            self.load_trial_balance() # Update trial balance after new entry

    def load_trial_balance(self):
        # Calculate balances for all accounts
        account_balances = {}
        accounts = run_query("SELECT id, account_name, account_type, initial_balance FROM chart_of_accounts", fetch="all")
        for acc_id, acc_name, acc_type, initial_balance in accounts:
            account_balances[acc_id] = {"name": acc_name, "type": acc_type, "balance": initial_balance}

        journal_items = run_query("SELECT account_id, debit, credit FROM journal_entry_items", fetch="all")
        for acc_id, debit, credit in journal_items:
            if acc_id in account_balances:
                account_balances[acc_id]["balance"] += (debit - credit)

        # Populate trial balance table
        self.trial_balance_table.setRowCount(len(account_balances))
        row_num = 0
        total_debits = 0.0
        total_credits = 0.0

        for acc_id, data in account_balances.items():
            self.trial_balance_table.setItem(row_num, 0, QTableWidgetItem(data["name"]))
            if data["balance"] >= 0:
                self.trial_balance_table.setItem(row_num, 1, QTableWidgetItem(f"${data["balance"]:.2f}"))
                self.trial_balance_table.setItem(row_num, 2, QTableWidgetItem("$0.00"))
                total_debits += data["balance"]
            else:
                self.trial_balance_table.setItem(row_num, 1, QTableWidgetItem("$0.00"))
                self.trial_balance_table.setItem(row_num, 2, QTableWidgetItem(f"${abs(data["balance"]):.2f}"))
                total_credits += abs(data["balance"])
            row_num += 1
        
        # Add total row
        self.trial_balance_table.insertRow(row_num)
        self.trial_balance_table.setItem(row_num, 0, QTableWidgetItem("Total"))
        self.trial_balance_table.setItem(row_num, 1, QTableWidgetItem(f"${total_debits:.2f}"))
        self.trial_balance_table.setItem(row_num, 2, QTableWidgetItem(f"${total_credits:.2f}"))

    def load_income_statement(self):
        # For simplicity, assuming a period. In a real app, date range would be needed.
        revenue_accounts = run_query("SELECT id, account_name, initial_balance FROM chart_of_accounts WHERE account_type = 'Revenue'", fetch="all")
        expense_accounts = run_query("SELECT id, account_name, initial_balance FROM chart_of_accounts WHERE account_type = 'Expense'", fetch="all")

        income_statement_data = []
        total_revenue = 0.0
        total_expenses = 0.0

        for acc_id, acc_name, initial_balance in revenue_accounts:
            balance = initial_balance + (run_query("SELECT SUM(credit) - SUM(debit) FROM journal_entry_items WHERE account_id = ?", (acc_id,), fetch="one")[0] or 0.0)
            income_statement_data.append((acc_name, balance))
            total_revenue += balance
        
        income_statement_data.append(("Total Revenue", total_revenue))
        income_statement_data.append(("", 0.0)) # Spacer

        for acc_id, acc_name, initial_balance in expense_accounts:
            balance = initial_balance + (run_query("SELECT SUM(debit) - SUM(credit) FROM journal_entry_items WHERE account_id = ?", (acc_id,), fetch="one")[0] or 0.0)
            income_statement_data.append((acc_name, balance))
            total_expenses += balance

        income_statement_data.append(("Total Expenses", total_expenses))
        income_statement_data.append(("", 0.0)) # Spacer

        net_income = total_revenue - total_expenses
        income_statement_data.append(("Net Income", net_income))

        self.income_statement_table.setRowCount(len(income_statement_data))
        for row_num, data in enumerate(income_statement_data):
            self.income_statement_table.setItem(row_num, 0, QTableWidgetItem(data[0]))
            self.income_statement_table.setItem(row_num, 1, QTableWidgetItem(f"${data[1]:.2f}"))

    def load_balance_sheet(self):
        asset_accounts = run_query("SELECT id, account_name, initial_balance FROM chart_of_accounts WHERE account_type = 'Asset'", fetch="all")
        liability_accounts = run_query("SELECT id, account_name, initial_balance FROM chart_of_accounts WHERE account_type = 'Liability'", fetch="all")
        equity_accounts = run_query("SELECT id, account_name, initial_balance FROM chart_of_accounts WHERE account_type = 'Equity'", fetch="all")

        balance_sheet_data = []
        total_assets = 0.0
        total_liabilities = 0.0
        total_equity = 0.0

        balance_sheet_data.append(("ASSETS", 0.0))
        for acc_id, acc_name, initial_balance in asset_accounts:
            balance = initial_balance + (run_query("SELECT SUM(debit) - SUM(credit) FROM journal_entry_items WHERE account_id = ?", (acc_id,), fetch="one")[0] or 0.0)
            balance_sheet_data.append((acc_name, balance))
            total_assets += balance
        balance_sheet_data.append(("Total Assets", total_assets))
        balance_sheet_data.append(("", 0.0)) # Spacer

        balance_sheet_data.append(("LIABILITIES", 0.0))
        for acc_id, acc_name, initial_balance in liability_accounts:
            balance = initial_balance + (run_query("SELECT SUM(credit) - SUM(debit) FROM journal_entry_items WHERE account_id = ?", (acc_id,), fetch="one")[0] or 0.0)
            balance_sheet_data.append((acc_name, balance))
            total_liabilities += balance
        balance_sheet_data.append(("Total Liabilities", total_liabilities))
        balance_sheet_data.append(("", 0.0)) # Spacer

        balance_sheet_data.append(("EQUITY", 0.0))
        for acc_id, acc_name, initial_balance in equity_accounts:
            balance = initial_balance + (run_query("SELECT SUM(credit) - SUM(debit) FROM journal_entry_items WHERE account_id = ?", (acc_id,), fetch="one")[0] or 0.0)
            balance_sheet_data.append((acc_name, balance))
            total_equity += balance
        balance_sheet_data.append(("Total Equity", total_equity))
        balance_sheet_data.append(("", 0.0)) # Spacer

        total_liabilities_equity = total_liabilities + total_equity
        balance_sheet_data.append(("Total Liabilities & Equity", total_liabilities_equity))

        self.balance_sheet_table.setRowCount(len(balance_sheet_data))
        for row_num, data in enumerate(balance_sheet_data):
            self.balance_sheet_table.setItem(row_num, 0, QTableWidgetItem(data[0]))
            self.balance_sheet_table.setItem(row_num, 1, QTableWidgetItem(f"${data[1]:.2f}"))

class CustomerManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customer Management")
        self.layout = QVBoxLayout(self)

        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(4)
        self.customer_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Email"])
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.customer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.layout.addWidget(self.customer_table)

        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Customer")
        add_button.clicked.connect(self.add_customer)
        update_button = QPushButton("Update Customer")
        update_button.clicked.connect(self.update_customer)
        delete_button = QPushButton("Delete Customer")
        delete_button.clicked.connect(self.delete_customer)
        button_layout.addWidget(add_button)
        button_layout.addWidget(update_button)
        button_layout.addWidget(delete_button)
        self.layout.addLayout(button_layout)

        self.load_customers()

    def load_customers(self):
        customers = run_query("SELECT * FROM customers", fetch="all")
        if customers is not None:
            self.customer_table.setRowCount(len(customers))
            for row_num, customer in enumerate(customers):
                for col_num, data in enumerate(customer):
                    self.customer_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))

    def add_customer(self):
        form = CustomerForm(parent=self)
        if form.exec() == QDialog.DialogCode.Accepted:
            data = form.get_data()
            run_query("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", (data["name"], data["phone"], data["email"]))
            self.load_customers()

    def update_customer(self):
        selected_row = self.customer_table.currentRow()
        if selected_row == -1:
            show_error_message("Please select a customer to update.")
            return
        customer_id = self.customer_table.item(selected_row, 0).text()
        customer = run_query("SELECT * FROM customers WHERE id = ?", (customer_id,), fetch="one")
        if customer:
            form = CustomerForm(customer=customer, parent=self)
            if form.exec() == QDialog.DialogCode.Accepted:
                data = form.get_data()
                run_query("UPDATE customers SET name=?, phone=?, email=? WHERE id=?", (data["name"], data["phone"], data["email"], customer_id))
                self.load_customers()

    def delete_customer(self):
        selected_row = self.customer_table.currentRow()
        if selected_row == -1:
            show_error_message("Please select a customer to delete.")
            return
        customer_id = self.customer_table.item(selected_row, 0).text()
        confirm = QMessageBox.question(self, "Confirm Delete", 
                                       f"Are you sure you want to delete customer ID {customer_id}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            run_query("DELETE FROM customers WHERE id = ?", (customer_id,))
            self.load_customers()

class UserManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Management")
        self.setGeometry(150, 150, 700, 500)
        self.layout = QVBoxLayout(self)

        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Role"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.layout.addWidget(self.user_table)

        button_layout = QHBoxLayout()
        add_button = QPushButton("Add User")
        add_button.clicked.connect(self.add_user)
        update_button = QPushButton("Update User")
        update_button.clicked.connect(self.update_user)
        delete_button = QPushButton("Delete User")
        delete_button.clicked.connect(self.delete_user)
        button_layout.addWidget(add_button)
        button_layout.addWidget(update_button)
        button_layout.addWidget(delete_button)
        self.layout.addLayout(button_layout)

        self.load_users()

    def load_users(self):
        users = run_query("SELECT id, username, role FROM users", fetch="all")
        if users is not None:
            self.user_table.setRowCount(len(users))
            for row_num, user in enumerate(users):
                self.user_table.setItem(row_num, 0, QTableWidgetItem(str(user[0])))
                self.user_table.setItem(row_num, 1, QTableWidgetItem(user[1]))
                self.user_table.setItem(row_num, 2, QTableWidgetItem(user[2]))

    def add_user(self):
        form = UserForm(parent=self)
        if form.exec() == QDialog.DialogCode.Accepted:
            data = form.get_data()
            hashed_password = hash_password(data["password"])
            run_query("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (data["username"], hashed_password, data["role"]))
            self.load_users()

    def update_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row == -1:
            show_error_message("Please select a user to update.")
            return
        user_id = self.user_table.item(selected_row, 0).text()
        user = run_query("SELECT * FROM users WHERE id = ?", (user_id,), fetch="one")
        if user:
            form = UserForm(user=user, parent=self)
            if form.exec() == QDialog.DialogCode.Accepted:
                data = form.get_data()
                if data["password"]:
                    hashed_password = hash_password(data["password"])
                    run_query("UPDATE users SET username=?, password=?, role=? WHERE id=?", (data["username"], hashed_password, data["role"], user_id))
                else:
                    run_query("UPDATE users SET username=?, role=? WHERE id=?", (data["username"], data["role"], user_id))
                self.load_users()

    def delete_user(self):
        selected_row = self.user_table.currentRow()
        if selected_row == -1:
            show_error_message("Please select a user to delete.")
            return
        user_id = self.user_table.item(selected_row, 0).text()
        confirm = QMessageBox.question(self, "Confirm Delete", 
                                       f"Are you sure you want to delete user ID {user_id}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            run_query("DELETE FROM users WHERE id = ?", (user_id,))
            self.load_users()

class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setFixedSize(420, 240)
        self.setStyleSheet("background-color: #23272e; color: #fff; border-radius: 14px;")
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(22)
        self.layout.setContentsMargins(28, 28, 28, 28)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFont(QFont('Arial', 16))
        self.username_input.setStyleSheet("background: #181a20; color: #fff; border-radius: 8px; padding: 10px 14px; font-size: 16px;")
        self.layout.addWidget(self.username_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont('Arial', 16))
        self.password_input.setStyleSheet("background: #181a20; color: #fff; border-radius: 8px; padding: 10px 14px; font-size: 16px;")
        self.layout.addWidget(self.password_input)
        login_button = QPushButton("Login")
        login_button.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        login_button.setStyleSheet("background: #388e3c; color: #fff; border-radius: 8px; padding: 12px 0; font-size: 18px;")
        login_button.clicked.connect(self.check_login)
        self.layout.addWidget(login_button)
        # Add a default admin user if no users exist
        if not run_query("SELECT * FROM users", fetch="all"):
            hashed_password = hash_password("admin")
            run_query("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", hashed_password, "Admin"))
            show_info_message("Default admin user created: username='admin', password='admin'")

    def check_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        hashed_password = hash_password(password)

        user = run_query("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password), fetch="one")

        if user:
            global current_user_role
            current_user_role = user[3] # Set global role
            self.accept()
        else:
            show_error_message("Invalid username or password.")

# --- Main Application Entry Point ---
if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        login_dialog = LoginWindow()
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            import classic_main_window
            classic_main_window.current_user = login_dialog.username_input.text()
            # Set role if available
            import sqlite3
            conn = sqlite3.connect('pos_system.db')
            cur = conn.cursor()
            cur.execute('SELECT role FROM users WHERE username = ?', (login_dialog.username_input.text(),))
            row = cur.fetchone()
            conn.close()
            if row:
                classic_main_window.current_user_role = row[0]
            main_window = ClassicMainWindow()
            main_window.show()
            sys.exit(app.exec())
        else:
            sys.exit(0)
    except Exception as e:
        import traceback
        print('An unhandled exception occurred:')
        print(e)
        traceback.print_exc()
        import sys
        sys.exit(1)