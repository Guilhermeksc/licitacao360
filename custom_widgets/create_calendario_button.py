import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QCalendarWidget
from PyQt6.QtGui import QPainter, QFont, QColor, QPalette
from PyQt6.QtCore import QDate, Qt, QRect

from PyQt6.QtWidgets import QMenu, QAction

class CustomCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.date_info = {}
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            self.open_menu(event.pos())

    def paintCell(self, painter, rect, date):
        painter.save()

        # Verifica se a data é a data selecionada e muda a cor de fundo
        if date == self.selectedDate():
            painter.fillRect(rect, QColor('#ffff00'))  # Cor amarela para a data selecionada

        # Desenha a borda da célula
        painter.setPen(QColor('#000000'))  
        painter.drawRect(rect.adjusted(0, 0, -1, -1))  

        # Restante do código de pintura...
        if date.month() != self.monthShown():
            painter.fillRect(rect, QColor('#f0f0f0'))

        if date.dayOfWeek() in [6, 7]:
            painter.setPen(Qt.red)
        else:
            painter.setPen(self.palette().color(QPalette.Text))

        painter.setFont(QFont('Arial', 12))
        painter.drawText(rect, Qt.AlignTop | Qt.AlignHCenter, str(date.day()))

        if date in self.date_info:
            info = self.date_info[date]
            painter.setPen(self.palette().highlight().color())
            painter.setFont(QFont('Arial', 8))
            text_rect = QRect(rect.left(), rect.top() + 24, rect.width(), rect.height() - 24)
            painter.drawText(text_rect, Qt.AlignCenter, info)

        painter.restore()


    def open_menu(self, position):
        menu = QMenu(self)

        options = [
            "PE XX/XXXX - Sessão",
            "PE XX/XXXX - Recurso",
            "PE XX/XXXX - Contra-razão",
            "PE XX/XXXX - Decisão",
            "Férias 'Nome'",
            "Contrato 87000/2023"
        ]

        for option in options:
            action = QAction(option, self)
            action.triggered.connect(lambda _, opt=option: self.set_date_info(self.selectedDate(), opt))
            menu.addAction(action)

        menu.exec_(self.mapToGlobal(position))

    def set_date_info(self, date, info):
        self.date_info[date] = info
        self.updateCell(date)

    def cellDate(self, position):
        # Retorna a data da célula na posição do cursor
        hit_test = self.hitTest(position, QCalendarWidget.ExactDate)
        return hit_test


class CalendarApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.calendar = CustomCalendar(self)
        self.setCentralWidget(self.calendar)
        self.setGeometry(300, 300, 400, 400)
        self.setWindowTitle('Calendário Customizado')
        self.show()

        # Exemplo de como adicionar informações ao calendário
        self.calendar.set_date_info(QDate.currentDate(), "Evento")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CalendarApp()
    sys.exit(app.exec_())