import json
import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView  # Добавленный импорт
from kivy.properties import StringProperty, BooleanProperty
from kivy.lang import Builder
from datetime import datetime
import os
from kivy.animation import Animation


# Определение класса EmotionItem
class EmotionItem(BoxLayout):
    emotion_name = StringProperty()

    def __init__(self, emotion_name, **kwargs):
        super().__init__(**kwargs)
        self.emotion_name = emotion_name

        # Создание виджетов внутри EmotionItem
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = '40dp'
        self.spacing = '10dp'
        self.padding = '5dp'

        # Label для отображения имени эмоции
        self.add_widget(Label(text=self.emotion_name, halign='left', valign='middle', text_size=(200, None)))

        # Кнопка для добавления эмоции
        add_button = Button(text='Добавить', size_hint_x=None, width='100dp')
        add_button.bind(on_press=lambda x: App.get_running_app().add_emotion(self.emotion_name))
        self.add_widget(add_button)


# Определение класса StatisticItem
class StatisticItem(BoxLayout):
    date = StringProperty()
    emotion_name = StringProperty()
    count = StringProperty()
    duration = StringProperty()
    reasons = StringProperty()
    reasons_visible = BooleanProperty(False)

    def __init__(self, date, emotion_name, count, duration, reasons, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.date = date
        self.emotion_name = emotion_name
        self.count = count
        self.duration = duration
        self.reasons = reasons
        self.reasons_visible = False

        # Создание горизонтального лэйаута для основной информации и кнопки
        info_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)

        info_layout.add_widget(Label(text=f"Дата: {self.date}", size_hint_x=0.3))
        info_layout.add_widget(Label(text=f"Эмоция: {self.emotion_name}", size_hint_x=0.3))
        info_layout.add_widget(Label(text=f"Количество: {self.count}", size_hint_x=0.2))
        info_layout.add_widget(Label(text=f"Длительность: {self.duration} мин", size_hint_x=0.2))

        # Кнопка для отображения/скрытия причин
        self.detail_button = Button(text='Подробнее', size_hint_x=0.2)
        self.detail_button.bind(on_press=self.toggle_reasons)
        info_layout.add_widget(self.detail_button)

        self.add_widget(info_layout)

        # Label для отображения причин, изначально скрыт
        self.reasons_label = Label(text=f"Причины: {self.reasons}", size_hint_y=None, height=0, opacity=0,
                                   halign='left', valign='top', text_size=(400, None))
        self.reasons_label.bind(texture_size=self.reasons_label.setter('size'))
        self.add_widget(self.reasons_label)

    def toggle_reasons(self, instance):
        if self.reasons_visible:
            # Скрыть причины
            anim = Animation(height=0, opacity=0, duration=0.3)
            anim.start(self.reasons_label)
            self.reasons_visible = False
            self.detail_button.text = 'Подробнее'
        else:
            # Показать причины
            self.reasons_label.height = self.reasons_label.texture_size[1]
            anim = Animation(height=self.reasons_label.texture_size[1], opacity=1, duration=0.3)
            anim.start(self.reasons_label)
            self.reasons_visible = True
            self.detail_button.text = 'Скрыть'


