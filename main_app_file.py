import sys
from dataclasses import dataclass
from multiprocessing.managers import Array
from typing import Optional, List, Dict, Any
from datetime import date
import faulthandler
from xmlrpc.client import Boolean

from Scripts.pywin32_testall import project_root

faulthandler.enable()

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QGroupBox, QFormLayout, \
    QLineEdit, QGridLayout, QTabWidget, QComboBox, QDialog, QCheckBox, QDateEdit, QSpinBox, QTableWidget, QHeaderView, \
    QTableWidgetItem, QAbstractItemView

# ===== SQLAlchemy =====
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Date,
    ForeignKey, UniqueConstraint, CheckConstraint, select, insert, delete, ForeignKeyConstraint, Boolean
)
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import ARRAY


# -------------------------------
# Конфигурация подключения
# -------------------------------
@dataclass
class PgConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "outsource"
    user: str = "postgres"
    password: str = "root"
    sslmode: str = "prefer"
    connect_timeout: int = 5


def make_engine(cfg: PgConfig) -> Engine:
    query = {
        "sslmode": cfg.sslmode,
        "application_name": "QtEduDemo",
        "connect_timeout": str(cfg.connect_timeout),
    }

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=cfg.user,
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
        database=cfg.dbname,
        query=query,
    )

    engine = create_engine(url, future=True, pool_pre_ping=True)
    # sanity ping
    with engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
    return engine


