from Neat import algo_gen_motif, algo_gen_ouvert, Genome, load
import Simulation_graphique
import Simulation
import numpy as np
import matplotlib.pyplot as plt
from pickle import Unpickler


def load(nom_fichier='Sauvegarde'):
    with open(nom_fichier, 'rb') as fichier:
        unpickler = Unpickler(fichier)
        obj = unpickler.load()
    return obj


def demo_xor():
    """crée un réseau se comportant comme XOR"""
    motif = [([0, 0], [0]),
             ([0, 1], [1]),
             ([1, 0], [1]),
             ([1, 1], [0])]
    genome, fitness, nb_generations = algo_gen_motif(motif)
    return genome


def demo_sin():
    X = np.arange(-np.pi, np.pi, np.pi / 6)
    motif = [[[x], [np.sin(x)]] for x in X]
    reseau, _, _ = algo_gen_motif(
        motif, objectif=0.01, seuil_finesse=0.08, nb_generations_max=40)

    for [e], [s] in motif:
        plt.plot(e, s, 'o', color='r')

    X = np.arange(-np.pi, np.pi, 0.01)

    Y = [np.sin(x) for x in X]
    plt.plot(X, Y)

    Y = [reseau.evaluer_reseau([x])[0] for x in X]
    plt.plot(X, Y)

    plt.show()


def demo_saut_dobstacles():
    reseau, _, _ = algo_gen_ouvert(Simulation.evaluer, 5, 1, 10000, 30000, nb_individus=150, nb_generations_max=20,
                                   reprendre=False)
    Simulation_graphique.evaluer([reseau])


demo_saut_dobstacles()
# demo_sin()
# demo_xor()
# Simulation_graphique.evaluer([load('Sauvegarde_Ouverte').meilleur_individu])
