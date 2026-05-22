import sys
import numpy as np
import math
from scipy import stats

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDoubleSpinBox, QSpinBox, QGroupBox,
    QFrame, QSizePolicy, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


C_BG       = "#F7F3EE"      
C_PANEL    = "#FFFFFF"  
C_BORDER   = "#E0D8CE"    
C_TEXT     = "#2C2416"     
C_MUTED    = "#8A7E6F"      
C_ACCENT   = "#C0392B"   
C_ACCENT2  = "#2980B9"      
C_SUCCESS  = "#27AE60"
C_WARN     = "#E67E22"
C_BAR_EMP  = "#C0392B"     
C_BAR_THEO = "#2980B9"    

STYLE = f"""
QMainWindow, QWidget {{
    background-color: {C_BG};
    font-family: 'Georgia', serif;
    color: {C_TEXT};
}}
QGroupBox {{
    border: 1.5px solid {C_BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 12px 10px 12px;
    background: {C_PANEL};
    font-size: 11px;
    font-weight: bold;
    color: {C_MUTED};
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    background: {C_PANEL};
}}
QLabel {{
    color: {C_TEXT};
    background: transparent;
}}
QDoubleSpinBox, QSpinBox {{
    border: 1.5px solid {C_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    background: {C_BG};
    color: {C_TEXT};
    font-size: 15px;
    font-family: 'Courier New', monospace;
    selection-background-color: {C_ACCENT};
}}
QDoubleSpinBox:focus, QSpinBox:focus {{
    border-color: {C_ACCENT};
}}
QPushButton#runBtn {{
    background-color: {C_ACCENT};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 1px;
}}
QPushButton#runBtn:hover {{
    background-color: #A93226;
}}
QPushButton#runBtn:pressed {{
    background-color: #922B21;
}}
QPushButton#runBtn:disabled {{
    background-color: #E0D8CE;
    color: {C_MUTED};
}}
QProgressBar {{
    border: 1.5px solid {C_BORDER};
    border-radius: 5px;
    background: {C_BG};
    height: 6px;
    text-align: center;
    font-size: 10px;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {C_ACCENT};
    border-radius: 4px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
"""


class FlowSimulator:
    @staticmethod
    def poisson_pmf(k, lam_T):
        return (math.exp(-lam_T) * (lam_T ** k)) / math.factorial(k)

    @staticmethod
    def one_run(lam: float, T: float) -> int:
        t, count = 0.0, 0
        while True:
            t += np.random.exponential(1.0 / lam)
            if t > T:
                break
            count += 1
        return count

    @classmethod
    def simulate(cls, lam: float, T: float, N: int, progress_cb=None) -> np.ndarray:
        data = np.empty(N, dtype=int)
        step = max(1, N // 100)
        for i in range(N):
            data[i] = cls.one_run(lam, T)
            if progress_cb and (i + 1) % step == 0:
                progress_cb(int((i + 1) / N * 100))
        return data


class SimWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object, float, float)

    def __init__(self, lam: float, T: float, N: int):
        super().__init__()
        self.lam = lam
        self.T   = T
        self.N   = N

    def run(self):
        data = FlowSimulator.simulate(
            self.lam, self.T, self.N,
            progress_cb=lambda v: self.progress.emit(v)
        )
        self.finished.emit(data, self.lam, self.T)


class ChartCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6, 4.5), dpi=110, facecolor=C_PANEL)
        super().__init__(self.fig)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self._draw_placeholder()

    def _draw_placeholder(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor=C_PANEL)
        ax.text(0.5, 0.5, "Запустите симуляцию,\nчтобы увидеть результат",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color=C_MUTED, style="italic", fontfamily="Georgia")
        for spine in ax.spines.values():
            spine.set_color(C_BORDER)
        ax.set_xticks([])
        ax.set_yticks([])
        self.fig.tight_layout()
        self.draw()

    def plot(self, data: np.ndarray, lam: float, T: float):
        self.fig.clear()
        lT = lam * T

        ax = self.fig.add_subplot(111, facecolor="#FDFAF6")
        for spine in ax.spines.values():
            spine.set_color(C_BORDER)
        ax.tick_params(colors=C_MUTED, labelsize=9)
        ax.xaxis.label.set_color(C_TEXT)
        ax.yaxis.label.set_color(C_TEXT)

        kmax = max(data)
        kmin = min(data)
        k_vals = np.arange(kmin, kmax + 1)

        freq = np.bincount(data - kmin, minlength=kmax - kmin + 1) / len(data)
        theo = [FlowSimulator.poisson_pmf(k, lT) for k in k_vals]

        width = 0.35
        xpos = np.arange(len(k_vals))

        ax.bar(xpos - width / 2, freq, width, color=C_BAR_EMP, alpha=0.85, label="Эмпирическое", zorder=3)
        ax.bar(xpos + width / 2, theo, width, color=C_BAR_THEO, alpha=0.80, label=f"Пуассон (λT={lT:.2f})", zorder=3)

        ax.set_xticks(xpos)
        ax.set_xticklabels([str(k) for k in k_vals], fontsize=9)
        ax.set_xlabel("Число заявок за интервал T", fontsize=10, labelpad=8)
        ax.set_ylabel("Относительная частота / вероятность", fontsize=10, labelpad=8)
        ax.set_title(f"Распределение числа заявок  |  λ = {lam} зап/с  T = {T} с", fontsize=11, color=C_TEXT, pad=14)
        ax.grid(axis="y", linestyle=":", alpha=0.5, color=C_BORDER, zorder=0)
        ax.legend(fontsize=9, framealpha=0.95, edgecolor=C_BORDER, facecolor=C_PANEL, loc="upper right")

        self.fig.tight_layout()
        self.draw()


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "—", accent: str = C_ACCENT):
        super().__init__()
        self.setFixedHeight(75)
        self.setStyleSheet(f"QFrame {{ background: {C_PANEL}; border: 1.5px solid {C_BORDER}; border-left: 4px solid {accent}; border-radius: 8px; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {C_MUTED}; font-size: 9px; letter-spacing: 1px; text-transform: uppercase; font-weight: bold;")
        lay.addWidget(self.title_lbl)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 20px; font-family: 'Courier New'; font-weight: bold;")
        lay.addWidget(self.value_lbl)

    def set_value(self, v: str):
        self.value_lbl.setText(v)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Пуассоновский поток — Сервер")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(STYLE)

        root = QWidget()
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)
        root_lay.addWidget(self._make_header())

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(20, 15, 20, 15)
        body_lay.setSpacing(20)
        root_lay.addWidget(body)

        left_scroll = QScrollArea()
        left_scroll.setFixedWidth(310)
        left_scroll.setWidgetResizable(True)
        left_container = QWidget()
        self.left_lay = QVBoxLayout(left_container)
        self.left_lay.setContentsMargins(0, 0, 10, 0)
        self.left_lay.setSpacing(12)
        self._build_left_panel()
        left_scroll.setWidget(left_container)
        body_lay.addWidget(left_scroll, stretch=0)

        right_container = QWidget()
        right_lay = QVBoxLayout(right_container)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(12)

        lbl = QLabel("Распределение числа заявок за интервал T")
        lbl.setStyleSheet(f"font-size: 12px; color: {C_MUTED}; font-weight: bold;")
        right_lay.addWidget(lbl)

        self.chart = ChartCanvas()
        right_lay.addWidget(self.chart, stretch=1)
        body_lay.addWidget(right_container, stretch=1)

    def _make_header(self):
        w = QWidget()
        w.setFixedHeight(55)
        w.setStyleSheet(f"background: {C_TEXT};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(20, 0, 20, 0)
        title = QLabel("ПУАССОНОВСКИЙ ПОТОК ЗАЯВОК НА СЕРВЕР")
        title.setStyleSheet("color: white; font-size: 14px; font-weight: bold; letter-spacing: 1.5px;")
        lay.addWidget(title)
        lay.addStretch()
        return w

    def _build_left_panel(self):
        grp1 = QGroupBox("Параметры потока")
        g1_lay = QVBoxLayout(grp1)
        self.lam_spin = self._add_spin(g1_lay, "λ — интенсивность (зап/с)", 0.1, 50.0, 3.0, 0.5)
        self.T_spin   = self._add_spin(g1_lay, "T — интервал наблюдения (с)", 0.1, 60.0, 5.0, 0.5)

        self.lT_label = QLabel()
        self.lT_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lT_label.setStyleSheet(
            f"background: {C_BG}; border: 1px solid {C_BORDER}; border-radius: 6px; "
            f"padding: 6px; font-family: 'Courier New'; color: {C_ACCENT}; font-weight: bold;"
        )
        g1_lay.addWidget(self.lT_label)
        self.left_lay.addWidget(grp1)

        grp2 = QGroupBox("Эксперимент")
        g2_lay = QVBoxLayout(grp2)
        self.N_spin = self._add_spin_int(g2_lay, "N — число тестов", 100, 200000, 10000, 1000)
        self.left_lay.addWidget(grp2)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.left_lay.addWidget(self.progress)

        self.run_btn = QPushButton("▶  ЗАПУСТИТЬ СИМУЛЯЦИЮ")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.setFixedHeight(42)
        self.run_btn.clicked.connect(self.run_simulation)
        self.left_lay.addWidget(self.run_btn)

        self.left_lay.addWidget(self._make_divider("Результаты"))

        self.card_mean = StatCard("Среднее x̄", accent=C_ACCENT)
        self.card_var  = StatCard("Дисперсия D", accent=C_ACCENT2)
        self.card_lT   = StatCard("λ·T (Теория)", accent=C_WARN)

        for c in (self.card_mean, self.card_var, self.card_lT):
            self.left_lay.addWidget(c)

        self.left_lay.addStretch()

        self.lam_spin.valueChanged.connect(self._update_lT)
        self.T_spin.valueChanged.connect(self._update_lT)
        self._update_lT()

    def _add_spin(self, lay, text, lo, hi, val, step):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 11px; color: {C_MUTED};")
        lay.addWidget(lbl)
        spin = QDoubleSpinBox()
        spin.setRange(lo, hi)
        spin.setValue(val)
        spin.setSingleStep(step)
        spin.setDecimals(1)
        spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        lay.addWidget(spin)
        return spin

    def _add_spin_int(self, lay, text, lo, hi, val, step):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 11px; color: {C_MUTED};")
        lay.addWidget(lbl)
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setValue(val)
        spin.setSingleStep(step)
        spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        lay.addWidget(spin)
        return spin

    def _make_divider(self, text):
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(
            f"color: {C_MUTED}; font-size: 10px; letter-spacing: 2px; "
            f"border-bottom: 1px solid {C_BORDER}; padding-bottom: 2px; font-weight: bold;"
        )
        return lbl

    def _update_lT(self):
        self.lT_label.setText(f"λ · T = {self.lam_spin.value() * self.T_spin.value():.2f}")

    def run_simulation(self):
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳  Выполняется…")
        self.progress.setVisible(True)
        self.progress.setValue(0)

        lam = self.lam_spin.value()
        T   = self.T_spin.value()
        N   = self.N_spin.value()

        self._worker = SimWorker(lam, T, N)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, data, lam, T):
        self._show_results(data, lam, T)
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  ЗАПУСТИТЬ СИМУЛЯЦИЮ")
        self.progress.setVisible(False)

    def _show_results(self, data: np.ndarray, lam: float, T: float):
        lT   = lam * T
        mean = float(np.mean(data))
        var  = float(np.var(data, ddof=0))

        self.card_mean.set_value(f"{mean:.4f}")
        self.card_var.set_value(f"{var:.4f}")
        self.card_lT.set_value(f"{lT:.4f}")

        self.chart.plot(data, lam, T)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()