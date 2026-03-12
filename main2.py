import asyncio
import os
import webbrowser

# We will import libsql_client inside a try-except block later to catch missing dependencies
try:
    import libsql_client
except ImportError:
    libsql_client = None
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDList, ThreeLineRightIconListItem, IconRightWidget, OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.card import MDCard
from kivymd.uix.fitimage import FitImage
from kivy.metrics import dp
from kivy.utils import platform
from kivy.core.window import Window 
from kivy.graphics import Color, Line # Para dibujar la línea azul

# --- Configuración de Logs ---
from kivy.logger import Logger
import logging

def setup_logging():
    try:
        if platform == 'android':
            from android.storage import app_storage_path
            # Use app internal storage for maximum reliability
            log_dir = os.path.join(app_storage_path(), 'logs')
        else:
            log_dir = os.path.dirname(os.path.abspath(__file__))

        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app_log.txt")
        
        # Configurar un file handler para el logger de Kivy
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger('kivy').addHandler(fh)
        
        Logger.info(f"Logging initialized. File: {log_file}")
        return log_file
    except Exception as e:
        Logger.error(f"Failed to initialize file logging: {e}")
        return None

# --- Database Manager (Turso/libSQL) ---
class DatabaseManager:
    def __init__(self):
        self.url = "https://historiasclinica-smhuglich.aws-us-east-1.turso.io"
        self.token = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJleHAiOjE3NzM4NDkwOTYsImlhdCI6MTc3MzI0NDI5NiwiaWQiOiIwMTljZGQ5NC0wODAxLTc4OWQtOWMwNS0xN2MzY2Q1OWZjMDkiLCJyaWQiOiI5ZjAzMDdhYy0wODk3LTQ5YjEtYmQ1OC02MzViMTMxMjQ3MjkifQ.lXR31lF8cKw6imVLcFGbKGAMPcdZSDS0vQwjvXXGQMAvPzAUGHXDVhfTj3qHuPO73z3gaCYdQPMv5SZlUbz8Aw"
        if libsql_client is None:
            raise ImportError("libsql_client is not installed or failed to import. Check requirements.")
        self.client = libsql_client.create_client(self.url, auth_token=self.token)

    async def get_specialties(self):
        try:
            Logger.info("DatabaseManager: Fetching specialties...")
            rs = await self.client.execute("SELECT id, nombre FROM especialidades ORDER BY nombre ASC")
            Logger.info(f"DatabaseManager: Found {len(rs.rows)} specialties.")
            return [{"id": str(row[0]), "nombre": row[1]} for row in rs.rows]
        except Exception as e:
            Logger.error(f"DatabaseManager Error (get_specialties): {e}")
            import traceback
            Logger.error(traceback.format_exc())
            raise e

    async def get_institutions(self, specialty_id):
        # Retorna instituciones que ofrecen la especialidad dada
        rs = await self.client.execute(
            "SELECT id, nombre, direccion, telefono FROM instituciones WHERE especialidad_id = ? ORDER BY nombre ASC",
            [specialty_id]
        )
        return [{"id": str(row[0]), "nombre": row[1], "direccion": row[2], "telefono": row[3]} for row in rs.rows]

    async def get_schedules(self, institution_id):
        # Retorna horarios para una institución, uniendo con profesionales
        query = """
            SELECT p.nombre, p.apellido, h.dia_semana, h.hora_inicio, h.hora_fin
            FROM horarios_atencion h
            JOIN profesionales p ON h.profesional_id = p.id
            WHERE h.institucion_id = ?
            ORDER BY h.dia_semana, h.hora_inicio
        """
        rs = await self.client.execute(query, [institution_id])
        return [
            (
                row[0], 
                row[1], 
                row[2], 
                row[3], 
                row[4]
            ) for row in rs.rows
        ]

# --- Componentes de Interfaz ---

