import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QGridLayout, QDialogButtonBox, QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QComboBox, QDateEdit, QMessageBox, QCompleter, QInputDialog
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QStringListModel
from datetime import datetime
import sqlite3
import hashlib

# Sample icons from Qt (can be replaced with custom icons)
ICON_MAP = {
    'POS': QIcon.fromTheme('cart'),
    'Sales': QIcon.fromTheme('document'),
    'Stock': QIcon.fromTheme('package'),
    'Purchases': QIcon.fromTheme('printer'),
    'Accounts': QIcon.fromTheme('folder'),
    'Directory': QIcon.fromTheme('address-book'),
    'Telephones': QIcon.fromTheme('phone'),
    'Maintenance': QIcon.fromTheme('tools'),
    'Help': QIcon.fromTheme('help'),
    'About': QIcon.fromTheme('info'),
    'Exit': QIcon.fromTheme('application-exit'),
}

NAV_BUTTONS = [
    ('POS', 'POS'),
    ('Sales', 'Sales'),
    ('Stock', 'Stock'),
    ('Purchases', 'Purchases'),
    ('Accounts', 'Accounts'),
    ('Directory', 'Directory'),
    ('Telephones', 'Telephones'),
    ('Maintenance', 'Maintenance'),
    ('Help', 'Help'),
    ('About', 'About'),
    ('Exit', 'Exit'),
]

# --- Global Variables for Current User ---
current_user = None
current_user_role = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
        QMessageBox.warning(None, "Database Error", str(e))
        return None
    finally:
        if conn:
            conn.close()

