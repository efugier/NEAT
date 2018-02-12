from tkinter import *
from random import random, randint


class Box:
    def __init__(self, can, x, y, w, h, color='violet'):
        self.can = can
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.x2 = x + w
        self.y2 = y + h
        self.obj = can.create_rectangle(x, y, self.x2, self.y2, fill=color)

    def redraw(self, newx, newy):
        self.can.coords(self.obj, newx, newy, newx + self.w, newy + self.h)
        if newx < -self.w - 10:
            self.w = randint(10, 50)
            self.h = randint(10, 40)
            self.x += self.can.winfo_width() * (1 + random())
            self.y = self.can.winfo_height() - self.h

    def collide(self):
        """pos relative = self.pos - pos"""
        global x, y, w, h  # uni est gauche, dessus, droite, dessous
        if 100 + w <= self.x - x or y + h <= self.y or self.x + self.w - x <= 100 or self.y + self.h <= y:
            return False
        return True


def move():
    """ délpacement de la licorne"""
    global dt, x, y, h, w, dx, dy, vx, canh, canw, flag, liste_obstacles, nb_sauts, perdu

    if flag > 0:
        x += dx + vx
        y += dy
        if vx < 25:
            vx = 5 + 0.1 * x ** 0.5
        if y > canh - h:
            dy = 0
            dx = vx
            y = canh - h
            nb_sauts = 0
        else:
            dy += 1  # Gravité
            dx -= 0  # 0.2 # frottements

        can.coords(uni, 100, y)
        for obs in liste_obstacles:
            obs.redraw(obs.x - x, obs.y)
            if obs.collide():
                print(x)
                x = 0
                perdu = True
                pause()
        root.after(dt, move)


def pause_clavier(event):
    pause()


def pause():
    """arret/reprise de l'animation"""
    global flag, perdu
    if flag == 0 and not perdu:  # pour ne lancer qu'une seule boucle
        flag = 1
        move()
    else:
        flag = 0


def init_obstacles():
    global liste_obstacles
    for box in liste_obstacles:  # Ménage
        can.delete(box.obj)
    liste_obstacles = []
    for i in range(3):
        boxw, boxh = randint(10, 50), randint(10, 40)
        boxx, boxy = canw * (random() + 1 + i), canh - boxh
        liste_obstacles.append(Box(can, boxx, boxy, boxw, boxh))


def reset(event):
    global dt, x, y, dx, dy, vx, canh, canw, w, h, flag, liste_obstacles, nb_sauts, perdu
    flag = 1
    w, h, = 50, 50
    dt = 50
    x, y, = 100, canh - h
    vx = 6
    dx, dy = vx, 0
    nb_sauts = 0
    perdu = False
    init_obstacles()
    move()


def saut(event):
    global dx, dy, nb_sauts
    if nb_sauts < 3 and dy >= 0:  # La licorne ne peut pas enchainer plus de 5 sauts sans toucher le sol
        nb_sauts += 1
        dx += 0  # 0.87 * 20 # augmentation vitesse horizontale
        dy += -0.5 * 20


flag = 0  # commutateur
canh, canw = 350, 1000
w, h = 50, 50
dt = 50
x, y, = 10, canh - h
vx = 6
dx, dy = vx, 0
nb_sauts = 0
perdu = False

# Création du bazard
root = Tk()
root.title("FlYing UnIcOrn, YoLo")
can = Canvas(root, bg='purple', height=canh, width=canw)
can.pack()

photo = PhotoImage(file="unicorn.png")
uni = can.create_image(100, canh - h, anchor=NW, image=photo)

liste_obstacles = []

can.focus_set()
can.bind("<space>", saut)
can.bind("<p>", pause_clavier)
can.bind("<r>", reset)
can.pack()
init_obstacles()
# Boucle principale
move()
root.mainloop()
