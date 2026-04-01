from kivy.app import App
from kivy.lang import Builder
import sqlite3
from datetime import datetime, timedelta

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: 10
    spacing: 10
    canvas.before:
        Color:
            rgba: 0.1, 0.15, 0.25, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Image:
        source: "logo.png"
        size_hint_y: None
        height: 120

    Label:
        text: "Pilot Logbook"
        font_size: 24
        bold: True
        color: 1,1,1,1
        size_hint_y: None
        height: 40

    BoxLayout:
        orientation: 'vertical'
        spacing: 8
        padding: 10
        size_hint_y: None
        height: 270
        canvas.before:
            Color:
                rgba: 0.2, 0.3, 0.5, 0.9
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10]

        TextInput:
            id: tanggal
            hint_text: "Tanggal (YYYY-MM-DD)"
            multiline: False

        TextInput:
            id: flight
            hint_text: "Flight Number"
            multiline: False

        TextInput:
            id: route
            hint_text: "Route (CGK-DPS)"
            multiline: False

        BoxLayout:
            spacing: 5

            TextInput:
                id: depart
                hint_text: "Depart (HH:MM)"
                multiline: False

            TextInput:
                id: arrive
                hint_text: "Arrive (HH:MM)"
                multiline: False

    BoxLayout:
        size_hint_y: None
        height: 50
        spacing: 5

        Button:
            text: "Save"
            background_color: 0.2, 0.6, 0.9, 1
            on_press: app.simpan_data()

        Button:
            text: "Logbook"
            background_color: 0.3, 0.7, 0.4, 1
            on_press: app.tampilkan_data()

        Button:
            text: "Total"
            background_color: 0.8, 0.5, 0.2, 1
            on_press: app.total_jam()

        Button:
            text: "PDF"
            background_color: 0.7, 0.2, 0.3, 1
            on_press: app.export_pdf()

    ScrollView:
        canvas.before:
            Color:
                rgba: 1,1,1,1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10]

        Label:
            id: output
            text: ""
            color: 0,0,0,1
            size_hint_y: None
            text_size: self.width, None
            height: self.texture_size[1]

    Label:
        text: "Developed by Irvan Rahadiyan - 2026"
        font_size: 22
        color: 1,1,1,0.7
        size_hint_y: None
        height: 30
'''

class PilotApp(App):

    def build(self):
        self.conn = sqlite3.connect("logbook.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            flight TEXT,
            route TEXT,
            duration INTEGER
        )
        ''')

        return Builder.load_string(KV)

    def hitung_durasi(self, depart, arrive):
        fmt = "%H:%M"
        d1 = datetime.strptime(depart, fmt)
        d2 = datetime.strptime(arrive, fmt)

        if d2 < d1:
            d2 += timedelta(days=1)

        durasi = d2 - d1
        return int(durasi.total_seconds() // 60)

    def format_jam(self, menit):
        jam = menit // 60
        sisa = menit % 60
        return f"{jam} jam {sisa} menit"

    def simpan_data(self):
        try:
            tanggal = self.root.ids.tanggal.text.strip()
            flight = self.root.ids.flight.text.strip()
            route = self.root.ids.route.text.strip()
            depart = self.root.ids.depart.text.strip()
            arrive = self.root.ids.arrive.text.strip()

            if not all([tanggal, flight, route, depart, arrive]):
                self.root.ids.output.text = "Semua field harus diisi"
                return

            durasi = self.hitung_durasi(depart, arrive)

            self.cursor.execute(
                "INSERT INTO flights (tanggal, flight, route, duration) VALUES (?, ?, ?, ?)",
                (tanggal, flight, route, durasi)
            )
            self.conn.commit()

            self.root.ids.output.text = f"Data tersimpan. Durasi: {self.format_jam(durasi)}"

            self.root.ids.tanggal.text = ""
            self.root.ids.flight.text = ""
            self.root.ids.route.text = ""
            self.root.ids.depart.text = ""
            self.root.ids.arrive.text = ""

        except:
            self.root.ids.output.text = "Format jam harus HH:MM"

    def tampilkan_data(self):
        self.cursor.execute("""
            SELECT tanggal, flight, route, duration 
            FROM flights 
            ORDER BY tanggal DESC
        """)
        data = self.cursor.fetchall()

        if not data:
            self.root.ids.output.text = "Belum ada data"
            return

        hasil = ""
        for d in data:
            hasil += (
                f"Tanggal : {d[0]}\\n"
                f"Flight  : {d[1]}\\n"
                f"Route   : {d[2]}\\n"
                f"Durasi  : {self.format_jam(d[3])}\\n"
                f"------------------------\\n"
            )

        self.root.ids.output.text = hasil

    def total_jam(self):
        self.cursor.execute("SELECT SUM(duration) FROM flights")
        total = self.cursor.fetchone()[0]

        if total:
            self.root.ids.output.text = f"Total jam terbang: {self.format_jam(total)}"
        else:
            self.root.ids.output.text = "Belum ada data"

    def export_pdf(self):
        try:
            self.cursor.execute("""
                SELECT tanggal, flight, route, duration 
                FROM flights 
                ORDER BY tanggal DESC
            """)
            data = self.cursor.fetchall()

            if not data:
                self.root.ids.output.text = "Tidak ada data untuk export"
                return

            file_path = "/storage/emulated/0/Documents/pilot_logbook.pdf"

            doc = SimpleDocTemplate(file_path)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("Pilot Logbook", styles['Title']))
            elements.append(Spacer(1, 12))

            for d in data:
                text = (
                    f"Tanggal: {d[0]}<br/>"
                    f"Flight: {d[1]}<br/>"
                    f"Route: {d[2]}<br/>"
                    f"Durasi: {self.format_jam(d[3])}<br/>"
                    f"-------------------------"
                )
                elements.append(Paragraph(text, styles['Normal']))
                elements.append(Spacer(1, 10))

            doc.build(elements)

            self.root.ids.output.text = "PDF has been saved in Documents"

        except Exception as e:
            self.root.ids.output.text = f"Error: {str(e)}"


PilotApp().run()