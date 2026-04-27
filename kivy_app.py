import os
import threading
import sys
from kivy.utils import platform
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty
from plyer import notification

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineListItem

import yt_dlp
import ssl

# Disable SSL warnings
ssl._create_default_https_context = ssl._create_unverified_context

# Android Setup
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass


# Logger class
class MyLogger:
    def debug(self, msg): pass

    def warning(self, msg): pass

    def error(self, msg): pass


KV = """
MDScreen:
    md_bg_color: app.theme_cls.bg_normal

    MDBoxLayout:
        orientation: 'vertical'
        padding: ["10dp", "0dp", "10dp", "10dp"]
        spacing: "0dp"

        # Top Bar
        MDBoxLayout:
            size_hint_y: None
            height: "60dp"
            padding: ["5dp", 0]
            MDLabel:
                text: "NexDownloader Pro"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: (0.91, 0.27, 0.37, 1)

            MDIconButton:
                icon: "brightness-4" if app.theme_cls.theme_style == "Dark" else "brightness-7"
                on_release: app.toggle_theme()

        # Main Card
        MDCard:
            orientation: "vertical"
            padding: "20dp"
            spacing: "20dp"
            radius: [25, 25, 25, 25]
            elevation: 2
            size_hint_y: None
            height: self.minimum_height
            md_bg_color: app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else [0.98, 0.98, 0.98, 1]

            MDTextField:
                id: url_input
                hint_text: "Paste YouTube Link Here"
                mode: "rectangle"
                icon_left: "link-variant"

            MDBoxLayout:
                size_hint_y: None
                height: "50dp"
                spacing: "15dp"

                MDRaisedButton:
                    id: type_button
                    text: "Format: Video"
                    size_hint_x: 0.5
                    md_bg_color: (0.91, 0.27, 0.37, 1)
                    on_release: app.type_menu.open()

                MDRaisedButton:
                    id: quality_button
                    text: "Quality: 720p"
                    size_hint_x: 0.5
                    md_bg_color: (0.1, 0.3, 0.5, 1)
                    on_release: app.quality_menu.open()

            # Start/Cancel Button
            MDBoxLayout:
                size_hint_y: None
                height: "55dp"
                id: btn_container

                MDRaisedButton:
                    id: download_btn
                    text: "START DOWNLOAD"
                    size_hint_x: 1
                    height: "55dp"
                    md_bg_color: (0.91, 0.27, 0.37, 1)
                    bold: True
                    on_release: app.start_download()

                MDRaisedButton:
                    id: cancel_btn
                    text: "CANCEL"
                    size_hint_x: 0
                    opacity: 0
                    disabled: True
                    height: "55dp"
                    md_bg_color: (0.5, 0.5, 0.5, 1)
                    on_release: app.cancel_download()

            # Progress Section
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                spacing: "10dp"
                padding: [0, "30dp", 0, 0]

                MDLabel:
                    id: progress_label
                    text: "0%"
                    halign: "center"
                    font_style: "H4"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: (0.2, 1, 0.5, 1)

                MDProgressBar:
                    id: progress_bar
                    value: 0
                    max: 100
                    size_hint_y: None
                    height: "10dp"

            MDLabel:
                id: status_label
                text: "Ready to download!"
                halign: "center"
                theme_text_color: "Secondary"
                font_style: "Caption"

        Widget:
            size_hint_y: 1
"""


