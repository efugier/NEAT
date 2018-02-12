from copy import copy
from pickle import Pickler, Unpickler
import random as rd
import numpy as np

# # # PARAMETRES D'EVOLUTION

chance_de_mutation = 0.8
chance_perturbation = 0.9

chance_ajout_neurone = 0.05

chance_ajout_connexion = 0.1  # 0.05
chance_connexion_recursive = 0  # 0.005

chance_transmettre_desactiv = 0.75

seuil_mm_espece = 2
c1, c2 = 1, 0.4  # distance = 1/N*(c1*Disjoints) + c2*dif_ moyenne_poids

stagnation_espece_max = 13
stagnation_globale_max = 20

entr, pds, sort, inno = 0, 1, 2, 3
# Gene = quadruplet [n° entrée, poids, n°sortie, n° d'innovation]
# Convention: gene désactivé si son n°sortie est < 0, gene récursif si n°entree < 0

val, conn = 0, 1


# Neurone = [valeur, connexion liste [(entree, poids)]]

# # Je n'ai pas fait des objets pour des raisons de rapidité


# # # OBJETS

class BassinGenetique(object):
    """La classe englobant tout"""

    def __init__(self, nb_entrees=2, nb_sorties=1, nb_individus=150, nb_neurones_max=30):
        self.nb_entrees = nb_entrees
        self.nb_sorties = nb_sorties
        self.nb_neurones_max = nb_neurones_max

        self.stagnation = 0
        self.nb_generation = 0

        self.meilleur_individu = None
        self.fitness_max = -1

        self.innovations = nb_entrees * nb_sorties - \
            1  # On numérote les génes à partir de 0

        self.nb_individus = nb_individus
        self.population = []
        self.especes = []

        # Liste des génes de l'actuelle géneration, pour ne pas mélanger les innovations
        self.nouveaux_genes = []

    def nouvelle_generation(self, fct_eval, finesse):

        self.nouveaux_genes = []
        nouvelle_population = []
        nouvelles_especes = []

        self.nb_generation += 1

        self.generer_especes()

        fitness, meill_genome = self.get_meilleur_fit_genome(fct_eval)

        if fitness > self.fitness_max:
            self.fitness_max = fitness
            self.meilleur_individu = meill_genome

        nouvelle_population.append(copy(self.meilleur_individu))

        # Plus une espèce compte pour beaucoup dans ce nombre, plus elle aura de descendants
        potentiel_total = 0

        for esp in self.especes:

            espece_eteinte = False

            if not esp.genomes:  # Un espèce réduite à un seul représentant n'est pas autorisée à se reproduire
                nouvelle_population.append(esp.representant)
                self.especes.remove(esp)
            else:
                fct_eval(esp.genomes)  # Evaluation des individus de l'espèce
                esp.trier()  # Trie les genomes de l'espèce par fitness décroissante

                if esp.genomes[0].fitness > esp.representant.fitness:
                    # Chaque espèce est représentée par son meilleur élément de la generation précédente
                    if esp.genomes[0].fitness > 1.01 * esp.representant.fitness:
                        esp.stagnation = 0
                    esp.representant = copy(esp.genomes[0])

                else:
                    esp.stagnation += 1
                    if esp.stagnation > stagnation_espece_max:  # Si l'espèce n'évolue plus, elle est éliminée
                        self.especes.remove(esp)
                        # Le meilleur individu survit quand même
                        nouvelle_population.append(esp.representant)
                        espece_eteinte = True

                if not espece_eteinte:
                    esp.potentiel = esp.representant.fitness * \
                        (1 - esp.stagnation / stagnation_espece_max)

                    nouvelles_especes.append(esp)
                    potentiel_total += esp.potentiel

        self.especes = nouvelles_especes

        nb_indivs_deja_presents = len(nouvelle_population)
        if potentiel_total:
            for esp in self.especes:
                # Plus un espèce est prometteuse, plus elle engendre d'individus
                n = int(esp.potentiel / potentiel_total *
                        (self.nb_individus - nb_indivs_deja_presents))
                # On garde eventuellement une place pour le meilleur individu
                n -= (len(esp.genomes) > 5)
                # On ne reproduit pas les individus les plus faibles (ne vaut que pour les espèces nombreuses)
                if len(esp.genomes) > 3:
                    esp.genomes = esp.genomes[:len(esp.genomes) // 2]

                # un quart des nouveaux sont issus de mutation directe
                for _ in range(int(n / 4)):
                    genome = rd.choice(esp.genomes)
                    muter(genome, finesse)
                    nouvelle_population.append(genome)

                # un autre quart de croisements de génomes aléatoires
                for _ in range(int(n / 4), int(n / 2)):
                    if len(esp.genomes) > 2:
                        genome1, genome2 = rd.sample(esp.genomes, 2)
                        fils = croiser(genome1, genome2)
                    else:
                        fils = copy(rd.choice(esp.genomes))
                    muter(fils, finesse)
                    nouvelle_population.append(fils)

                # La moitié restante issue de croisements de génomes qui se suivent par ordre de fitness
                l = len(esp.genomes)
                for i in range(n - int(n / 2)):
                    fils = croiser(
                        esp.genomes[i % l], esp.genomes[(i + 1) % l])
                    muter(fils, finesse)
                    nouvelle_population.append(fils)

                if len(esp.genomes) > 5:
                    # Le représentant survit inchangé
                    nouvelle_population.append(copy(esp.representant))
                else:
                    esp.genomes = []

        # On complète eventuellement
        for _ in range(self.nb_individus - len(nouvelle_population)):
            nouvelle_population.append(genome_simple(self))

        self.population = nouvelle_population

    def generer_especes(self):
        """Genère les espèces à partir des représentants et de la population"""

        for genome in self.population:
            ok = False  # Faux tant que le génome n'est pas rangé
            for esp in self.especes:
                _, _, distance = get_match_disj_distance(
                    genome, esp.representant)
                if distance <= seuil_mm_espece:
                    esp.genomes.append(genome)
                    ok = True
                    break
            if not ok:  # Si le genome ne rentre dans aucune espèce, il devient le représentant d'une nouvelle
                esp = Espece()
                esp.representant = genome
                esp.genomes.append(genome)
                self.especes.append(esp)

    def trier_especes(self):
        # -eval_genome(esp.representant))
        self.especes.sort(key=lambda esp: -esp.potentiel)

    def get_meilleur_fit_genome(self, fct_eval):
        """Renvoie une copie du meilleur individu et sa fitness"""
        fit_max, meill_genome = 0, None
        representants = [esp.representant for esp in self.especes]
        fct_eval(representants)
        for indiv in representants:
            fitness = indiv.fitness
            if fitness > fit_max:
                fit_max, meill_genome = fitness, indiv

        return fit_max, copy(meill_genome)

    def set_innovation_gene(self, gene, genome):
        ok = False
        for entree, _, sortie, innovation in self.nouveaux_genes:
            if gene[entr] == entree and abs(gene[sort]) == abs(sortie):
                gene[inno] = innovation
                ok = True
                break

        if not ok:
            self.innovations += 1
            gene[inno] = self.innovations

            self.nouveaux_genes.append(gene)

        genome.innovation_max = max(gene[inno], genome.innovation_max)


class Espece(object):
    def __init__(self):
        self.stagnation = 0  # Nombre de générations consécutives où l'espèce n'a pas évolué
        self.representant = None  # Meilleur genome de l'espèce
        self.potentiel = 0  # Combinaison de différents facteurs,
        # Plus une espèce a du potentiel, plus elle a de chances d'évoluer
        # ici il est défini par fitness * (1 - stagnation/stagnation-max)

        self.genomes = []

    def trier(self):
        """trie les individus par fitness DECROISSANTE"""
        self.genomes.sort(key=lambda g: -g.fitness)


class Genome(object):
    def __init__(self, bg=BassinGenetique()):
        self.bg = bg

        self.nb_entrees = bg.nb_entrees
        self.nb_sorties = bg.nb_sorties
        self.nb_neurones_max = bg.nb_neurones_max

        self.fitness = 0
        self.innovation_max = 0
        self.neurone_max = bg.nb_entrees + bg.nb_sorties - 1  # indice du dernier neurone

        self.reseau = {}  # neurone
        # Les genes sont des triplets (n° entree, poids, n°sortie)
        self.genes = []
        self.genes_recursifs = []

    def set_neur_inn_max(self):
        inn_max, neur_max = 0, 0
        for entree, _, sortie, innovation in self.genes:
            if neur_max < entree:
                neur_max = entree
            if neur_max < abs(sortie):
                neur_max = abs(sortie)
            if inn_max < innovation:
                inn_max = innovation

        self.innovation_max = max(self.innovation_max, inn_max)
        self.neurone_max = max(self.neurone_max, neur_max)

    def generer_reseau(self):
        self.reseau = {}

        for e in range(self.nb_entrees):
            self.reseau[e] = [0, []]
        for s in range(self.nb_entrees, self.nb_entrees + self.nb_sorties):
            self.reseau[s] = [0, []]

        for entree, poids, sortie, _ in self.genes:
            if entree not in self.reseau:  # verification d'existence des neurones
                self.reseau[entree] = [0, []]
            if sortie not in self.reseau and sortie > 0:
                self.reseau[sortie] = [0, []]

            if sortie > 0:  # Si la connexion est active, on l'ajoute
                self.reseau[sortie][conn].append(
                    (entree, poids))  # ajout des connexions

    def evaluer_reseau(self, entrees):

        deja_evalues = {}  # Dictionnaires ayant pour clefs les neurones déjà évalués

        for e in range(self.nb_entrees):
            deja_evalues[e] = 0
            self.reseau[e][val] += entrees[e]

        res = []

        # On évalue chaque neurone de sortie
        for s in range(self.nb_entrees, self.nb_entrees + self.nb_sorties):
            res.append(self.evaluer(s, deja_evalues))

        for entree, poids, sortie, _ in self.genes_recursifs:  # Stockage des valeurs récursives
            # /!\ Espquive de bug, à corriger !
            if sortie in deja_evalues and abs(entree) in self.reseau:
                deja_evalues[sortie] += poids * self.reseau[abs(entree)][val]

        for key in self.reseau:  # Reset du réseau
            self.reseau[key][val] = 0

        for entree, poids, sortie, _ in self.genes_recursifs:  # Application des connexions récursives
            # /!\ Espquive de bug, à corriger !
            if sortie in self.reseau and abs(entree) in deja_evalues:
                self.reseau[sortie][val] += poids * deja_evalues[abs(entree)]

        return res

    def evaluer(self, num_neurone, deja_evalues):
        """Evalue la valeur du neurone"""
        if num_neurone in deja_evalues:
            return self.reseau[num_neurone][val]

        # On évalue chaque neurone entrant
        for entree, poids in self.reseau[num_neurone][conn]:
            self.reseau[num_neurone][val] += poids * \
                self.evaluer(entree, deja_evalues)

        self.reseau[num_neurone][val] = phi(self.reseau[num_neurone][val])
        deja_evalues[num_neurone] = 0  # On marque le neurone comme évalué

        return self.reseau[num_neurone][val]

    def est_necessaire_a_evaluation(self, neurone1, neurone2):

        for entree, _ in self.reseau[neurone2][conn]:
            if entree == neurone1 or self.est_necessaire_a_evaluation(neurone1, entree):
                return True

        return False

    # def est_necessaire_a_evaluation(self, neurone1, neurone2):

    #     for entree, _ in self.reseau[neurone2][conn]:
    #         if not self.est_necessaire_a_evaluation(neurone1, entree):
    #             return False

    #     return True

    def est_recursif(self, gene):
        self.generer_reseau()
        return self.est_necessaire_a_evaluation(gene[sort], gene[entr])

    def contient_connexion(self, gene):
        for g in self.genes:
            if gene[entr] == g[entr] and gene[sort] == g[sort]:
                return True

        for g in self.genes_recursifs:
            if gene[entr] == g[entr] and gene[sort] == g[sort]:
                return True

        return False

    def __copy__(self):
        nouveau_genome = Genome()
        nouveau_genome.bg = self.bg

        nouveau_genome.nb_entrees = self.nb_entrees
        nouveau_genome.nb_sorties = self.nb_sorties

        nouveau_genome.nb_neurones_max = self.nb_neurones_max

        nouveau_genome.innovation_max = self.innovation_max
        nouveau_genome.neurone_max = self.neurone_max

        nouveau_genome.fitness = self.fitness

        nouveau_genome.genes = [copy(gene) for gene in self.genes]
        nouveau_genome.genes_recursifs = [
            copy(gene) for gene in self.genes_recursifs]

        nouveau_genome.generer_reseau()

        return nouveau_genome


# # # FONCTIONS


def phi(x):
    """Fonction d'activation"""
    return np.tanh(x)


def uniforme(borne=3.0):
    """renvoie un nombre choisi entre -borne et +borne"""
    return borne * (2 * rd.random() - 1)


def genome_simple(bg):
    """un genome dont toutes les entrées sont connectées aux sorties"""
    genome = Genome(bg)
    inn = -1
    for e in range(genome.nb_entrees):
        for s in range(genome.nb_entrees, genome.nb_entrees + genome.nb_sorties):
            inn += 1
            genome.genes.append([e, uniforme(), s, inn])
    genome.generer_reseau()
    return genome


def init_population(bg, nb_individus):
    bg.nb_generation = 0
    bg.population = [genome_simple(bg) for _ in range(nb_individus)]


def get_match_disj_distance(genome1: Genome, genome2: Genome):
    """renvoie les genes présents dans les deux génomes, les autres, et la distances entre les génomes"""
    match = []  # gènes présents dans le deux génomes
    disj = []  # gènes uniques
    innov_max = max(genome1.innovation_max, genome2.innovation_max)

    genes1 = sorted(genome1.genes + genome2.genes_recursifs,
                    key=lambda g: g[inno])
    genes2 = sorted(genome2.genes + genome2.genes_recursifs,
                    key=lambda g: g[inno])

    i = 0
    j1, j2 = 0, 0  # Curseurs des listes
    while i <= innov_max and genes1 and genes2:  # On a forcément moins de genes que d'innovation max
        if genes1[j1][inno] == i and genes2[j2][inno] == i:
            match.append((copy(genes1[j1]), (copy(genes2[j2]))))
            if j1 < len(genes1) - 1:
                j1 += 1
            if j2 < len(genes2) - 1:
                j2 += 1
        elif genes1[j1][inno] == i:
            disj.append((copy(genes1[j1]), []))
            if j1 < len(genes1) - 1:
                j1 += 1
        elif genes2[j2][inno] == i:
            disj.append(([], copy(genes2[j2])))
            if j2 < len(genes2) - 1:
                j2 += 1

        i += 1

    w = 0  # Calcul de la différence moyenne de poids
    for g1, g2 in match:
        w += abs(g1[pds] - g2[pds])
    w = abs(w / len(match))

    distance = c1 * len(disj) / max(len(genes1), len(genes2)) + c2 * w

    return match, disj, distance


def croiser(genome1: Genome, genome2: Genome):
    match, disj, _ = get_match_disj_distance(genome1, genome2)

    indice_meilleur = 0  # Numéro du meilleur parent
    if genome2.fitness > genome1.fitness:
        indice_meilleur = 1

    fils = Genome(bg=genome1.bg)
    nouveaux_genes = []
    for paire in match:  # Ajout aléatoire du gène de l'un des parents
        # On choisit au hasard le parent qui transmettra le gene en commun
        r = rd.randint(0, 1)
        # and rd.random() < chance_transmettre_desactiv:  # Gene désactivé
        if paire[0][sort] < 0 and paire[1][sort] < 0:
            paire[r][sort] = -abs(paire[r][sort])
        nouveaux_genes.append(paire[r])

    for paire in disj:
        if paire[indice_meilleur]:
            # Ajout les caractères uniques du meilleur parent
            nouveaux_genes.append(paire[indice_meilleur])

    for gene in nouveaux_genes:  # On sépare les gènes récursifs
        if gene[entr] < 0:
            fils.genes_recursifs.append(gene)
        else:
            fils.genes.append(gene)

    fils.set_neur_inn_max()
    fils.generer_reseau()

    return fils


# # Mutations structurelles

def muter_ajout_neurone(genome: Genome):
    """Ajoute un neurone au milieu d'une connexion existante: o-o => o-o-o
    Attention il faut impérativement re-générer le réseau avant d'utiliser le genome"""

    if rd.random() < chance_ajout_neurone and genome.neurone_max < genome.nb_neurones_max:
        gene = rd.choice(genome.genes)

        genome.neurone_max += 1  # nouveau neurone

        gene1 = [gene[entr], 1, genome.neurone_max, 0]
        genome.bg.set_innovation_gene(gene1, genome)

        gene2 = [genome.neurone_max, gene[pds], gene[sort], 0]
        genome.bg.set_innovation_gene(gene2, genome)

        genome.genes.append(gene1)
        genome.genes.append(gene2)

        gene[sort] = -abs(gene[sort])  # Désactivation de l'ancien gène


def muter_ajout_connexion(genome: Genome):
    """Ajoute une connexion entre deux neurones non encore reliés: o o => o-o"""

    if rd.random() < chance_ajout_connexion:
        nums_neurones = list(genome.reseau.keys())
        n1, n2 = rd.sample(nums_neurones, 2)

        # On verifie que la bonne orientation est n1 -> n2
        if genome.est_necessaire_a_evaluation(n2, n1):
            n1, n2 = n2, n1

        if rd.random() < chance_connexion_recursive:  # connexion récursive
            gene = [-1 * n2, uniforme(), n1, 0]
            if not genome.contient_connexion(gene):
                genome.bg.set_innovation_gene(gene, genome)
                genome.genes_recursifs.append(gene)

        elif genome.nb_entrees <= n2 != n1:  # Pas faire de connexion recursive, ni relier 2 neurones d'entrée
            gene = [n1, uniforme(), n2, 0]
            if not genome.contient_connexion(gene):
                genome.bg.set_innovation_gene(gene, genome)
                genome.genes.append(gene)


# # Autres


def muter_poids(genome, finesse=False):
    if rd.random() < chance_de_mutation:
        if not finesse:
            for gene in genome.genes:
                if rd.random() < chance_perturbation:
                    gene[pds] += uniforme(1)
                else:
                    gene[pds] = uniforme()
        else:
            gene = rd.choice(genome.genes)
            if rd.random() < chance_perturbation:
                gene[pds] += uniforme()
            else:
                gene[pds] = uniforme()


def muter(genome: Genome, finesse=False):
    """Effectue l'ensemble des mutations possibles sur un génome,
    seuls des petits ajustements sont effectués si finesse est vrai"""

    if not finesse:
        # mutations topologiques (pas fines)
        muter_ajout_connexion(genome)
        muter_ajout_neurone(genome)
    muter_poids(genome, finesse)

    genome.generer_reseau()


# Algo genetique


def algo_gen_motif(motif, objectif=0.1, seuil_finesse=0.15, nb_individus=150, eval_fct=None, nb_generations_max=125):
    gen = 0
    flag = True
    nb_entrees = max([len(m[0]) for m in motif])
    nb_sorties = max([len(m[1]) for m in motif])
    bg = BassinGenetique(nb_entrees=nb_entrees,
                         nb_sorties=nb_sorties, nb_individus=nb_individus)
    init_population(bg, nb_individus)
    fitness_max = -1
    meilleur_genome = None
    finesse = False

    if not eval_fct:
        def fct_eval(genome_liste, mot=motif):
            for genome in genome_liste:
                fitness = 0
                for entree, sortie in mot:
                    reponse = genome.evaluer_reseau(entree)[0]
                    fitness += 1 - min(1, abs(sortie - reponse))
                genome.fitness = fitness
    else:
        fct_eval = eval_fct

    while flag:

        gen += 1

        bg.nouvelle_generation(fct_eval, finesse)
        fit_actuelle, meill_genome = bg.fitness_max, bg.meilleur_individu

        if fit_actuelle > 1 * bg.fitness_max:  # Un progrès remet la stagnation à 0
            bg.stagnation = 0
        else:
            bg.stagnation += 1
            if bg.stagnation > stagnation_globale_max:  # On recentre la recherche lorsque l'évolution stagne
                print("\nRecentrage de la recherche aux deux meilleurs espèces")
                bg.stagnation = 0
                if len(bg.especes) > 2:
                    bg.trier_especes()
                    bg.especes = bg.especes[:2]
        if fit_actuelle > fitness_max:
            print("\nAmélioration ! +", fit_actuelle - fitness_max)
            print("-> ", fit_actuelle, ", generation n°", gen)

            fitness_max, meilleur_genome = fit_actuelle, meill_genome
            save(bg, "Sauvegarde_motif")

        if not finesse and erreur(meilleur_genome, motif) < seuil_finesse:
            print("\nAjustement en finessee\n")
            finesse = True

        if gen % 30 == 0:  # Affichage de la progression toutes les k generations
            print("generation n°", gen)
            print("Nombre d'espèces: ", len(bg.especes))
            print("fitness actuelle: ", fit_actuelle)
            print(meill_genome.reseau)
            afficher_reponse(motif, meill_genome)

        if erreur(meilleur_genome, motif) < objectif or gen > nb_generations_max:
            print("\n\nFIN, GENERATION n°", gen)
            print("Fitness: ", fitness_max)
            print("Genome: ", meilleur_genome.genes)
            print("Connexions récursives: ", meilleur_genome.genes_recursifs)
            print("Réseau: ", meilleur_genome.reseau)
            afficher_reponse(motif, meilleur_genome)

            return meilleur_genome, fitness_max, gen


def algo_gen_ouvert(fct_eval, nb_entrees, nb_sorties, objectif, seuil_finesse, nb_individus=150, nb_generations_max=125, reprendre=False):
    """fct_eval(liste_de_genomes) met à jour la fitness des genomes"""
    gen = 0
    flag = True
    finesse = False

    if reprendre:
        bg = load('Sauvegarde_Ouverte')
        fitness_max = bg.fitness_max
        meilleur_genome = bg.meilleur_individu

    else:
        bg = BassinGenetique(nb_entrees=nb_entrees,
                             nb_sorties=nb_sorties, nb_individus=nb_individus)
        init_population(bg, nb_individus)
        fitness_max = -1
        meilleur_genome = None

    while flag:

        gen += 1

        bg.nouvelle_generation(fct_eval, finesse)
        fit_actuelle, meill_genome = bg.fitness_max, bg.meilleur_individu

        if fit_actuelle > 1 * bg.fitness_max:  # Un progrès remet la stagnation à 0
            bg.stagnation = 0
        else:
            bg.stagnation += 1
            if bg.stagnation > stagnation_globale_max:  # On recentre la recherche lorsque l'évolution stagne
                print("\nRecentrage de la recherche aux deux meilleurs espèces")
                bg.stagnation = 0
                if len(bg.especes) > 2:
                    bg.trier_especes()
                    bg.especes = bg.especes[:2]
        if fit_actuelle > fitness_max:
            print("\nAmélioration ! +", fit_actuelle - fitness_max)
            print("-> ", fit_actuelle, ", generation n°", gen)

            fitness_max, meilleur_genome = fit_actuelle, meill_genome
            save(bg, "Sauvegarde_Ouverte")

        if not finesse and fitness_max > seuil_finesse:
            print("\nAjustement en finessee\n")
            finesse = True

        if gen % 2 == 0:  # Affichage de la progression toutes les k generations
            print("generation n°", gen)
            print("Nombre d'espèces: ", len(bg.especes))
            print("fitness actuelle: ", fit_actuelle)
            print(meill_genome.reseau)

        if fitness_max > objectif or gen > nb_generations_max:
            print("\n\nFIN, GENERATION n°", gen)
            print("Fitness: ", fitness_max)
            print("Genome: ", meilleur_genome.genes)
            print("Connexions récursives: ", meilleur_genome.genes_recursifs)
            print("Réseau: ", meilleur_genome.reseau)

            return meilleur_genome, fitness_max, gen


def simplifier_genome(genome):
    """Arrondi au centième les poids du genome pour en faciliter la lecture"""
    nouveaux_genes = []
    for gene in genome.genes:
        gene[pds] = round(gene[pds], 2)
        if gene[sort] > 0:
            nouveaux_genes.append(gene)
    genome.genes = nouveaux_genes
    genome.generer_reseau()


def erreur(genome, motif):
    """renvoie l'erreur max"""
    err = 0
    for entree, sortie in motif:
        e = abs(sortie - genome.evaluer_reseau(entree)[0])
        if e > err:
            err = e
    return err


def afficher_reponse(motif, genome):
    for entree, _ in motif:
        print(entree, " --> ", genome.evaluer_reseau(entree))


# Utilitaires

def save(obj, nom_fichier='Sauvegarde'):
    with open(nom_fichier, 'wb') as fichier:
        pickler = Pickler(fichier)
        pickler.dump(obj)

    print("Sauvegarde effectuée dans ", nom_fichier)


def load(nom_fichier='Sauvegarde'):
    with open(nom_fichier, 'rb') as fichier:
        unpickler = Unpickler(fichier)
        obj = unpickler.load()
    return obj
