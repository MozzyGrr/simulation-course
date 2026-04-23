import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from scipy.stats import chisquare
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


VALUES = np.array([1, 2, 3, 4])
DEFAULT_PROBS = np.array([0.25, 0.25, 0.25, 0.25])
SIZES = [10, 100, 1000, 10000]


def theoretical_stats(probs):
    mean = np.sum(VALUES * probs)
    var = np.sum((VALUES - mean) ** 2 * probs)
    return mean, var



def sample_discrete(n, probs):
    return np.random.choice(VALUES, size=n, p=probs)


def sample_normal(n):
    return np.random.normal(0, 1, size=n)


def compute_stats(sample, probs, true_mean, true_var):
    n = len(sample)

    counts = np.array([np.sum(sample == v) for v in VALUES]) # считаем сколько раз встречалось значение
    emp_probs = counts / n# эмпирическая p

    mean = np.mean(sample)
    var = np.var(sample)

    err_mean = abs(mean - true_mean) / true_mean
    err_var = abs(var - true_var) / true_var

    chi2, p_val = chisquare(counts, probs * n)# Xi^2

    return {
        "mean": mean,
        "var": var,
        "err_mean": err_mean,
        "err_var": err_var,
        "chi2": chi2,
        "p": p_val
    }



class SimulatorUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Статистический симулятор")
        self.root.geometry("1100x750")

        self.probs = DEFAULT_PROBS.copy()

        self.create_layout()

    def create_layout(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        # Разделение на левую и правую часть
        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=10)

        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        self.build_controls(left)
        self.build_output(right)

    def build_controls(self, parent):
        ttk.Label(parent, text="Параметры распределения", font=("Arial", 12, "bold")).pack(pady=5)

        self.entries = []
        for i, v in enumerate(VALUES):
            row = ttk.Frame(parent)
            row.pack(pady=2)

            ttk.Label(row, text=f"P(X={v})").pack(side="left")
            e = ttk.Entry(row, width=7)
            e.insert(0, str(self.probs[i]))
            e.pack(side="right")

            self.entries.append(e)

        ttk.Button(parent, text="Сделать равномерным", command=self.make_uniform).pack(pady=10)
        ttk.Button(parent, text="Запустить дискретную", command=self.run_discrete).pack(pady=5)
        ttk.Button(parent, text="Запустить нормальную", command=self.run_normal).pack(pady=5)

    def build_output(self, parent):
        # Таблица
        cols = ("N", "Mean", "Var", "ErrMean", "ErrVar", "Chi2", "p")
        self.table = ttk.Treeview(parent, columns=cols, show="headings", height=8)

        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=120)

        self.table.pack(fill="x", pady=10)

        # График
        self.fig = Figure(figsize=(7, 6))
        self.axes = [self.fig.add_subplot(2, 2, i + 1) for i in range(4)]

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def read_probs(self):
        try:
            probs = np.array([float(e.get()) for e in self.entries])

            if np.any(probs < 0) or abs(probs.sum() - 1) > 1e-6:
                raise ValueError

            self.probs = probs
            return True
        except:
            messagebox.showerror("Ошибка", "Некорректные вероятности")
            return False

    def make_uniform(self):
        for e in self.entries:
            e.delete(0, tk.END)
            e.insert(0, "0.25")
        self.probs = np.array([0.25]*4)

    def clear(self):
        self.table.delete(*self.table.get_children())
        for ax in self.axes:
            ax.clear()

    def run_discrete(self):
        if not self.read_probs():
            return

        self.clear()

        true_mean, true_var = theoretical_stats(self.probs)

        for i, n in enumerate(SIZES):
            sample = sample_discrete(n, self.probs)
            stats = compute_stats(sample, self.probs, true_mean, true_var)

            self.table.insert("", "end", values=(
                n,
                round(stats["mean"], 4),
                round(stats["var"], 4),
                round(stats["err_mean"], 4),
                round(stats["err_var"], 4),
                round(stats["chi2"], 4),
                round(stats["p"], 4)
            ))

            self.axes[i].hist(sample, bins=np.arange(0.5, 5.5, 1), density=True)
            self.axes[i].set_title(f"N={n}")

        self.fig.suptitle("Дискретное распределение")
        self.canvas.draw()

    def run_normal(self):
        self.clear()

        x = np.linspace(-4, 4, 400)
        y = (1 / np.sqrt(2*np.pi)) * np.exp(-x**2 / 2)

        for i, n in enumerate(SIZES):
            sample = sample_normal(n)

            self.axes[i].hist(sample, bins=30, density=True)
            self.axes[i].plot(x, y)
            self.axes[i].set_title(f"N={n}")

        self.fig.suptitle("Нормальное распределение")
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulatorUI(root)
    root.mainloop()
