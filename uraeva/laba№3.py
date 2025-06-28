import sys
import random
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, QPushButton,
    QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QMessageBox,
    QDialog, QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont

# Конфигурационные файлы
USERS_FILE = "users.json"
SCORES_FILE = "scores.json"

# Инициализация данных
users = {}
scores = {}
current_user = None
settings = {'sound': True, 'theme': 'default'}
words = ['ПРОГРАММИРОВАНИЕ', 'КОМПЬЮТЕР', 'ПИТОН', 'ИГРА', 'БАРАБАН']

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)

if os.path.exists(SCORES_FILE):
    with open(SCORES_FILE, 'r') as f:
        scores = json.load(f)


class LeaderboardWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Таблица лидеров')
        self.setGeometry(400, 400, 400, 300)
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Игрок', 'Рекорд'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)
        self.setLayout(layout)
        self.update_table()

    def update_table(self):
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        self.table.setRowCount(len(sorted_scores))
        for row, (user, score) in enumerate(sorted_scores):
            self.table.setItem(row, 0, QTableWidgetItem(user))
            self.table.setItem(row, 1, QTableWidgetItem(str(score)))


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Авторизация')
        self.setGeometry(300, 300, 300, 150)
        layout = QVBoxLayout()

        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_btn = QPushButton('Войти')
        login_btn.clicked.connect(self.login)
        register_btn = QPushButton('Создать аккаунт')
        register_btn.clicked.connect(self.register)

        layout.addWidget(QLabel('Логин:'))
        layout.addWidget(self.login_input)
        layout.addWidget(QLabel('Пароль:'))
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)

        self.setLayout(layout)

    def login(self):
        global current_user
        login = self.login_input.text()
        password = self.password_input.text()

        if users.get(login) == password:
            current_user = login
            self.accept()
            if self.parent():
                self.parent().update_ui()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверные данные!')

    def register(self):
        login = self.login_input.text()
        if login in users:
            QMessageBox.warning(self, 'Ошибка', 'Логин занят!')
            return
        users[login] = self.password_input.text()
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
        QMessageBox.information(self, 'Успех', 'Аккаунт создан!')


class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Настройки')
        self.setGeometry(300, 300, 300, 150)
        layout = QVBoxLayout()

        self.sound_check = QRadioButton('Звук')
        self.sound_check.setChecked(settings['sound'])

        self.theme_group = QButtonGroup(self)
        self.light_theme = QRadioButton('Светлая тема')
        self.dark_theme = QRadioButton('Темная тема')
        self.theme_group.addButton(self.light_theme)
        self.theme_group.addButton(self.dark_theme)


        if settings['theme'] == 'dark':
            self.dark_theme.setChecked(True)
        else:
            self.light_theme.setChecked(True)

        save_btn = QPushButton('Сохранить')
        save_btn.clicked.connect(self.save_settings)

        layout.addWidget(self.sound_check)
        layout.addWidget(QLabel('Тема:'))
        layout.addWidget(self.light_theme)
        layout.addWidget(self.dark_theme)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_settings(self):
        settings['sound'] = self.sound_check.isChecked()
        settings['theme'] = 'dark' if self.dark_theme.isChecked() else 'light'
        apply_theme()
        self.accept()


