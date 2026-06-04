import math
import random

def exp_rv(rate: float) -> float:
    return -math.log(random.random()) / rate

def run_simulation(
    lam: float,
    mu: float,
    T: float,
    breakdown_period: float = 200.0,
    breakdown_duration: float = 20.0,
) -> dict:
    served = 0
    refused = 0
    refused_breakdown = 0
    service_end = 0.0

    t = exp_rv(lam)
    while t <= T:
        cycle_pos = t % breakdown_period
        is_broken = cycle_pos >= (breakdown_period - breakdown_duration)

        if is_broken:
            refused_breakdown += 1
            refused += 1    
        elif t >= service_end:
            service_end = t + exp_rv(mu)
            served += 1
        else:
            refused += 1

        t += exp_rv(lam)

    total = served + refused
    p_served = served / total if total > 0 else 0.0
    p_refused = refused / total if total > 0 else 0.0

    return {
        "total": total,
        "served": served,
        "refused": refused,
        "refused_breakdown": refused_breakdown,
        "p_served": p_served,
        "p_refused": p_refused,
    }

def main():
    lam = float(input("λ (arrival rate):  "))
    mu  = float(input("μ (service rate):  "))
    T   = float(input("T (sim time):      "))

    res = run_simulation(lam, mu, T)

    print(f"\nParameters: λ={lam}, μ={mu}, T={T}")
    print(f"Total customers:          {res['total']}")
    print(f"Served:                   {res['served']}")
    print(f"Refused (total):          {res['refused']}")
    print(f"  of which breakdowns:    {res['refused_breakdown']}")
    print(f"P(success): {res['p_served']:.4f}")
    print(f"P(refused): {res['p_refused']:.4f}")

if __name__ == "__main__":
    main()