import random
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation
from IPython.display import HTML
from collections import defaultdict


class HealthState:
    def __init__(self):
        self.states = {0: 'healthy',
                       1: 'infected',
                       2: 'immune',
                       3: 'dead'}
        self.stateProperies = {'healthy': {'color': 'tab:blue',
                                           'rate': None, 'daysTo': None},
                               'infected': {'color': 'tab:red',
                                            'rate': None, 'daysTo': None},
                               'immune': {'color': 'tab:green',
                                          'rate': None, 'daysTo': None},
                               'dead': {'color': 'tab:grey',
                                        'rate': None, 'daysTo': None}}
        self.transitions = {'healthy': ['infected'],
                            'infected': ['immune', 'dead']}

    def probabilities(self, state):
        return self.probs[state]

    def updateProbabilites(self):
        self.probs = defaultdict(lambda: [[], []])
        for key, value in self.transitions.items():
            for v in value:
                if self.stateProperies[v]['rate']:
                    r = self.stateProperies[v]['rate']
                    if len(self.probs[key][0]) > 0:
                        self.probs[key][0].append(self.probs[key][0][-1]+r)
                        self.probs[key][1].append(v)
                    else:
                        self.probs[key][0].append(r)
                        self.probs[key][1].append(v)

    def color(self, state):
        return self.stateProperies[self.states[state]]['color']

    def stateName(self, state):
        return self.states[state]

    def stateIndex(self, state):
        for key, value in self.states.items():
            if value == state:
                return key
        raise KeyError('State {} not found!'.format(state))


class Node:
    def __init__(self, healthState, plot):
        self.state = 0
        self.plot = plot
        self.daysInfected = 0
        self.hs = healthState
        if self.plot:
            self.colors = []

    def getStateName(self):
        return self.hs.stateName(self.state)

    def getStateIndex(self):
        return self.hs.stateName(self.state)

    def update(self):
        if self.hs.stateName(self.state) is not 'healthy':
            self.daysInfected += 1
        if self.plot:
            self.colors.append(self.hs.color(self.state))

    def changeState(self, newState):
        if isinstance(newState, str):
            self.state = self.hs.stateIndex(newState)
        else:
            self.state = int(newState)


class NetworkSpreaderAdvanced:
    def __init__(self, N, m, hs, plot=False, seed=None):
        random.seed(seed)
        self.G = nx.barabasi_albert_graph(N, m, seed)
        self.N = [Node(hs, plot) for n in range(N)]
        self.step = 0
        self.hs = hs
        self.hs.updateProbabilites()
        self.data = defaultdict(list)
        self.plot = plot

    def collectData(self):
        self.data['Step'].append(self.step-1)
        for index in self.hs.states:
            self.data[self.hs.stateName(index)].append(0)
        for n in self.N:
            self.data[self.hs.stateName(n.state)][-1] += 1
        for key in self.data:
            if key != 'Step':
                self.data[key][-1] /= self.G.number_of_nodes()

    def processNodes(self):
        inf = []
        for i, n in enumerate(self.N):
            if n.getStateName() == 'infected':
                inf.append(i)
        inf = set(inf)
        for i, n in enumerate(self.N):
            state = n.getStateName()
            if state in self.hs.transitions:
                p = self.hs.probabilities(state)
                u = random.random()
                newState = self._first(*p, u)
                if newState == 'infected':
                    nn = self.G.edges(i)
                    if any([n[1] in inf for n in nn]):
                        n.changeState(newState)
                elif newState:
                    n.changeState(newState)

    def _first(self, p, m, u):
        for i, v in enumerate(p):
            if v > u:
                return m[i]
        return None

    def takeStep(self):
        if self.step == 0:
            self.N[
                random.randint(0, self.G.number_of_nodes()-1)].changeState('infected')
        else:
            self.processNodes()
        for n in self.N:
            n.update()
        self.step += 1

    def _anim(self, i):
        self.ax.clear()
        c = [n.colors[i] for n in self.N]
        nx.draw_kamada_kawai(self.G, node_color=c, with_labels=True)

    def _run_animated(self, step, inter):
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        for i in range(step):
            self.takeStep()
            self.collectData()
        anim = matplotlib.animation.FuncAnimation(
            self.fig, self._anim, frames=self.step, interval=inter, repeat=True)
        return HTML(anim.to_jshtml())

    def _run_static(self, step):
        for i in range(step):
            self.takeStep()
            self.collectData()

    def run(self, steps, inter=200):
        if self.plot:
            ani = self._run_animated(steps, inter)
            return self.data, ani
        else:
            self._run_static(steps)
            return self.data
