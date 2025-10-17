import sys
from pathlib import Path
from dataclasses import dataclass
from multiprocessing.managers import Array
from typing import Optional, List, Dict, Any
from datetime import date
import faulthandler
from xmlrpc.client import Boolean

faulthandler.enable()

from PySide6.QtCore import QDate, Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QGroupBox, QFormLayout, QMessageBox, \
    QLineEdit, QGridLayout, QTabWidget, QComboBox, QDialog, QCheckBox, QDateEdit, QSpinBox, \
    QTableView, QAbstractSpinBox, QHBoxLayout

# ===== SQLAlchemy =====
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Date,
    ForeignKey, UniqueConstraint, CheckConstraint, select, insert, delete, ForeignKeyConstraint, Boolean, asc, desc
)
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import ARRAY

from datetime import datetime

def makeLog(str):
    f = open('log.txt','a')
    now = datetime.now()
    f.write(f"{now}: {str}\n")
    f.close()

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
        CheckConstraint("duty IN ('Frontend', 'Backend', 'DevOps', 'Teamlead', 'HR', 'PM', 'CEO')"),
    )

    task = Table(
        "task", md,
        Column("task_id", Integer, primary_key=True, autoincrement=True),
        Column("employee_id", Integer, nullable=False),
        Column("name", String(300), nullable=False),
        Column("description", String),
        Column("deadline", Date),
        Column("status", String(50), nullable=False),
        CheckConstraint("status IN ('Новая', 'В работе', 'Можно проверять', 'Завершена')"),
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
# QAbstractTableModel для SQLAlchemy
# -------------------------------
class SATableModel(QAbstractTableModel):
    """Универсальная модель для QTableView (SQLAlchemy)."""
    def __init__(self, engine: Engine, table: Table, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.table = table
        self.columns: List[str] = [c.name for c in self.table.columns]
        self.pk_col = list(self.table.primary_key.columns)[0]
        self._rows: List[Dict[str, Any]] = []
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(select(self.table).order_by(self.pk_col.asc()))
                self._rows = [dict(r._mapping) for r in res]
        finally:
            self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        row = self._rows[index.row()]
        col_name = self.columns[index.column()]
        val = row.get(col_name)
        return "" if val is None else str(val)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        return self.columns[section] if orientation == Qt.Horizontal else section + 1

    def pk_value_at(self, row: int):
        return self._rows[row].get(self.pk_col.name) if 0 <= row < len(self._rows) else None

    def sort(self, column: int, order=Qt.AscendingOrder):
        if column < 0 or column >= len(self.columns):
            return

        col_name = self.columns[column]

        sort_order = asc(col_name) if order == Qt.AscendingOrder else desc(col_name)

        self.beginResetModel()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(select(self.table).order_by(sort_order))
                self._rows = [dict(r._mapping) for r in res]
        finally:
            self.endResetModel()


# -------------------------------
# Окно Добавления данных в БД
# -------------------------------
class AlterTableWindow(QDialog):
    def __init__(self, engine: Engine, tables: Dict[str, Table]):
        super().__init__()
        self.setWindowTitle('Alter Table')
        self.setGeometry(300, 300, 600, 220)
        self.engine = engine
        self.t = tables

        self.tab = QTabWidget()

        self.empl_form = QFormLayout()  # макет для блока ввода данных для таблицы Сотрудники
        # текстовые и числовые поля для блока ввода данных
        self.empl_lineedit_fullname = QLineEdit();
        self.empl_lineedit_fullname.setPlaceholderText("Иванов Иван Иванович")
        self.empl_spinbox_age = QSpinBox()
        self.empl_spinbox_age.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.empl_spinbox_age.setRange(18, 200)
        self.empl_spinbox_salary = QSpinBox()
        self.empl_spinbox_salary.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.empl_spinbox_salary.setRange(1, 2147483647)
        self.empl_spinbox_salary.setSuffix(" ₽")
        self.empl_combobox_duty = QComboBox()
        self.empl_combobox_duty.addItem('Frontend'); self.empl_combobox_duty.addItem('Backend')
        self.empl_combobox_duty.addItem('DevOps'); self.empl_combobox_duty.addItem('Teamlead')
        self.empl_combobox_duty.addItem('HR'); self.empl_combobox_duty.addItem('PM')
        self.empl_combobox_duty.addItem('CEO')
        self.empl_lineedit_skills = QLineEdit()
        self.empl_lineedit_skills.setPlaceholderText("#SQL#Python")

        # добавление полей ввода в макет
        self.empl_form.addRow("Полное имя:", self.empl_lineedit_fullname)
        self.empl_form.addRow("Возраст:", self.empl_spinbox_age)
        self.empl_form.addRow("Зарплата:", self.empl_spinbox_salary)
        self.empl_form.addRow("Должность:", self.empl_combobox_duty)
        self.empl_form.addRow("Умения:", self.empl_lineedit_skills)

        self.empl_add_button = QPushButton('Добавить данные')  # кнопка добавления данных
        # Создание макета всего внутреннего содержимого блока ввода данных (сами поля данных и кнопка)
        self.empl_layout = QVBoxLayout()
        self.empl_layout.addLayout(self.empl_form)
        self.empl_layout.addWidget(self.empl_add_button)
        self.empl_layout.addStretch()

        # создание и именование блока ввода данных
        self.empl_box = QGroupBox("Данные нового сотрудника")
        self.empl_box.setLayout(self.empl_layout)  # установка макета в блок

        self.tab.insertTab(0, self.empl_box, 'Сотрудники')

        # Данная процедура повторяется ещё два раза для создания ещё двух вкладок

        self.task_form = QFormLayout()

        self.task_lineedit_name = QLineEdit();
        self.task_lineedit_name.setPlaceholderText("Разгром")
        self.task_lineedit_description = QLineEdit()
        self.task_spinbox_id_employ = QSpinBox()
        self.task_spinbox_id_employ.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.task_spinbox_id_employ.setRange(1, 2147483647)
        self.task_spinbox_id_project = QSpinBox()
        self.task_spinbox_id_project.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.task_spinbox_id_project.setRange(1, 2147483647)
        self.task_dateedit_deadline = QDateEdit()
        self.task_dateedit_deadline.setCalendarPopup(True)
        self.task_dateedit_deadline.setDisplayFormat('yyyy-MM-dd')
        self.task_dateedit_deadline.setDate(QDate(2000, 1, 1))
        self.task_combobox_status = QComboBox()
        self.task_combobox_status.addItem('Новая');
        self.task_combobox_status.addItem('В работе')
        self.task_combobox_status.addItem('Можно проверять');
        self.task_combobox_status.addItem('Завершена')

        self.task_form.addRow("Название задачи:", self.task_lineedit_name)
        self.task_form.addRow("Описание задачи:", self.task_lineedit_description)
        self.task_form.addRow("ID работника:", self.task_spinbox_id_employ)
        self.task_form.addRow("ID проекта:", self.task_spinbox_id_project)
        self.task_form.addRow("Дата дедлайна:", self.task_dateedit_deadline)
        self.task_form.addRow("Статус задачи:", self.task_combobox_status)

        self.task_add_button = QPushButton('Добавить данные')

        self.task_layout = QVBoxLayout()
        self.task_layout.addLayout(self.task_form)
        self.task_layout.addWidget(self.task_add_button)
        self.task_layout.addStretch()

        self.task_box = QGroupBox("Данные новой задачи")
        self.task_box.setLayout(self.task_layout)

        self.tab.insertTab(1, self.task_box, 'Задачи')
        # -------------------------------
        self.projects_form = QFormLayout()

        self.projects_add_button = QPushButton('Добавить данные')

        self.projects_layout = QVBoxLayout()
        self.projects_layout.addLayout(self.projects_form)
        self.projects_layout.addWidget(self.projects_add_button)
        self.projects_layout.addStretch()

        self.projects_box = QGroupBox("Данные нового проекта")
        self.projects_box.setLayout(self.projects_layout)

        self.tab.insertTab(2, self.projects_box, 'Проекты')

        # Конец создания вкладок

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab)
        self.layout.addStretch()

        self.setLayout(self.layout)


# -------------------------------
# Окно Добавления данных в БД
# -------------------------------
class AddDataWindow(QDialog):
    def __init__(self, engine: Engine, tables: Dict[str, Table]):
        super().__init__()
        self.setWindowTitle('Data Input')
        self.setGeometry(300, 300, 600, 220)
        self.engine = engine
        self.t = tables
        self.modelEmployee = SATableModel(engine, self.t["employee"], self)
        self.modelTask = SATableModel(engine, self.t["task"], self)
        self.modelProject = SATableModel(engine, self.t["project"], self)
        self.modelProject = SATableModel(engine, self.t["project_task"], self)

        self.tab = QTabWidget()

        self.empl_form = QFormLayout()  # макет для блока ввода данных для таблицы Сотрудники
        # текстовые и числовые поля для блока ввода данных
        self.empl_lineedit_fullname = QLineEdit(); self.empl_lineedit_fullname.setPlaceholderText("Иванов Иван Иванович")
        self.empl_spinbox_age = QSpinBox()
        self.empl_spinbox_age.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.empl_spinbox_age.setRange(18, 200)
        self.empl_spinbox_salary = QSpinBox()
        self.empl_spinbox_salary.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.empl_spinbox_salary.setRange(1, 2147483647)
        self.empl_spinbox_salary.setSuffix(" ₽")
        self.empl_combobox_duty = QComboBox()
        self.empl_combobox_duty.addItem('Frontend'); self.empl_combobox_duty.addItem('Backend'); self.empl_combobox_duty.addItem('DevOps')
        self.empl_combobox_duty.addItem('Teamlead'); self.empl_combobox_duty.addItem('HR'); self.empl_combobox_duty.addItem('PM')
        self.empl_combobox_duty.addItem('CEO')
        self.empl_lineedit_skills = QLineEdit(); self.empl_lineedit_skills.setPlaceholderText("#SQL#Python")

        # добавление полей ввода в макет
        self.empl_form.addRow("Полное имя:", self.empl_lineedit_fullname)
        self.empl_form.addRow("Возраст:", self.empl_spinbox_age)
        self.empl_form.addRow("Зарплата:", self.empl_spinbox_salary)
        self.empl_form.addRow("Должность:", self.empl_combobox_duty)
        self.empl_form.addRow("Умения:", self.empl_lineedit_skills)

        self.empl_add_button = QPushButton('Добавить данные') # кнопка добавления данных
        self.empl_add_button.clicked.connect(self.add_employee)
        # Создание макета всего внутреннего содержимого блока ввода данных (сами поля данных и кнопка)
        self.empl_layout = QVBoxLayout()
        self.empl_layout.addLayout(self.empl_form)
        self.empl_layout.addWidget(self.empl_add_button)
        self.empl_layout.addStretch()

        # создание и именование блока ввода данных
        self.empl_box = QGroupBox("Данные нового сотрудника")
        self.empl_box.setLayout(self.empl_layout)  # установка макета в блок

        self.tab.insertTab(0, self.empl_box, 'Сотрудники')


        # Данная процедура повторяется ещё два раза для создания ещё двух вкладок


        self.task_form = QFormLayout()

        self.task_lineedit_name = QLineEdit(); self.task_lineedit_name.setPlaceholderText("Разгром")
        self.task_lineedit_description = QLineEdit()
        self.task_spinbox_id_employ = QSpinBox()
        self.task_spinbox_id_employ.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.task_spinbox_id_employ.setRange(1, 2147483647)
        self.task_spinbox_id_project = QSpinBox()
        self.task_spinbox_id_project.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.task_spinbox_id_project.setRange(1, 2147483647)
        self.task_dateedit_deadline = QDateEdit()
        self.task_dateedit_deadline.setCalendarPopup(True)
        self.task_dateedit_deadline.setDisplayFormat('yyyy-MM-dd')
        self.task_dateedit_deadline.setDate(QDate(2000, 1, 1))
        self.task_combobox_status = QComboBox()
        self.task_combobox_status.addItem('Новая'); self.task_combobox_status.addItem('В работе')
        self.task_combobox_status.addItem('Можно проверять'); self.task_combobox_status.addItem('Завершена')

        self.task_form.addRow("Название задачи:", self.task_lineedit_name)
        self.task_form.addRow("Описание задачи:", self.task_lineedit_description)
        self.task_form.addRow("ID работника:", self.task_spinbox_id_employ)
        self.task_form.addRow("ID проекта:", self.task_spinbox_id_project)
        self.task_form.addRow("Дата дедлайна:", self.task_dateedit_deadline)
        self.task_form.addRow("Статус задачи:", self.task_combobox_status)

        self.task_add_button = QPushButton('Добавить данные')
        self.task_add_button.clicked.connect(self.add_task)

        self.task_layout = QVBoxLayout()
        self.task_layout.addLayout(self.task_form)
        self.task_layout.addWidget(self.task_add_button)
        self.task_layout.addStretch()

        self.task_box = QGroupBox("Данные новой задачи")
        self.task_box.setLayout(self.task_layout)

        self.tab.insertTab(1, self.task_box, 'Задачи')
        # -------------------------------
        self.projects_form = QFormLayout()

        self.projects_lineedit_name = QLineEdit(); self.projects_lineedit_name.setPlaceholderText("Разгром")
        self.projects_lineedit_customer = QLineEdit(); self.projects_lineedit_customer.setPlaceholderText("ООО 'Рога и Копыта'")
        self.projects_dateedit_deadline = QDateEdit()
        self.projects_dateedit_deadline.setCalendarPopup(True)
        self.projects_dateedit_deadline.setDisplayFormat('yyyy-MM-dd')
        self.projects_dateedit_deadline.setDate(QDate(2000, 1 ,1))
        self.projects_spinbox_prize = QSpinBox()
        self.projects_spinbox_prize.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.projects_spinbox_prize.setRange(1, 2147483647)
        self.projects_spinbox_prize.setSuffix(" ₽")
        self.projects_checkbox_finished = QCheckBox()

        self.projects_form.addRow("Название проекты:", self.projects_lineedit_name)

        self.projects_form.addRow("Заказчик:", self.projects_lineedit_customer)
        self.projects_form.addRow("Дата дедлайна:", self.projects_dateedit_deadline)
        self.projects_form.addRow("Премия за проект:", self.projects_spinbox_prize)
        self.projects_form.addRow("Завершён:", self.projects_checkbox_finished)

        self.projects_add_button = QPushButton('Добавить данные')
        self.projects_add_button.clicked.connect(self.add_project)

        self.projects_layout = QVBoxLayout()
        self.projects_layout.addLayout(self.projects_form)
        self.projects_layout.addWidget(self.projects_add_button)
        self.projects_layout.addStretch()

        self.projects_box = QGroupBox("Данные нового проекта")
        self.projects_box.setLayout(self.projects_layout)

        self.tab.insertTab(2, self.projects_box, 'Проекты')

        # Конец создания вкладок

        self.close_button = QPushButton('Закрыть окно')
        self.close_button.clicked.connect(self.close) # при нажатии кнопки окно будет закрываться

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab)
        self.layout.addWidget(self.close_button)
        self.layout.addStretch()

        self.setLayout(self.layout)

    def add_employee(self):
        full_name = self.empl_lineedit_fullname.text().strip()
        age = self.empl_spinbox_age.value()
        salary = self.empl_spinbox_salary.value()
        duty = self.empl_combobox_duty.currentText()
        skills = self.empl_lineedit_skills.text().split("#")[1:]
        if not full_name or not age or not salary or not duty:
            QMessageBox.warning(self, "Ввод", "ФИО, Возраст, Зарплата и Должность обязательны (NOT NULL)")
            makeLog("Ошибка при добавления записи сотрудника. Название и статус обязательны")
            return
        try:
            with self.engine.begin() as conn:
                conn.execute(insert(self.t["employee"]).values(
                    full_name=full_name, age=age, salary=salary, duty=duty, skills=skills
                ))
            self.modelEmployee.refresh()
            self.empl_lineedit_fullname.clear(); self.empl_spinbox_age.clear(); self.empl_lineedit_skills.clear()
            makeLog("Запись сотрудника успешно добавлена!")
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка INSERT (UNIQUE/CHECK)", str(e.orig))
            makeLog("Ошибка при добавления записи сотрудника. Ошибка INSERT (UNIQUE/CHECK)")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка INSERT", str(e))
            makeLog(f"Ошибка при добавления записи сотрудника. {e}")

    def _qdate_to_pydate(self, qd: QDate) -> date:
        return date(qd.year(), qd.month(), qd.day())

    def add_task(self):
        name = self.task_lineedit_name.text().strip()
        description = self.task_lineedit_description.text().strip()
        deadline = self._qdate_to_pydate(self.task_dateedit_deadline.date())
        status = self.task_combobox_status.currentText()
        employee = self.task_spinbox_id_employ.value()
        project = self.task_spinbox_id_project.value()

        if not name or not status:
            QMessageBox.warning(self, "Ввод", "Название и статус обязательны (NOT NULL)")
            makeLog("Ошибка при добавления записи задачи. Название и статус обязательны")
            return
        try:
            task = -1
            with self.engine.begin() as conn:
                task = conn.execute(insert(self.t["task"]).values(
                    name=name, description=description, deadline=deadline, status=status, employee_id=employee
                ).returning(self.t["task"].c.task_id))
            with self.engine.begin() as conn:
                task = conn.execute(insert(self.t["project_task"]).values(
                    task_id=task.scalar(), project_id=project
                ))
            self.task_lineedit_name.clear(); self.task_lineedit_description.clear(); self.task_spinbox_id_employ.clear(); self.task_spinbox_id_project.clear()
            self.modelTask.refresh()
            makeLog("Запись задачи успешно добавлена!")
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка INSERT (UNIQUE/CHECK)", str(e.orig))
            makeLog("Ошибка при добавления записи задачи. Ошибка INSERT (UNIQUE/CHECK)")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка INSERT", str(e))
            makeLog(f"Ошибка при добавления записи задачи. {e}")

    def add_project(self):
        name = self.projects_lineedit_name.text().strip()
        deadline = self._qdate_to_pydate(self.projects_dateedit_deadline.date())
        prize = self.projects_spinbox_prize.value()
        customer = self.projects_lineedit_customer.text().strip()
        finished =self.projects_checkbox_finished.isChecked()

        if not name or not prize:
            QMessageBox.warning(self, "Ввод", "Название и Стоимость обязательны (NOT NULL)")
            makeLog("Ошибка при добавления записи проекта. Название и статус обязательны")
            return
        try:
            with self.engine.begin() as conn:
                conn.execute(insert(self.t["project"]).values(
                    name=name, deadline=deadline, prize=prize, customer=customer, finished=finished
                ))
            self.projects_lineedit_name.clear(); self.projects_lineedit_customer.clear(); self.projects_spinbox_prize.clear()
            self.modelProject.refresh()
            makeLog("Запись проекта успешно добавлена!")
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка INSERT (UNIQUE/CHECK)", str(e.orig))
            makeLog("Ошибка при добавления записи проекта. Ошибка INSERT (UNIQUE/CHECK)")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка INSERT", str(e))
            makeLog(f"Ошибка при добавления записи проекта. {e}")


