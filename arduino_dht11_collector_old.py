#!/usr/bin/env python3
"""
Application temps réel pour Arduino + DHT11
- Connexion auto au port série
- Pas de bouton Start: la collecte démarre immédiatement
- Graphique temps réel de température et humidité
- Interface Tkinter + Matplotlib
"""

import serial
import serial.tools.list_ports
import time
from datetime import datetime
import statistics

import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates


class DHT11RealtimeApp:
    def __init__(self):
        self.data = []  # liste de dicts {timestamp, temperature, humidite}
        self.serial_port = None
        self.is_collecting = False

        # Création de l'interface
        self.root = tk.Tk()
        self.root.title("Station DHT11 - Temps réel")
        self.root.geometry("1100x750")

        self.build_ui()

        # Connexion automatique au port série au démarrage
        self.root.after(500, self.auto_connect_and_start)

    # ================== UI ==================
    def build_ui(self):
        # Frame info haut
        info_frame = ttk.Frame(self.root, padding=10)
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text="Port série:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(info_frame, textvariable=self.port_var, width=25)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(info_frame, text="Rafraîchir ports", command=self.refresh_ports).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(info_frame, text="Température:", font=("Arial", 14, "bold")).grid(row=1, column=0, padx=10, pady=5)
        self.temp_label = ttk.Label(info_frame, text="-- °C", font=("Arial", 20, "bold"), foreground="blue")
        self.temp_label.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(info_frame, text="Humidité:", font=("Arial", 14, "bold")).grid(row=1, column=2, padx=10, pady=5)
        self.hum_label = ttk.Label(info_frame, text="-- %", font=("Arial", 20, "bold"), foreground="green")
        self.hum_label.grid(row=1, column=3, padx=10, pady=5)

        ttk.Label(info_frame, text="Mesures:", font=("Arial", 14, "bold")).grid(row=1, column=4, padx=10, pady=5)
        self.count_label = ttk.Label(info_frame, text="0", font=("Arial", 20, "bold"))
        self.count_label.grid(row=1, column=5, padx=10, pady=5)

        # Stats rapides
        stats_frame = ttk.Frame(self.root, padding=10)
        stats_frame.pack(fill=tk.X)

        ttk.Label(stats_frame, text="Temp moy:").grid(row=0, column=0, padx=5)
        self.temp_avg_label = ttk.Label(stats_frame, text="-- °C")
        self.temp_avg_label.grid(row=0, column=1, padx=5)

        ttk.Label(stats_frame, text="Temp min:").grid(row=0, column=2, padx=5)
        self.temp_min_label = ttk.Label(stats_frame, text="-- °C")
        self.temp_min_label.grid(row=0, column=3, padx=5)

        ttk.Label(stats_frame, text="Temp max:").grid(row=0, column=4, padx=5)
        self.temp_max_label = ttk.Label(stats_frame, text="-- °C")
        self.temp_max_label.grid(row=0, column=5, padx=5)

        ttk.Label(stats_frame, text="Hum moy:").grid(row=0, column=6, padx=5)
        self.hum_avg_label = ttk.Label(stats_frame, text="-- %")
        self.hum_avg_label.grid(row=0, column=7, padx=5)

        # Graphique temps réel
        graph_frame = ttk.LabelFrame(self.root, text="Graphique temps réel", padding=10)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fig = Figure(figsize=(10, 5), dpi=100)
        self.ax_temp = self.fig.add_subplot(2, 1, 1)
        self.ax_hum = self.fig.add_subplot(2, 1, 2, sharex=self.ax_temp)

        self.ax_temp.set_ylabel("Température (°C)")
        self.ax_temp.set_title("Évolution de la température")
        self.ax_temp.grid(True, alpha=0.3)

        self.ax_hum.set_ylabel("Humidité (%)")
        self.ax_hum.set_xlabel("Temps")
        self.ax_hum.set_title("Évolution de l'humidité")
        self.ax_hum.grid(True, alpha=0.3)

        self.temp_line, = self.ax_temp.plot([], [], "r-", label="Température")
        self.hum_line, = self.ax_hum.plot([], [], "b-", label="Humidité")

        self.ax_temp.legend(loc="upper left")
        self.ax_hum.legend(loc="upper left")

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()

        # Logs
        log_frame = ttk.LabelFrame(self.root, text="Logs série", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.refresh_ports()

    # ================== PORT SÉRIE & LOG ==================
    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        names = [p.device for p in ports]
        self.port_combo["values"] = names
        if names:
            self.port_combo.current(0)
        self.log("Ports détectés: " + (", ".join(names) if names else "aucun"))

    def auto_connect_and_start(self):
        """Essaie de se connecter au premier port dispo et démarre la collecte automatiquement."""
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.log("Aucun port série détecté. Brancher l'Arduino et cliquer sur 'Rafraîchir'.")
            return

        port_name = ports[0].device
        self.port_var.set(port_name)
        self.log(f"Connexion automatique au port {port_name}...")

        try:
            self.serial_port = serial.Serial(port_name, 9600, timeout=2)
            time.sleep(2)  # laisse le temps à l'Arduino de reboot
            self.is_collecting = True
            self.port_combo.config(state=tk.DISABLED)
            self.log("Connexion réussie, démarrage de la lecture série...")

            # thread de collecte
            import threading
            t = threading.Thread(target=self.collect_loop, daemon=True)
            t.start()

            # démarrage de l'update graphique périodique
            self.root.after(500, self.update_plot)
        except serial.SerialException as e:
            self.log(f"Erreur série: {e}")
            messagebox.showerror("Erreur série", str(e))

    # ================== COLLECTE ==================
    def collect_loop(self):
        while self.is_collecting and self.serial_port:
            try:
                line_bytes = self.serial_port.readline()
                if not line_bytes:
                    continue

                # décodage robuste: ignorer les erreurs UTF-8
                line = line_bytes.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                # log brut
                self.root.after(0, lambda l=line: self.log(l))

                # parse seulement les lignes "DATA:temp,hum"
                if line.startswith("DATA:"):
                    payload = line[5:].strip()
                    if "," in payload:
                        temp_str, hum_str = payload.split(",", 1)
                        try:
                            temp = float(temp_str)
                            hum = float(hum_str)
                            ts = datetime.now()
                            self.data.append({"timestamp": ts, "temperature": temp, "humidite": hum})
                            self.root.after(0, lambda t=temp, h=hum: self.update_labels(t, h))
                        except ValueError:
                            # ignore les lignes mal formatées
                            pass
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Erreur lecture série: {e}"))
                time.sleep(0.5)

    # ================== MISE À JOUR UI & GRAPHIQUE ==================
    def update_labels(self, temp, hum):
        self.temp_label.config(text=f"{temp:.1f} °C")
        self.hum_label.config(text=f"{hum:.1f} %")
        self.count_label.config(text=str(len(self.data)))

        if self.data:
            temps = [d["temperature"] for d in self.data]
            hums = [d["humidite"] for d in self.data]
            self.temp_avg_label.config(text=f"{statistics.mean(temps):.1f} °C")
            self.temp_min_label.config(text=f"{min(temps):.1f} °C")
            self.temp_max_label.config(text=f"{max(temps):.1f} °C")
            self.hum_avg_label.config(text=f"{statistics.mean(hums):.1f} %")

    def update_plot(self):
        if self.data:
            ts = [d["timestamp"] for d in self.data]
            temps = [d["temperature"] for d in self.data]
            hums = [d["humidite"] for d in self.data]

            self.temp_line.set_data(ts, temps)
            self.hum_line.set_data(ts, hums)

            # limites
            self.ax_temp.relim()
            self.ax_temp.autoscale_view()
            self.ax_hum.relim()
            self.ax_hum.autoscale_view()

            # format de temps sur l'axe X
            self.ax_temp.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            self.fig.autofmt_xdate()

            self.canvas.draw()

        # re-programmer l'update toutes les 500 ms
        self.root.after(500, self.update_plot)

    # ================== MAIN ==================
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = DHT11RealtimeApp()
    app.run()