def build_metadata() -> (MetaData, Dict[str, Table]):
    md = MetaData()

    employee = Table(
        "employee", md,
        Column("employee_id", Integer, primary_key=True, autoincrement=True),
        Column("full_name", String(300), nullable=False),
        Column("age", Integer, nullable=False),
        Column("salary", Integer, nullable=False),
        Column("duty", String(10), nullable=False),
        Column("skills", ARRAY(String)),
        CheckConstraint("age > 0", name="employee_age_check"),
        CheckConstraint("salary > 0", name="employee_salary_check"),
        CheckConstraint("duty IN ('Frontend', 'Backend', 'DevOps', 'HR', 'PM', 'CEO')"),
    )

    task = Table(
        "task", md,
        Column("task_id", Integer, primary_key=True, autoincrement=True),
        Column("employee_id", Integer, nullable=False),
        Column("name", String(300), nullable=False),
        Column("description", String),
        Column("deadline", Date),
        Column("status", String(10), nullable=False),
        CheckConstraint("status IN ('Новая', 'В процессе', 'Можно проверять', 'Завершена')"),
        ForeignKeyConstraint(["employee_id"], ["employee.employee_id"], name="fk_employee"),
    )

    project = Table(
        "project", md,
        Column("project_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(300), nullable=False),
        Column("deadline", Date),
        Column("prize", Integer, nullable=False),
        Column("customer", String(500)),
        Column("finished", Boolean, nullable=False),
        CheckConstraint("prize > 0", name="project_prize_check")
    )

    project_task = Table(
        "project_task", md,
        Column("project_task_id", Integer, primary_key=True, autoincrement=True),
        Column("project_id", Integer, nullable=False),
        Column("task_id", Integer, nullable=False),
        ForeignKeyConstraint(["project_id"], ["project.project_id"], name="fk_project"),
        ForeignKeyConstraint(["task_id"], ["task.task_id"], name="fk_task"),
    )

    return md, {"employee": employee, "task": task, "project": project, "project_task": project_task}


def drop_and_create_schema_sa(engine: Engine, md: MetaData) -> bool:
    try:
        md.drop_all(engine)
        md.create_all(engine)
        return True
    except SQLAlchemyError as e:
        print("SA schema error:", e)
        return False


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

        self.engine: Optional[Engine] = None
        self.md: Optional[MetaData] = None
        self.tables: Optional[Dict[str, Table]] = None

        self.conn_form = QFormLayout() # макет для блока подключения
        # текстовые поля для блока подключения
        self.lineedit_host = QLineEdit("localhost")
        self.lineedit_port = QLineEdit("5432")
        self.lineedit_dbname = QLineEdit("outsource")
        self.lineedit_user = QLineEdit("postgres")
        self.lineedit_password = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.lineedit_sslmode = QLineEdit("prefer")

        # добавление полей ввода в макет
        self.conn_form.addRow("Host:", self.lineedit_host)
        self.conn_form.addRow("Port:", self.lineedit_port)
        self.conn_form.addRow("DB name:", self.lineedit_dbname)
        self.conn_form.addRow("User:", self.lineedit_user)
        self.conn_form.addRow("Password:", self.lineedit_password)
        self.conn_form.addRow("sslmode:", self.lineedit_sslmode)

        # создание и именование блока подключение
        self.conn_box = QGroupBox("Параметры подключения (SQLAlchemy)")
        self.conn_box.setLayout(self.conn_form) # установка макета в блок

        self.w_layout = QVBoxLayout() # общий макет всего окна
        self.w_layout.addWidget(self.conn_box) # добавление блока подключения в общий макет

        self.newdb_grid_buttons = QGridLayout() # сетка-макет кнопок для работы с подключением и созданием бд
        self.button_conn = QPushButton('Подключиться')
        self.button_conn.clicked.connect(self.do_connect)
        self.button_disconn = QPushButton('Отключиться')
        self.button_disconn.clicked.connect(self.do_disconnect)
        self.button_disconn.setDisabled(True)
        self.button_create = QPushButton('Сбросить и создать БД (CREATE)')
        self.button_create.clicked.connect(self.reset_db)
        self.button_create.setDisabled(True)

        # добавление кнопок в сетку
        self.newdb_grid_buttons.addWidget(self.button_conn, 0, 0)
        self.newdb_grid_buttons.addWidget(self.button_disconn, 0, 1)
        self.newdb_grid_buttons.addWidget(self.button_create, 1, 0, 1, 2)
        self.w_layout.addLayout(self.newdb_grid_buttons) # добавление сетки кнопок в общий макет

        self.w_layout.addSpacing(30) # пробел между кнопками создания таблицы и работы с таблицей

        self.button_adddata = QPushButton('Добавить данные')
        self.button_showdb = QPushButton('Вывести данные')
        self.button_adddata.clicked.connect(self.addData)
        self.button_showdb.clicked.connect(self.showDataBase)
        self.button_adddata.setDisabled(True)
        self.button_showdb.setDisabled(True)

        self.curdb_grid_buttons = QGridLayout() # сетка-макет кнопок для работы с нынешней бд
        self.curdb_grid_buttons.addWidget(self.button_adddata, 0, 0)
        self.curdb_grid_buttons.addWidget(self.button_showdb, 1, 0)
        self.w_layout.addLayout(self.curdb_grid_buttons) # добавление сетки кнопок в общий макет



        self.w_layout.addStretch()  # объекты прилипают друг к другу, поэтому блок подключения не растягивается при расширении окна
        self.setLayout(self.w_layout) # установка общего макета

    def current_cfg(self) -> PgConfig:
        try:
            port = int(self.lineedit_port.text().strip())
        except ValueError:
            port = 5432
        return PgConfig(
            host=self.lineedit_host.text().strip() or "localhost",
            port=port,
            dbname=self.lineedit_dbname.text().strip() or "outsource",
            user=self.lineedit_user.text().strip() or "postgres",
            password=self.lineedit_password.text(),
            sslmode=self.lineedit_sslmode.text().strip() or "prefer",
        )

    def do_connect(self):
        main = self.window()  # <-- было parent().parent()
        # если уже подключены — просим отключиться
        if getattr(main, "engine", None) is not None:
            #self.log.append("Уже подключено. Нажмите «Отключиться» для переподключения.")
            return
        cfg = self.current_cfg()
        try:
            engine = make_engine(cfg)
            md, tables = build_metadata()
            main.attach_engine(engine, md, tables)
            #self.log.append(
            #    f"Успешное подключение: psycopg2 → {cfg.host}:{cfg.port}/{cfg.dbname} (user={cfg.user})"
            #)
            self.button_conn.setDisabled(True)
            self.button_create.setDisabled(False)
            self.button_adddata.setDisabled(False)
            self.button_showdb.setDisabled(False)
            self.button_disconn.setDisabled(False)
            #main.ensure_data_tabs()
        except SQLAlchemyError as e:
            pass
            #self.log.append(f"Ошибка подключения: {e}")

    def attach_engine(self, engine: Engine, md: MetaData, tables: Dict[str, Table]):
        self.engine = engine
        self.md = md
        self.tables = tables

    def do_disconnect(self):
        if self.engine is not None:
            self.engine.dispose()
        self.engine = None; self.md = None; self.tables = None
        self.button_conn.setDisabled(False)
        self.button_create.setDisabled(True)
        self.button_adddata.setDisabled(True)
        self.button_showdb.setDisabled(True)
        self.button_disconn.setDisabled(True)
        #self.log.append("Соединение закрыто.")

    def reset_db(self):
        main = self.window()  # <-- было parent().parent()
        if getattr(main, "engine", None) is None:
            QMessageBox.warning(self, "Схема", "Нет подключения к БД.")
            return
        if drop_and_create_schema_sa(main.engine, main.md):
            pass
            #self.log.append("Схема БД создана: students, courses, enrollments.")
        else:
            QMessageBox.critical(self, "Схема", "Ошибка при создании схемы. См. консоль/лог.")

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