class InstitutionCard(MDBoxLayout):
    def __init__(self, inst, schedules, call_phone_cb, open_map_cb, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))
        
        # Fondo y línea divisoria azul oscuro más fina
        with self.canvas.before:
            Color(0.05, 0.2, 0.4, 1) # Azul muy oscuro
            self.line = Line(points=[0, 0, 0, 0], width=1)
        self.bind(size=self._update_line, pos=self._update_line)
        
        # Fila principal con botones integrados
        main_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), padding=dp(10))
        
        # Texto de la institución
        text_box = MDBoxLayout(orientation='vertical')
        text_box.add_widget(MDLabel(text=inst['nombre'], font_style="Subtitle1", theme_text_color="Primary"))
        text_box.add_widget(MDLabel(text=inst['direccion'], font_style="Caption", theme_text_color="Secondary"))
        
        main_row.add_widget(text_box)
        
        # Botones de acción integrados
        actions_box = MDBoxLayout(orientation='horizontal', size_hint_x=None, width=dp(100), spacing=dp(5))
        
        if inst['telefono']:
            btn_call = MDIconButton(icon="phone", theme_text_color="Custom", text_color=[0.05, 0.2, 0.4, 1])
            btn_call.bind(on_release=lambda x: call_phone_cb(inst['telefono']))
            actions_box.add_widget(btn_call)
            
        btn_map = MDIconButton(icon="map-marker-radius", theme_text_color="Custom", text_color=[0.05, 0.2, 0.4, 1])
        btn_map.bind(on_release=lambda x: open_map_cb(inst['direccion']))
        actions_box.add_widget(btn_map)
        
        main_row.add_widget(actions_box)
        self.add_widget(main_row)

        # Horarios
        if schedules:
            sched_box = MDBoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(16), 0, dp(16), dp(10)])
            sched_box.bind(minimum_height=sched_box.setter('height'))
            profs = {}
            for r in schedules:
                name = f"{r[0]} {r[1]}"
                if name not in profs: profs[name] = []
                profs[name].append(r)
            for p, rows in profs.items():
                p_container = MDBoxLayout(
                    orientation='vertical', 
                    size_hint_y=None, 
                    md_bg_color=[0.74, 0.78, 0.55, 1],
                    padding=[dp(8), dp(4), dp(8), dp(4)],
                    radius=[dp(4), dp(4), dp(4), dp(4)],
                    spacing=dp(2)
                )
                p_container.bind(minimum_height=p_container.setter('height'))
                
                p_container.add_widget(MDLabel(text=f"[b]{p.upper()}[/b]", markup=True, size_hint_y=None, height=dp(25), font_style="Caption"))
                for r in rows:
                    row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(18))
                    row.add_widget(MDLabel(text=r[2], font_style="Caption", theme_text_color="Secondary"))
                    row.add_widget(MDLabel(text=f"{r[3]}-{r[4]}", font_style="Caption", halign="right", theme_text_color="Secondary"))
                    p_container.add_widget(row)
                sched_box.add_widget(p_container)
                # Espacio entre profesionales
                sched_box.add_widget(MDBoxLayout(size_hint_y=None, height=dp(5)))
            self.add_widget(sched_box)

    def _update_line(self, *args):
        self.line.points = [self.x, self.y, self.x + self.width, self.y]

class MainScreen(Screen): pass

