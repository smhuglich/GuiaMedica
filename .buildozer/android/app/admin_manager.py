import asyncio
import os
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, TwoLineIconListItem, OneLineIconListItem, IconLeftWidget
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from main import DatabaseManager, create_db_manager
import logging

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class AdminDashboard(Screen): pass
class InstitutionListScreen(Screen): pass
class ProfessionalListScreen(Screen): pass
class SpecialtyListScreen(Screen): pass
class InstitutionEditScreen(Screen): pass
class ProfessionalEditScreen(Screen): pass
class SpecialtyEditScreen(Screen): pass
class ScheduleEditScreen(Screen): pass

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

KV = """
<AdminDashboard>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Administración - Guía Médica"
            elevation: 4
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(20)
            spacing: dp(15)
            pos_hint: {"center_y": .5}
            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(15)
                size_hint_y: None
                height: dp(120)
                MDCard:
                    orientation: "vertical"
                    padding: dp(10)
                    radius: [dp(15)]
                    ripple_behavior: True
                    md_bg_color: 0.13, 0.59, 0.95, 1
                    on_release: app.root.current = "inst_list"
                    MDLabel:
                        text: "Instituciones"
                        halign: "center"
                        valign: "center"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_style: "H6"
                MDCard:
                    orientation: "vertical"
                    padding: dp(10)
                    radius: [dp(15)]
                    ripple_behavior: True
                    md_bg_color: 0.0, 0.74, 0.83, 1
                    on_release: app.root.current = "prof_list"
                    MDLabel:
                        text: "Profesionales"
                        halign: "center"
                        valign: "center"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_style: "H6"
            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(15)
                size_hint_y: None
                height: dp(120)
                MDCard:
                    orientation: "vertical"
                    padding: dp(10)
                    radius: [dp(15)]
                    ripple_behavior: True
                    md_bg_color: 0.61, 0.15, 0.69, 1
                    on_release: app.root.current = "spec_list"
                    MDLabel:
                        text: "Especialidades"
                        halign: "center"
                        valign: "center"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_style: "H6"
                MDCard:
                    orientation: "vertical"
                    padding: dp(10)
                    radius: [dp(15)]
                    ripple_behavior: True
                    md_bg_color: 0.30, 0.69, 0.31, 1
                    on_release: app.show_report_menu()
                    MDLabel:
                        text: "Reportes"
                        halign: "center"
                        valign: "center"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_style: "H6"

<InstitutionListScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Instituciones"
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["plus", lambda x: app.edit_institution()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(10)
            MDTextField:
                id: search_field
                hint_text: "Buscar institución..."
                on_text: app.filter_institutions(self.text)
            MDScrollView:
                MDList:
                    id: inst_list_container

<ProfessionalListScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Profesionales"
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["plus", lambda x: app.edit_professional()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(10)
            MDTextField:
                id: search_field
                hint_text: "Buscar profesional..."
                on_text: app.filter_professionals(self.text)
            MDScrollView:
                MDList:
                    id: prof_list_container

<SpecialtyListScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Especialidades"
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["plus", lambda x: app.edit_specialty()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(10)
            MDTextField:
                id: search_field
                hint_text: "Buscar especialidad..."
                on_text: app.filter_specialties(self.text)
            MDScrollView:
                MDList:
                    id: spec_list_container

<InstitutionEditScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            id: toolbar
            title: "Editar Institución"
            left_action_items: [["arrow-left", lambda x: app.go_to("inst_list")]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(20)
            spacing: dp(10)
            MDTextField:
                id: name_field
                hint_text: "Nombre"
            MDTextField:
                id: addr_field
                hint_text: "Dirección"
            MDTextField:
                id: phone_field
                hint_text: "Teléfono"
            MDBoxLayout:
                size_hint_y: None
                height: dp(50)
                spacing: dp(10)
                MDRaisedButton:
                    text: "GUARDAR"
                    on_release: app.save_institution()
                MDFlatButton:
                    text: "ELIMINAR"
                    theme_text_color: "Custom"
                    text_color: 1, 0, 0, 1
                    on_release: app.confirm_delete_institution()

<ProfessionalEditScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            id: toolbar
            title: "Editar Profesional"
            left_action_items: [["arrow-left", lambda x: app.go_to("prof_list")]]
            right_action_items: [["calendar-clock", lambda x: app.manage_schedules()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(20)
            spacing: dp(10)
            MDTextField:
                id: name_field
                hint_text: "Nombre"
            MDTextField:
                id: last_name_field
                hint_text: "Apellido"
            MDTextField:
                id: mat_field
                hint_text: "Matrícula"
            MDTextField:
                id: phone_field
                hint_text: "Teléfono"
            MDBoxLayout:
                size_hint_y: None
                height: dp(50)
                spacing: dp(10)
                MDRaisedButton:
                    text: "GUARDAR"
                    on_release: app.save_professional()
                MDFlatButton:
                    text: "ELIMINAR"
                    theme_text_color: "Custom"
                    text_color: 1, 0, 0, 1
                    on_release: app.confirm_delete_professional()
            MDRaisedButton:
                id: btn_schedules
                text: "GESTIONAR HORARIOS"
                pos_hint: {"center_x": .5}
                size_hint_x: .9
                size_hint_y: None
                height: dp(50)
                md_bg_color: 0.05, 0.3, 0.6, 1
                on_release: app.manage_schedules()

<SpecialtyEditScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            id: toolbar
            title: "Editar Especialidad"
            left_action_items: [["arrow-left", lambda x: app.go_to("spec_list")]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(20)
            spacing: dp(10)
            MDTextField:
                id: name_field
                hint_text: "Nombre de Especialidad"
            MDBoxLayout:
                size_hint_y: None
                height: dp(50)
                spacing: dp(10)
                MDRaisedButton:
                    text: "GUARDAR"
                    on_release: app.save_specialty()
                MDFlatButton:
                    text: "ELIMINAR"
                    theme_text_color: "Custom"
                    text_color: 1, 0, 0, 1
                    on_release: app.confirm_delete_specialty()

<ScheduleEditScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            id: toolbar
            title: "Gestionar Horarios"
            left_action_items: [["arrow-left", lambda x: app.go_to("prof_edit")]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(10)
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: dp(5)
                spacing: dp(5)
                MDTextField:
                    id: inst_field
                    hint_text: "Institución"
                    readonly: True
                    on_focus: if self.focus: app.open_inst_menu()
                MDTextField:
                    id: day_field
                    hint_text: "Día"
                    readonly: True
                    on_focus: if self.focus: app.open_day_menu()
                MDBoxLayout:
                    spacing: dp(10)
                    MDTextField:
                        id: start_field
                        hint_text: "Inicio (Ej: 08:00)"
                    MDTextField:
                        id: end_field
                        hint_text: "Fin (Ej: 12:00)"
                MDRaisedButton:
                    text: "AGREGAR HORARIO"
                    pos_hint: {"center_x": .5}
                    on_release: app.add_schedule_item()
            MDScrollView:
                MDList:
                    id: schedule_list_container
"""

class AdminManagerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = None
        self.current_item = None
        self.inst_menu = None
        self.day_menu = None
        self.selected_inst_id = None
        self.selected_day_num = None

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        Builder.load_string(KV)
        self.db = create_db_manager()
        self.sm = ScreenManager()
        self.sm.add_widget(AdminDashboard(name="dashboard"))
        self.sm.add_widget(InstitutionListScreen(name="inst_list"))
        self.sm.add_widget(ProfessionalListScreen(name="prof_list"))
        self.sm.add_widget(SpecialtyListScreen(name="spec_list"))
        self.sm.add_widget(InstitutionEditScreen(name="inst_edit"))
        self.sm.add_widget(ProfessionalEditScreen(name="prof_edit"))
        self.sm.add_widget(SpecialtyEditScreen(name="spec_edit"))
        self.sm.add_widget(ScheduleEditScreen(name="sched_edit"))
        return self.sm

    def on_start(self): asyncio.create_task(self.load_data())
    async def load_data(self):
        await self.refresh_institutions()
        await self.refresh_professionals()
        await self.refresh_specialties()

    # --- REFRESH METHODS ---
    async def refresh_institutions(self, filter_text=""):
        container = self.sm.get_screen("inst_list").ids.inst_list_container
        container.clear_widgets()
        data = await self.db.get_all_institutions()
        for i in data:
            if filter_text.lower() in i["nombre"].lower():
                container.add_widget(TwoLineIconListItem(text=i["nombre"], secondary_text=i["direccion"] or "", on_release=lambda x, it=i: self.edit_institution(it)))

    async def refresh_professionals(self, filter_text=""):
        container = self.sm.get_screen("prof_list").ids.prof_list_container
        container.clear_widgets()
        data = await self.db.get_all_professionals()
        for p in data:
            fullname = f"{p['nombre']} {p['apellido']}"
            if filter_text.lower() in fullname.lower():
                container.add_widget(TwoLineIconListItem(text=fullname, secondary_text=f"Mat: {p['matricula'] or 'N/A'}", on_release=lambda x, it=p: self.edit_professional(it)))

    async def refresh_specialties(self, filter_text=""):
        container = self.sm.get_screen("spec_list").ids.spec_list_container
        container.clear_widgets()
        data = await self.db.get_all_specialties()
        for s in data:
            if filter_text.lower() in s["nombre"].lower():
                container.add_widget(OneLineIconListItem(text=s["nombre"], on_release=lambda x, it=s: self.edit_specialty(it)))

    # --- FILTER METHODS ---
    def filter_institutions(self, t): asyncio.create_task(self.refresh_institutions(t))
    def filter_professionals(self, t): asyncio.create_task(self.refresh_professionals(t))
    def filter_specialties(self, t): asyncio.create_task(self.refresh_specialties(t))

    # --- NAVIGATION ---
    def go_back(self): self.sm.current = "dashboard"
    def go_to(self, s): self.sm.current = s

    # --- INSTITUTIONS ---
    def edit_institution(self, item=None):
        self.current_item = item
        s = self.sm.get_screen("inst_edit")
        s.ids.toolbar.title = "Editar Institución" if item else "Nueva Institución"
        s.ids.name_field.text = item["nombre"] if item else ""
        s.ids.addr_field.text = (item["direccion"] or "") if item else ""
        s.ids.phone_field.text = (item["telefono"] or "") if item else ""
        self.sm.current = "inst_edit"

    def save_institution(self): asyncio.create_task(self._save_inst_task())
    async def _save_inst_task(self):
        s = self.sm.get_screen("inst_edit")
        name, addr, phone = s.ids.name_field.text, s.ids.addr_field.text, s.ids.phone_field.text
        if not name: return
        try:
            if self.current_item: await self.db.update_institution(self.current_item["id"], name, addr, phone, None, None)
            else: await self.db.add_institution(name, addr, phone)
            await self.refresh_institutions()
            self.sm.current = "inst_list"
        except Exception as e: self.show_error(str(e))

    def confirm_delete_institution(self):
        if not self.current_item: return
        self.dialog = MDDialog(title="Eliminar?", text=f"Seguro?", buttons=[MDFlatButton(text="NO", on_release=lambda x: self.dialog.dismiss()), MDRaisedButton(text="SI", on_release=lambda x: self.delete_institution())])
        self.dialog.open()

    def delete_institution(self):
        self.dialog.dismiss()
        asyncio.create_task(self._delete_inst_task())
    async def _delete_inst_task(self):
        await self.db.delete_institution(self.current_item["id"])
        await self.refresh_institutions()
        self.sm.current = "inst_list"

    # --- PROFESSIONALS ---
    def edit_professional(self, item=None):
        self.current_item = item
        s = self.sm.get_screen("prof_edit")
        s.ids.toolbar.title = "Editar Profesional" if item else "Nuevo Profesional"
        s.ids.name_field.text = item["nombre"] if item else ""
        s.ids.last_name_field.text = item["apellido"] if item else ""
        s.ids.mat_field.text = (item["matricula"] or "") if item else ""
        s.ids.phone_field.text = (item["telefono"] or "") if item else ""
        self.sm.current = "prof_edit"

    def save_professional(self): asyncio.create_task(self._save_prof_task())
    async def _save_prof_task(self):
        s = self.sm.get_screen("prof_edit")
        name, ln, mat, ph = s.ids.name_field.text, s.ids.last_name_field.text, s.ids.mat_field.text, s.ids.phone_field.text
        if not name or not ln: return
        try:
            if self.current_item: await self.db.update_professional(self.current_item["id"], name, ln, mat, ph)
            else: await self.db.add_professional(name, ln, mat, ph)
            await self.refresh_professionals()
            self.sm.current = "prof_list"
        except Exception as e: self.show_error(str(e))

    def confirm_delete_professional(self):
        if not self.current_item: return
        self.dialog = MDDialog(title="Eliminar?", text=f"Seguro?", buttons=[MDFlatButton(text="NO", on_release=lambda x: self.dialog.dismiss()), MDRaisedButton(text="SI", on_release=lambda x: self.delete_professional())])
        self.dialog.open()

    def delete_professional(self):
        self.dialog.dismiss()
        asyncio.create_task(self._delete_prof_task())
    async def _delete_prof_task(self):
        await self.db.delete_professional(self.current_item["id"])
        await self.refresh_professionals()
        self.sm.current = "prof_list"

    # --- SPECIALTIES ---
    def edit_specialty(self, item=None):
        self.current_item = item
        s = self.sm.get_screen("spec_edit")
        s.ids.name_field.text = item["nombre"] if item else ""
        self.sm.current = "spec_edit"

    def save_specialty(self): asyncio.create_task(self._save_spec_task())
    async def _save_spec_task(self):
        name = self.sm.get_screen("spec_edit").ids.name_field.text
        if not name: return
        try:
            if self.current_item: await self.db.update_specialty(self.current_item["id"], name)
            else: await self.db.add_specialty(name)
            await self.refresh_specialties()
            self.sm.current = "spec_list"
        except Exception as e: self.show_error(str(e))

    def confirm_delete_specialty(self):
        if not self.current_item: return
        self.dialog = MDDialog(title="Eliminar?", text="Seguro?", buttons=[MDFlatButton(text="NO", on_release=lambda x: self.dialog.dismiss()), MDRaisedButton(text="SI", on_release=lambda x: self.delete_specialty())])
        self.dialog.open()

    def delete_specialty(self):
        self.dialog.dismiss()
        asyncio.create_task(self._delete_spec_task())
    async def _delete_spec_task(self):
        await self.db.delete_specialty(self.current_item["id"])
        await self.refresh_specialties()
        self.sm.current = "spec_list"

    # --- SCHEDULES ---
    def manage_schedules(self):
        if not self.current_item:
            self.show_error("Primero guarde el profesional antes de gestionar sus horarios.")
            return
        sched_screen = self.sm.get_screen("sched_edit")
        prof_name = f"{self.current_item['nombre']} {self.current_item['apellido']}"
        sched_screen.ids.toolbar.title = f"Horarios: {prof_name}"
        self.sm.current = "sched_edit"
        asyncio.create_task(self.refresh_schedules())

    async def refresh_schedules(self):
        container = self.sm.get_screen("sched_edit").ids.schedule_list_container
        container.clear_widgets()
        data = await self.db.get_schedules_by_professional(self.current_item["id"])
        day_map = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}
        for s in data:
            row = TwoLineIconListItem(text=f"{day_map.get(s['dia_num'], 'S/D')}: {s['inicio']} - {s['fin']}", secondary_text=s["inst_nombre"])
            row.add_widget(IconLeftWidget(icon="delete", on_release=lambda x, sid=s["id"]: self.delete_schedule(sid)))
            container.add_widget(row)

    def delete_schedule(self, sid): asyncio.create_task(self._del_sched_task(sid))
    async def _del_sched_task(self, sid):
        await self.db.delete_schedule(sid)
        await self.refresh_schedules()

    def open_inst_menu(self): asyncio.create_task(self._open_inst_menu_task())
    async def _open_inst_menu_task(self):
        insts = await self.db.get_all_institutions()
        items = [{"text": i["nombre"], "viewclass": "OneLineIconListItem", "on_release": lambda x=i: self.set_inst(x)} for i in insts]
        self.inst_menu = MDDropdownMenu(caller=self.sm.get_screen("sched_edit").ids.inst_field, items=items, width_mult=4)
        self.inst_menu.open()

    def set_inst(self, i):
        self.sm.get_screen("sched_edit").ids.inst_field.text = i["nombre"]
        self.selected_inst_id = i["id"]
        self.inst_menu.dismiss()

    def open_day_menu(self):
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        items = [{"text": d, "viewclass": "OneLineIconListItem", "on_release": lambda x=d, n=i+1: self.set_day(x, n)} for i, d in enumerate(days)]
        self.day_menu = MDDropdownMenu(caller=self.sm.get_screen("sched_edit").ids.day_field, items=items, width_mult=4)
        self.day_menu.open()

    def set_day(self, d, n):
        self.sm.get_screen("sched_edit").ids.day_field.text = d
        self.selected_day_num = n
        self.day_menu.dismiss()

    def add_schedule_item(self): asyncio.create_task(self._add_sched_task())
    async def _add_sched_task(self):
        s = self.sm.get_screen("sched_edit")
        if not self.selected_inst_id or not self.selected_day_num: return
        try:
            await self.db.add_schedule(self.current_item["id"], self.selected_inst_id, self.selected_day_num, s.ids.start_field.text, s.ids.end_field.text)
            await self.refresh_schedules()
        except Exception as e: self.show_error(str(e))

    # --- COMMON ---
    def show_error(self, t): MDDialog(title="Error", text=t, buttons=[MDFlatButton(text="OK", on_release=lambda x: x.parent.parent.parent.parent.dismiss())]).open()

    def show_report_menu(self):
        if not REPORTLAB_AVAILABLE:
            self.show_error("Instale reportlab: pip install reportlab")
            return
        self.report_dialog = MDDialog(
            title="Generar Reporte",
            text="Elija el reporte a generar:",
            buttons=[
                MDFlatButton(text="PROFESIONALES", on_release=lambda x: self._run_report("prof")),
                MDFlatButton(text="HORARIOS", on_release=lambda x: self._run_report("sched")),
                MDFlatButton(text="INSTITUCIONES", on_release=lambda x: self._run_report("inst")),
            ]
        )
        self.report_dialog.open()

    def _run_report(self, tipo):
        self.report_dialog.dismiss()
        asyncio.create_task(self._gen_report(tipo))

    async def _gen_report(self, tipo):
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as cv
        from datetime import datetime
        day_map = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}
        width, height = letter
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        try:
            if tipo == "prof":
                filename = "reporte_profesionales.pdf"
                c = cv.Canvas(filename, pagesize=letter)
                c.setFont("Helvetica-Bold", 18)
                c.drawString(50, height - 50, "Listado de Profesionales")
                c.setFont("Helvetica", 9)
                c.drawString(50, height - 65, f"Generado: {now}")
                c.line(50, height - 70, width - 50, height - 70)
                y = height - 90
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "Apellido y Nombre")
                c.drawString(300, y, "Matrícula")
                c.drawString(430, y, "Teléfono")
                y -= 5
                c.line(50, y, width - 50, y)
                y -= 15
                c.setFont("Helvetica", 10)
                for p in await self.db.get_all_professionals():
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    c.drawString(50, y, f"{p['apellido']}, {p['nombre']}")
                    c.drawString(300, y, p['matricula'] or 'S/D')
                    c.drawString(430, y, p['telefono'] or 'S/D')
                    y -= 15
                c.save()

            elif tipo == "sched":
                filename = "reporte_horarios.pdf"
                c = cv.Canvas(filename, pagesize=letter)
                c.setFont("Helvetica-Bold", 18)
                c.drawString(50, height - 50, "Horarios de Profesionales")
                c.setFont("Helvetica", 9)
                c.drawString(50, height - 65, f"Generado: {now}")
                c.line(50, height - 70, width - 50, height - 70)
                y = height - 90
                profs = await self.db.get_all_professionals()
                for p in profs:
                    if y < 100:
                        c.showPage()
                        y = height - 50
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, y, f"{p['apellido']}, {p['nombre']}")
                    y -= 18
                    scheds = await self.db.get_schedules_by_professional(p['id'])
                    if scheds:
                        c.setFont("Helvetica", 10)
                        for s in scheds:
                            if y < 50:
                                c.showPage()
                                y = height - 50
                            dia = day_map.get(s['dia_num'], 'S/D')
                            c.drawString(70, y, f"{dia}: {s['inicio']} - {s['fin']}  ({s['inst_nombre']})")
                            y -= 14
                    else:
                        c.setFont("Helvetica-Oblique", 9)
                        c.drawString(70, y, "Sin horarios asignados")
                        y -= 14
                    y -= 8
                c.save()

            elif tipo == "inst":
                filename = "reporte_instituciones.pdf"
                c = cv.Canvas(filename, pagesize=letter)
                c.setFont("Helvetica-Bold", 18)
                c.drawString(50, height - 50, "Listado de Instituciones")
                c.setFont("Helvetica", 9)
                c.drawString(50, height - 65, f"Generado: {now}")
                c.line(50, height - 70, width - 50, height - 70)
                y = height - 90
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "Institución")
                c.drawString(280, y, "Dirección")
                c.drawString(470, y, "Teléfono")
                y -= 5
                c.line(50, y, width - 50, y)
                y -= 15
                c.setFont("Helvetica", 10)
                for i in await self.db.get_all_institutions():
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    c.drawString(50, y, i['nombre'][:30])
                    c.drawString(280, y, (i['direccion'] or 'S/D')[:25])
                    c.drawString(470, y, i['telefono'] or 'S/D')
                    y -= 15
                c.save()

            MDDialog(title="Reporte generado", text=f"Archivo: {filename}").open()
        except Exception as e:
            self.show_error(str(e))

if __name__ == "__main__": asyncio.run(AdminManagerApp().async_run(async_lib="asyncio"))
