from random import random, randint
from tkinter import *


root = Tk()
image = PhotoImage(file="unicorn.png")

# # # Variables d'évaluation
objectif = 40000
nb_essais = 3

# # # Variables de simulation

genomes = None
score = 0
res = []
n = 0
canh, canw = 350, 1000
dt = 50
dx = 6
nb_sauts_max = 3
liste_obstacles = []


class Box:
    def __init__(self, x, y, w, h, color='violet'):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.dessin = can.create_rectangle(x, y, x + w, y + h, fill=color)

    def update(self, score):
        global can, canw, canh
        if self.x + self.w < score:
            self.w = 20  # randint(10, 50)
            self.h = randint(10, 30)
            self.x += canw * (1 + random())
            self.y = canh - self.h

        can.coords(self.dessin, self.x - score, self.y,
                   self.x + self.w - score, self.y + self.h)

    def collide(self, lic):
        """pos relative = self.pos - pos"""
        if (lic.x + lic.w <= self.x  # la licorne est à gauche, au dessus, à droite, (en dessous)
            or lic.y + lic.h <= self.y  # /!\axe y inversé
            or self.x + self.w <= lic.x
                or self.y + self.h <= lic.y):
            return False
        return True


class Licorne:
    def __init__(self, genome, numero):
        global canh, can, image
        self.numero = numero
        self.w, self.h = 50, 50
        self.x, self.y, = 100, canh - self.h
        self.perdu = False

        self.dy = 0
        self.nb_sauts = 0
        self.genome = genome  # le 'cerveau' de la licorne
        self.genome.generer_reseau()

        self.dessin = can.create_image(
            self.x, canh - self.h, anchor=NW, image=image)

    def reponse(self, entrees):
        if not self.perdu:
            return self.genome.evaluer_reseau(entrees)
        return False

    def saut(self):
        global nb_sauts_max
        # La licorne ne peut pas enchainer plus de X sauts sans toucher le sol
        if self.nb_sauts < nb_sauts_max and self.dy >= 0:
            self.nb_sauts += 1
            self.dy += -11

    def update(self, score, dx, pos_rel_obstacles, liste_obstacles):
        global res, n
        if not self.perdu:

            entrees = [dx, self.y] + pos_rel_obstacles

            if self.reponse(entrees)[0]:
                self.saut()

            self.x += dx

            if self.y + self.h > canh:
                self.dy = 0
                self.y = canh - self.h
                self.nb_sauts = 0
            else:
                self.dy += 1   # gravité
            self.y += self.dy

            for obs in liste_obstacles:  # ajout du score aux résultats
                if obs.collide(self):
                    self.perdu = True
                    n -= 1
                    res[self.numero] = score

        can.coords(self.dessin, self.x - score, self.y)


def move():
    """ délpacement de la licorne"""
    global score, dx, licornes, n, res

    pos_rel_obstacles = []
    for obs in liste_obstacles:
        obs.update(score)
        x_relatif = obs.x - score
        if x_relatif < canw:  # l'obsatacle est dans le champ de vision
            pos_rel_obstacles.append(x_relatif)
        else:
            pos_rel_obstacles.append(canw * 2)  # sinon il est 'loin'

    for lic in licornes:
        lic.update(score, dx, pos_rel_obstacles, liste_obstacles)

    score += dx

    if dx < 25:  # vitesse max
        dx = 5 + 0.1 * score ** 0.5

    if n > 0:
        root.after(50, move)
    else:
        for i in range(len(res)):
            if res[i] == -1:
                res[i] = score
        print(res)
        # root.quit()


def init_obstacles():
    global liste_obstacles
    liste_obstacles = []
    for i in range(3):
        boxw, boxh = 20, randint(10, 30)
        # boxx, boxy = canw * (random() + 1 + i), canh - boxh
        boxx, boxy = canw * (1 + i), canh - boxh
        liste_obstacles.append(Box(boxx, boxy, boxw, boxh))


def reset():
    global score, can, genomes, licornes, n, res
    score = 0
    can.delete(ALL)
    dx = 6
    init_obstacles()
    licornes = [Licorne(genomes[i], i) for i in range(len(genomes))]
    n = len(licornes)
    res = [-1] * n
    move()


def evaluer(gs):
    global genomes
    genomes = gs
    root.mainloop()
    reset()


def reset_clavier(event):
    reset()


root.title("azertyuiop")
can = Canvas(root, bg='purple', height=canh, width=canw)
can.pack()

can.focus_set()
can.bind("<r>", reset_clavier)
can.pack()
