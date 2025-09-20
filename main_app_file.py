import sys

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QGroupBox, QFormLayout, \
    QLineEdit, QGridLayout, QTabWidget, QComboBox


# -------------------------------
# Окно Добавления данных в БД
# -------------------------------
class AddDataWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Data Input')
        self.setGeometry(100, 100, 600, 220)

        tab = QTabWidget()

        empl_form = QFormLayout()  # макет для блока ввода данных для таблицы Сотрудники
        # текстовые поля для блока ввода данных
        empl_lineedit_fullname = QLineEdit()
        empl_lineedit_age = QLineEdit()
        empl_lineedit_salary = QLineEdit()
        empl_combobox_duty = QComboBox()
        empl_combobox_duty.addItem('front'); empl_combobox_duty.addItem('back'); empl_combobox_duty.addItem('devops')
        empl_combobox_duty.addItem('teamlead'); empl_combobox_duty.addItem('HR'); empl_combobox_duty.addItem('PM')
        empl_combobox_duty.addItem('CEO')
        empl_lineedit_skills = QLineEdit()

        # добавление полей ввода в макет
        empl_form.addRow("Полное имя:", empl_lineedit_fullname)
        empl_form.addRow("Возраст:", empl_lineedit_age)
        empl_form.addRow("Зарплата:", empl_lineedit_salary)
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
        # Данная процедура повторяется ещё три раза для создания ещё трёх вкладок
        # -------------------------------

        task_form = QFormLayout()

        task_lineedit_name = QLineEdit()
        task_lineedit_description = QLineEdit()
        task_lineedit_id_employ = QLineEdit()
        task_lineedit_deadline = QLineEdit()
        task_combobox_status = QComboBox()
        task_combobox_status.addItem('Выдана'); task_combobox_status.addItem('В работе'); task_combobox_status.addItem('Завершена')

        task_form.addRow("Название задачи:", task_lineedit_name)
        task_form.addRow("Описание задачи:", task_lineedit_description)
        task_form.addRow("ID работника:", task_lineedit_id_employ)
        task_form.addRow("Дата дедлайна:", task_lineedit_deadline)
        task_form.addRow("Статус задачи:", task_combobox_status)

        task_add_button = QPushButton('Добавить данные')

        task_layout = QVBoxLayout()
        task_layout.addLayout(task_form)
        task_layout.addWidget(task_add_button)
        task_layout.addStretch()

        task_box = QGroupBox("Данные новой задачи")
        task_box.setLayout(task_layout)

        tab.insertTab(1, task_box, 'Задачи')





        projects_form = QFormLayout()

        projects_lineedit_name = QLineEdit()
        projects_lineedit_deadline = QLineEdit()
        projects_lineedit_prize = QLineEdit()
        projects_lineedit_customer = QLineEdit()
        projects_combobox_finished = QComboBox()
        projects_combobox_finished.addItem('1'); projects_combobox_finished.addItem('0')

        projects_form.addRow("Название проекты:", projects_lineedit_name)
        projects_form.addRow("Дата дедлайна:", projects_lineedit_deadline)
        projects_form.addRow("Премия за проект:", projects_lineedit_prize)
        projects_form.addRow("Заказчик:", projects_lineedit_customer)

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


        layout = QVBoxLayout()
        layout.addWidget(tab)
        self.setLayout(layout)

    def on_call(self):
        self.show()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('IT Outsource DB')
        self.setGeometry(100, 100, 700, 500)

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
        button_create = QPushButton('Сбросить и создать БД (CREATE)')

        # добавление кнопок в сетку
        newdb_grid_buttons.addWidget(button_conn, 0, 0)
        newdb_grid_buttons.addWidget(button_disconn, 0, 1)
        newdb_grid_buttons.addWidget(button_create, 1, 0, 1, 2)
        w_layout.addLayout(newdb_grid_buttons) # добавление сетки кнопок в общий макет

        w_layout.addSpacing(30) # пробел между кнопками создания таблицы и работы с таблицей

        button_adddata = QPushButton('Добавить данные')
        button_showdb = QPushButton('Вывести данные')
        curdb_grid_buttons = QGridLayout() # сетка-макет кнопок для работы с нынешней бд
        curdb_grid_buttons.addWidget(button_adddata, 0, 0)
        curdb_grid_buttons.addWidget(button_showdb, 1, 0)
        w_layout.addLayout(curdb_grid_buttons) # добавление сетки кнопок в общий макет


        w_layout.addStretch()  # объекты прилипают друг к другу, поэтому блок подключения не растягивается при расширении окна
        self.setLayout(w_layout) # установка общего макета

        # button_adddata.clicked.connect(AddDataWindow.on_call) # ПОКА НЕ ЗНАЮ КАК СДЕЛАТЬ СИГНАЛЬНО СЛОТОВУЮ СИСТЕМУ


app = QApplication(sys.argv)
window = MainWindow()
tabs = AddDataWindow()
window.show()
tabs.show()
sys.exit(app.exec())