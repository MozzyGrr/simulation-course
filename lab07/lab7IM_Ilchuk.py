import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import csv
import time
import threading
from datetime import datetime

STATES = {1: "Ясно ", 2: "Облачно ", 3: "Пасмурно "}
STATE_COLORS = {1: "#FFD700", 2: "#87CEEB", 3: "#778899"}
STATE_COLORS_HEX = ["#FFD700", "#87CEEB", "#778899"]

# Скорости переходов
DEFAULT_Q_OFF = np.array([
    [0,    0.5,  0.2],
    [0.3,  0,    0.4],  
    [0.1,  0.3,  0  ],  
], dtype=float)

# Построение матрицы с учетом суммы скоростей переходов
def build_Q(off_diag: np.ndarray) -> np.ndarray:
    Q = off_diag.copy()
    for i in range(3):
        Q[i, i] = -np.sum(Q[i, :])
    return Q


def stationary_distribution(Q: np.ndarray) -> np.ndarray:
    n = Q.shape[0]
    A = Q.T.copy()# Транспонируем чтобы взаимодействовать как с матрицей, а не строчкой
    A[-1, :] = 1.0# Нормируем, то есть заменяем последнюю строчку на 1
    b = np.zeros(n)
    b[-1] = 1.0
    return np.linalg.solve(A, b)


def simulate_ctmc(Q: np.ndarray, T_days: float, state0: int = 0):
   
    times = [0.0]
    states = [state0]
    t = 0.0
    cur = state0

    while t < T_days:
        lam = -Q[cur, cur]          
        if lam <= 0:
            break
        dt = np.random.exponential(1.0 / lam)# не имеет "истории"
        t += dt
        if t >= T_days:
            break
        probs = Q[cur, :].copy()
        probs[cur] = 0
        probs = probs / probs.sum()# Переделываем скорости в вероятности
        nxt = np.random.choice(3, p=probs)
        times.append(t)
        states.append(nxt)
        cur = nxt

    times.append(T_days)
    states.append(states[-1]) 
    return np.array(times), np.array(states)


