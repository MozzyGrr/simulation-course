import random
import numpy as np
import matplotlib.pyplot as plt
from statistics import mean, variance


def multiplicative_rng(seed=1, n=100000):
    m = 2**31-1
    a = 12345

    numbers = []
    x = seed

    for _ in range(n):
        x = (a * x) % m
        numbers.append(x / m)

    return numbers


n = 100000

lcg_nums = multiplicative_rng(seed=1, n=n)
lcg_mean = mean(lcg_nums)
lcg_var = variance(lcg_nums)

random.seed(1)
rand_nums = [random.random() for i in range(n)]
rand_mean = mean(rand_nums)
rand_var = variance(rand_nums)


theory_mean = 0.5
theory_var = 1 / 12

print("Результаты:")
print(f"Multiplicative: mean={lcg_mean:.6f}, var={lcg_var:.6f}")
print(f"random: mean={rand_mean:.6f}, var={rand_var:.6f}")
print(f"Theory: mean={theory_mean:.6f}, var={theory_var:.6f}")


fig = plt.figure(figsize=(14, 6))


ax1 = plt.subplot(1, 2, 1)
ax1.hist(lcg_nums, bins=50, density=True, alpha=0.6, label='Multiplicative', edgecolor='black')
ax1.hist(rand_nums, bins=50, density=True, alpha=0.6, label='random', edgecolor='black')


x = np.linspace(0, 1, 200)
ax1.plot(x, np.ones_like(x), 'r--', linewidth=2, label='Theory')

ax1.set_title('Distribution comparison (n=100000)')
ax1.set_xlabel('Value')
ax1.set_ylabel('Density')
ax1.legend()
ax1.grid(True, alpha=0.3)


ax2 = plt.subplot(1, 2, 2)
ax2.axis('off')

text = (
    f"Theory:\nmean = {theory_mean:.6f}\nvar = {theory_var:.6f}\n\n"
    f"Multiplicative:\nmean = {lcg_mean:.6f}\nvar = {lcg_var:.6f}\n\n"
    f"Random:\nmean = {rand_mean:.6f}\nvar = {rand_var:.6f}"
)

ax2.text(0.1, 0.5, text, fontsize=12)

plt.tight_layout()
plt.show()



