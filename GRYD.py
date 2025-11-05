import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QProgressBar,
    QFileDialog, QMessageBox, QStackedWidget, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QUrl
from PySide6.QtGui import QFont, QPixmap, QIcon, QFontDatabase
from PySide6.QtMultimedia import QSoundEffect
import yt_dlp
import requests

def update_yt_dlp():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        print("yt-dlp update ✅")
    except Exception as e:
        print(f"Error update yt-dlp: {e}")

update_yt_dlp()


def human_size(b):
    if not b:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024 or unit == "GB":
            return f"{b:.1f} {unit}"
        b /= 1024

class AnimatedButton(QPushButton):
    def __init__(self, text, animate=True):
        super().__init__(text)
        self._animate = animate
        self.setStyleSheet("text-align: center; padding-left: 8px;")
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self._base_geometry = None
        self._is_active = False

        self.hover_sound = QSoundEffect()
        self.hover_sound.setSource(QUrl.fromLocalFile("assets/sounds/hover.wav"))
        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile("assets/sounds/click.wav"))

    def enterEvent(self, event):
        if self._animate and not self._is_active:
            if self._base_geometry is None:
                self._base_geometry = self.geometry()
            self.anim.stop()
            self.anim.setStartValue(self.geometry())
            self.anim.setEndValue(self._base_geometry.adjusted(-3, -3, 3, 3))
            self.anim.start()
            self.hover_sound.play()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._animate and not self._is_active:
            if self._base_geometry is None:
                self._base_geometry = self.geometry()
            self.anim.stop()
            self.anim.setStartValue(self.geometry())
            self.anim.setEndValue(self._base_geometry)
            self.anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.click_sound.play()
        super().mousePressEvent(event)

    def set_active(self, active: bool, theme):
        self._is_active = active
        if self._base_geometry is None:
            self._base_geometry = self.geometry()
        if active:
            if self._animate:
                self.anim.stop()
                self.anim.setStartValue(self.geometry())
                self.anim.setEndValue(self._base_geometry.adjusted(-5, -5, 5, 5))
                self.anim.start()
            self.setStyleSheet(f"""
                background-color: {theme['secondary']};
                color: {theme['primary']};
                border-radius: 10px;
                font-weight: bold;
                text-align: left;
                padding-left: 8px;
            """)
        else:
            if self._animate:
                self.anim.stop()
                self.anim.setStartValue(self.geometry())
                self.anim.setEndValue(self._base_geometry)
                self.anim.start()
            self.setStyleSheet("text-align: left; padding-left: 8px;")

