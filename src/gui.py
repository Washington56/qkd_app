# src/gui.py
import tkinter as tk
from tkinter import ttk, filedialog, Menu, messagebox
import matplotlib.pyplot as plt
from matplotlib.widgets import RangeSlider
import pandas as pd
import logging

from calculations import (
    get_alpha, get_protocol_factor,
    calc_loss_curve, calc_qkd_speed_curve, calc_qkd_rate
)

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='app.log', filemode='a')
logger = logging.getLogger(__name__)

class QuantumKeyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Система квантового распределения ключей")
        self.geometry("800x600")

        # Переменные интерфейса
        self.protocol_var = tk.StringVar(value="BB84")
        self.initial_speed_var = tk.StringVar(value="1.0")
        self.result_text = tk.StringVar()
        self.distance_entries = []
        self.method_vars = []
        self.wavelength_vars = []
        self.frames = []

        self._build_ui()
        self._create_menu()
        self.add_section()

    def _build_ui(self):
        style = ttk.Style()
        style.configure("TButton", padding=6, font=('Arial', 10))
        style.configure("TLabel", font=('Arial', 10))
        style.configure("TCombobox", padding=4)

        # Протокол и скорость
        ttk.Label(self, text="Выберите протокол:").pack(pady=5)
        ttk.Combobox(self, textvariable=self.protocol_var,
                     values=["BB84", "B92"]).pack()

        ttk.Label(self, text="Введите начальную скорость (Мбит/с):").pack(pady=5)
        ttk.Entry(self, textvariable=self.initial_speed_var).pack()

        # Панель управления
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Добавить участок", command=self.add_section).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="График потерь", command=self.plot_losses).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="График скорости", command=self.plot_speed).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Рассчитать скорость КРК", command=self.calc_rates).pack(side=tk.LEFT, padx=5)

        # Область результатов
        ttk.Label(self, textvariable=self.result_text, justify=tk.LEFT).pack(fill='x', padx=10, pady=10)

    def _create_menu(self):
        menubar = Menu(self)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт графика в PDF", command=self._export_plot_pdf)
        file_menu.add_command(label="Экспорт отчёта в CSV", command=self._export_report_csv)
        menubar.add_cascade(label="Файл", menu=file_menu)
        self.config(menu=menubar)

    def _export_plot_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF files", "*.pdf")])
        if path:
            plt.gcf().savefig(path, format='pdf')
            messagebox.showinfo("Экспорт", f"График сохранён в {path}")

    def _export_report_csv(self):
        txt = self.result_text.get()
        rows = []
        for line in txt.splitlines():
            parts = [p.strip() for p in line.split('→')]
            if len(parts) == 2:
                meta, val = parts
                method, wavelength, L = meta.split(', ')
                rows.append({
                    'Метод': method,
                    'Длина волны': wavelength,
                    'L (км)': float(L.split()[0]),
                    'Скорость': val
                })
        df = pd.DataFrame(rows)
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")])
        if path:
            df.to_csv(path, index=False, encoding='utf-8-sig')
            messagebox.showinfo("Экспорт", f"Отчёт сохранён в {path}")

    def add_section(self):
        frame = ttk.Frame(self, padding=5)
        frame.pack(fill='x', pady=3)
        ttk.Label(frame, text="Длина участка (км):").pack(side=tk.LEFT, padx=2)
        entry = ttk.Entry(frame, width=10)
        entry.pack(side=tk.LEFT, padx=2)
        self.distance_entries.append(entry)

        ttk.Label(frame, text="Метод:").pack(side=tk.LEFT, padx=2)
        method_var = tk.StringVar(value='ВОЛС')
        ttk.Combobox(frame, textvariable=method_var,
                     values=['ВОЛС', 'АОЛС'], width=10).pack(side=tk.LEFT, padx=2)
        self.method_vars.append(method_var)

        ttk.Label(frame, text="Длина волны:").pack(side=tk.LEFT, padx=2)
        wavelength_var = tk.StringVar(value='1550 нм')
        ttk.Combobox(frame, textvariable=wavelength_var,
                     values=['1550 нм', '1310 нм', '850 нм'], width=10).pack(side=tk.LEFT, padx=2)
        self.wavelength_vars.append(wavelength_var)

        ttk.Button(frame, text="Удалить",
                   command=lambda f=frame: self.remove_section(f)).pack(side=tk.LEFT, padx=5)
        self.frames.append(frame)

    def remove_section(self, frame):
        idx = self.frames.index(frame)
        self.frames.pop(idx)
        frame.destroy()
        self.distance_entries.pop(idx)
        self.method_vars.pop(idx)
        self.wavelength_vars.pop(idx)

    def plot_losses(self):
        plt.figure(figsize=(8,5))
        for entry, method_var, wl_var in zip(self.distance_entries, self.method_vars, self.wavelength_vars):
            try:
                L_max = float(entry.get())
            except ValueError:
                continue
            method = method_var.get()
            wavelength = wl_var.get()
            alpha = get_alpha(wavelength, method)
            L_vals, P_vals = calc_loss_curve(L_max, alpha)
            plt.loglog(L_vals, P_vals, label=f'{method} {wavelength} (α={alpha})')
        plt.xlabel('L, км')
        plt.ylabel('P₀')
        plt.title('Потери в линии')
        plt.legend()
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.show()

    def plot_speed(self):
        try:
            B0 = float(self.initial_speed_var.get()) * 1e6
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную начальную скорость")
            return
        protocol = self.protocol_var.get()
        segments = []
        for entry, method_var, wl_var in zip(self.distance_entries, self.method_vars, self.wavelength_vars):
            try:
                L = float(entry.get())
            except ValueError:
                continue
            segments.append({'L': L,
                             'method': method_var.get(),
                             'wavelength': wl_var.get()})
        L_cum, B_list = calc_qkd_speed_curve(B0, segments, protocol)

        fig, ax = plt.subplots(figsize=(8,5))
        ax.plot(L_cum, B_list, marker='o', linestyle='-')
        ax.set_yscale('log')
        ax.set_xlabel('Общее расстояние (км)')
        ax.set_ylabel('Скорость КРК (бит/с)')
        ax.set_title('Скорость КРК от расстояния')
        ax.grid(True, linestyle='--', linewidth=0.5)

        # Range slider для оси X
        ax_slider = plt.axes([0.15, 0.02, 0.7, 0.03])
        slider = RangeSlider(ax_slider, 'Диапазон L', min(L_cum), max(L_cum),
                             valinit=(min(L_cum), max(L_cum)))
        def update(val):
            ax.set_xlim(slider.val)
            fig.canvas.draw_idle()
        slider.on_changed(update)

        # Аннотации точек
        annot = ax.annotate("", xy=(0,0), xytext=(20,20),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        def on_click(event):
            if event.inaxes == ax:
                xdata, ydata = L_cum, B_list
                dist = [(event.xdata - x)**2 + (event.ydata - y)**2 for x,y in zip(xdata,ydata)]
                idx = dist.index(min(dist))
                annot.xy = (xdata[idx], ydata[idx])
                annot.set_text(f"L={xdata[idx]:.1f} км\nB={ydata[idx]:.2e} бит/с")
                annot.set_visible(True)
                fig.canvas.draw_idle()
        fig.canvas.mpl_connect("button_press_event", on_click)

        plt.show()

    def calc_rates(self):
        try:
            B0 = float(self.initial_speed_var.get()) * 1e6
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную начальную скорость")
            return
        protocol = self.protocol_var.get()
        segments = []
        for entry, method_var, wl_var in zip(self.distance_entries, self.method_vars, self.wavelength_vars):
            try:
                L = float(entry.get())
            except ValueError:
                continue
            segments.append({'L': L,
                             'method': method_var.get(),
                             'wavelength': wl_var.get()})
        results = calc_qkd_rate(B0, segments, protocol)
        self.result_text.set("\n".join(results))
        logger.info(f"Calculated rates for segments: {segments}")
