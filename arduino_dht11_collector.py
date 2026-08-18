#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Station météo DHT11 : affichage série, statistiques, records et graphique en direct."""

import csv
import math
import statistics
import threading
import time
from datetime import datetime
from pathlib import Path

import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.legend import Legend

try:
    import winsound
except ImportError:
    winsound = None


class WeatherStation:
    BAUDRATE = 9600
    MAX_POINTS = 500
    UPDATE_MS = 500
    EPSILON = 0.0001

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Station météo DHT11")
        self.root.geometry("1250x850")
        self.root.minsize(950, 650)

        self.serial_port = None
        self.running = False
        self.data = []
        self.sound_enabled = True
        self.markers_visible = True
        self.legend_visible = False
        self.legend_left = None
        self.legend_right = None
        self.last_sound_time = 0.0
        self.csv_path = Path(__file__).with_name("mesures_dht11.csv")

        self.configure_style()
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(500, self.auto_connect)

    def configure_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#17324D")
        style.configure("Value.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Card.TLabelframe", padding=12)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 10), foreground="#536273")

    def build_ui(self):
        header = ttk.Frame(self.root, padding=(18, 14, 18, 4))
        header.pack(fill=tk.X)
        ttk.Label(header, text="Station météo DHT11", style="Title.TLabel").pack(side=tk.LEFT)
        self.status_label = ttk.Label(header, text="Initialisation...", style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT, pady=8)

        connection = ttk.Frame(self.root, padding=(18, 4, 18, 4))
        connection.pack(fill=tk.X)
        ttk.Label(connection, text="Port série :").pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(connection, textvariable=self.port_var, width=18, state="readonly")
        self.port_combo.pack(side=tk.LEFT, padx=8)
        ttk.Button(connection, text="Rafraîchir", command=self.refresh_ports).pack(side=tk.LEFT)

        self.legend_button = ttk.Button(connection, text="Afficher légende", command=self.toggle_legend)
        self.legend_button.pack(side=tk.RIGHT)
        self.markers_button = ttk.Button(connection, text="Masquer points records", command=self.toggle_markers)
        self.markers_button.pack(side=tk.RIGHT, padx=(8, 0))
        self.sound_button = ttk.Button(connection, text="🔊 Bruitage : activé", command=self.toggle_sound)
        self.sound_button.pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(connection, text="Exporter CSV", command=self.export_csv).pack(side=tk.RIGHT, padx=(0, 8))

        cards = ttk.Frame(self.root, padding=(18, 8, 18, 8))
        cards.pack(fill=tk.X)
        self.temp_label = self.create_card(cards, "TEMPÉRATURE", "-- °C", "#D94841", 0)
        self.hum_label = self.create_card(cards, "HUMIDITÉ", "-- %", "#2878B5", 1)
        self.avg_label = self.create_card(cards, "MOYENNE TEMP.", "-- °C", "#7656A6", 2)
        self.count_label = self.create_card(cards, "MESURES", "0", "#3B8068", 3)
        for i in range(4):
            cards.columnconfigure(i, weight=1)

        stats = ttk.Frame(self.root, padding=(18, 0, 18, 8))
        stats.pack(fill=tk.X)
        self.temp_min_label = self.create_stat(stats, "Min température", 0)
        self.temp_max_label = self.create_stat(stats, "Max température", 1)
        self.hum_avg_label = self.create_stat(stats, "Moyenne humidité", 2)
        self.record_label = self.create_stat(stats, "Dernier événement", 3)
        for i in range(4):
            stats.columnconfigure(i, weight=1)

        graph_frame = ttk.LabelFrame(self.root, text="Évolution en direct", style="Card.TLabelframe", padding=8)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 8))

        self.figure = Figure(figsize=(11, 5.5), dpi=100, facecolor="#F8FAFC")
        self.ax_temp = self.figure.add_subplot(2, 1, 1)
        self.ax_hum = self.figure.add_subplot(2, 1, 2, sharex=self.ax_temp)
        self.figure.subplots_adjust(left=0.08, right=0.98, top=0.93, bottom=0.12, hspace=0.45)

        self.temp_line, = self.ax_temp.plot([], [], color="#D94841", linewidth=2.4, marker="o", markersize=3)
        self.avg_line, = self.ax_temp.plot([], [], color="#7656A6", linewidth=2, linestyle="--")
        self.max_point = self.ax_temp.scatter([], [], s=55, marker="o", color="#E31B23", edgecolors="#7A1014", linewidths=0.7, zorder=5)
        self.min_point = self.ax_temp.scatter([], [], s=55, marker="o", color="#1A73E8", edgecolors="#0B3D91", linewidths=0.7, zorder=5)
        self.old_max_points = self.ax_temp.scatter([], [], s=28, marker="o", color="#F5AAAA", edgecolors="none", alpha=0.95, zorder=4)
        self.old_min_points = self.ax_temp.scatter([], [], s=28, marker="o", color="#A8C8F4", edgecolors="none", alpha=0.95, zorder=4)
        self.hum_line, = self.ax_hum.plot([], [], color="#2878B5", linewidth=2.4, marker="o", markersize=3, label="Humidité")

        self.ax_temp.set_ylabel("Température (°C)")
        self.ax_temp.set_title("Température, moyenne et records", loc="left", fontweight="bold")
        self.ax_hum.set_ylabel("Humidité (%)")
        self.ax_hum.set_xlabel("Heure")
        self.ax_hum.set_title("Humidité", loc="left", fontweight="bold")
        for ax in (self.ax_temp, self.ax_hum):
            ax.set_facecolor("#FFFFFF")
            ax.grid(True, alpha=0.22)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
        self.ax_hum.legend(loc="upper left", frameon=False)
        self.ax_hum.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(self.root, text="Journal série", style="Card.TLabelframe", padding=6)
        log_frame.pack(fill=tk.X, padx=18, pady=(0, 12))
        self.log_text = tk.Text(log_frame, height=5, font=("Consolas", 9), bg="#17212B", fg="#E8F1F8", insertbackground="white", relief="flat")
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.refresh_ports()

    def create_card(self, parent, title, initial, color, column):
        frame = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe")
        frame.grid(row=0, column=column, sticky="nsew", padx=5)
        label = ttk.Label(frame, text=initial, style="Value.TLabel", foreground=color, anchor="center")
        label.pack(fill=tk.X, pady=4)
        return label

    def create_stat(self, parent, title, column):
        frame = ttk.Frame(parent, padding=8)
        frame.grid(row=0, column=column, sticky="ew", padx=5)
        ttk.Label(frame, text=title, foreground="#536273").pack()
        label = ttk.Label(frame, text="--", font=("Segoe UI", 11, "bold"), foreground="#17324D")
        label.pack()
        return label

    def log(self, text):
        if self.log_text.winfo_exists():
            stamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{stamp}] {text}\n")
            self.log_text.see(tk.END)

    def set_status(self, text, color="#536273"):
        self.status_label.configure(text=text, foreground=color)

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        state = "activé" if self.sound_enabled else "désactivé"
        icon = "🔊" if self.sound_enabled else "🔇"
        self.sound_button.configure(text=f"{icon} Bruitage : {state}")
        self.log(f"Bruitage {state}.")

    def toggle_markers(self):
        self.markers_visible = not self.markers_visible
        for points in (self.max_point, self.min_point, self.old_max_points, self.old_min_points):
            points.set_visible(self.markers_visible)
        self.markers_button.configure(text="Masquer points records" if self.markers_visible else "Afficher points records")
        self.canvas.draw_idle()

    def remove_temp_legends(self):
        # La première légende est dans ax_temp.artists, la deuxième est ax_temp.legend_.
        # Les deux sont retirées explicitement afin qu'aucun doublon ne reste affiché.
        for legend in (self.legend_left, self.legend_right):
            if legend is not None:
                try:
                    legend.remove()
                except (ValueError, AttributeError):
                    pass
        self.legend_left = None
        self.legend_right = None

        for artist in list(self.ax_temp.artists):
            if isinstance(artist, Legend):
                artist.remove()
        if self.ax_temp.get_legend() is not None:
            self.ax_temp.get_legend().remove()

    def toggle_legend(self):
        self.legend_visible = not self.legend_visible
        self.remove_temp_legends()

        if self.legend_visible:
            # Deux légendes séparées : ordre exact demandé, sans réorganisation automatique de Matplotlib.
            # Colonne gauche : Température / Records Min / Ancien Min
            self.legend_left = self.ax_temp.legend(
                handles=[self.temp_line, self.min_point, self.old_min_points],
                labels=["Température", "Records Min", "Ancien Min"],
                loc="upper left",
                bbox_to_anchor=(0.00, 1.02),
                frameon=False,
                handlelength=2.0,
                handletextpad=0.6,
                borderaxespad=0,
                labelspacing=0.55,
                fontsize=8,
            )
            self.ax_temp.add_artist(self.legend_left)

            # Colonne droite : Moyenne / Records Max / Ancien Max
            self.legend_right = self.ax_temp.legend(
                handles=[self.avg_line, self.max_point, self.old_max_points],
                labels=["Moyenne", "Records Max", "Ancien Max"],
                loc="upper left",
                bbox_to_anchor=(0.42, 1.02),
                frameon=False,
                handlelength=2.0,
                handletextpad=0.6,
                borderaxespad=0,
                labelspacing=0.55,
                fontsize=8,
            )
            self.legend_button.configure(text="Masquer légende")
        else:
            self.legend_button.configure(text="Afficher légende")

        self.canvas.draw_idle()

    def refresh_ports(self):
        ports = list(serial.tools.list_ports.comports())
        names = [port.device for port in ports]
        self.port_combo["values"] = names
        if names and self.port_var.get() not in names:
            self.port_var.set(names[0])
        self.log("Ports détectés : " + (", ".join(names) if names else "aucun"))

    def auto_connect(self):
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            self.set_status("Arduino non détecté", "#B54747")
            self.log("Branche l'Arduino puis clique sur Rafraîchir.")
            return
        self.port_var.set(ports[0].device)
        try:
            self.serial_port = serial.Serial(self.port_var.get(), self.BAUDRATE, timeout=1)
            time.sleep(2)
            self.serial_port.reset_input_buffer()
            self.running = True
            self.port_combo.configure(state="disabled")
            self.set_status(f"Connecté à {self.port_var.get()}", "#2F855A")
            self.log("Connexion réussie : collecte automatique démarrée.")
            threading.Thread(target=self.read_serial, daemon=True).start()
            self.root.after(self.UPDATE_MS, self.update_graph)
        except serial.SerialException as exc:
            self.set_status("Erreur de connexion", "#B54747")
            self.log(f"Impossible d'ouvrir le port : {exc}")

    def read_serial(self):
        while self.running and self.serial_port:
            try:
                raw = self.serial_port.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    self.root.after(0, self.log, line)
                if not line.startswith("DATA:"):
                    continue
                parts = line[5:].split(",", 1)
                if len(parts) != 2:
                    continue
                temp = float(parts[0].strip())
                hum = float(parts[1].strip())
                if math.isfinite(temp) and math.isfinite(hum):
                    self.root.after(0, self.add_measurement, temp, hum)
            except (ValueError, serial.SerialException) as exc:
                self.root.after(0, self.log, f"Lecture série : {exc}")
                time.sleep(0.5)

    def add_measurement(self, temp, hum):
        now = datetime.now()
        previous_max = max((item["temperature"] for item in self.data), default=None)
        previous_min = min((item["temperature"] for item in self.data), default=None)

        if previous_max is None:
            event = "initial"
        elif temp > previous_max + self.EPSILON:
            event = "new_max"
        elif temp < previous_min - self.EPSILON:
            event = "new_min"
        elif math.isclose(temp, previous_max, abs_tol=self.EPSILON):
            event = "equal_max"
        elif math.isclose(temp, previous_min, abs_tol=self.EPSILON):
            event = "equal_min"
        else:
            event = None

        self.data.append({"timestamp": now, "temperature": temp, "humidite": hum, "event": event})
        self.data = self.data[-self.MAX_POINTS:]
        temps = [item["temperature"] for item in self.data]
        hums = [item["humidite"] for item in self.data]

        self.temp_label.configure(text=f"{temp:.1f} °C")
        self.hum_label.configure(text=f"{hum:.1f} %")
        self.avg_label.configure(text=f"{statistics.fmean(temps):.1f} °C")
        self.count_label.configure(text=str(len(self.data)))
        self.temp_min_label.configure(text=f"{min(temps):.1f} °C")
        self.temp_max_label.configure(text=f"{max(temps):.1f} °C")
        self.hum_avg_label.configure(text=f"{statistics.fmean(hums):.1f} %")

        messages = {
            "new_max": (f"Nouveau maximum : {temp:.1f} °C", "max"),
            "new_min": (f"Nouveau minimum : {temp:.1f} °C", "min"),
            "equal_max": (f"Maximum égalé : {temp:.1f} °C", None),
            "equal_min": (f"Minimum égalé : {temp:.1f} °C", None),
        }
        if event in messages:
            text, sound = messages[event]
            self.record_label.configure(text=text)
            self.log(text)
            if sound:
                self.play_sound(sound)

    def play_sound(self, kind):
        if not self.sound_enabled or winsound is None:
            return
        now = time.monotonic()
        if now - self.last_sound_time < 0.8:
            return
        self.last_sound_time = now
        if kind == "max":
            winsound.Beep(1100, 180)
        elif kind == "min":
            winsound.Beep(500, 280)

    @staticmethod
    def empty_offsets():
        return [[float("nan"), float("nan")]]

    @staticmethod
    def point_offsets(points):
        return [[mdates.date2num(timestamp), value] for timestamp, value in points]

    def set_scatter_points(self, collection, points):
        collection.set_offsets(self.point_offsets(points) if points else self.empty_offsets())

    def update_graph(self):
        if self.data:
            timestamps = [item["timestamp"] for item in self.data]
            temps = [item["temperature"] for item in self.data]
            hums = [item["humidite"] for item in self.data]
            averages = [statistics.fmean(temps[:index + 1]) for index in range(len(temps))]

            max_events = [(item["timestamp"], item["temperature"]) for item in self.data if item["event"] in ("new_max", "equal_max")]
            min_events = [(item["timestamp"], item["temperature"]) for item in self.data if item["event"] in ("new_min", "equal_min")]

            self.temp_line.set_data(timestamps, temps)
            self.avg_line.set_data(timestamps, averages)
            self.hum_line.set_data(timestamps, hums)
            self.set_scatter_points(self.max_point, max_events[-1:])
            self.set_scatter_points(self.min_point, min_events[-1:])
            self.set_scatter_points(self.old_max_points, max_events[:-1])
            self.set_scatter_points(self.old_min_points, min_events[:-1])

            self.ax_temp.relim()
            self.ax_temp.autoscale_view()
            self.ax_hum.relim()
            self.ax_hum.autoscale_view()
            self.canvas.draw_idle()

        if self.root.winfo_exists():
            self.root.after(self.UPDATE_MS, self.update_graph)

    def export_csv(self):
        if not self.data:
            messagebox.showinfo("Export CSV", "Aucune mesure à exporter.")
            return
        with self.csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(["Date", "Heure", "Temperature_C", "Humidite_pourcent", "Moyenne_temperature_C", "Evenement"])
            temps = []
            for item in self.data:
                temps.append(item["temperature"])
                writer.writerow([
                    item["timestamp"].strftime("%Y-%m-%d"),
                    item["timestamp"].strftime("%H:%M:%S"),
                    f"{item['temperature']:.2f}",
                    f"{item['humidite']:.2f}",
                    f"{statistics.fmean(temps):.2f}",
                    item["event"] or "",
                ])
        self.log(f"CSV exporté : {self.csv_path.name}")
        messagebox.showinfo("Export CSV", f"Export terminé :\n{self.csv_path}")

    def close(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    WeatherStation().run()