class NexDownloaderApp(MDApp):
    selected_type = StringProperty("Video")
    selected_quality = StringProperty("720")
    should_cancel = False

    def build(self):
        self.theme_cls.primary_palette = "Red"
        self.theme_cls.theme_style = "Dark"
        if platform != 'android':
            Window.size = (400, 750)
        return Builder.load_string(KV)

    def on_start(self):
        self.setup_menus()
        if platform == 'android':
            # Request permissions
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
            self.show_notification("✅ App Ready! Files will be saved in Android/media/")

    def setup_menus(self):
        type_items = [
            {"viewclass": "OneLineListItem", "text": "Video", "on_release": lambda x="Video": self.set_type(x)},
            {"viewclass": "OneLineListItem", "text": "Audio (MP3)",
             "on_release": lambda x="Audio (MP3)": self.set_type(x)}
        ]
        self.type_menu = MDDropdownMenu(caller=self.root.ids.type_button, items=type_items, width_mult=4)

        qualities = ["360p", "480p", "720p", "1080p"]
        quality_items = [{"viewclass": "OneLineListItem", "text": q, "on_release": lambda x=q: self.set_quality(x)} for
                         q in qualities]
        self.quality_menu = MDDropdownMenu(caller=self.root.ids.quality_button, items=quality_items, width_mult=3)

    def set_type(self, text):
        self.selected_type = text
        self.root.ids.type_button.text = f"Format: {text}"
        self.type_menu.dismiss()

    def set_quality(self, text):
        self.selected_quality = text.replace('p', '')
        self.root.ids.quality_button.text = f"Quality: {text}"
        self.quality_menu.dismiss()

    def start_download(self):
        url = self.root.ids.url_input.text.strip()
        if not url:
            self.show_notification("❌ Please enter a URL")
            return
        self.should_cancel = False
        self.toggle_buttons(True)
        threading.Thread(target=self.download_engine, args=(url,), daemon=True).start()

    def progress_hook(self, d):
        """yt-dlp progress hook"""
        if self.should_cancel:
            raise Exception("Download cancelled by user")

        if d['status'] == 'downloading':
            try:
                # Calculate percentage
                if 'total_bytes' in d:
                    total = d['total_bytes']
                    downloaded = d.get('downloaded_bytes', 0)
                    percent = (downloaded / total) * 100
                elif 'total_bytes_estimate' in d:
                    total = d['total_bytes_estimate']
                    downloaded = d.get('downloaded_bytes', 0)
                    percent = (downloaded / total) * 100
                else:
                    percent = 0

                # Get speed
                speed = d.get('speed', 0)
                if speed:
                    speed_mb = speed / 1024 / 1024
                    speed_str = f"{speed_mb:.1f} MB/s"
                else:
                    speed_str = "Calculating..."

                # Update UI
                self.update_ui(percent, speed_str)
            except:
                pass

        elif d['status'] == 'finished':
            self.update_ui(100, "Processing...")

        elif d['status'] == 'error':
            self.show_notification("❌ Download error")

    def download_engine(self, url):
        """Main download engine"""
        path = None

        if platform == 'android':
            try:
                # Method 1: External Media Directory (Best for Android 10+)
                context = autoclass('org.kivy.android.PythonActivity').mActivity
                media_dirs = context.getExternalMediaDirs()
                if media_dirs and len(media_dirs) > 0:
                    path = os.path.join(media_dirs[0].getAbsolutePath(), "NexDownloads")
                    print(f"✅ Using Media Dir: {path}")
            except Exception as e:
                print(f"Media Dir error: {e}")

        # Fallback paths
        if not path:
            try:
                path = os.path.join(self.user_data_dir, "NexDownloads")
                print(f"✅ Using User Data Dir: {path}")
            except:
                pass

        if not path:
            path = os.path.join(os.getcwd(), "NexDownloads")

        # Create directory
        try:
            os.makedirs(path, exist_ok=True)
            self.show_notification(f"📁 Saving to: {path}")
        except Exception as e:
            print(f"Dir creation error: {e}")
            path = os.getcwd()
            os.makedirs(path, exist_ok=True)

        # Prepare download options
        if self.selected_type == "Video":
            format_spec = f'best[height<={self.selected_quality}][ext=mp4]/best[height<={self.selected_quality}]/best'
        else:
            format_spec = 'bestaudio/best'

        ydl_opts = {
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'progress_hooks': [self.progress_hook],
            'format': format_spec,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'logger': MyLogger(),
        }

        # Audio post-processing
        if self.selected_type == "Audio (MP3)":
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

        try:
            self.show_notification("⏬ Downloading...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                # Handle audio filename
                if self.selected_type == "Audio (MP3)":
                    filename = filename.rsplit('.', 1)[0] + '.mp3'

                self.show_notification(f"✅ Saved: {os.path.basename(filename)}")
                self.finalize("✅ Download completed!")

                # Send notification
                try:
                    notification.notify(
                        title="NexDownloader Pro",
                        message=f"Download complete!\n{os.path.basename(filename)}",
                        timeout=5
                    )
                except:
                    pass

        except Exception as e:
            error_msg = str(e)
            print(f"Download error: {error_msg}")
            self.show_notification(f"❌ Error: {error_msg[:50]}")
            self.finalize(f"❌ Error: {error_msg[:50]}")

    def show_notification(self, message):
        """Show status message"""
        try:
            self.root.ids.status_label.text = message
        except:
            pass

    @mainthread
    def update_ui(self, percent, speed):
        """Update progress UI"""
        try:
            self.root.ids.progress_bar.value = percent
            self.root.ids.progress_label.text = f"{int(percent)}%"
            if speed:
                self.root.ids.status_label.text = f"Downloading... {speed}"
        except:
            pass

    @mainthread
    def toggle_buttons(self, downloading):
        """Toggle between start/cancel buttons"""
        try:
            d_btn = self.root.ids.download_btn
            c_btn = self.root.ids.cancel_btn

            if downloading:
                d_btn.size_hint_x = 0
                d_btn.opacity = 0
                d_btn.disabled = True
                c_btn.size_hint_x = 1
                c_btn.opacity = 1
                c_btn.disabled = False
            else:
                d_btn.size_hint_x = 1
                d_btn.opacity = 1
                d_btn.disabled = False
                c_btn.size_hint_x = 0
                c_btn.opacity = 0
                c_btn.disabled = True
        except:
            pass

    def cancel_download(self):
        """Cancel ongoing download"""
        self.should_cancel = True
        self.show_notification("⏹️ Cancelling...")

    @mainthread
    def finalize(self, msg):
        """Finalize download"""
        self.show_notification(msg)
        self.toggle_buttons(False)
        # Reset progress
        try:
            self.root.ids.progress_bar.value = 0
            self.root.ids.progress_label.text = "0%"
        except:
            pass

    def toggle_theme(self):
        """Toggle dark/light theme"""
        self.theme_cls.theme_style = "Light" if self.theme_cls.theme_style == "Dark" else "Dark"


if __name__ == "__main__":
    NexDownloaderApp().run()