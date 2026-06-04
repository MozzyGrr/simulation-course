import math
import random
import heapq


def exp_rv(rate):
    return -math.log(random.random()) / rate


class Event:
    def __init__(self, time, kind, server_id=None):
        self.time = time
        self.kind = kind          # 'arrival' | 'departure'
        self.server_id = server_id

    def __lt__(self, other):
        return self.time < other.time



class Server:
    def __init__(self, server_id):
        self.id = server_id
        self.busy = False

    def start_service(self, start_time, service_time):
        self.busy = True
        return start_time + service_time

    def finish_service(self):
        self.busy = False

    def is_free(self):
        return not self.busy



class BoundedQueue:
    def __init__(self, max_length):
        self.max_length = max_length
        self._queue = []

    def enqueue(self, arrival_time):
        if len(self._queue) >= self.max_length:
            return False
        self._queue.append(arrival_time)
        return True

    def dequeue(self):
        if self._queue:
            return self._queue.pop(0)
        return None



class Statistics:
    def __init__(self):
        self.total_arrivals = 0
        self.served = 0
        self.refused_busy = 0
        self.refused_breakdown = 0

    def refused(self):
        return self.refused_busy + self.refused_breakdown

    def p_served(self):
        return self.served / self.total_arrivals if self.total_arrivals else 0.0

    def p_refused(self):
        return self.refused() / self.total_arrivals if self.total_arrivals else 0.0

    def report(self):
        lines = [
            f"  Всего заявок:              {self.total_arrivals}",
            f"  Обслужено:                 {self.served}",
            f"  Отказов (всего):           {self.refused()}",
            f"    из-за занятости/очереди: {self.refused_busy}",
            f"    из-за поломки:           {self.refused_breakdown}",
            f"  P(обслужен):               {self.p_served():.4f}",
            f"  P(отказ):                  {self.p_refused():.4f}",
        ]
        return "\n".join(lines)



class MMcKSystem:
    def __init__(self, lam, mu, num_servers, queue_capacity, T,
                 breakdown_period=200.0, breakdown_duration=20.0):
        self.lam = lam
        self.mu = mu
        self.T = T
        self.breakdown_period = breakdown_period
        self.breakdown_duration = breakdown_duration

        self.servers = [Server(i) for i in range(num_servers)]
        self.queue = BoundedQueue(queue_capacity)
        self.stats = Statistics()
        self._calendar = []

    def _schedule(self, event):
        heapq.heappush(self._calendar, event)

    def _next_event(self):
        return heapq.heappop(self._calendar)

    def _is_broken(self, t):
        cycle_pos = t % self.breakdown_period
        return cycle_pos >= (self.breakdown_period - self.breakdown_duration)

    def _free_server(self):
        for s in self.servers:
            if s.is_free():
                return s
        return None

    def _handle_arrival(self, event):
        t = event.time
        self.stats.total_arrivals += 1

        if self._is_broken(t):
            self.stats.refused_breakdown += 1
            return

        server = self._free_server()
        if server is not None:
            finish_time = server.start_service(t, exp_rv(self.mu))
            self._schedule(Event(finish_time, 'departure', server.id))
        else:
            accepted = self.queue.enqueue(t)
            if not accepted:
                self.stats.refused_busy += 1

    def _handle_departure(self, event):
        t = event.time
        server = self.servers[event.server_id]

        self.stats.served += 1
        server.finish_service()

        waiting = self.queue.dequeue()
        if waiting is not None:
            finish_time = server.start_service(t, exp_rv(self.mu))
            self._schedule(Event(finish_time, 'departure', server.id))

    def run(self):
        self._schedule(Event(exp_rv(self.lam), 'arrival'))

        while self._calendar:
            event = self._next_event()

            if event.time > self.T:
                break

            if event.kind == 'arrival':
                self._handle_arrival(event)
                next_arrival = event.time + exp_rv(self.lam)
                if next_arrival <= self.T:
                    self._schedule(Event(next_arrival, 'arrival'))

            elif event.kind == 'departure':
                self._handle_departure(event)

        return self.stats

def main():
    print("=== M/M/c/K с поломками ===\n")
    lam = float(input("λ (интенсивность прибытий):     "))
    mu  = float(input("μ (интенсивность обслуживания):  "))
    c   = int(input("c (число приборов):              "))
    K   = int(input("K (ёмкость очереди):             "))
    T   = float(input("T (время моделирования):         "))

    system = MMcKSystem(lam=lam, mu=mu, num_servers=c, queue_capacity=K, T=T)
    stats = system.run()

    print(f"\nРезультаты (λ={lam}, μ={mu}, c={c}, K={K}, T={T}):")
    print(stats.report())


if __name__ == "__main__":
    main()