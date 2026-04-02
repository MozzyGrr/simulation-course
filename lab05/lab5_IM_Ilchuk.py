import tkinter as tk
import random

class EventModel:
    def __init__(self, events):
        self.events = events

    def sample(self):
        alpha = random.random()
        cumulative = 0

        for name, p in self.events:
            cumulative += p
            if alpha < cumulative:
                return name

        return self.events[-1][0]



class ModernApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stochastic Lab")
        self.root.geometry("700x550")
        self.root.configure(bg="#0f172a")
        self.root.resizable(False, False)

        self.yesno = EventModel([("ДА", 0.5), ("НЕТ", 0.5)])
        self.magic = EventModel([
            ("Да", 0.125), ("Нет", 0.125), ("Скорее всего", 0.125),
            ("Сомнительно", 0.125), ("Без сомнений", 0.125),
            ("Спроси позже", 0.125), ("Определенно да", 0.125),
            ("Маловероятно", 0.125)
        ])

        self.history = []

        self.build_home()

    def build_home(self):
        self.clear()

        container = tk.Frame(self.root, bg="#0f172a")
        container.pack(expand=True)

        title = tk.Label(container,
                         text="Random Event Simulator",
                         font=("Segoe UI", 26, "bold"),
                         fg="#e2e8f0",
                         bg="#0f172a")
        title.pack(pady=30)

        self.create_card(container, "Да / Нет", "#22c55e", self.screen_yesno)
        self.create_card(container, "Magic Ball", "#6366f1", self.screen_magic)

    def create_card(self, parent, text, color, command):
        card = tk.Frame(parent, bg="#1e293b", width=250, height=120)
        card.pack(pady=15)
        card.pack_propagate(False)

        label = tk.Label(card,
                         text=text,
                         font=("Segoe UI", 18, "bold"),
                         fg="white",
                         bg="#1e293b")
        label.pack(expand=True)

        btn = tk.Button(card,
                        text="Открыть",
                        command=command,
                        bg=color,
                        fg="black",
                        relief="flat")
        btn.pack(pady=10)

    def screen_yesno(self):
        self.clear()

        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(expand=True)

        self.answer = tk.Label(frame,
                               text="?",
                               font=("Segoe UI", 80, "bold"),
                               fg="#38bdf8",
                               bg="#0f172a")
        self.answer.pack(pady=80)

        btn = tk.Button(frame,
                        text="Спросить",
                        command=self.animate_yesno,
                        bg="#38bdf8",
                        fg="black",
                        font=("Segoe UI", 14),
                        relief="flat",
                        padx=20, pady=10)
        btn.pack()

        self.back_button(frame)

    def animate_yesno(self):
        self.answer.config(text="...")
        self.root.after(400, self.show_yesno)

    def show_yesno(self):
        res = self.yesno.sample()
        color = "#22c55e" if res == "ДА" else "#ef4444"
        self.answer.config(text=res, fg=color)


    def screen_magic(self):
        self.clear()

        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(expand=True)

        self.magic_text = tk.Label(frame,
                                   text="Нажми 🔮",
                                   font=("Segoe UI", 22),
                                   fg="#cbd5f5",
                                   bg="#0f172a",
                                   wraplength=400)
        self.magic_text.pack(pady=60)

        btn = tk.Button(frame,
                        text="🔮",
                        command=self.animate_magic,
                        font=("Segoe UI", 30),
                        bg="#6366f1",
                        fg="white",
                        relief="flat",
                        width=4, height=1)
        btn.pack()

        self.stats = tk.Label(frame,
                              text="",
                              fg="#94a3b8",
                              bg="#0f172a")
        self.stats.pack(pady=30)

        self.back_button(frame)

    def animate_magic(self):
        self.magic_text.config(text="Думаю...")
        self.root.after(600, self.show_magic)

    def show_magic(self):
        res = self.magic.sample()
        self.history.append(res)

        self.magic_text.config(text=res,
                               font=("Segoe UI", 24, "bold"),
                               fg="#ffffff")

        self.update_stats()

    def update_stats(self):
        total = len(self.history)
        freq = {}

        for r in self.history:
            freq[r] = freq.get(r, 0) + 1

        text = "Статистика:\n"
        for k, v in freq.items():
            text += f"{k}: {round(v/total, 2)}\n"

        self.stats.config(text=text)

    def back_button(self, parent):
        tk.Button(parent,
                  text="← Назад",
                  command=self.build_home,
                  bg="#1e293b",
                  fg="white",
                  relief="flat").pack(pady=20)

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()


root = tk.Tk()
app = ModernApp(root)
root.mainloop()
