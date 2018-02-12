from random import random, randint


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

    def update(self, score):
        global canw, canh
        if self.x + self.w < score:
            self.w = 20  # randint(10, 50)
            self.h = randint(10, 30)
            self.x += canw * (1 + random())
            self.y = canh - self.h

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
        global canh, image
        self.numero = numero
        self.penalite = 0
        self.w, self.h = 50, 50
        self.x, self.y, = 100, canh - self.h
        self.perdu = False

        self.dy = 0
        self.nb_sauts = 0
        self.genome = genome  # le 'cerveau' de la licorne
        self.genome.generer_reseau()

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
            self.penalite += 150

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
                    self.genome.fitness += max(1, score - self.penalite) / 4
                    n -= 1


def move():
    """ délpacement de la licorne"""
    global score, dx, licornes, n, res

    while score < objectif and n > 0:
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


def init_obstacles():
    global liste_obstacles
    liste_obstacles = []
    for i in range(3):
        boxw, boxh = 20, randint(10, 30)
        # boxx, boxy = canw * (random() + 1 + i), canh - boxh
        boxx, boxy = canw * (1 + i), canh - boxh
        liste_obstacles.append(Box(boxx, boxy, boxw, boxh))


def reset():
    global score, genomes, licornes, n, res
    score = 0
    dx = 6
    init_obstacles()
    licornes = [Licorne(genomes[i], i) for i in range(len(genomes))]
    n = len(licornes)
    res = [-1] * n
    move()


"""def evaluer(genome):
    global nb_essais
    s = 0
    for i in range(nb_essais):
        s += evaluer_liste([genome])[0]
    return s/nb_essais"""


def evaluer(gs):
    global genomes
    genomes = gs
    for gen in genomes:
        gen.fitness = 0
    for i in range(4):
        reset()