class EmotionTrackerApp(App):
    current_date = StringProperty(datetime.now().strftime('%Y-%m-%d'))

    def build(self):
        # Убедитесь, что директория data существует
        os.makedirs('data', exist_ok=True)

        self.conn = sqlite3.connect('data/emotions.db')
        self.create_tables()
        return Builder.load_file('main.kv')

    def on_start(self):
        self.load_emotions()

    def create_tables(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    duration INTEGER DEFAULT 0,
                    reason TEXT,
                    date TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
        except Exception as e:
            self.show_error_popup(f'Ошибка при создании таблицы: {e}')

    def load_emotions(self):
        try:
            with open('emotions.json', 'r', encoding='utf-8') as f:
                emotions = json.load(f)
            emotions_list = self.root.ids.emotions_list
            for emotion in emotions['emotions']:
                emotions_list.add_widget(EmotionItem(emotion_name=emotion))
        except FileNotFoundError:
            self.show_error_popup('Файл emotions.json не найден.')
        except json.JSONDecodeError:
            self.show_error_popup('Ошибка формата в файле emotions.json.')
        except Exception as e:
            self.show_error_popup(f'Ошибка при загрузке эмоций: {e}')

    def update_current_date(self, date_str):
        if self.validate_date(date_str):
            self.current_date = date_str
        else:
            # Если дата неверна, уведомляем пользователя и возвращаем старую дату
            self.show_error_popup('Неверный формат даты. Используйте YYYY-MM-DD.')
            self.root.ids.date_input.text = self.current_date  # Возвращаем старую дату

    def add_emotion(self, emotion_name):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        duration_input = TextInput(hint_text='Длительность (мин)', input_filter='int', multiline=False)
        reason_input = TextInput(hint_text='Причина', multiline=False)

        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        save_btn = Button(text='Сохранить')
        cancel_btn = Button(text='Отмена')

        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)

        content.add_widget(Label(text=f'Добавить эмоцию: {emotion_name}', size_hint_y=None, height='30dp'))
        content.add_widget(duration_input)
        content.add_widget(reason_input)
        content.add_widget(buttons)

        popup = Popup(title=f'Добавить эмоцию: {emotion_name}',
                      content=content,
                      size_hint=(0.8, 0.6))

        def save(instance):
            try:
                date = self.current_date.strip()
                if not self.validate_date(date):
                    raise ValueError('Неверный формат даты. Используйте YYYY-MM-DD.')

                try:
                    duration = int(duration_input.text)
                except ValueError:
                    duration = 0  # Устанавливаем длительность в 0, если ввод некорректен

                reason = reason_input.text.strip() if reason_input.text.strip() else 'Не указана'

                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO emotions (name, count, duration, reason, date)
                    VALUES (?, 1, ?, ?, ?)
                ''', (emotion_name, duration, reason, date))
                self.conn.commit()

                popup.dismiss()
            except Exception as e:
                self.show_error_popup(f'Не удалось добавить эмоцию: {e}')

        def cancel(instance):
            popup.dismiss()

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=cancel)

        popup.open()

    def validate_date(self, date_str):
        try:
            datetime_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def show_statistics(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT date, name, COUNT(*), SUM(duration), GROUP_CONCAT(reason, '; ')
                FROM emotions
                GROUP BY date, name
                ORDER BY date ASC
            ''')
            stats = cursor.fetchall()

            if not stats:
                stats_text = "Нет данных для отображения."
                # Создание лэйаута с сообщением
                layout = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint_y=None)
                layout.bind(minimum_height=layout.setter('height'))

                stats_label = Label(text=stats_text, size_hint_y=None, text_size=(400, None), halign='left',
                                    valign='top')
                stats_label.bind(texture_size=stats_label.setter('size'))

                layout.add_widget(stats_label)

                # Кнопка закрытия попапа
                close_button = Button(text='Закрыть', size_hint_y=None, height='40dp')
                close_button.bind(on_press=lambda x: popup.dismiss())
                layout.add_widget(close_button)

                # Создание ScrollView и добавление в него лэйаута
                scroll_view = ScrollView(size_hint=(1, 0.9))
                scroll_view.add_widget(layout)

                # Создание и отображение попапа
                popup = Popup(title='Статистика',
                              content=scroll_view,
                              size_hint=(0.9, 0.9))
                popup.open()
                return

            # Если данные есть, создаём лэйаут с элементами статистики
            layout = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint_y=None)
            layout.bind(minimum_height=layout.setter('height'))

            total_duration = 0

            for stat in stats:
                date, name, count, duration, reasons = stat
                total_duration += duration if duration else 0
                reasons = reasons if reasons else 'Не указаны'
                item = StatisticItem(date, name, str(count), str(duration if duration else 0), reasons)
                layout.add_widget(item)

            # Добавляем общее время в конце
            total_label = Label(text=f"Общее время, проведенное в эмоциях: {total_duration} минут",
                                size_hint_y=None, height='30dp', halign='left', valign='top', text_size=(400, None))
            total_label.bind(texture_size=total_label.setter('size'))
            layout.add_widget(total_label)

            # Кнопка закрытия попапа
            close_button = Button(text='Закрыть', size_hint_y=None, height='40dp')
            close_button.bind(on_press=lambda x: popup.dismiss())
            layout.add_widget(close_button)

            # Создание ScrollView и добавление в него лэйаута
            scroll_view = ScrollView(size_hint=(1, 0.9))
            scroll_view.add_widget(layout)

            # Создание и отображение попапа
            popup = Popup(title='Статистика',
                          content=scroll_view,
                          size_hint=(0.9, 0.9))
            popup.open()

        except Exception as e:
            self.show_error_popup(f'Не удалось отобразить статистику: {e}')

    def confirm_clear_statistics(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        message = Label(text='Вы уверены, что хотите очистить всю статистику? Это действие необратимо.',
                        halign='center')
        message.bind(size=message.setter('text_size'))

        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        confirm_btn = Button(text='Да', background_color=(1, 0, 0, 1))
        cancel_btn = Button(text='Нет')

        buttons.add_widget(confirm_btn)
        buttons.add_widget(cancel_btn)

        content.add_widget(message)
        content.add_widget(buttons)

        popup = Popup(title='Подтверждение Очистки',
                      content=content,
                      size_hint=(0.7, 0.4))

        def confirm(instance):
            self.clear_statistics()
            popup.dismiss()

        def cancel(instance):
            popup.dismiss()

        confirm_btn.bind(on_press=confirm)
        cancel_btn.bind(on_press=cancel)

        popup.open()

    def clear_statistics(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM emotions')
            self.conn.commit()

            success_popup = Popup(title='Статистика Очищена',
                                  content=Label(text='Вся статистика успешно очищена.'),
                                  size_hint=(0.6, 0.4))
            success_popup.open()
        except Exception as e:
            self.show_error_popup(f'Не удалось очистить статистику: {e}')

    def open_date_picker(self):
        # Реализация простого DatePicker
        date_picker = SimpleDatePicker(on_date_selected=self.set_date_from_picker)
        date_picker.open()

    def set_date_from_picker(self, selected_date):
        if self.validate_date(selected_date):
            self.current_date = selected_date
            # Обновляем текст в TextInput
            self.root.ids.date_input.text = selected_date
        else:
            self.show_error_popup('Неверный формат даты. Используйте YYYY-MM-DD.')

    def show_error_popup(self, message):
        popup = Popup(title='Ошибка',
                      content=Label(text=message, halign='center', valign='middle', text_size=(400, None)),
                      size_hint=(0.6, 0.4))
        popup.open()


class SimpleDatePicker(Popup):
    def __init__(self, on_date_selected, **kwargs):
        super().__init__(**kwargs)
        self.on_date_selected = on_date_selected
        self.title = "Выберите Дату"
        self.size_hint = (0.8, 0.8)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Поля для ввода года, месяца и дня
        year_input = TextInput(hint_text='Год (YYYY)', input_filter='int', multiline=False)
        month_input = TextInput(hint_text='Месяц (MM)', input_filter='int', multiline=False)
        day_input = TextInput(hint_text='День (DD)', input_filter='int', multiline=False)

        layout.add_widget(year_input)
        layout.add_widget(month_input)
        layout.add_widget(day_input)

        # Кнопки сохранения и отмены
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        save_btn = Button(text='Сохранить')
        cancel_btn = Button(text='Отмена')
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)

        layout.add_widget(buttons)

        self.content = layout

        save_btn.bind(on_press=lambda x: self.save_date(year_input.text, month_input.text, day_input.text))
        cancel_btn.bind(on_press=self.dismiss)

    def save_date(self, year, month, day):
        # Добавляем ведущие нули и проверяем длину
        year = year.strip().zfill(4) if len(year.strip()) < 4 else year.strip()
        month = month.strip().zfill(2) if len(month.strip()) < 2 else month.strip()
        day = day.strip().zfill(2) if len(day.strip()) < 2 else day.strip()

        selected_date = f"{year}-{month}-{day}"
        self.on_date_selected(selected_date)
        self.dismiss()


if __name__ == '__main__':
    EmotionTrackerApp().run()