class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setGeometry(400, 300, 300, 150)
        self.layout = QVBoxLayout(self)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.layout.addWidget(self.username_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_input)
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.check_login)
        self.layout.addWidget(login_button)
        # Add a default admin user if no users exist
        if not run_query("SELECT * FROM users", fetch="all"):
            hashed_password = hash_password("admin")
            run_query("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", hashed_password, "Admin"))
            QMessageBox.information(self, "Default Admin Created", "Default admin user created: username='admin', password='admin'")
    def check_login(self):
        global current_user, current_user_role
        username = self.username_input.text()
        password = self.password_input.text()
        hashed_password = hash_password(password)
        user = run_query("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password), fetch="one")
        if user:
            current_user = user[1]
            current_user_role = user[3]
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

class ModuleWindow(QDialog):
    def __init__(self, module_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(module_name)
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        layout = QVBoxLayout(self)
        label = QLabel(f"{module_name} Window")
        label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        close_btn.setStyleSheet("background: #d32f2f; color: white; border-radius: 8px; font-weight: bold; font-size: 15px;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

class POSWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Point of Sale")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(18)
        # Title
        title = QLabel("Point of Sale")
        title.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        # Info row
        info_row = QWidget()
        info_layout = QHBoxLayout(info_row)
        info_layout.setSpacing(24)
        # Invoice No. (auto-increment)
        invoice_label = QLabel("Invoice No.:")
        invoice_label.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        self.invoice_no = QLabel(self.get_next_invoice_no())
        self.invoice_no.setFont(QFont('Arial', 13))
        self.invoice_no.setToolTip("Auto-generated invoice number")
        # User
        user_label = QLabel("User:")
        user_label.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        self.user = QLabel(current_user if current_user else "USER 1")
        self.user.setFont(QFont('Arial', 13))
        self.user.setToolTip("Logged-in user")
        # Client
        client_label = QLabel("Client No./Name:")
        client_label.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        self.client = QLineEdit()
        self.client.setFixedWidth(200)
        self.client.setStyleSheet("background: #e3eafc; color: #0a2a66; border-radius: 6px; padding: 4px;")
        self.client.setToolTip("Enter client number or name")
        info_layout.addWidget(invoice_label)
        info_layout.addWidget(self.invoice_no)
        info_layout.addSpacing(30)
        info_layout.addWidget(user_label)
        info_layout.addWidget(self.user)
        info_layout.addSpacing(30)
        info_layout.addWidget(client_label)
        info_layout.addWidget(self.client)
        info_layout.addStretch()
        layout.addWidget(info_row)
        # Divider
        divider = QWidget()
        divider.setFixedHeight(2)
        divider.setStyleSheet("background: #1976d2; margin-top: 4px; margin-bottom: 4px;")
        layout.addWidget(divider)
        # Product entry row
        entry_row = QWidget()
        entry_layout = QHBoxLayout(entry_row)
        entry_layout.setSpacing(18)
        entry_layout.setContentsMargins(0, 0, 0, 0)
        part_label = QLabel("Part No./Barcode:")
        part_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        self.part_input = QLineEdit()
        self.part_input.setFixedWidth(220)
        self.part_input.setFont(QFont('Arial', 18))
        self.part_input.setStyleSheet("background: #e3eafc; color: #0a2a66; border-radius: 8px; padding: 10px 12px; font-size: 18px;")
        self.part_input.setToolTip("Scan or enter barcode/part number")
        desc_label = QLabel("Description:")
        desc_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        self.desc_input = QLineEdit()
        self.desc_input.setFixedWidth(320)
        self.desc_input.setFont(QFont('Arial', 18))
        self.desc_input.setStyleSheet("background: #e3eafc; color: #0a2a66; border-radius: 8px; padding: 10px 12px; font-size: 18px;")
        self.desc_input.setToolTip("Product description (type to search)")
        # QCompleter for product search
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.desc_input.setCompleter(self.completer)
        self.desc_input.textEdited.connect(self.update_completer)
        self.completer.activated.connect(self.completer_selected)
        qty_label = QLabel("Qty:")
        qty_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        self.qty_input = QLineEdit("1")
        self.qty_input.setFixedWidth(80)
        self.qty_input.setFont(QFont('Arial', 18))
        self.qty_input.setStyleSheet("background: #e3eafc; color: #0a2a66; border-radius: 8px; padding: 10px 12px; font-size: 18px;")
        self.qty_input.setToolTip("Quantity")
        price_label = QLabel("Price:")
        price_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        self.price_input = QLineEdit()
        self.price_input.setFixedWidth(120)
        self.price_input.setFont(QFont('Arial', 18))
        self.price_input.setStyleSheet("background: #e3eafc; color: #0a2a66; border-radius: 8px; padding: 10px 12px; font-size: 18px;")
        self.price_input.setToolTip("Unit price")
        add_btn = QPushButton("Add")
        add_btn.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        add_btn.setStyleSheet("background: #1976d2; color: white; border-radius: 10px; font-weight: bold; font-size: 18px; padding: 12px 32px;")
        add_btn.setToolTip("Add item to sale")
        add_btn.clicked.connect(self.add_item)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        entry_layout.addWidget(part_label)
        entry_layout.addWidget(self.part_input)
        entry_layout.addWidget(desc_label)
        entry_layout.addWidget(self.desc_input)
        entry_layout.addWidget(qty_label)
        entry_layout.addWidget(self.qty_input)
        entry_layout.addWidget(price_label)
        entry_layout.addWidget(self.price_input)
        entry_layout.addWidget(add_btn)
        entry_layout.addStretch()
        layout.addWidget(entry_row)
        # Sales grid
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Part No.", "Description", "Qty", "Price", "Disc.%", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("background: white; color: #0a2a66; font-size: 14px; border-radius: 8px;")
        layout.addWidget(self.table)
        # Summary panel
        summary = QWidget()
        summary_layout = QHBoxLayout(summary)
        summary_layout.setSpacing(18)
        total_label = QLabel("Total R")
        total_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.total = QLabel("0.00")
        self.total.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        cash_label = QLabel("CASH Paid R")
        cash_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.cash_paid = QLineEdit("0.00")
        self.cash_paid.setFixedWidth(100)
        self.cash_paid.setStyleSheet("background: #e3eafc; color: #0a2a66; border-radius: 6px; padding: 4px;")
        self.cash_paid.setToolTip("Amount paid by customer")
        change_label = QLabel("Change R")
        change_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.change = QLabel("0.00")
        self.change.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        summary_layout.addWidget(total_label)
        summary_layout.addWidget(self.total)
        summary_layout.addWidget(cash_label)
        summary_layout.addWidget(self.cash_paid)
        summary_layout.addWidget(change_label)
        summary_layout.addWidget(self.change)
        summary_layout.addStretch()
        layout.addWidget(summary)
        # Action buttons
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setSpacing(18)
        save_btn = QPushButton("Save (F2)")
        save_btn.setStyleSheet("background: #388e3c; color: white; border-radius: 8px; font-weight: bold; font-size: 15px; padding: 6px 18px;")
        save_btn.setToolTip("Save this sale (F2)")
        print_btn = QPushButton("Print (F3)")
        print_btn.setStyleSheet("background: #1976d2; color: white; border-radius: 8px; font-weight: bold; font-size: 15px; padding: 6px 18px;")
        print_btn.setToolTip("Print receipt (F3)")
        hold_btn = QPushButton("Hold / Recall")
        hold_btn.setStyleSheet("background: #ffa000; color: white; border-radius: 8px; font-weight: bold; font-size: 15px; padding: 6px 18px;")
        hold_btn.setToolTip("Hold or recall this sale")
        close_btn = QPushButton("Close (Esc)")
        close_btn.setStyleSheet("background: #d32f2f; color: white; border-radius: 8px; font-weight: bold; font-size: 15px; padding: 6px 18px;")
        close_btn.setToolTip("Close POS window (Esc)")
        close_btn.clicked.connect(self.close)
        for btn in [save_btn, print_btn, hold_btn, close_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(hold_btn)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addWidget(btn_row)
        # Footer with date/time
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(0)
        now = datetime.now().strftime("%d-%b-%Y %H:%M")
        self.footer_date = QLabel(f"Date: {now}")
        self.footer_date.setFont(QFont('Arial', 11, QFont.Weight.Normal))
        self.footer_date.setStyleSheet("color: #b0c4de; padding: 4px 0 0 8px;")
        footer_layout.addWidget(self.footer_date)
        footer_layout.addStretch()
        layout.addWidget(footer)
        # Connect cash paid change
        self.cash_paid.textChanged.connect(self.update_change)
        # Keyboard shortcuts (optional)
        save_btn.setShortcut('F2')
        print_btn.setShortcut('F3')
        close_btn.setShortcut('Esc')
        self.part_input.returnPressed.connect(self.lookup_product)
        self.setCentralWidget(central)
        self.showMaximized()

    def get_next_invoice_no(self):
        try:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM sales")
            result = cursor.fetchone()
            next_no = (result[0] or 0) + 1
            return str(next_no)
        except Exception:
            return "1"
        finally:
            if 'conn' in locals():
                conn.close()

    def add_item(self):
        part = self.part_input.text().strip()
        desc = self.desc_input.text().strip()
        try:
            qty = float(self.qty_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Quantity must be a number.")
            return
        try:
            price = float(self.price_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Price must be a number.")
            return
        disc = 0.0
        total = qty * price * (1 - disc/100)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(part))
        self.table.setItem(row, 1, QTableWidgetItem(desc))
        self.table.setItem(row, 2, QTableWidgetItem(str(qty)))
        self.table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
        self.table.setItem(row, 4, QTableWidgetItem(f"{disc:.2f}"))
        self.table.setItem(row, 5, QTableWidgetItem(f"{total:.2f}"))
        self.update_total()
        self.part_input.clear()
        self.desc_input.clear()
        self.qty_input.setText("1")
        self.price_input.clear()

    def update_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                total += float(self.table.item(row, 5).text())
            except Exception:
                pass
        self.total.setText(f"{total:.2f}")
        self.update_change()

    def update_change(self):
        try:
            cash = float(self.cash_paid.text())
        except ValueError:
            cash = 0.0
        try:
            total = float(self.total.text())
        except ValueError:
            total = 0.0
        change = cash - total
        self.change.setText(f"{change:.2f}")

    def lookup_product(self):
        barcode = self.part_input.text().strip()
        if not barcode:
            return
        try:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, price FROM products WHERE barcode = ?", (barcode,))
            result = cursor.fetchone()
            if result:
                self.desc_input.setText(result[0])
                self.price_input.setText(str(result[1]))
            else:
                QMessageBox.warning(self, "Product Not Found", f"No product found for barcode/part number: {barcode}")
                self.desc_input.clear()
                self.price_input.clear()
        except Exception as e:
            QMessageBox.warning(self, "Database Error", str(e))
        finally:
            if 'conn' in locals():
                conn.close()

    def update_completer(self, text):
        if not text:
            self.completer.setModel(QStringListModel([]))
            return
        try:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM products WHERE name LIKE ? LIMIT 10", (f"%{text}%",))
            results = [row[0] for row in cursor.fetchall()]
            self.completer.setModel(QStringListModel(results))
        except Exception:
            self.completer.setModel(QStringListModel([]))
        finally:
            if 'conn' in locals():
                conn.close()

    def completer_selected(self, text):
        # When a product is selected from the completer, fill barcode and price
        try:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT barcode, price FROM products WHERE name = ?", (text,))
            result = cursor.fetchone()
            if result:
                self.part_input.setText(result[0])
                self.price_input.setText(str(result[1]))
        except Exception:
            pass
        finally:
            if 'conn' in locals():
                conn.close()

class StockWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock Management")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(18)
        # Title
        title = QLabel("Stock Management")
        title.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        self.products = []
        self.categories = []
        # Category filter and controls row
        controls_row = QWidget()
        controls_layout = QHBoxLayout(controls_row)
        controls_layout.setSpacing(12)
        cat_label = QLabel("Category:")
        cat_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.cat_filter = QComboBox()
        self.cat_filter.setFont(QFont('Arial', 14))
        self.cat_filter.setFixedWidth(180)
        search_label = QLabel("Search:")
        search_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.search_input = QLineEdit()
        self.search_input.setFont(QFont('Arial', 14))
        self.search_input.setFixedWidth(220)
        self.search_input.setPlaceholderText("Name, Barcode, or ID")
        self.load_categories_for_filter()
        manage_cat_btn = QPushButton("Manage Categories")
        manage_cat_btn.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        manage_cat_btn.setStyleSheet("background: #ffa000; color: white; border-radius: 8px; font-size: 13px; padding: 6px 18px;")
        manage_cat_btn.clicked.connect(self.manage_categories)
        low_stock_btn = QPushButton("Show Low Stock")
        low_stock_btn.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        low_stock_btn.setStyleSheet("background: #ffa000; color: white; border-radius: 8px; font-size: 13px; padding: 6px 18px;")
        low_stock_btn.clicked.connect(self.show_low_stock)
        self.low_stock_label = QLabel("")
        self.low_stock_label.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        self.low_stock_label.setStyleSheet("color: #ffa000;")
        export_btn = QPushButton("Export CSV")
        export_btn.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        export_btn.setStyleSheet("background: #1976d2; color: white; border-radius: 8px; font-size: 13px; padding: 6px 18px;")
        export_btn.clicked.connect(self.export_csv)
        import_btn = QPushButton("Import CSV")
        import_btn.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        import_btn.setStyleSheet("background: #388e3c; color: white; border-radius: 8px; font-size: 13px; padding: 6px 18px;")
        import_btn.clicked.connect(self.import_csv)
        controls_layout.addWidget(cat_label)
        controls_layout.addWidget(self.cat_filter)
        controls_layout.addWidget(manage_cat_btn)
        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.search_input)
        controls_layout.addWidget(low_stock_btn)
        controls_layout.addWidget(self.low_stock_label)
        controls_layout.addStretch()
        controls_layout.addWidget(export_btn)
        controls_layout.addWidget(import_btn)
        layout.addWidget(controls_row)
        # Product Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Barcode", "Category", "Price", "Stock"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("background: white; color: #0a2a66; font-size: 18px; border-radius: 8px;")
        layout.addWidget(self.table)
        # Now connect signals (after self.table is created)
        self.search_input.textChanged.connect(self.filter_products)
        self.cat_filter.currentIndexChanged.connect(self.filter_products)
        # Button Row
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setSpacing(18)
        add_btn = QPushButton("Add Product")
        add_btn.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        add_btn.setStyleSheet("background: #388e3c; color: white; border-radius: 8px; font-size: 16px; padding: 8px 24px;")
        add_btn.clicked.connect(self.add_product)
        edit_btn = QPushButton("Edit Product")
        edit_btn.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        edit_btn.setStyleSheet("background: #1976d2; color: white; border-radius: 8px; font-size: 16px; padding: 8px 24px;")
        edit_btn.clicked.connect(self.edit_product)
        del_btn = QPushButton("Delete Product")
        del_btn.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        del_btn.setStyleSheet("background: #d32f2f; color: white; border-radius: 8px; font-size: 16px; padding: 8px 24px;")
        del_btn.clicked.connect(self.delete_product)
        for btn in [add_btn, edit_btn, del_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addWidget(btn_row)
        self.setCentralWidget(central)
        self.showMaximized()
        self.load_products()

    def load_categories_for_filter(self):
        self.cat_filter.clear()
        self.cat_filter.addItem("All", None)
        try:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            self.categories = cursor.fetchall()
            for cat in self.categories:
                self.cat_filter.addItem(cat[1], cat[0])
        except Exception:
            pass
        finally:
            if 'conn' in locals():
                conn.close()

    def load_products(self):
        self.table.setRowCount(0)
        try:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, p.barcode, c.name, p.price, p.stock_quantity
                FROM products p LEFT JOIN categories c ON p.category_id = c.id
            """)
            self.products = cursor.fetchall()
            self.show_products(self.products)
        except Exception as e:
            QMessageBox.warning(self, "Database Error", str(e))
        finally:
            if 'conn' in locals():
                conn.close()
        self.update_low_stock_label()
        self.load_categories_for_filter()

    def show_products(self, products):
        self.table.setRowCount(0)
        for row_num, product in enumerate(products):
            self.table.insertRow(row_num)
            for col_num, data in enumerate(product):
                item = QTableWidgetItem(str(data))
                if col_num == 5 and int(data) <= 10:
                    item.setBackground(Qt.GlobalColor.yellow)
                self.table.setItem(row_num, col_num, item)

    def filter_products(self):
        text = self.search_input.text().lower()
        cat_id = self.cat_filter.currentData()
        filtered = self.products
        if cat_id:
            filtered = [p for p in filtered if p[3] == self.cat_filter.currentText()]
        if text:
            filtered = [p for p in filtered if text in str(p[0]).lower() or text in p[1].lower() or text in str(p[2]).lower()]
        self.show_products(filtered)

    def show_low_stock(self):
        low_stock = [p for p in self.products if int(p[5]) <= 10]
        self.show_products(low_stock)

    def update_low_stock_label(self):
        count = sum(1 for p in self.products if int(p[5]) <= 10)
        self.low_stock_label.setText(f"Low Stock: {count}")

    def export_csv(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Export Products", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Barcode", "Category", "Price", "Stock"])
                for p in self.products:
                    writer.writerow(p)
            QMessageBox.information(self, "Export Complete", f"Products exported to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    def import_csv(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Import Products", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            import csv
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        conn = sqlite3.connect('pos_system.db')
                        cursor = conn.cursor()
                        # Find or create category
                        cat_id = None
                        if 'Category' in row and row['Category']:
                            cursor.execute("SELECT id FROM categories WHERE name = ?", (row['Category'],))
                            cat = cursor.fetchone()
                            if not cat:
                                cursor.execute("INSERT INTO categories (name) VALUES (?)", (row['Category'],))
                                conn.commit()
                                cat_id = cursor.lastrowid
                            else:
                                cat_id = cat[0]
                        cursor.execute("INSERT OR IGNORE INTO products (id, name, barcode, category_id, price, stock_quantity) VALUES (?, ?, ?, ?, ?, ?)", (row['ID'], row['Name'], row['Barcode'], cat_id, float(row['Price']), int(row['Stock'])))
                        conn.commit()
                    except Exception:
                        pass
                    finally:
                        if 'conn' in locals():
                            conn.close()
            QMessageBox.information(self, "Import Complete", f"Products imported from {path}")
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", str(e))
        self.load_products()

    def add_product(self):
        dlg = ProductDialog(self, categories=self.categories)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                conn = sqlite3.connect('pos_system.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO products (name, barcode, category_id, price, stock_quantity) VALUES (?, ?, ?, ?, ?)", (
                    data['name'],
                    data['barcode'],
                    data['category_id'],
                    data['price'],
                    data['stock']
                ))
                conn.commit()
            except Exception as e:
                QMessageBox.warning(self, "Database Error", str(e))
            finally:
                if 'conn' in locals():
                    conn.close()
            self.load_products()

    def edit_product(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Select Product", "Please select a product to edit.")
            return
        product_id = self.table.item(row, 0).text()
        try:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, barcode, category_id, price, stock_quantity FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
        except Exception as e:
            QMessageBox.warning(self, "Database Error", str(e))
            return
        finally:
            if 'conn' in locals():
                conn.close()
        if product:
            dlg = ProductDialog(self, product, categories=self.categories)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_data()
                try:
                    conn = sqlite3.connect('pos_system.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET name=?, barcode=?, category_id=?, price=?, stock_quantity=? WHERE id=?", (data['name'], data['barcode'], data['category_id'], data['price'], data['stock'], product_id))
                    conn.commit()
                except Exception as e:
                    QMessageBox.warning(self, "Database Error", str(e))
                finally:
                    if 'conn' in locals():
                        conn.close()
                self.load_products()

    def delete_product(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Select Product", "Please select a product to delete.")
            return
        product_id = self.table.item(row, 0).text()
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete product ID {product_id}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect('pos_system.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                conn.commit()
            except Exception as e:
                QMessageBox.warning(self, "Database Error", str(e))
            finally:
                if 'conn' in locals():
                    conn.close()
            self.load_products()

    def manage_categories(self):
        dlg = CategoryManagerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_products()

class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None, categories=None):
        super().__init__(parent)
        self.setWindowTitle("Product Details")
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        self.setFixedSize(400, 400)
        layout = QVBoxLayout(self)
        name_label = QLabel("Name:")
        name_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.name_input = QLineEdit(product[1] if product else "")
        self.name_input.setFont(QFont('Arial', 14))
        barcode_label = QLabel("Barcode:")
        barcode_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.barcode_input = QLineEdit(product[2] if product else "")
        self.barcode_input.setFont(QFont('Arial', 14))
        cat_label = QLabel("Category:")
        cat_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.cat_combo = QComboBox()
        self.cat_combo.setFont(QFont('Arial', 14))
        self.cat_combo.addItem("None", None)
        if categories:
            for cat in categories:
                self.cat_combo.addItem(cat[1], cat[0])
        if product and product[3]:
            idx = self.cat_combo.findData(product[3])
            if idx != -1:
                self.cat_combo.setCurrentIndex(idx)
        price_label = QLabel("Price:")
        price_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.price_input = QLineEdit(str(product[4]) if product else "")
        self.price_input.setFont(QFont('Arial', 14))
        stock_label = QLabel("Stock:")
        stock_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.stock_input = QLineEdit(str(product[5]) if product else "")
        self.stock_input.setFont(QFont('Arial', 14))
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(barcode_label)
        layout.addWidget(self.barcode_input)
        layout.addWidget(cat_label)
        layout.addWidget(self.cat_combo)
        layout.addWidget(price_label)
        layout.addWidget(self.price_input)
        layout.addWidget(stock_label)
        layout.addWidget(self.stock_input)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def validate_and_accept(self):
        try:
            name = self.name_input.text().strip()
            barcode = self.barcode_input.text().strip()
            price = float(self.price_input.text())
            stock = int(self.stock_input.text())
            # category_id can be None
            self.accept()
        except Exception:
            QMessageBox.warning(self, "Input Error", "Please fill all fields correctly. Price and Stock must be numbers.")

    def get_data(self):
        return {
            'name': self.name_input.text(),
            'barcode': self.barcode_input.text(),
            'category_id': self.cat_combo.currentData() if self.cat_combo.currentData() is not None else None,
            'price': float(self.price_input.text()),
            'stock': int(self.stock_input.text())
        }

class CategoryManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        self.setFixedSize(350, 350)
        layout = QVBoxLayout(self)
        self.cat_list = QTableWidget()
        self.cat_list.setColumnCount(2)
        self.cat_list.setHorizontalHeaderLabels(["ID", "Name"])
        self.cat_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.cat_list)
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_category)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_category)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_category)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        layout.addWidget(btn_row)
        self.load_categories()
    def load_categories(self):
        self.cat_list.setRowCount(0)
        try:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            cats = cursor.fetchall()
            for row_num, cat in enumerate(cats):
                self.cat_list.insertRow(row_num)
                self.cat_list.setItem(row_num, 0, QTableWidgetItem(str(cat[0])))
                self.cat_list.setItem(row_num, 1, QTableWidgetItem(cat[1]))
        except Exception:
            pass
        finally:
            if 'conn' in locals():
                conn.close()
    def add_category(self):
        name, ok = QInputDialog.getText(self, "Add Category", "Category Name:")
        if ok and name:
            try:
                conn = sqlite3.connect('pos_system.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                conn.commit()
            except Exception:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            self.load_categories()
    def edit_category(self):
        row = self.cat_list.currentRow()
        if row == -1:
            return
        cat_id = self.cat_list.item(row, 0).text()
        old_name = self.cat_list.item(row, 1).text()
        name, ok = QInputDialog.getText(self, "Edit Category", "Category Name:", text=old_name)
        if ok and name:
            try:
                conn = sqlite3.connect('pos_system.db')
                cursor = conn.cursor()
                cursor.execute("UPDATE categories SET name=? WHERE id=?", (name, cat_id))
                conn.commit()
            except Exception:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            self.load_categories()
    def delete_category(self):
        row = self.cat_list.currentRow()
        if row == -1:
            return
        cat_id = self.cat_list.item(row, 0).text()
        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete category ID {cat_id}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect('pos_system.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categories WHERE id=?", (cat_id,))
                conn.commit()
            except Exception:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
            self.load_categories()

class SalesHistoryWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sales History & Reports")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        central = QWidget()
        layout = QVBoxLayout(central)
        label = QLabel("Sales History & Reports Module")
        label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setCentralWidget(central)
        self.showMaximized()

class PurchasingWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Purchasing")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        central = QWidget()
        layout = QVBoxLayout(central)
        label = QLabel("Purchasing Module")
        label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setCentralWidget(central)
        self.showMaximized()

class AccountsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Accounts")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        central = QWidget()
        layout = QVBoxLayout(central)
        label = QLabel("Accounts Module")
        label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setCentralWidget(central)
        self.showMaximized()

class ClientsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Client Management")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        central = QWidget()
        layout = QVBoxLayout(central)
        label = QLabel("Client Management Module")
        label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setCentralWidget(central)
        self.showMaximized()

class UsersWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Management")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        central = QWidget()
        layout = QVBoxLayout(central)
        label = QLabel("User Management Module")
        label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setCentralWidget(central)
        self.showMaximized()

class SettingsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings & Maintenance")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.Window)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        central = QWidget()
        layout = QVBoxLayout(central)
        label = QLabel("Settings & Maintenance Module")
        label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setCentralWidget(central)
        self.showMaximized()

class ClassicMenuDialog(QDialog):
    def __init__(self, title, actions, reports, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet("background-color: #0a2a66; color: white; border-radius: 12px;")
        self.setFixedSize(600, 380)
        layout = QGridLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setHorizontalSpacing(36)
        # Actions (left)
        action_panel = QWidget()
        action_layout = QVBoxLayout(action_panel)
        action_layout.setSpacing(24)
        for i, (label, icon_name) in enumerate(actions):
            btn = QPushButton(label)
            btn.setIcon(ICON_MAP.get(icon_name, QIcon()))
            btn.setMinimumHeight(48)
            btn.setFont(QFont('Arial', 15, QFont.Weight.Bold))
            btn.setStyleSheet("background: white; color: #0a2a66; border-radius: 8px; font-weight: bold; font-size: 18px;")
            btn.clicked.connect(lambda checked, l=label: self.open_module_window(l))
            action_layout.addWidget(btn)
        close_btn = QPushButton("\u2716 Close (Esc)")
        close_btn.setIcon(QIcon.fromTheme('window-close'))
        close_btn.setMinimumHeight(44)
        close_btn.setFont(QFont('Arial', 15, QFont.Weight.Bold))
        close_btn.setStyleSheet("background: #d32f2f; color: white; border-radius: 8px; font-weight: bold; font-size: 18px; margin-top: 10px;")
        close_btn.clicked.connect(self.close)
        action_layout.addWidget(close_btn)
        action_layout.addStretch()
        layout.addWidget(action_panel, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        # Reports (right)
        report_panel = QWidget()
        report_layout = QVBoxLayout(report_panel)
        report_layout.setSpacing(16)
        report_label = QLabel(f"{title} Reports")
        report_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        report_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        report_label.setStyleSheet("color: white; margin-bottom: 10px;")
        report_layout.addWidget(report_label)
        for label, icon_name in reports:
            btn = QPushButton(label)
            btn.setIcon(ICON_MAP.get(icon_name, QIcon()))
            btn.setMinimumHeight(38)
            btn.setFont(QFont('Arial', 13, QFont.Weight.Bold))
            btn.setStyleSheet("background: white; color: #0a2a66; border-radius: 8px; font-size: 15px; text-align: left; padding-left: 16px;")
            btn.clicked.connect(lambda checked, l=label: self.open_module_window(l))
            report_layout.addWidget(btn)
        report_layout.addStretch()
        layout.addWidget(report_panel, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)

    def open_module_window(self, module_name):
        if module_name == "Point of Sale":
            self.close()
            win = POSWindow(self.parent())
            win.show()
            win.raise_()
            win.activateWindow()
        elif module_name in ["Add/Modify Stock", "Stock Groups Maintenance", "Global Stock Maintenance", "Stock Quantity Adjustment"]:
            self.close()
            win = StockWindow(self.parent())
            win.show()
            win.raise_()
            win.activateWindow()
        elif module_name in ["Invoicing", "Payments Received", "Add/Modify Clients"]:
            self.close()
            win = SalesHistoryWindow(self.parent())
            win.show()
            win.raise_()
            win.activateWindow()
        elif module_name in ["Purchasing", "Payments to Suppliers", "Add/Modify Suppliers"]:
            self.close()
            win = PurchasingWindow(self.parent())
            win.show()
            win.raise_()
            win.activateWindow()
        elif module_name in ["Chart of Accounts", "Journal Posting", "Entry Posting", "Bank Reconciliation"]:
            self.close()
            win = AccountsWindow(self.parent())
            win.show()
            win.raise_()
            win.activateWindow()
        elif module_name in ["Manage Clients"]:
            self.close()
            win = ClientsWindow(self.parent())
            win.show()
            win.raise_()
            win.activateWindow()
        elif module_name in ["Users Settings", "Add/Modify Users"]:
            self.close()
            win = UsersWindow(self.parent())
            win.show()
            win.raise_()
            win.activateWindow()
        elif module_name in ["System Settings", "Files Reindex", "Files Export / Import", "Restore From Backup", "Tax File Maintenance", "Default Accounts Setup", "Clear Data Files"]:
            self.close()
            win = SettingsWindow(self.parent())
            win.show()
            win.raise_()
            win.activateWindow()
        else:
            dlg = ModuleWindow(module_name, self)
            dlg.exec()

class ClassicMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kayan Point of Sale")
        self.setGeometry(100, 100, 1024, 700)
        self.setStyleSheet("background-color: #0a2a66;")
        # Top navigation bar
        nav_bar = QWidget()
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(20, 16, 20, 16)  # Less padding
        nav_layout.setSpacing(16)  # Less space between buttons
        nav_layout.addStretch()
        for label, icon_name in NAV_BUTTONS:
            btn = QPushButton(label)
            btn.setIcon(ICON_MAP.get(icon_name, QIcon()))
            btn.setMinimumSize(110, 54)  # Moderately sized buttons
            btn.setFont(QFont('Arial', 15, QFont.Weight.Bold))
            btn.setStyleSheet("background: white; color: #0a2a66; border-radius: 8px; margin-right: 6px;")
            btn.clicked.connect(lambda checked, l=label: self.menu_clicked(l))
            nav_layout.addWidget(btn)
        nav_layout.addStretch()
        # Main area
        main_panel = QWidget()
        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(nav_bar, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addSpacing(50)  # Less space below nav bar
        welcome = QLabel("\nWelcome to Kayan Point of Sale\n\nClick a menu above to open a module.")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setFont(QFont('Arial', 22, QFont.Weight.Bold))
        welcome.setStyleSheet("color: white;")
        main_layout.addWidget(welcome)
        main_layout.addStretch()
        self.setCentralWidget(main_panel)

    def menu_clicked(self, label):
        if label == 'POS':
            actions = [
                ("Point of Sale", 'POS'),
                ("Start / End of day", 'POS'),
            ]
            reports = [
                ("1 Summary Income Report", 'Sales'),
                ("2 Daily Sales Report", 'Sales'),
                ("3 Staff Sales Report", 'Sales'),
                ("4 Groups Sales Report", 'Sales'),
            ]
            dlg = ClassicMenuDialog("POS Menu", actions, reports, self)
            dlg.exec()
        elif label == 'Sales':
            actions = [
                ("Invoicing", 'Sales'),
                ("Payments Received", 'Sales'),
                ("Add/Modify Clients", 'Directory'),
            ]
            reports = [
                ("1 List of Clients", 'Directory'),
                ("2 Invoices List Report", 'Sales'),
                ("3 Summary Sales Report", 'Sales'),
                ("4 Aged Clients Report", 'Sales'),
                ("5 Client's Statements", 'Sales'),
                ("6 Sales Analysis Report", 'Sales'),
                ("7 Back Orders Report", 'Sales'),
                ("8 Sales Tax Report", 'Sales'),
                ("9 Bank Deposit", 'Sales'),
                ("a Sale Payments Report", 'Sales'),
                ("b Sales by Client", 'Sales'),
                ("c Sales by Product", 'Stock'),
                ("d Client Sales/Product", 'Sales'),
                ("e Product Sales/Client", 'Sales'),
                ("f Staff Sales Report", 'Sales'),
                ("g Loyalty Points Report", 'Sales'),
            ]
            dlg = ClassicMenuDialog("Sales Menu", actions, reports, self)
            dlg.exec()
        elif label == 'Stock':
            actions = [
                ("Add/Modify Stock", 'Stock'),
                ("Stock Groups Maintenance", 'Stock'),
                ("Global Stock Maintenance", 'Stock'),
                ("Stock Quantity Adjustment", 'Stock'),
            ]
            reports = [
                ("1 Items Enquiry", 'Stock'),
                ("2 Transactions Enquiry", 'Stock'),
                ("3 Quantities Report", 'Stock'),
                ("4 Selling Prices Report", 'Stock'),
                ("5 Cost Price Report", 'Stock'),
                ("6 Stock Performance Report", 'Stock'),
                ("7 Out of Stock Report", 'Stock'),
                ("8 Stock Reorder Report", 'Stock'),
                ("9 Stock Take Report", 'Stock'),
                ("v Stock Value Report", 'Stock'),
                ("h Items History", 'Stock'),
                ("b Print Stock Barcodes", 'Stock'),
            ]
            dlg = ClassicMenuDialog("Stock Menu", actions, reports, self)
            dlg.exec()
        elif label == 'Purchases':
            actions = [
                ("Purchasing", 'Purchases'),
                ("Payments to Suppliers", 'Purchases'),
                ("Add/Modify Suppliers", 'Directory'),
            ]
            reports = [
                ("1 List of Suppliers", 'Directory'),
                ("2 Purchases List Report", 'Purchases'),
                ("3 Purchase Orders Report", 'Purchases'),
                ("4 Summary Purchases", 'Purchases'),
                ("5 Aged Suppliers Report", 'Purchases'),
                ("6 Supplier's Statements", 'Purchases'),
                ("7 Purchase Analysis Report", 'Purchases'),
                ("8 Back Orders Report", 'Purchases'),
                ("9 Stock On Order Report", 'Stock'),
                ("a Purchases Tax Report", 'Purchases'),
                ("b Purchase Payments Report", 'Purchases'),
                ("c Equivalent Part Numbers", 'Stock'),
            ]
            dlg = ClassicMenuDialog("Purchase Menu", actions, reports, self)
            dlg.exec()
        elif label == 'Accounts':
            actions = [
                ("Chart of Accounts", 'Accounts'),
                ("Journal Posting", 'Accounts'),
                ("Entry Posting", 'Accounts'),
                ("Bank Reconciliation", 'Accounts'),
            ]
            reports = [
                ("1 List of Accounts", 'Accounts'),
                ("2 Daily Entries Report", 'Accounts'),
                ("3 Daily Balances Report", 'Accounts'),
                ("4 Monthly Balances Report", 'Accounts'),
                ("5 Statement of Account", 'Accounts'),
                ("6 Trial Balance Report", 'Accounts'),
                ("7 Trading, Profit & Loss", 'Accounts'),
                ("8 Balance Sheet Report", 'Accounts'),
            ]
            dlg = ClassicMenuDialog("Accounts Menu", actions, reports, self)
            dlg.exec()
        elif label == 'Directory':
            actions = [
                ("Manage Clients", 'Directory'),
                ("Manage Suppliers", 'Directory'),
            ]
            reports = [
                ("1 Client List", 'Directory'),
                ("2 Supplier List", 'Directory'),
            ]
            dlg = ClassicMenuDialog("Directory Menu", actions, reports, self)
            dlg.exec()
        elif label == 'Telephones':
            actions = [
                ("Manage Phonebook", 'Telephones'),
            ]
            reports = [
                ("1 Phonebook List", 'Telephones'),
            ]
            dlg = ClassicMenuDialog("Telephones Menu", actions, reports, self)
            dlg.exec()
        elif label == 'Maintenance':
            actions = [
                ("Files Reindex", 'Maintenance'),
                ("System Settings", 'Maintenance'),
                ("Files Export / Import", 'Maintenance'),
                ("Restore From Backup", 'Maintenance'),
                ("Users Settings", 'Maintenance'),
                ("Tax File Maintenance", 'Maintenance'),
                ("Default Accounts Setup", 'Accounts'),
                ("Clear Data Files", 'Maintenance'),
            ]
            reports = []
            dlg = ClassicMenuDialog("Maintenance Menu", actions, reports, self)
            dlg.exec()
        elif label == 'Help':
            actions = [
                ("User Manual", 'Help'),
                ("Contact Support", 'Help'),
            ]
            reports = []
            dlg = ClassicMenuDialog("Help Menu", actions, reports, self)
            dlg.exec()
        elif label == 'About':
            actions = [
                ("About This Software", 'About'),
            ]
            reports = []
            dlg = ClassicMenuDialog("About", actions, reports, self)
            dlg.exec()
        elif label == 'Exit':
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_dialog = LoginWindow()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        window = ClassicMainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0) 