# -------------------------------
# Окно отображения данных из БД
# -------------------------------
class ShowDataBaseWindow(QDialog):
    def __init__(self, engine: Engine, tables: Dict[str, Table]):
        super().__init__()
        self.setWindowTitle('Data Base show')
        self.resize(1300, 800)
        self.engine = engine
        self.t = tables
        self.modelEmployee = SATableModel(engine, self.t["employee"], self)
        self.modelTask = SATableModel(engine, self.t["task"], self)
        self.modelProject = SATableModel(engine, self.t["project"], self)

        tab = QTabWidget()
        tab.setObjectName("show")

        self.empl_table = QTableView()
        self.empl_table.setSortingEnabled(True)
        self.empl_table.setModel(self.modelEmployee)
        self.empl_table.setSelectionBehavior(QTableView.SelectRows)
        self.empl_table.setSelectionMode(QTableView.SingleSelection)

        tab.insertTab(0, self.empl_table, 'Сотрудники') # добавляем вкладочку


        # Данная процедура повторяется ещё три раза для создания ещё трёх вкладок

        self.task_widget = QWidget()
        self.task_layout = QHBoxLayout()
        self.task_table = QTableView()
        self.task_table.setMinimumWidth(700)
        self.task_table.setSortingEnabled(True)
        self.task_table.setModel(self.modelTask)
        self.task_table.setSelectionBehavior(QTableView.SelectRows)
        self.task_table.setSelectionMode(QTableView.SingleSelection)

        self.button_select = QPushButton('SELECT')
        self.button_searchtext = QPushButton('SEARCH')
        self.button_textedit = QPushButton('TEXTEDIT')

        self.task_oper_layout = QVBoxLayout()
        self.task_oper_layout.addWidget(self.button_select);
        self.task_oper_layout.addWidget(self.button_searchtext)
        self.task_oper_layout.addWidget(self.button_textedit)

        self.task_select_form = QFormLayout()
        self.task_select_combobox_column = QComboBox()
        self.task_select_combobox_column.addItem(''); self.task_select_combobox_column.addItem('Какой-то столбец')
        self.task_where_lineedit = QLineEdit()
        self.task_orderby_lineedit = QLineEdit()
        self.task_groupby_lineedit = QLineEdit()
        self.task_having_lineedit = QLineEdit()
        self.task_select_button_accept = QPushButton('Принять фильтр')


        self.task_select_form.addRow("Столбец:", self.task_select_combobox_column)
        self.task_select_form.addRow("Вхере:", self.task_where_lineedit)
        self.task_select_form.addRow("Ордербу:", self.task_orderby_lineedit)
        self.task_select_form.addRow("Гроупбу:", self.task_groupby_lineedit)
        self.task_select_form.addRow("Хавинг:", self.task_having_lineedit)
        self.task_select_form.addWidget(self.task_select_button_accept)

        self.task_oper_layout.addLayout(self.task_select_form)
        self.task_oper_layout.addStretch()
        self.task_layout.addWidget(self.task_table); self.task_layout.addLayout(self.task_oper_layout)
        self.task_widget.setLayout(self.task_layout)
        tab.insertTab(1, self.task_widget, 'Задачи')
        # -------------------------------
        self.project_table = QTableView()
        self.project_table.setSortingEnabled(True)
        self.project_table.setModel(self.modelProject)
        self.project_table.setSelectionBehavior(QTableView.SelectRows)
        self.project_table.setSelectionMode(QTableView.SingleSelection)

        tab.insertTab(2, self.project_table, 'Проекты')
        # -------------------------------
        # protas = project + task
        #protas_table = QTableWidget()
        #protas_table.setColumnCount(3)
        #protas_table.setRowCount(7)
        #protas_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Запрет на редактирование ячеек
        #protas_table.setHorizontalHeaderItem(0, QTableWidgetItem('ID'))
        #protas_table.setHorizontalHeaderItem(1, QTableWidgetItem('ID задачи'))
        #protas_table.setHorizontalHeaderItem(2, QTableWidgetItem('ID проекта'))

        #tab.insertTab(3, protas_table, 'Проекты/задачи')
        # -------------------------------
        # Конец создания вкладок
        # -------------------------------






        layout = QHBoxLayout()
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
        self.button_alterdb = QPushButton('Изменить таблицу')
        self.button_jointable = QPushButton('Мастер соединений')
        self.button_adddata.clicked.connect(self.addData)
        self.button_showdb.clicked.connect(self.showDataBase)
        self.button_alterdb.clicked.connect(self.alterTables)
        self.button_adddata.setDisabled(True)
        self.button_showdb.setDisabled(True)
        self.button_alterdb.setDisabled(True)
        self.button_jointable.setDisabled(True)

        self.curdb_grid_buttons = QGridLayout() # сетка-макет кнопок для работы с нынешней бд
        self.curdb_grid_buttons.addWidget(self.button_adddata, 0, 0)
        self.curdb_grid_buttons.addWidget(self.button_showdb, 0, 1)
        self.curdb_grid_buttons.addWidget(self.button_alterdb, 2, 0, 1, 2)
        self.curdb_grid_buttons.addWidget(self.button_jointable, 3, 0, 1, 2)
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
        main = self.window()
        if getattr(main, "engine", None) is not None:
            makeLog("Уже подключено. Нажмите «Отключиться» для переподключения.")
            return
        cfg = self.current_cfg()
        try:
            engine = make_engine(cfg)
            md, tables = build_metadata()
            main.attach_engine(engine, md, tables)
            makeLog(f"Успешное подключение: psycopg2 => {cfg.host}:{cfg.port}/{cfg.dbname} (user={cfg.user})")
            self.button_conn.setDisabled(True)
            self.button_create.setDisabled(False)
            self.button_adddata.setDisabled(False)
            self.button_showdb.setDisabled(False)
            self.button_disconn.setDisabled(False)
            self.button_alterdb.setDisabled(False)
            self.button_jointable.setDisabled(False)
        except SQLAlchemyError as e:
            pass
            makeLog(f"Ошибка подключения: {e}")

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
        self.button_alterdb.setDisabled(True)
        self.button_jointable.setDisabled(True)
        makeLog("Соединение закрыто.")

    def reset_db(self):
        main = self.window()  # <-- было parent().parent()
        if getattr(main, "engine", None) is None:
            QMessageBox.warning(self, "Схема", "Нет подключения к БД.")
            makeLog("Нет подключения к БД.")
            return
        if drop_and_create_schema_sa(main.engine, main.md):
            pass
            makeLog("Схема БД создана: students, courses, enrollments.")
        else:
            QMessageBox.critical(self, "Схема", "Ошибка при создании схемы.")
            makeLog("Ошибка при создании схемы.")

    def addData(self):
        dlg = AddDataWindow(self.engine, self.tables)
        dlg.exec()

    def showDataBase(self):
        dlg = ShowDataBaseWindow(self.engine, self.tables)
        dlg.exec()

    def alterTables(self):
        dlg = AlterTableWindow(self.engine, self.tables)
        dlg.exec()


app = QApplication(sys.argv)
app.setStyleSheet(Path('styles.qss').read_text())
window = MainWindow()
window.show()
sys.exit(app.exec())