class GRYD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GRYD")
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowIcon(QIcon("assets/icons/favicon.ico"))

        # --- Темы ---
        self.dark_theme = {
            'background': '#111111',
            'primary': '#faebd7',
            'secondary': '#ff6b35',
            'logo': 'assets/logo/logo_dark.png',
            'icons': {
                'video': 'assets/icons/dark_download.png',
                'settings': 'assets/icons/dark_settings.png',
                'about': 'assets/icons/dark_about.png',
                'exit': 'assets/icons/dark_exit.png',
            }
        }
        self.light_theme = {
            'background': '#faebd7',
            'primary': '#111111',
            'secondary': '#ff6b35',
            'logo': 'assets/logo/logo_light.png',
            'icons': {
                'video': 'assets/icons/light_download.png',
                'settings': 'assets/icons/light_settings.png',
                'about': 'assets/icons/light_about.png',
                'exit': 'assets/icons/light_exit.png',
            }
        }
        self.current_theme = self.dark_theme

        self.languages = {
            "English": {
                "download": "Download",
                "settings": "Settings",
                "about": "About",
                "exit": "Exit",
                "enter_url": "Enter YouTube URL",
                "load": "Load",
                "title": "Title: ",
                "author": "Author: ",
                "duration": "Duration: ",
                "views": "Views: ",
                "likes": "Likes: ",
                "type": "Type",
                "format": "Format",
                "select_theme": "Select Theme",
                "select_language": "Select Language",
                "download_completed": "Download completed successfully!",
                "enter_url_warning": "Enter YouTube URL",
                "ffmpeg_required": "FFmpeg is required. Install FFmpeg and try again.",
                "download_error": "Download error:",
                "only_audio": "only audio",
                "only_video": "only video",
                "video_audio": "video+audio"
            },
            "Русский": {
                "download": "Скачать",
                "settings": "Настройки",
                "about": "О программе",
                "exit": "Выход",
                "enter_url": "Введите URL YouTube",
                "load": "Загрузить",
                "title": "Название: ",
                "author": "Автор: ",
                "duration": "Длительность: ",
                "views": "Просмотры: ",
                "likes": "Лайки: ",
                "type": "Тип",
                "format": "Формат",
                "select_theme": "Выбор темы",
                "select_language": "Выбор языка",
                "download_completed": "Загрузка успешно завершена!",
                "enter_url_warning": "Введите URL YouTube",
                "ffmpeg_required": "Требуется FFmpeg. Установите FFmpeg и повторите попытку.",
                "download_error": "Ошибка загрузки:",
                "only_audio": "только аудио",
                "only_video": "только видео",
                "video_audio": "видео + аудио"
            }
        }
        self.current_language = "English"
        self.tr = self.languages[self.current_language]

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout()
        self.sidebar.setLayout(self.sidebar_layout)
        self.sidebar.setFixedWidth(200)
        self.main_layout.addWidget(self.sidebar)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_opacity = QGraphicsOpacityEffect()
        self.logo_label.setGraphicsEffect(self.logo_opacity)
        self.sidebar_layout.addWidget(self.logo_label, alignment=Qt.AlignTop | Qt.AlignHCenter)

        self.menu_buttons = QWidget()
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setAlignment(Qt.AlignCenter)
        self.menu_buttons.setLayout(self.menu_layout)

        self.btn_video = AnimatedButton(f" {self.tr['download']}")
        self.btn_video.clicked.connect(lambda: self.pages.setCurrentWidget(self.video_page))
        self.btn_settings = AnimatedButton(f" {self.tr['settings']}")
        self.btn_settings.clicked.connect(lambda: self.pages.setCurrentWidget(self.settings_page))
        self.btn_about = AnimatedButton(f" {self.tr['about']}")
        self.btn_about.clicked.connect(lambda: self.pages.setCurrentWidget(self.about_page))

        for btn in [self.btn_video, self.btn_settings, self.btn_about]:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.menu_layout.addWidget(btn)

        self.sidebar_layout.addWidget(self.menu_buttons, alignment=Qt.AlignCenter)

        self.exit_btn = AnimatedButton(f" {self.tr['exit']}")
        self.exit_btn.setFixedWidth(100)
        self.exit_btn.clicked.connect(self.close)
        self.sidebar_layout.addWidget(self.exit_btn, alignment=Qt.AlignBottom | Qt.AlignHCenter)

        self.pages = QStackedWidget()
        self.main_layout.addWidget(self.pages)

        self.video_page = QWidget()
        video_layout = QVBoxLayout()
        self.video_page.setLayout(video_layout)

        url_layout = QHBoxLayout()
        self.video_url_input = QLineEdit()
        self.video_url_input.setPlaceholderText(self.tr['enter_url'])
        url_layout.addWidget(self.video_url_input)
        self.get_info_btn = AnimatedButton(self.tr['load'], animate=False)
        self.get_info_btn.setFixedHeight(32)
        self.get_info_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.get_info_btn.clicked.connect(self.get_video_info)
        url_layout.addWidget(self.get_info_btn)
        video_layout.addLayout(url_layout)
        video_layout.addSpacing(60)

        info_preview_layout = QHBoxLayout()
        self.video_info_layout = QVBoxLayout()
        self.video_title_label = QLabel(f"{self.tr['title']}")
        self.video_author_label = QLabel(f"{self.tr['author']}")
        self.video_duration_label = QLabel(f"{self.tr['duration']}")
        self.video_views_label = QLabel(f"{self.tr['views']}")
        self.video_likes_label = QLabel(f"{self.tr['likes']}")
        for lbl in [self.video_title_label, self.video_author_label, self.video_duration_label,
                    self.video_views_label, self.video_likes_label]:
            self.video_info_layout.addWidget(lbl)
        info_preview_layout.addLayout(self.video_info_layout)

        self.video_thumbnail = QLabel()
        self.video_thumbnail.setFixedSize(320, 180)
        self.video_thumbnail.setStyleSheet("border: 1px solid #ff6b35;")
        self.video_thumbnail.setAlignment(Qt.AlignCenter)
        info_preview_layout.addWidget(self.video_thumbnail)
        video_layout.addLayout(info_preview_layout)

        options_layout = QHBoxLayout()
        type_layout = QHBoxLayout()
        self.download_type_label = QLabel(self.tr['type'])
        self.download_type_label.setFixedWidth(45)
        self.download_type_label.setFixedHeight(170)
        type_layout.addWidget(self.download_type_label)
        self.download_type_combo = QComboBox()
        self.set_download_types()
        self.download_type_combo.currentTextChanged.connect(self.get_video_info)
        self.download_type_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        type_layout.addWidget(self.download_type_combo)
        options_layout.addLayout(type_layout)

        options_layout.addSpacing(40)

        format_layout = QHBoxLayout()
        self.format_label = QLabel(self.tr['format'])
        self.format_label.setFixedWidth(65)
        self.format_label.setFixedHeight(170)
        format_layout.addWidget(self.format_label)
        self.format_combo = QComboBox()
        self.format_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)

        video_layout.addLayout(options_layout)
        video_layout.addStretch(1)

        self.video_download_btn = AnimatedButton(self.tr['download'], animate=False)
        self.video_download_btn.clicked.connect(self.download_video)
        self.video_download_btn.setEnabled(False)
        self.video_download_btn.setFixedWidth(90)
        self.video_download_btn.setFixedHeight(35)
        video_layout.addWidget(self.video_download_btn, alignment=Qt.AlignBottom | Qt.AlignHCenter)

        self.video_progress = QProgressBar()
        self.video_progress.setValue(0)
        self.video_progress.setAlignment(Qt.AlignCenter)
        self.update_progress_style()
        video_layout.addWidget(self.video_progress)

        self.pages.addWidget(self.video_page)

        self.settings_page = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setAlignment(Qt.AlignTop)
        self.settings_page.setLayout(settings_layout)

        theme_layout = QHBoxLayout()
        self.theme_label = QLabel(self.tr['select_theme'])
        self.theme_label.setFixedWidth(150)
        theme_layout.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setMaximumWidth(150)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        settings_layout.addLayout(theme_layout)

        language_layout = QHBoxLayout()
        self.language_label = QLabel(self.tr['select_language'])
        self.language_label.setFixedWidth(150)
        language_layout.addWidget(self.language_label)
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(self.languages.keys()))
        self.language_combo.setMaximumWidth(150)
        self.language_combo.currentTextChanged.connect(self.change_language)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        settings_layout.addLayout(language_layout)

        self.pages.addWidget(self.settings_page)

        self.about_page = QWidget()
        about_layout = QVBoxLayout()
        self.about_page.setLayout(about_layout)
        self.about_label = QLabel("GRYD by deACTA\nVersion 1.0\nhttps://github.com/deACTA\n")
        self.about_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(self.about_label)
        self.pages.addWidget(self.about_page)

        self.pages.setCurrentWidget(self.video_page)
        self.update_logo()
        self.update_icons()
        self.available_formats = {}
        self.apply_theme()

    def set_download_types(self):
        self.download_type_combo.clear()
        self.download_type_combo.addItems([
            self.tr['only_audio'], 
            self.tr['only_video'], 
            self.tr['video_audio']
        ])

    def change_language(self, lang):
        self.current_language = lang
        self.tr = self.languages[self.current_language]
        self.btn_video.setText(f" {self.tr['download']}")
        self.btn_settings.setText(f" {self.tr['settings']}")
        self.btn_about.setText(f" {self.tr['about']}")
        self.exit_btn.setText(f" {self.tr['exit']}")
        self.video_url_input.setPlaceholderText(self.tr['enter_url'])
        self.get_info_btn.setText(self.tr['load'])
        self.video_download_btn.setText(self.tr['download'])
        self.download_type_label.setText(self.tr['type'])
        self.format_label.setText(self.tr['format'])
        self.theme_label.setText(self.tr['select_theme'])
        self.language_label.setText(self.tr['select_language'])
        self.video_title_label.setText(f"{self.tr['title']}")
        self.video_author_label.setText(f"{self.tr['author']}")
        self.video_duration_label.setText(f"{self.tr['duration']}")
        self.video_views_label.setText(f"{self.tr['views']}")
        self.video_likes_label.setText(f"{self.tr['likes']}")
        self.set_download_types()
        for btn in [self.btn_video, self.btn_settings, self.btn_about, self.exit_btn]:
            btn._base_geometry = None

    def apply_theme(self):
        style = f"""
            * {{
                font-family: '{QApplication.font().family()}';
                font-size: 14px;
                color: {self.current_theme['primary']};
            }}
            QMainWindow {{
                background-color: {self.current_theme['background']};
            }}
            QLabel {{
                color: {self.current_theme['primary']};
            }}
            QLineEdit {{
                background-color: {self.current_theme['background']};
                color: {self.current_theme['primary']};
                border: 1px solid {self.current_theme['secondary']};
                padding: 5px;
            }}
            QPushButton {{
                background-color: {self.current_theme['secondary']};
                color: {self.current_theme['primary']};
                border: none;
                padding: 8px;
                border-radius: 8px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {self.current_theme['primary']};
                color: {self.current_theme['secondary']};
            }}
            QComboBox {{
                background-color: {self.current_theme['background']};
                color: {self.current_theme['primary']};
                border: 1px solid {self.current_theme['secondary']};
                padding: 5px;
            }}
        """
        self.setStyleSheet(style)

    def change_theme(self, theme):
        self.current_theme = self.dark_theme if theme == "Dark" else self.light_theme
        self.apply_theme()
        self.update_logo()
        self.update_icons()
        self.update_progress_style()

    def update_logo(self):
        logo_path = self.current_theme['logo']
        pixmap = QPixmap(logo_path)
        if pixmap.isNull():
            return
        fade_out = QPropertyAnimation(self.logo_opacity, b"opacity")
        fade_out.setDuration(250)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        def set_new_logo():
            self.logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            fade_in = QPropertyAnimation(self.logo_opacity, b"opacity")
            fade_in.setDuration(250)
            fade_in.setStartValue(0)
            fade_in.setEndValue(1)
            fade_in.start()
            self.fade_in = fade_in
        fade_out.finished.connect(set_new_logo)
        fade_out.start()
        self.fade_out = fade_out

    def update_icons(self):
        self.btn_video.setIcon(QIcon(self.current_theme['icons']['video']))
        self.btn_settings.setIcon(QIcon(self.current_theme['icons']['settings']))
        self.btn_about.setIcon(QIcon(self.current_theme['icons']['about']))
        self.exit_btn.setIcon(QIcon(self.current_theme['icons']['exit']))

    def update_progress_style(self):
        self.video_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 10px;
                background-color: {self.current_theme['background']};
                color: {self.current_theme['primary']};
                text-align: center;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                border: none;
                border-radius: 10px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.current_theme['secondary']},
                    stop:1 {self.current_theme['primary']}
                );
            }}
        """)
        self.video_progress.setTextVisible(False)

    def get_video_info(self):
        url = self.video_url_input.text().strip()
        if not url:
            return
        ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True, 'ignoreconfig': True, 'no_warnings': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            self.video_title_label.setText(f"{self.tr['title']}{info.get('title', 'N/A')}")
            self.video_author_label.setText(f"{self.tr['author']}{info.get('uploader', 'N/A')}")
            duration = int(info.get('duration') or 0)
            hours, remainder = divmod(duration, 3600)
            mins, secs = divmod(remainder, 60)
            self.video_duration_label.setText(f"{self.tr['duration']}{hours:02d}:{mins:02d}:{secs:02d}")
            self.video_views_label.setText(f"{self.tr['views']}{info.get('view_count', 'N/A')}")
            self.video_likes_label.setText(f"{self.tr['likes']}{info.get('like_count', 'N/A')}")

            thumb = info.get('thumbnail')
            if thumb:
                try:
                    r = requests.get(thumb, timeout=10)
                    p = QPixmap()
                    p.loadFromData(r.content)
                    self.video_thumbnail.setPixmap(p.scaled(self.video_thumbnail.width(), self.video_thumbnail.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                except Exception:
                    self.video_thumbnail.setText("No thumbnail")

            self.video_download_btn.setEnabled(True)
            self.format_combo.clear()
            self.available_formats.clear()
            fmts = info.get('formats', [])
            seen = set()
            dl_type = self.download_type_combo.currentText()
            for f in fmts:
                fid = f.get('format_id')
                if not fid or fid in seen:
                    continue
                seen.add(fid)
                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                has_v = vcodec and vcodec != 'none'
                has_a = acodec and acodec != 'none'
                ext = f.get('ext', '?')
                if dl_type == self.tr['only_audio']:
                    if not (has_a and not has_v): continue
                    if ext not in ["webm", "m4a", "mp3", "opus"]: continue
                if dl_type == self.tr['only_video']:
                    if not (has_v and not has_a): continue
                    if ext not in ["webm", "mp4"]: continue
                if dl_type == self.tr['video_audio']:
                    if not (has_v and has_a): continue
                    if ext not in ["webm", "mp4"]: continue
                width, height = f.get('width'), f.get('height')
                res = f"{height}p" if width and height else "?"
                fps = f.get('fps')
                fps_s = f" {fps}fps" if fps else ""
                size = f.get('filesize') or f.get('filesize_approx')
                size_s = human_size(float(size)) if size else "?"
                label = f"{res}{fps_s} | {ext} | {size_s}"
                self.format_combo.addItem(label, fid)
                self.available_formats[label] = fid
            self.format_combo.insertItem(0, "⭐ Best (auto)", "best")
            self.format_combo.setCurrentIndex(0)

        except Exception as e:
            msg = QMessageBox(self)
            msg.setWindowIcon(QIcon("assets/icons/favicon.ico"))
            msg.critical(self, "GRYD", f"{self.tr['download_error']}\n{e}")

    def progress_hook(self, d, progress_bar):
        try:
            if d.get('status') == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes') or 0
                if total:
                    progress_bar.setValue(int(downloaded * 100 / total))
            elif d.get('status') == 'finished':
                progress_bar.setValue(100)
        except Exception:
            pass

    def download_video(self):
        url = self.video_url_input.text().strip()
        if not url:
            msg = QMessageBox(self)
            msg.setWindowIcon(QIcon("assets/icons/favicon.ico"))
            msg.warning(self, "GRYD", self.tr['enter_url_warning'])
            return
        save_path = QFileDialog.getExistingDirectory(self, "GRYD: Select Download Directory")
        if not save_path:
            return
        self.video_progress.setValue(0)
        self.video_progress.setTextVisible(True)

        format_string = self.format_combo.currentData()
        dl_type = self.download_type_combo.currentText()
        ydl_opts = {
            'outtmpl': os.path.join(save_path, '%(title)s [%(id)s].%(ext)s'),
            'noplaylist': True,
            'ignoreconfig': True,
            'quiet': True,
            'progress_hooks': [lambda d: self.progress_hook(d, self.video_progress)]
        }

        try:
            if dl_type == self.tr['video_audio']:
                ydl_opts['format'] = f"{format_string}+bestaudio" if format_string != "best" else "bestvideo+bestaudio/best"
                ydl_opts['merge_output_format'] = 'mp4'
            elif dl_type == self.tr['only_audio']:
                ydl_opts['format'] = "bestaudio/best" if format_string == "best" else format_string
                ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
            elif dl_type == self.tr['only_video']:
                ydl_opts['format'] = "bestvideo/best" if format_string == "best" else format_string
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            msg = QMessageBox(self)
            msg.setWindowIcon(QIcon("assets/icons/favicon.ico"))
            msg.information(self, "GRYD", self.tr['download_completed'])
        except yt_dlp.utils.DownloadError as e:
            msg = QMessageBox(self)
            msg.setWindowIcon(QIcon("assets/icons/favicon.ico"))
            if "ffmpeg" in str(e).lower():
                msg.critical(self, "GRYD", self.tr['ffmpeg_required'])
            else:
                msg.critical(self, "GRYD", f"{self.tr['download_error']}\n{e}")
        except Exception as e:
            msg = QMessageBox(self)
            msg.setWindowIcon(QIcon("assets/icons/favicon.ico"))
            msg.critical(self, "GRYD", f"{self.tr['download_error']}\n{e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    font_path = "assets/fonts/JetBrainsMono-Regular.ttf"
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        font_families = QFontDatabase().applicationFontFamilies(font_id)
        if font_families:
            app.setFont(QFont(font_families[0], 12))
        else:
            print("Не удалось загрузить шрифт: семьи шрифтов недоступны")
            app.setFont(QFont('Arial', 12))
    else:
        print("Не удалось загрузить шрифт из ресурса")
        app.setFont(QFont('Arial', 12))

    window = GRYD()
    window.show()
    sys.exit(app.exec())