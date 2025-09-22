import sys

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QGroupBox, QFormLayout, \
    QLineEdit, QGridLayout, QTabWidget, QComboBox, QDialog, QCheckBox, QDateEdit, QSpinBox, QTableWidget, QHeaderView, \
    QTableWidgetItem, QAbstractItemView


# -------------------------------
# Окно Добавления данных в БД
# -------------------------------
class AddDataWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Data Input')
        self.setGeometry(300, 300, 600, 220)

        tab = QTabWidget()

        empl_form = QFormLayout()  # макет для блока ввода данных для таблицы Сотрудники
        # текстовые и числовые поля для блока ввода данных
        empl_lineedit_fullname = QLineEdit()
        empl_spinbox_age = QSpinBox()
        empl_spinbox_age.setRange(0, 200)
        empl_spinbox_salary = QSpinBox()
        empl_spinbox_salary.setRange(0, 2147483647)
        empl_spinbox_salary.setSuffix(" ₽")
        empl_combobox_duty = QComboBox()
        empl_combobox_duty.addItem('front'); empl_combobox_duty.addItem('back'); empl_combobox_duty.addItem('devops')
        empl_combobox_duty.addItem('teamlead'); empl_combobox_duty.addItem('HR'); empl_combobox_duty.addItem('PM')
        empl_combobox_duty.addItem('CEO')
        empl_lineedit_skills = QLineEdit()

        # добавление полей ввода в макет
        empl_form.addRow("Полное имя:", empl_lineedit_fullname)
        empl_form.addRow("Возраст:", empl_spinbox_age)
        empl_form.addRow("Зарплата:", empl_spinbox_salary)
        empl_form.addRow("Должность:", empl_combobox_duty)
        empl_form.addRow("Умения:", empl_lineedit_skills)

        empl_add_button = QPushButton('Добавить данные') # кнопка добавления данных

        # Создание макета всего внутреннего содержимого блока ввода данных (сами поля данных и кнопка)
        empl_layout = QVBoxLayout()
        empl_layout.addLayout(empl_form)
        empl_layout.addWidget(empl_add_button)
        empl_layout.addStretch()

        # создание и именование блока ввода данных
        empl_box = QGroupBox("Данные нового сотрудника")
        empl_box.setLayout(empl_layout)  # установка макета в блок

        tab.insertTab(0, empl_box, 'Сотрудники')

        # -------------------------------
        # Данная процедура повторяется ещё два раза для создания ещё двух вкладок
        # -------------------------------

        task_form = QFormLayout()

        task_lineedit_name = QLineEdit()
        task_lineedit_description = QLineEdit()
        task_spinbox_id_employ = QSpinBox()
        task_dateedit_deadline = QDateEdit()
        task_dateedit_deadline.setCalendarPopup(True)
        task_dateedit_deadline.setDisplayFormat('yyyy-MM-dd')
        task_dateedit_deadline.setDate(QDate(2000, 1, 1))
        task_combobox_status = QComboBox()
        task_combobox_status.addItem('Новая'); task_combobox_status.addItem('В работе')
        task_combobox_status.addItem('Можно проверять'); task_combobox_status.addItem('Завершена')

        task_form.addRow("Название задачи:", task_lineedit_name)
        task_form.addRow("Описание задачи:", task_lineedit_description)
        task_form.addRow("ID работника:", task_spinbox_id_employ)
        task_form.addRow("Дата дедлайна:", task_dateedit_deadline)
        task_form.addRow("Статус задачи:", task_combobox_status)

        task_add_button = QPushButton('Добавить данные')

        task_layout = QVBoxLayout()
        task_layout.addLayout(task_form)
        task_layout.addWidget(task_add_button)
        task_layout.addStretch()

        task_box = QGroupBox("Данные новой задачи")
        task_box.setLayout(task_layout)

        tab.insertTab(1, task_box, 'Задачи')
        # -------------------------------
        projects_form = QFormLayout()

        projects_lineedit_name = QLineEdit()
        projects_lineedit_customer = QLineEdit()
        projects_dateedit_deadline = QDateEdit()
        projects_dateedit_deadline.setCalendarPopup(True)
        projects_dateedit_deadline.setDisplayFormat('yyyy-MM-dd')
        projects_dateedit_deadline.setDate(QDate(2000, 1 ,1))
        projects_spinbox_prize = QSpinBox()
        projects_spinbox_prize.setRange(0, 2147483647)
        projects_spinbox_prize.setSuffix(" ₽")
        projects_checkbox_finished = QCheckBox()

        projects_form.addRow("Название проекты:", projects_lineedit_name)

        projects_form.addRow("Заказчик:", projects_lineedit_customer)
        projects_form.addRow("Дата дедлайна:", projects_dateedit_deadline)
        projects_form.addRow("Премия за проект:", projects_spinbox_prize)
        projects_form.addRow("Завершён:", projects_checkbox_finished)

        projects_add_button = QPushButton('Добавить данные')

        projects_layout = QVBoxLayout()
        projects_layout.addLayout(projects_form)
        projects_layout.addWidget(projects_add_button)
        projects_layout.addStretch()

        projects_box = QGroupBox("Данные нового проекта")
        projects_box.setLayout(projects_layout)

        tab.insertTab(2, projects_box, 'Проекты')

        # -------------------------------
        # Конец создания вкладок
        # -------------------------------

        close_button = QPushButton('Закрыть окно')
        close_button.clicked.connect(self.close) # при нажатии кнопки окно будет закрываться

        layout = QVBoxLayout()
        layout.addWidget(tab)
        layout.addWidget(close_button)
        layout.addStretch()

        self.setLayout(layout)


