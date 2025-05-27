from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QTabWidget, QMenuBar, QMenu, QAction,
    QDockWidget, QScrollArea, QStatusBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard
import sys
import sqlite3
import csv

class BookManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manajemen Buku")
        self.resize(700, 550)
        self.connection = sqlite3.connect("books.db")
        self.cursor = self.connection.cursor()
        self.create_table()
        self.init_ui()
        self.load_data()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )
        """)
        self.connection.commit()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        save_action = QAction("Simpan", self)
        export_action = QAction("Ekspor ke CSV", self)
        exit_action = QAction("Keluar", self)
        file_menu.addAction(save_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("Edit")
        search_action = QAction("Cari Judul", self)
        delete_action = QAction("Hapus Data", self)
        edit_menu.addAction(search_action)
        edit_menu.addAction(delete_action)

        save_action.triggered.connect(self.save_data)
        export_action.triggered.connect(self.export_csv)
        exit_action.triggered.connect(self.close)
        search_action.triggered.connect(self.focus_search)
        delete_action.triggered.connect(self.delete_data)

        self.tabs = QTabWidget()
        self.data_tab = QWidget()
        data_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_container = QWidget()
        form_layout = QVBoxLayout()
        form_container.setLayout(form_layout)

        label_width = 80

        row1 = QHBoxLayout()
        self.title_label = QLabel("Judul:")
        self.title_label.setFixedWidth(label_width)
        self.title_input = QLineEdit()
        self.paste_button = QPushButton("Paste from Clipboard")
        self.paste_button.clicked.connect(self.paste_clipboard_to_title)
        row1.addWidget(self.title_label)
        row1.addWidget(self.title_input)
        row1.addWidget(self.paste_button)
        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.author_label = QLabel("Pengarang:")
        self.author_label.setFixedWidth(label_width)
        self.author_input = QLineEdit()
        row2.addWidget(self.author_label)
        row2.addWidget(self.author_input)
        form_layout.addLayout(row2)
        row3 = QHBoxLayout()
        self.year_label = QLabel("Tahun:")
        self.year_label.setFixedWidth(label_width)
        self.year_input = QLineEdit()
        row3.addWidget(self.year_label)
        row3.addWidget(self.year_input)
        form_layout.addLayout(row3)

        scroll_area.setWidget(form_container)
        data_layout.addWidget(scroll_area)

        self.save_button = QPushButton("Simpan")
        data_layout.addWidget(self.save_button)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Judul", "Pengarang", "Tahun"])
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.setSortingEnabled(True)  
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        data_layout.addWidget(self.table)

        delete_layout = QHBoxLayout()
        self.delete_button = QPushButton("Hapus Data")
        self.delete_button.setFixedWidth(100)
        delete_layout.addWidget(self.delete_button)
        delete_layout.addStretch()
        data_layout.addLayout(delete_layout)
        self.data_tab.setLayout(data_layout)
        self.export_tab = QWidget()
        export_layout = QVBoxLayout()
        export_button_layout = QHBoxLayout()
        export_button_layout.addStretch()
        self.export_button = QPushButton("Ekspor CSV")
        self.export_button.setFixedWidth(150)
        export_button_layout.addWidget(self.export_button)
        export_button_layout.addStretch()
        export_layout.addLayout(export_button_layout)
        self.export_tab.setLayout(export_layout)

        self.tabs.addTab(self.data_tab, "Data Buku")
        self.tabs.addTab(self.export_tab, "Ekspor")

        main_layout.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Nama: Fernandao Kwangtama Tekayadi | NIM: F1D022120")

        self.search_dock = QDockWidget("Cari Judul", self)
        self.search_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        search_widget = QWidget()
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari judul...")
        search_layout.addWidget(self.search_input)
        search_widget.setLayout(search_layout)
        self.search_dock.setWidget(search_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.search_dock)

        # Connect signals
        self.save_button.clicked.connect(self.save_data)
        self.delete_button.clicked.connect(self.delete_data)
        self.export_button.clicked.connect(self.export_csv)
        self.search_input.textChanged.connect(self.search_data)
        self.table.itemChanged.connect(self.update_data)

    def paste_clipboard_to_title(self):
        clipboard = QApplication.clipboard()
        clip_text = clipboard.text()
        self.title_input.setText(clip_text)

    def save_data(self):
        title = self.title_input.text()
        author = self.author_input.text()
        year = self.year_input.text()
        if title and author and year:
            try:
                self.cursor.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
                                    (title, author, int(year)))
                self.connection.commit()
                self.clear_inputs()
                self.load_data()
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Tahun harus berupa angka.")
        else:
            QMessageBox.warning(self, "Input Error", "Semua field harus diisi.")

    def clear_inputs(self):
        self.title_input.clear()
        self.author_input.clear()
        self.year_input.clear()

    def load_data(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.cursor.execute("SELECT * FROM books")
        for row_number, row_data in enumerate(self.cursor.fetchall()):
            self.table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                if column_number == 0:
                    item.setFlags(Qt.ItemIsEnabled)  
                self.table.setItem(row_number, column_number, item)
        self.table.blockSignals(False)

    def delete_data(self):
        selected = self.table.currentRow()
        if selected >= 0:
            id_item = self.table.item(selected, 0)
            if id_item:
                id_value = id_item.text()
                self.cursor.execute("DELETE FROM books WHERE id = ?", (id_value,))
                self.connection.commit()
                self.load_data()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV", "", "CSV Files (*.csv)")
        if path:
            with open(path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = ["ID", "Judul", "Pengarang", "Tahun"]
                writer.writerow(headers)
                self.cursor.execute("SELECT * FROM books")
                for row in self.cursor.fetchall():
                    writer.writerow(row)
            QMessageBox.information(self, "Sukses", "Data berhasil diekspor.")

    def search_data(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1) 
            if item is not None:
                match = text.lower() in item.text().lower()
                self.table.setRowHidden(row, not match)

    def update_data(self, item):
        row = item.row()
        column = item.column()
        if column == 0:
            return
        id_value = self.table.item(row, 0).text()
        new_value = item.text()
        field = ["title", "author", "year"][column - 1]
        if field == "year":
            try:
                new_value_int = int(new_value)
                self.cursor.execute(f"UPDATE books SET {field} = ? WHERE id = ?", (new_value_int, id_value))
                self.connection.commit()
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Tahun harus berupa angka.")
                self.load_data()  
        else:
            self.cursor.execute(f"UPDATE books SET {field} = ? WHERE id = ?", (new_value, id_value))
            self.connection.commit()

    def focus_search(self):
        self.search_input.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookManager()
    window.show()
    sys.exit(app.exec_())