def apply_theme():
    app = QApplication.instance()
    if settings['theme'] == 'dark':
        app.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                padding: 5px;
            }
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3d3d3d;
                color: #ffffff;
            }
        """)
    else:
        app.setStyleSheet("")


class GameWindow(QWidget):
    def __init__(self, stacked_widget, main_window):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.main_window = main_window
        self.game = None
        self.spin_done = False
        self.current_spin_value = 0
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Игра')
        self.setGeometry(100, 100, 600, 400)
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.player_label = QLabel('Игрок: ')
        self.drum_value = QLabel('Барабан: 0')
        self.score_label = QLabel('Очки: 0')
        top_layout.addWidget(self.player_label)
        top_layout.addStretch()
        top_layout.addWidget(self.drum_value)
        top_layout.addWidget(self.score_label)

        game_layout = QVBoxLayout()

        drum_layout = QHBoxLayout()
        self.drum_image = QLabel()
        pixmap = QPixmap('drum.jpg')
        if not pixmap.isNull():
            self.drum_image.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.drum_image.setText("Изображение барабана")
        self.drum_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drum_layout.addWidget(self.drum_image)
        game_layout.addLayout(drum_layout)

        self.word_label = QLabel()
        self.word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.word_label.font()
        font.setPointSize(24)
        self.word_label.setFont(font)
        
        self.used_letters = QLabel('Использованные буквы: ')
        self.attempts_label = QLabel('Попытки: 3')

        btn_layout = QHBoxLayout()
        self.spin_btn = QPushButton('Вращать барабан')
        self.spin_btn.clicked.connect(self.spin_drum)
        self.guess_btn = QPushButton('Назвать букву')
        self.guess_btn.clicked.connect(self.guess_letter)
        self.guess_btn.setEnabled(False)

        extra_btn_layout = QHBoxLayout()
        self.guess_word_btn = QPushButton('Назвать слово')
        self.guess_word_btn.clicked.connect(self.guess_word)
        self.guess_word_btn.setEnabled(False)
        self.hint_btn = QPushButton('Подсказка (500)')
        self.hint_btn.clicked.connect(self.show_hint)
        self.hint_btn.setEnabled(False)
        self.surrender_btn = QPushButton('Сдаться')
        self.surrender_btn.clicked.connect(self.surrender)

        btn_layout.addWidget(self.spin_btn)
        btn_layout.addWidget(self.guess_btn)
        extra_btn_layout.addWidget(self.guess_word_btn)
        extra_btn_layout.addWidget(self.hint_btn)
        extra_btn_layout.addWidget(self.surrender_btn)

        main_layout.addLayout(top_layout)
        main_layout.addLayout(game_layout)
        game_layout.addWidget(self.word_label)
        game_layout.addWidget(self.used_letters)
        game_layout.addWidget(self.attempts_label)
        main_layout.addLayout(btn_layout)
        main_layout.addLayout(extra_btn_layout)

        self.setLayout(main_layout)

    def start_game(self):
        self.game = GameLogic()
        self.update_ui()
        self.spin_done = False
        self.current_spin_value = 0
        self.toggle_buttons(False)
        self.show()


    def spin_drum(self):
        self.current_spin_value = self.game.spin_drum()
        self.drum_value.setText(f'Барабан: {self.current_spin_value}')
        self.spin_done = True
        self.toggle_buttons(True)

    def toggle_buttons(self, state):
        self.guess_btn.setEnabled(state)
        self.guess_word_btn.setEnabled(state)
        self.hint_btn.setEnabled(state)

    def guess_letter(self):
        if not self.spin_done:
            QMessageBox.warning(self, 'Ошибка', 'Сначала вращайте барабан!')
            return

        letter, ok = QInputDialog.getText(self, 'Ввод', 'Введите букву:')
        if ok and letter:
            letter = letter.upper()
            if len(letter) != 1 or not letter.isalpha():
                QMessageBox.warning(self, 'Ошибка', 'Введите одну букву!')
                return

            if self.game.guess_letter(letter, self.current_spin_value):
                QMessageBox.information(self, 'Успех', 'Буква угадана!')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Такой буквы нет!')

            self.spin_done = False
            self.current_spin_value = 0
            self.drum_value.setText('Барабан: 0')
            self.toggle_buttons(False)
            self.update_ui()
            self.check_game_over()

    def guess_word(self):
        word, ok = QInputDialog.getText(self, 'Угадать слово', 'Введите слово целиком:')
        if ok and word:
            if self.game.guess_word(word.upper()):
                QMessageBox.information(self, 'Победа!', f'Правильно! Ваш счет: {self.game.score}')
                self.close_game()
            else:
                QMessageBox.critical(self, 'Поражение', 'Неверное слово!')
                self.close_game()

    def show_hint(self):
        if self.game.score < 500:
            QMessageBox.warning(self, 'Ошибка', 'Недостаточно очков!')
            return

        pos, ok = QInputDialog.getInt(self, 'Подсказка', f'Введите позицию буквы (1-{len(self.game.word)}):', min=1,
                                      max=len(self.game.word))
        if ok:
            self.game.use_hint(pos - 1)
            self.update_ui()
            self.check_game_over()

    def surrender(self):
        self.game.score = 0
        QMessageBox.information(self, 'Игра окончена', f'Загаданное слово: {self.game.word}')
        self.close_game()

    def update_ui(self):
        self.word_label.setText(' '.join(self.game.hidden_word))
        self.used_letters.setText(f'Использованные буквы: {", ".join(sorted(self.game.used_letters))}')
        self.attempts_label.setText(f'Попытки: {self.game.attempts}')
        self.score_label.setText(f'Очки: {self.game.score}')
        self.player_label.setText(f'Игрок: {current_user}')

    def check_game_over(self):
        if self.game.is_win():
            QMessageBox.information(self, 'Победа!',
                                    f'Вы выиграли! Слово: {self.game.word}\nВаш счет: {self.game.score}')
            self.close_game()
        elif self.game.attempts <= 0:
            QMessageBox.critical(self, 'Поражение', f'Попытки закончились! Загаданное слово: {self.game.word}')
            self.close_game()

    def close_game(self):
        if current_user:
            if current_user in scores:
                if self.game.score > scores[current_user]:
                    scores[current_user] = self.game.score
            else:
                scores[current_user] = self.game.score

            with open(SCORES_FILE, 'w') as f:
                json.dump(scores, f)

            self.main_window.update_leaderboard()

        self.stacked_widget.setCurrentIndex(0)


class GameLogic:
    def __init__(self):
        self.word = random.choice(words)
        self.hidden_word = ['_' if c != ' ' else ' ' for c in self.word]
        self.used_letters = set()
        self.score = 0
        self.attempts = 3
        self.drum_values = [100, 150, 200, 250, 300]

    def spin_drum(self):
        return random.choice(self.drum_values)


    def guess_letter(self, letter, spin_value):
        if letter in self.used_letters:
            QMessageBox.warning(None, 'Ошибка', 'Эта буква уже была использована!')
            return False

        self.used_letters.add(letter)
        if letter in self.word:
            for i, c in enumerate(self.word):
                if c == letter:
                    self.hidden_word[i] = letter
            self.score += spin_value
            return True
        else:
            self.attempts -= 1
            return False

    def guess_word(self, word):
        if word == self.word:
            self.score *= 2
            return True
        else:
            self.attempts = 0
            return False

    def use_hint(self, position):
        if self.score >= 500:
            self.score -= 500
            letter = self.word[position]
            self.hidden_word[position] = letter
            self.used_letters.add(letter)

    def is_win(self):
        return '_' not in self.hidden_word


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_label = QLabel()
        self.initUI()
        apply_theme()

    def initUI(self):
        self.setWindowTitle('Поле Чудес')
        self.setGeometry(100, 100, 800, 600)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        main_menu = QWidget()
        layout = QVBoxLayout()

        user_frame = QHBoxLayout()
        user_frame.addWidget(QLabel('Текущий пользователь:'))
        user_frame.addWidget(self.user_label)
        layout.addLayout(user_frame)

        buttons = [
            ('Начать игру', self.start_game),
            ('Авторизация', self.show_login),
            ('Обучение', self.show_tutorial),
            ('Настройки', self.show_settings),
            ('Таблица лидеров', self.show_leaderboard),
            ('Выход', self.close)
        ]

        for text, handler in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        main_menu.setLayout(layout)
        self.stacked_widget.addWidget(main_menu)
        self.stacked_widget.addWidget(QWidget())

    def start_game(self):
        if current_user:
            # Удаляем предыдущий игровой виджет, если он существует
            if hasattr(self, 'game_window'):
                self.stacked_widget.removeWidget(self.game_window)
                self.game_window.deleteLater()

            # Создаем новый игровой виджет и добавляем его в стек
            self.game_window = GameWindow(self.stacked_widget, self)
            self.stacked_widget.addWidget(self.game_window)

            # Устанавливаем текущим виджетом игровое окно
            self.stacked_widget.setCurrentWidget(self.game_window)

            self.game_window.start_game()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Требуется авторизация!')

    def show_login(self):
        login_dialog = LoginWindow(self)
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, 'Успех', f'Добро пожаловать, {current_user}!')

    def show_tutorial(self):
        text = """Правила игры:
1. Вращайте барабан для получения очков
2. Угадывайте буквы в слове
3. У вас есть 3 попытки на ошибки
4. Можно назвать слово целиком"""
        QMessageBox.information(self, 'Обучение', text)

    def show_settings(self):
        settings_dialog = SettingsWindow()
        settings_dialog.exec()

    def show_leaderboard(self):
        leaderboard_dialog = LeaderboardWindow(self)
        leaderboard_dialog.exec()

    def update_ui(self):
        if current_user:
            self.user_label.setText(current_user)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