# -------------------------------
# Окно отображения данных из БД
# -------------------------------
class ShowDataBaseWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Data Base show')
        self.setGeometry(300, 300, 650, 400)

        tab = QTabWidget()


        empl_table = QTableWidget() # создание таблички
        empl_table.setColumnCount(6) # установка 6 колонок в табличке
        empl_table.setRowCount(7)
        empl_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Запрет на редактирование ячеек
        empl_table.setHorizontalHeaderItem(0, QTableWidgetItem('ID'))
        empl_table.setHorizontalHeaderItem(1, QTableWidgetItem('Полное имя'))
        empl_table.setHorizontalHeaderItem(2, QTableWidgetItem('Возраст'))
        empl_table.setHorizontalHeaderItem(3, QTableWidgetItem('Зарплата'))
        empl_table.setHorizontalHeaderItem(4, QTableWidgetItem('Должность'))
        empl_table.setHorizontalHeaderItem(5, QTableWidgetItem('Умения'))


        tab.insertTab(0, empl_table, 'Сотрудники') # добавляем вкладочку


        # -------------------------------
        # Данная процедура повторяется ещё три раза для создания ещё трёх вкладок
        # -------------------------------

        task_table = QTableWidget()
        task_table.setColumnCount(6)
        task_table.setRowCount(7)
        task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Запрет на редактирование ячеек
        task_table.setHorizontalHeaderItem(0, QTableWidgetItem('ID'))
        task_table.setHorizontalHeaderItem(1, QTableWidgetItem('Название'))
        task_table.setHorizontalHeaderItem(2, QTableWidgetItem('Описание'))
        task_table.setHorizontalHeaderItem(3, QTableWidgetItem('ID работника'))
        task_table.setHorizontalHeaderItem(4, QTableWidgetItem('Дата дедлайна'))
        task_table.setHorizontalHeaderItem(5, QTableWidgetItem('Статус задачи'))

        tab.insertTab(1, task_table, 'Задачи')
        # -------------------------------
        projects_table = QTableWidget()
        projects_table.setColumnCount(6)
        projects_table.setRowCount(7)
        projects_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Запрет на редактирование ячеек
        projects_table.setHorizontalHeaderItem(0, QTableWidgetItem('ID'))
        projects_table.setHorizontalHeaderItem(1, QTableWidgetItem('Название'))
        projects_table.setHorizontalHeaderItem(2, QTableWidgetItem('Заказчик'))
        projects_table.setHorizontalHeaderItem(3, QTableWidgetItem('Дата дедлайна'))
        projects_table.setHorizontalHeaderItem(4, QTableWidgetItem('Премия за проект'))
        projects_table.setHorizontalHeaderItem(5, QTableWidgetItem('Завершён'))

        tab.insertTab(2, projects_table, 'Проекты')
        # -------------------------------
        # protas = project + task
        protas_table = QTableWidget()
        protas_table.setColumnCount(3)
        protas_table.setRowCount(7)
        protas_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Запрет на редактирование ячеек
        protas_table.setHorizontalHeaderItem(0, QTableWidgetItem('ID'))
        protas_table.setHorizontalHeaderItem(1, QTableWidgetItem('ID задачи'))
        protas_table.setHorizontalHeaderItem(2, QTableWidgetItem('ID проекта'))

        tab.insertTab(3, protas_table, 'Проекты/задачи')
        # -------------------------------
        # Конец создания вкладок
        # -------------------------------

        layout = QVBoxLayout()
        layout.addWidget(tab)
        self.setLayout(layout)