class MedicalApp(MDApp):
    def build(self):
        try:
            self.theme_cls.primary_palette = "Blue"
            # We initialize DB later or wrap it to catch errors
            try:
                self.db = DatabaseManager()
            except Exception as e:
                Logger.error(f"DB Error: {e}")
                self.db = None

            self.sm = ScreenManager()
            self.all_current_data = [] 

            self.screen_main = MainScreen(name='main')
            layout = MDBoxLayout(orientation='vertical', spacing=10)
            
            # Intentar cargar la barra superior
            try:
                app_bar = MDTopAppBar(title="Guia Medica")
                layout.add_widget(app_bar)
            except Exception as e:
                Logger.error(f"MDTopAppBar Error: {e}")
                layout.add_widget(MDLabel(text="Guia Medica", halign="center", size_hint_y=None, height=dp(50)))
            
            filter_area = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=10, spacing=5)
            self.spec_field = MDTextField(hint_text="1. Elija Especialidad", readonly=True)
            self.spec_field.bind(on_touch_down=self.open_menu)
            filter_area.add_widget(self.spec_field)
            
            layout.add_widget(filter_area)
            self.prog = MDProgressBar(type="indeterminate", opacity=0, size_hint_y=None, height=dp(4))
            layout.add_widget(self.prog)
            
            self.scroll = MDScrollView(
                bar_width=dp(4), 
                scroll_type=['bars', 'content'],
                effect_cls="DampedScrollEffect"
            )
            self.list_ui = MDList()
            self.scroll.add_widget(self.list_ui)
            layout.add_widget(self.scroll)
            
            # Barra fija inferior
            footer = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(70),
                padding=[dp(20), dp(5), dp(20), dp(5)],
                spacing=dp(10),
                md_bg_color=[1, 1, 1, 1]
            )
            
            logo_img = "studio_logo.png"
            if not os.path.exists(logo_img):
                Logger.warning(f"Image not found: {logo_img}")
                logo = MDLabel(text="LOGO", size_hint=(None, None), size=(dp(40), dp(40)))
            else:
                logo = FitImage(
                    source=logo_img,
                    size_hint=(None, None),
                    size=(dp(40), dp(40)),
                    radius=[dp(20)],
                    pos_hint={'center_y': 0.5}
                )
            
            info_box = MDBoxLayout(orientation='vertical', spacing=dp(2), pos_hint={'center_y': 0.5})
            info_box.add_widget(MDLabel(
                text="STUDIO SOFTWARE",
                font_style="Subtitle2",
                theme_text_color="Primary",
                halign="left"
            ))
            info_box.add_widget(MDLabel(
                text="sergiohuglich1@gmail.com",
                font_style="Caption",
                theme_text_color="Secondary",
                halign="left"
            ))
            
            footer.add_widget(logo)
            footer.add_widget(info_box)
            
            layout.add_widget(footer)
            self.screen_main.add_widget(layout)
            self.sm.add_widget(self.screen_main)
            
            self.menu = None
            Window.bind(on_keyboard=self.on_key_down)
            return self.sm
        except Exception as e:
            Logger.error(f"CRITICAL BUILD ERROR: {e}")
            import traceback
            Logger.error(traceback.format_exc())
            # Si falla build(), devolvemos un label básico para que la app no muera sin decir nada
            return MDLabel(text=f"Error al iniciar:\n{str(e)}", halign="center")

    def on_start(self):
        asyncio.create_task(self.load_specs())

    def on_key_down(self, window, key, *args):
        if key == 27:
            return self.handle_back_button()
        return False

    def handle_back_button(self):
        if self.menu and self.menu.parent:
            self.menu.dismiss()
            return True
        if self.list_ui.children:
            self.list_ui.clear_widgets()
            self.spec_field.text = ""
            return True
        return False

    async def load_specs(self):
        try:
            if not self.db:
                Logger.error("MedicalApp: DatabaseManager not initialized.")
                self.show_error_dialog("Error de Base de Datos", "No se pudo conectar al servidor de datos.")
                return

            Logger.info("MedicalApp: Loading specialties...")
            specs = await self.db.get_specialties()
            if not specs:
                Logger.warning("MedicalApp: No specialties returned from DB.")
                self.show_error_dialog("Aviso", "No se encontraron especialidades cargadas.")
                return

            self.spec_map = {r['nombre']: r['id'] for r in specs}
            items = [{"text": r['nombre'], "viewclass": "OneLineListItem", "on_release": lambda x=r['nombre']: self.set_spec(x)} for r in specs]
            self.menu = MDDropdownMenu(caller=self.spec_field, items=items, width_mult=4)
            Logger.info("MedicalApp: Specialties loaded successfully.")
        except Exception as e:
            Logger.error(f"MedicalApp Error (load_specs): {e}")
            self.show_error_dialog("Error de Conexión", f"No se pudieron cargar las especialidades:\n{str(e)}")

    def show_error_dialog(self, title, text):
        from kivymd.uix.button import MDFlatButton
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="CERRAR",
                    on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
        dialog.open()

    def open_menu(self, inst, touch):
        if inst.collide_point(*touch.pos) and self.menu: self.menu.open()

    def set_spec(self, name):
        self.spec_field.text = name
        self.menu.dismiss()
        asyncio.create_task(self.fetch_data(name))

    async def fetch_data(self, spec_name):
        self.prog.opacity = 1
        self.prog.start()
        sid = self.spec_map[spec_name]
        raw_insts = await self.db.get_institutions(sid)
        self.all_current_data = []
        for r in raw_insts:
            scheds = await self.db.get_schedules(r['id'])
            self.all_current_data.append({'info': r, 'scheds': scheds})
        self.update_list(self.all_current_data)
        self.prog.stop()
        self.prog.opacity = 0

    def update_list(self, data_to_show):
        self.list_ui.clear_widgets()
        for item in data_to_show:
            card = InstitutionCard(item['info'], item['scheds'], self.call_phone, self.open_map)
            self.list_ui.add_widget(card)

    def call_phone(self, num): 
        webbrowser.open(f"tel:{num}")

    def open_map(self, direccion):
        # Aseguramos que la búsqueda incluya 'San Rafael, Mendoza' para centrar el mapa
        query = f"{direccion}, San Rafael, Mendoza".replace(" ", "+")
        url = f"https://www.google.com/maps/search/?api=1&query={query}"
        webbrowser.open(url)

from kivy.logger import Logger

if __name__ == "__main__":
    log_path = setup_logging()
    try:
        app = MedicalApp()
        asyncio.run(app.async_run(async_lib="asyncio"))
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        Logger.error(f"FATAL ERROR:\n{error_msg}")
        # Guardar redundante por si falla el logger de Kivy
        try:
            with open(log_path, "a") as f:
                import datetime
                f.write(f"\n--- FATAL CRASH {datetime.datetime.now()} ---\n")
                f.write(error_msg)
        except:
            pass
        raise e