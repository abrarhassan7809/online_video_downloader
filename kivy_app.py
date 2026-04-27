import os
import threading
import ssl
from kivy.utils import platform
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, ColorProperty
from plyer import notification

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu

import yt_dlp

# SSL & Android Setup
ssl._create_default_https_context = ssl._create_unverified_context
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass


class MyLogger:
    def debug(self, msg): pass

    def warning(self, msg): pass

    def error(self, msg): pass


KV = """
MDScreen:
    md_bg_color: app.bg_color

    MDBoxLayout:
        orientation: 'vertical'
        padding: "15dp"
        spacing: "15dp"

        # Top Bar
        MDCard:
            size_hint_y: None
            height: "70dp"
            padding: "15dp"
            radius: [20,]
            md_bg_color: app.card_color
            elevation: 1

            MDBoxLayout:
                MDLabel:
                    text: "NEX DOWNLOADER"
                    font_style: "H6"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: [0.91, 0.27, 0.37, 1]

                MDIconButton:
                    icon: "brightness-4" if app.theme_cls.theme_style == "Dark" else "brightness-7"
                    theme_icon_color: "Custom"
                    icon_color: [0.91, 0.27, 0.37, 1]
                    on_release: app.toggle_theme()

        # Main Input Card
        MDCard:
            orientation: "vertical"
            padding: "20dp"
            spacing: "20dp"
            radius: [25,]
            md_bg_color: app.card_color
            size_hint_y: None
            height: self.minimum_height
            elevation: 2

            MDTextField:
                id: url_input
                hint_text: "Paste YouTube Link"
                mode: "fill"
                fill_color_normal: app.input_bg
                icon_left: "youtube-subscription"
                text_color_normal: app.text_color
                hint_text_color_normal: [0.5, 0.5, 0.5, 1]

            MDBoxLayout:
                size_hint_y: None
                height: "50dp"
                spacing: "10dp"

                MDRaisedButton:
                    id: type_button
                    text: "Video"
                    size_hint_x: 1
                    md_bg_color: app.btn_secondary
                    on_release: app.type_menu.open()

                MDRaisedButton:
                    id: quality_button
                    text: "720p"
                    size_hint_x: 1
                    md_bg_color: app.btn_secondary
                    on_release: app.quality_menu.open()

            # Action Buttons
            MDBoxLayout:
                size_hint_y: None
                height: "60dp"
                id: btn_box

                MDFillRoundFlatButton:
                    id: download_btn
                    text: "START DOWNLOAD"
                    size_hint: (1, 1)
                    md_bg_color: [0.91, 0.27, 0.37, 1]
                    on_release: app.start_download()

                MDRoundFlatButton:
                    id: cancel_btn
                    text: "STOP"
                    size_hint: (0, 1)
                    opacity: 0
                    disabled: True
                    text_color: app.text_color
                    line_color: [0.91, 0.27, 0.37, 1]
                    on_release: app.cancel_download()

        # Progress Section
        MDCard:
            orientation: "vertical"
            padding: "20dp"
            radius: [25,]
            md_bg_color: app.card_color
            size_hint_y: None
            height: "150dp"

            MDLabel:
                id: status_label
                text: "Waiting for Link..."
                halign: "center"
                theme_text_color: "Secondary"
                font_style: "Caption"

            MDLabel:
                id: progress_label
                text: "0%"
                halign: "center"
                font_style: "H4"
                bold: True
                theme_text_color: "Custom"
                text_color: app.text_color

            MDProgressBar:
                id: progress_bar
                value: 0
                max: 100
                color: [0.91, 0.27, 0.37, 1]

        Widget:
            size_hint_y: 1
"""