# -------------------------------
# Окно Добавления данных в БД
# -------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('IT Outsource DB')
        self.setGeometry(200, 200, 1000, 500)

        conn_form = QFormLayout() # макет для блока подключения
        # текстовые поля для блока подключения
        lineedit_host = QLineEdit("localhost")
        lineedit_port = QLineEdit("5432")
        lineedit_dbname = QLineEdit("outsource")
        lineedit_user = QLineEdit("postgres")
        lineedit_password = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        lineedit_sslmode = QLineEdit("prefer")

        # добавление полей ввода в макет
        conn_form.addRow("Host:", lineedit_host)
        conn_form.addRow("Port:", lineedit_port)
        conn_form.addRow("DB name:", lineedit_dbname)
        conn_form.addRow("User:", lineedit_user)
        conn_form.addRow("Password:", lineedit_password)
        conn_form.addRow("sslmode:", lineedit_sslmode)

        # создание и именование блока подключение
        conn_box = QGroupBox("Параметры подключения (SQLAlchemy)")
        conn_box.setLayout(conn_form) # установка макета в блок

        w_layout = QVBoxLayout() # общий макет всего окна
        w_layout.addWidget(conn_box) # добавление блока подключения в общий макет

        newdb_grid_buttons = QGridLayout() # сетка-макет кнопок для работы с подключением и созданием бд
        button_conn = QPushButton('Подключиться')
        button_disconn = QPushButton('Отключиться')
        button_disconn.setDisabled(True)
        button_create = QPushButton('Сбросить и создать БД (CREATE)')
        button_create.setDisabled(True)

        # добавление кнопок в сетку
        newdb_grid_buttons.addWidget(button_conn, 0, 0)
        newdb_grid_buttons.addWidget(button_disconn, 0, 1)
        newdb_grid_buttons.addWidget(button_create, 1, 0, 1, 2)
        w_layout.addLayout(newdb_grid_buttons) # добавление сетки кнопок в общий макет

        w_layout.addSpacing(30) # пробел между кнопками создания таблицы и работы с таблицей

        button_adddata = QPushButton('Добавить данные')
        button_showdb = QPushButton('Вывести данные')
        button_adddata.clicked.connect(self.addData)
        button_showdb.clicked.connect(self.showDataBase)

        curdb_grid_buttons = QGridLayout() # сетка-макет кнопок для работы с нынешней бд
        curdb_grid_buttons.addWidget(button_adddata, 0, 0)
        curdb_grid_buttons.addWidget(button_showdb, 1, 0)
        w_layout.addLayout(curdb_grid_buttons) # добавление сетки кнопок в общий макет



        w_layout.addStretch()  # объекты прилипают друг к другу, поэтому блок подключения не растягивается при расширении окна
        self.setLayout(w_layout) # установка общего макета

    def addData(self):
        dlg = AddDataWindow()
        dlg.exec()

    def showDataBase(self):
        dlg = ShowDataBaseWindow()
        dlg.exec()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())