def empirical_stationary(times: np.ndarray, states: np.ndarray) -> np.ndarray:
    dur = np.zeros(3)
    for i in range(len(times) - 1):
        s = states[i]
        dt = times[i + 1] - times[i]
        dur[s] += dt
    total = dur.sum()
    return dur / total if total > 0 else dur

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Марковская модель погоды")
        self.configure(bg="#1e1e2e")
        self.resizable(True, True)
        self.geometry("1300x820")

        self._sim_running = False
        self._sim_thread = None
        self._sim_times = None
        self._sim_states = None

        self._build_ui()

    def _build_ui(self):
        left = tk.Frame(self, bg="#181825", padx=12, pady=12)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text=" Параметры", font=("Segoe UI", 13, "bold"),
                 bg="#181825", fg="#cdd6f4").pack(anchor="w", pady=(0, 8))
        
        tk.Label(left, text="Матрица интенсивностей λᵢⱼ",
                 font=("Segoe UI", 10, "bold"), bg="#181825", fg="#89b4fa").pack(anchor="w")

        header_row = tk.Frame(left, bg="#181825")
        header_row.pack(fill=tk.X)
        tk.Label(header_row, text="    ", bg="#181825", fg="#cdd6f4", width=4).pack(side=tk.LEFT)
        for j in range(3):
            tk.Label(header_row, text=f"→{j+1}", bg="#181825", fg="#a6e3a1",
                     font=("Segoe UI", 9), width=7).pack(side=tk.LEFT)

        self._q_entries = []
        for i in range(3):
            row = tk.Frame(left, bg="#181825")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"{i+1}→", bg="#181825", fg="#f38ba8",
                     font=("Segoe UI", 9), width=4).pack(side=tk.LEFT)
            row_entries = []
            for j in range(3):
                if i == j:
                    e = tk.Label(row, text="—", bg="#313244", fg="#585b70",
                                 font=("Consolas", 10), width=7, relief="flat")
                    e.pack(side=tk.LEFT, padx=1)
                    row_entries.append(None)
                else:
                    var = tk.StringVar(value=str(DEFAULT_Q_OFF[i, j]))
                    e = tk.Entry(row, textvariable=var, width=7, bg="#313244", fg="#cdd6f4",
                                 insertbackground="white", font=("Consolas", 10),
                                 relief="flat", justify="center")
                    e.pack(side=tk.LEFT, padx=1)
                    row_entries.append(var)
            self._q_entries.append(row_entries)

        sep(left)

        tk.Label(left, text="Длительность моделирования (дней):",
                 bg="#181825", fg="#89b4fa", font=("Segoe UI", 9)).pack(anchor="w")
        self._var_T = tk.StringVar(value="365")
        tk.Entry(left, textvariable=self._var_T, bg="#313244", fg="#cdd6f4",
                 insertbackground="white", font=("Consolas", 10), relief="flat").pack(fill=tk.X, pady=2)

        tk.Label(left, text="Начальное состояние:",
                 bg="#181825", fg="#89b4fa", font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 0))
        self._var_s0 = tk.IntVar(value=1)
        for val, name in STATES.items():
            tk.Radiobutton(left, text=name, variable=self._var_s0, value=val,
                           bg="#181825", fg="#cdd6f4", selectcolor="#313244",
                           activebackground="#181825", font=("Segoe UI", 9)).pack(anchor="w")

        sep(left)

        btn_kw = dict(font=("Segoe UI", 10, "bold"), relief="flat", pady=5, cursor="hand2")
        tk.Button(left, text=" Запустить симуляцию", bg="#89b4fa", fg="#1e1e2e",
                  command=self._run_simulation, **btn_kw).pack(fill=tk.X, pady=2)
        tk.Button(left, text=" Сохранить в CSV", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._save_csv, **btn_kw).pack(fill=tk.X, pady=2)
        tk.Button(left, text=" Очистить", bg="#f38ba8", fg="#1e1e2e",
                  command=self._clear, **btn_kw).pack(fill=tk.X, pady=2)

        sep(left)

        tk.Label(left, text=" Результаты", font=("Segoe UI", 11, "bold"),
                 bg="#181825", fg="#cdd6f4").pack(anchor="w")
        self._result_text = tk.Text(left, width=30, height=14, bg="#11111b", fg="#cdd6f4",
                                    font=("Consolas", 9), relief="flat", state="disabled",
                                    wrap="word")
        self._result_text.pack(fill=tk.BOTH, expand=True, pady=4)

      
        right = tk.Frame(self, bg="#1e1e2e")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._fig = Figure(figsize=(9, 6.5), facecolor="#1e1e2e")
        self._canvas = FigureCanvasTkAgg(self._fig, master=right)
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._draw_placeholder()


    def _get_Q(self):
        off = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                if i == j:
                    continue
                try:
                    v = float(self._q_entries[i][j].get())
                    if v < 0:
                        raise ValueError
                    off[i, j] = v
                except (ValueError, AttributeError):
                    raise ValueError(f"Некорректное значение λ[{i+1}][{j+1}]")
        return build_Q(off)

    def _set_result(self, text: str):
        self._result_text.config(state="normal")
        self._result_text.delete("1.0", tk.END)
        self._result_text.insert(tk.END, text)
        self._result_text.config(state="disabled")



    def _run_simulation(self):
        if self._sim_running:
            messagebox.showinfo("Подождите", "Симуляция уже выполняется.")
            return
        try:
            Q = self._get_Q()
            T = float(self._var_T.get())
            if T <= 0:
                raise ValueError("T должно быть > 0")
            s0 = self._var_s0.get() - 1  
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
            return

        self._sim_running = True
        self._set_result(" Выполняется симуляция...")

        def worker():
            times, states = simulate_ctmc(Q, T, s0)
            self._sim_times = times
            self._sim_states = states
            self.after(0, lambda: self._finish_simulation(Q, times, states, T))

        self._sim_thread = threading.Thread(target=worker, daemon=True)
        self._sim_thread.start()

    def _finish_simulation(self, Q, times, states, T):
        self._sim_running = False

        emp = empirical_stationary(times, states)
        theory = stationary_distribution(Q)
        n_transitions = len(times) - 2


        lines = ["=" * 28, "  СТАТИСТИКА СИМУЛЯЦИИ", "=" * 28,
                 f"Период: {T:.0f} дней",
                 f"Переходов: {n_transitions}",
                 f"Ср. время в состоянии: {T/max(n_transitions,1):.3f} дн.",
                 "", "СТАЦИОНАРНОЕ РАСПРЕДЕЛЕНИЕ",
                 "-" * 28,
                 f"{'Состояние':<12} {'Эмп.':>8} {'Теор.':>8} {'Δ':>8}"]
        for i, name in enumerate(["Ясно", "Облачно", "Пасмурно"]):
            diff = abs(emp[i] - theory[i])
            lines.append(f"{name:<12} {emp[i]:>8.4f} {theory[i]:>8.4f} {diff:>8.4f}")
        lines += ["", "МАТРИЦА ИНТЕНСИВНОСТЕЙ Q:",
                  "-" * 28]
        for i in range(3):
            lines.append("  " + "  ".join(f"{Q[i,j]:6.3f}" for j in range(3)))
        self._set_result("\n".join(lines))

        self._draw_charts(Q, times, states, emp, theory, T)



    def _draw_placeholder(self):
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.set_facecolor("#1e1e2e")
        ax.text(0.5, 0.5, "Задайте параметры и нажмите\n Запустить симуляцию",
                ha="center", va="center", fontsize=14, color="#585b70",
                transform=ax.transAxes)
        ax.axis("off")
        self._canvas.draw()

    def _draw_charts(self, Q, times, states, emp, theory, T):
        self._fig.clear()
        self._fig.patch.set_facecolor("#1e1e2e")

        gs = self._fig.add_gridspec(2, 2, hspace=0.45, wspace=0.35,
                                    left=0.08, right=0.97, top=0.93, bottom=0.08)

        ax1 = self._fig.add_subplot(gs[0, :])  
        ax2 = self._fig.add_subplot(gs[1, 0])  
        ax3 = self._fig.add_subplot(gs[1, 1])   

        dark, fg = "#1e1e2e", "#cdd6f4"
        for ax in (ax1, ax2, ax3):
            ax.set_facecolor("#181825")
            ax.tick_params(colors=fg, labelsize=8)
            for sp in ax.spines.values():
                sp.set_color("#313244")
            ax.xaxis.label.set_color(fg)
            ax.yaxis.label.set_color(fg)
            ax.title.set_color(fg)

        N_SHOW = 2000
        if len(times) > N_SHOW + 1:
            idx = np.linspace(0, len(times) - 2, N_SHOW, dtype=int)
        else:
            idx = np.arange(len(times) - 1)

        for k in idx:
            t0, t1 = times[k], times[k + 1]
            s = states[k]
            ax1.hlines(s + 1, t0, t1, colors=STATE_COLORS[s + 1], linewidth=2.5)

        ax1.set_xlim(0, T)
        ax1.set_ylim(0.3, 3.7)
        ax1.set_yticks([1, 2, 3])
        ax1.set_yticklabels(["Ясно", "Облачно", "Пасмурно"], fontsize=8, color=fg)
        ax1.set_xlabel("Время (дни)", color=fg, fontsize=9)
        ax1.set_title("Траектория погоды во времени", fontsize=10)
        ax1.yaxis.grid(True, color="#313244", linestyle="--", linewidth=0.5)

        labels = ["Ясно", "Облачно", "Пасмурно"]
        x = np.arange(3)
        w = 0.35
        bars_e = ax2.bar(x - w/2, emp, w, label="Эмпирическое",
                         color=STATE_COLORS_HEX, edgecolor="#1e1e2e", linewidth=0.8)
        bars_t = ax2.bar(x + w/2, theory, w, label="Теоретическое",
                         color=["#b8860b", "#4682b4", "#556b7a"],
                         edgecolor="#1e1e2e", linewidth=0.8, hatch="//")
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, fontsize=8, color=fg)
        ax2.set_ylabel("Вероятность", fontsize=9, color=fg)
        ax2.set_title("Сравнение распределений", fontsize=10)
        ax2.legend(fontsize=7, facecolor="#313244", labelcolor=fg, edgecolor="#585b70")
        ax2.set_ylim(0, max(max(emp), max(theory)) * 1.25)
        for b in list(bars_e) + list(bars_t):
            h = b.get_height()
            ax2.text(b.get_x() + b.get_width()/2, h + 0.005,
                     f"{h:.3f}", ha="center", va="bottom", fontsize=7, color=fg)
        wedge_props = {"linewidth": 1.5, "edgecolor": "#1e1e2e"}
        ax3.pie(emp, labels=labels, colors=STATE_COLORS_HEX,
                autopct="%1.1f%%", pctdistance=0.75,
                wedgeprops=wedge_props, textprops={"color": fg, "fontsize": 8},
                startangle=90)
        ax3.set_title("Доля времени\n(эмпирическая)", fontsize=10)

        self._fig.suptitle("Марковская модель погоды  |  Цепь Маркова с непрерывным временем",
                           color="#89b4fa", fontsize=11, y=0.99)
        self._canvas.draw()

    def _save_csv(self):
        if self._sim_times is None:
            messagebox.showwarning("Нет данных", "Сначала выполните симуляцию.")
            return
        try:
            Q = self._get_Q()
            emp = empirical_stationary(self._sim_times, self._sim_states)
            theory = stationary_distribution(Q)
            T = float(self._var_T.get())
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"C:/Users/ilchu/Desktop/имитационка/weather_simulation_{ts}.csv"

        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["=== Simulation Parameters ==="])
            w.writerow(["Date & time", datetime.now().isoformat()])
            w.writerow(["Num of days", T])
            w.writerow(["Transitions", len(self._sim_times) - 2])
            w.writerow([])

            w.writerow(["=== Q Matrix ==="])
            w.writerow(["", "→Clear", "→Cloudy", "→Overcast"])
            row_names = ["Clear→", "Cloudy→", "Overcast→"]
            for i in range(3):
                w.writerow([row_names[i]] + [f"{Q[i,j]:.6f}" for j in range(3)])
            w.writerow([])

            w.writerow(["=== Stationary Distribution ==="])
            w.writerow(["State", "Empirical", "Theoretical", "Abs. Deviation"])
            labels = ["Clear", "Cloudy", "Overcast"]
            for i in range(3):
                w.writerow([labels[i], f"{emp[i]:.6f}", f"{theory[i]:.6f}",
                             f"{abs(emp[i]-theory[i]):.6f}"])
            w.writerow([])

            w.writerow(["=== SIMULATION TRAJECTORY ==="])
            w.writerow(["Transition Moment (days)", "State (Number)", "State (Name)",
                        "Duration (days)"])
            state_names = {0: "Clear", 1: "Cloudy", 2: "Overcast"}
            for k in range(len(self._sim_times) - 1):
                t0 = self._sim_times[k]
                t1 = self._sim_times[k + 1]
                s = self._sim_states[k]
                w.writerow([f"{t0:.6f}", s + 1, state_names[s], f"{t1 - t0:.6f}"])

        messagebox.showinfo("Сохранено", f"Данные сохранены в:\n{fname}")

    def _clear(self):
        self._sim_times = None
        self._sim_states = None
        self._set_result("")
        self._draw_placeholder()


def sep(parent):
    ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=8)


if __name__ == "__main__":
    np.random.seed(None)
    app = WeatherApp()
    app.mainloop()