class NexDownloaderApp(MDApp):
    selected_type = StringProperty("Video")
    selected_quality = StringProperty("720")
    should_cancel = False

    # Theme Properties for Dynamic Update
    bg_color = ColorProperty([0.05, 0.05, 0.05, 1])
    card_color = ColorProperty([0.12, 0.12, 0.12, 1])
    text_color = ColorProperty([1, 1, 1, 1])
    input_bg = ColorProperty([0.15, 0.15, 0.15, 1])
    btn_secondary = ColorProperty([0.2, 0.2, 0.2, 1])

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"
        if platform != 'android': Window.size = (400, 700)
        return Builder.load_string(KV)

    def toggle_theme(self):
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.theme_style = "Light"
            self.bg_color = [0.95, 0.95, 0.95, 1]
            self.card_color = [1, 1, 1, 1]
            self.text_color = [0, 0, 0, 1]
            self.input_bg = [0.9, 0.9, 0.9, 1]
            self.btn_secondary = [0.8, 0.8, 0.8, 1]
        else:
            self.theme_cls.theme_style = "Dark"
            self.bg_color = [0.05, 0.05, 0.05, 1]
            self.card_color = [0.12, 0.12, 0.12, 1]
            self.text_color = [1, 1, 1, 1]
            self.input_bg = [0.15, 0.15, 0.15, 1]
            self.btn_secondary = [0.2, 0.2, 0.2, 1]

    def on_start(self):
        self.setup_menus()
        if platform == 'android':
            request_permissions(
                [Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

    def setup_menus(self):
        t_items = [{"viewclass": "OneLineListItem", "text": i, "on_release": lambda x=i: self.set_type(x)} for i in
                   ["Video", "Audio (MP3)"]]
        self.type_menu = MDDropdownMenu(caller=self.root.ids.type_button, items=t_items, width_mult=3)

        q_items = [{"viewclass": "OneLineListItem", "text": i, "on_release": lambda x=i: self.set_quality(x)} for i in
                   ["360p", "480p", "720p", "1080p"]]
        self.quality_menu = MDDropdownMenu(caller=self.root.ids.quality_button, items=q_items, width_mult=3)

    def set_type(self, text):
        self.selected_type = text
        self.root.ids.type_button.text = text
        self.type_menu.dismiss()

    def set_quality(self, text):
        self.selected_quality = text.replace('p', '')
        self.root.ids.quality_button.text = text
        self.quality_menu.dismiss()

    def start_download(self):
        url = self.root.ids.url_input.text.strip()
        if not url: return
        self.should_cancel = False
        self.toggle_ui(True)
        threading.Thread(target=self.download_engine, args=(url,), daemon=True).start()

    def progress_hook(self, d):
        if self.should_cancel: raise Exception("CANCELLED")
        if d['status'] == 'downloading':
            p = d.get('downloaded_bytes', 0)
            t = d.get('total_bytes') or d.get('total_bytes_estimate')
            if t:
                percent = (p / t) * 100
                speed = d.get('speed', 0) / 1024 / 1024
                self.update_ui(percent, f"{speed:.1f} MB/s")

    @mainthread
    def update_ui(self, p, s):
        self.root.ids.progress_bar.value = p
        self.root.ids.progress_label.text = f"{int(p)}%"
        self.root.ids.status_label.text = f"Downloading at {s}"

    def download_engine(self, url):
        path = ""
        if platform == 'android':
            try:
                context = autoclass('org.kivy.android.PythonActivity').mActivity
                media_dirs = context.getExternalMediaDirs()
                path = os.path.join(media_dirs[0].getAbsolutePath(), "NexDownloads")
            except:
                path = os.path.join(self.user_data_dir, "NexDownloads")
        else:
            path = "NexDownloads"

        os.makedirs(path, exist_ok=True)

        ydl_opts = {
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'progress_hooks': [self.progress_hook],
            'format': f'best[height<={self.selected_quality}]' if self.selected_type == "Video" else 'bestaudio',
            'logger': MyLogger(),
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if self.should_cancel: return
                info = ydl.extract_info(url, download=True)
            self.finalize("Download Complete!")
        except Exception as e:
            msg = "Stopped" if "CANCELLED" in str(e) else f"Error: {str(e)[:30]}"
            self.finalize(msg)

    @mainthread
    def toggle_ui(self, active):
        d, c = self.root.ids.download_btn, self.root.ids.cancel_btn
        if active:
            d.size_hint_x, d.opacity, d.disabled = 0, 0, True
            c.size_hint_x, c.opacity, c.disabled = 1, 1, False
        else:
            d.size_hint_x, d.opacity, d.disabled = 1, 1, False
            c.size_hint_x, c.opacity, c.disabled = 0, 0, True

    def cancel_download(self):
        self.should_cancel = True
        self.root.ids.status_label.text = "Cancelling..."

    @mainthread
    def finalize(self, msg):
        self.root.ids.status_label.text = msg
        self.toggle_ui(False)


if __name__ == "__main__":
    NexDownloaderApp().run()