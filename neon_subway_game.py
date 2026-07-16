"""
NEON RUNNER - Subway Runner version NEON / FUTURISTE NIGHT CITY
Auteur : généré avec Claude pour Reda (OFPPT)

Meme gameplay que la version classique (3 voies, saut, glisse)
mais avec une toute nouvelle interface : menu, ville de nuit,
grille neon façon Tron, effets de lueur (glow/bloom).

Contrôles :
    Menu       -> HAUT/BAS pour naviguer, ENTREE pour valider
    En jeu     -> FLECHE GAUCHE/DROITE : changer de voie
                  FLECHE HAUT / ESPACE : sauter
                  FLECHE BAS           : glisser
    Game Over  -> R : rejouer | M : menu | ECHAP : quitter

Astuce perso : mets un ou plusieurs fichiers "avatar*.png"
(fond transparent) a cote de ce script pour choisir ton personnage
dans le menu. Sinon, un personnage "filaire neon" par defaut est utilise.
"""

import pygame
import random
import sys
import os
import math
import glob

# ----------------------------------------------------------------------
# CONFIGURATION GENERALE
# ----------------------------------------------------------------------
LARGEUR, HAUTEUR = 480, 720
FPS = 60

NB_VOIES = 3
VOIE_LARGEUR = LARGEUR // NB_VOIES
VOIES_X = [VOIE_LARGEUR * i + VOIE_LARGEUR // 2 for i in range(NB_VOIES)]

SOL_Y = HAUTEUR - 140
HORIZON_Y = 220  # point de fuite de la grille neon (effet Tron)

# --- Palette neon ---
FOND_HAUT   = (8, 6, 20)
FOND_BAS    = (20, 8, 35)
CYAN        = (60, 240, 255)
MAGENTA     = (255, 40, 200)
VIOLET      = (150, 60, 255)
JAUNE_NEON  = (255, 230, 60)
ROUGE_NEON  = (255, 50, 90)
BLANC       = (235, 240, 255)
GRIS_UI     = (140, 150, 190)

GRAVITE = 1.1
FORCE_SAUT = -18


# ----------------------------------------------------------------------
# OUTILS DE RENDU NEON (glow / bloom)
# ----------------------------------------------------------------------
def surface_bloom(surface_source, intensite=170, reduction=6):
    """Cree un effet de lueur (bloom) en floutant une version reduite de la surface."""
    w, h = surface_source.get_size()
    petite = pygame.transform.smoothscale(surface_source, (max(1, w // reduction), max(1, h // reduction)))
    flou = pygame.transform.smoothscale(petite, (w, h))
    flou.set_alpha(intensite)
    return flou


def texte_neon(ecran, texte, police, centre, couleur, couleur_lueur=None, intensite=26):
    """Dessine un texte avec une aura lumineuse autour (effet neon)."""
    if couleur_lueur is None:
        couleur_lueur = couleur

    base_lueur = police.render(texte, True, couleur_lueur)
    rect = base_lueur.get_rect(center=centre)

    halo = pygame.Surface((rect.width + 60, rect.height + 60), pygame.SRCALPHA)
    base_lueur.set_alpha(intensite)
    for decalage in (6, 4, 2):
        for dx, dy in ((-decalage, 0), (decalage, 0), (0, -decalage), (0, decalage),
                       (-decalage, -decalage), (decalage, decalage), (-decalage, decalage), (decalage, -decalage)):
            halo.blit(base_lueur, (30 + dx, 30 + dy))

    ecran.blit(halo, (rect.x - 30, rect.y - 30), special_flags=pygame.BLEND_RGBA_ADD)
    texte_final = police.render(texte, True, couleur)
    ecran.blit(texte_final, rect)
    return rect


def ligne_neon(surface, couleur, p1, p2, largeur=3):
    pygame.draw.line(surface, couleur, p1, p2, largeur)


# ----------------------------------------------------------------------
# JOUEUR
# ----------------------------------------------------------------------
class Joueur:
    def __init__(self, image=None, couleur_neon=CYAN):
        self.voie = 1
        self.x = VOIES_X[self.voie]
        self.y = SOL_Y
        self.vitesse_y = 0
        self.en_saut = False
        self.en_glisse = False
        self.timer_glisse = 0
        self.largeur = 46
        self.hauteur = 84
        self.anim_jambe = 0
        self.image = image
        self.couleur_neon = couleur_neon  # couleur de l'aura autour du perso

    def changer_voie(self, direction):
        nouvelle_voie = self.voie + direction
        if 0 <= nouvelle_voie < NB_VOIES:
            self.voie = nouvelle_voie

    def sauter(self):
        if not self.en_saut and not self.en_glisse:
            self.en_saut = True
            self.vitesse_y = FORCE_SAUT

    def glisser(self):
        if not self.en_saut:
            self.en_glisse = True
            self.timer_glisse = 25

    def maj(self):
        cible_x = VOIES_X[self.voie]
        self.x += (cible_x - self.x) * 0.28

        if self.en_saut:
            self.y += self.vitesse_y
            self.vitesse_y += GRAVITE
            if self.y >= SOL_Y:
                self.y = SOL_Y
                self.en_saut = False
                self.vitesse_y = 0

        if self.en_glisse:
            self.timer_glisse -= 1
            if self.timer_glisse <= 0:
                self.en_glisse = False

        self.anim_jambe += 1

    def get_rect(self):
        if self.en_glisse:
            return pygame.Rect(self.x - self.largeur // 2, self.y - 38, self.largeur, 38)
        return pygame.Rect(self.x - self.largeur // 2, self.y - self.hauteur, self.largeur, self.hauteur)

    def dessiner(self, calque_glow, ecran):
        x, y = int(self.x), int(self.y)

        # --- Halo au sol sous le perso (toujours present, ambiance neon) ---
        halo_sol = pygame.Surface((120, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(halo_sol, (*self.couleur_neon, 90), (0, 0, 120, 40))
        calque_glow.blit(halo_sol, (x - 60, y - 20))

        # --- Avatar image ---
        if self.image is not None:
            if self.en_glisse:
                lw, lh = int(self.largeur * 1.7), int(self.hauteur * 0.45)
            else:
                variation = 1 + 0.04 * ((self.anim_jambe // 6) % 2)
                lw, lh = int(self.largeur * variation), self.hauteur

            img_redim = pygame.transform.smoothscale(self.image, (lw, lh))

            # silhouette neon derriere l'image pour l'effet de contour lumineux
            silhouette = pygame.mask.from_surface(img_redim).to_surface(
                setcolor=(*self.couleur_neon, 200), unsetcolor=(0, 0, 0, 0)
            )
            silhouette = pygame.transform.smoothscale(silhouette, (lw + 14, lh + 14))
            rect_s = silhouette.get_rect(midbottom=(x, y + 4))
            calque_glow.blit(silhouette, rect_s)

            rect_img = img_redim.get_rect(midbottom=(x, y))
            ecran.blit(img_redim, rect_img)
            return

        # --- Personnage filaire neon par defaut (style Tron) ---
        c = self.couleur_neon
        if self.en_glisse:
            ligne_neon(calque_glow, c, (x - 26, y - 30), (x + 30, y - 18), 6)
            pygame.draw.circle(calque_glow, c, (x + 34, y - 24), 10, 3)
        else:
            haut_y = y - self.hauteur
            decalage = 10 if (self.anim_jambe // 6) % 2 == 0 else -10
            if self.en_saut:
                decalage = 0
            # jambes
            ligne_neon(calque_glow, c, (x - 6, y - 30), (x - 6 + decalage, y), 5)
            ligne_neon(calque_glow, c, (x + 6, y - 30), (x + 6 - decalage, y), 5)
            # corps
            ligne_neon(calque_glow, c, (x, haut_y + 18), (x, y - 28), 5)
            # bras
            ligne_neon(calque_glow, c, (x, haut_y + 30), (x - 22 - decalage // 2, haut_y + 55), 4)
            ligne_neon(calque_glow, c, (x, haut_y + 30), (x + 22 + decalage // 2, haut_y + 55), 4)
            # tete
            pygame.draw.circle(calque_glow, c, (x, haut_y + 8), 13, 3)


# ----------------------------------------------------------------------
# OBSTACLES
# ----------------------------------------------------------------------
class Obstacle:
    def __init__(self, voie, type_obstacle, z):
        self.voie = voie
        self.type = type_obstacle
        self.z = z

    def maj(self, vitesse):
        self.z -= vitesse

    def hors_ecran(self):
        return self.z < -50

    def get_pos_taille(self):
        echelle = max(0.15, 1 - self.z / 900)
        x = VOIES_X[self.voie]
        y = SOL_Y - (self.z * 0.02)
        return x, y, echelle

    def get_rect(self):
        x, y, echelle = self.get_pos_taille()
        if self.type == "bas":
            largeur, hauteur = 55 * echelle, 55 * echelle
            return pygame.Rect(x - largeur / 2, y - hauteur, largeur, hauteur)
        largeur, hauteur = 70 * echelle, 40 * echelle
        return pygame.Rect(x - largeur / 2, y - 120 * echelle, largeur, hauteur)

    def dessiner(self, calque_glow, ecran):
        x, y, echelle = self.get_pos_taille()
        if echelle < 0.15:
            return
        if self.type == "bas":
            taille = 55 * echelle
            rect = (x - taille / 2, y - taille, taille, taille)
            pygame.draw.rect(calque_glow, MAGENTA, rect, border_radius=4)
            pygame.draw.rect(ecran, MAGENTA, rect, 3, border_radius=4)
            pygame.draw.rect(ecran, BLANC, rect, 1, border_radius=4)
        else:
            largeur = 90 * echelle
            haut = y - 130 * echelle
            barre = (x - largeur / 2, haut, largeur, 20 * echelle)
            pygame.draw.rect(calque_glow, CYAN, barre)
            pygame.draw.rect(ecran, CYAN, barre, 2)
            poteau_g = (x - largeur / 2, haut, 8 * echelle, 130 * echelle)
            poteau_d = (x + largeur / 2 - 8 * echelle, haut, 8 * echelle, 130 * echelle)
            pygame.draw.rect(ecran, CYAN, poteau_g)
            pygame.draw.rect(ecran, CYAN, poteau_d)


# ----------------------------------------------------------------------
# VILLE DE NUIT EN ARRIERE PLAN
# ----------------------------------------------------------------------
class VilleNuit:
    def __init__(self):
        self.batiments = []
        random.seed(42)
        x = -20
        while x < LARGEUR + 20:
            largeur_b = random.randint(35, 70)
            hauteur_b = random.randint(80, 200)
            couleur = random.choice([(20, 15, 45), (25, 18, 55), (15, 12, 35)])
            self.batiments.append([x, largeur_b, hauteur_b, couleur])
            x += largeur_b + random.randint(4, 14)
        random.seed()

    def dessiner(self, ecran):
        for (x, largeur_b, hauteur_b, couleur) in self.batiments:
            haut_y = HORIZON_Y - hauteur_b
            pygame.draw.rect(ecran, couleur, (x, haut_y, largeur_b, hauteur_b + 20))
            # fenetres allumees aleatoires (fixe par position pour ne pas clignoter)
            random.seed(int(x) * 7)
            for wy in range(int(haut_y) + 10, HORIZON_Y - 6, 14):
                for wx in range(int(x) + 6, int(x) + largeur_b - 6, 12):
                    if random.random() < 0.35:
                        c = random.choice([CYAN, MAGENTA, JAUNE_NEON])
                        ecran.fill(c, (wx, wy, 4, 6))
            random.seed()


# ----------------------------------------------------------------------
# JEU PRINCIPAL
# ----------------------------------------------------------------------
class Jeu:
    ETAT_MENU = "menu"
    ETAT_SELECTION = "selection"
    ETAT_JEU = "jeu"
    ETAT_GAMEOVER = "gameover"

    def __init__(self):
        pygame.init()
        self.ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
        pygame.display.set_caption("NEON RUNNER")
        self.horloge = pygame.time.Clock()

        self.police_titre = pygame.font.SysFont("arial", 46, bold=True)
        self.police_grande = pygame.font.SysFont("arial", 30, bold=True)
        self.police_moyenne = pygame.font.SysFont("arial", 22, bold=True)
        self.police_petite = pygame.font.SysFont("arial", 16)

        self.ville = VilleNuit()
        self.temps = 0.0

        # --- Recherche des avatars disponibles (avatar*.png a cote du script) ---
        dossier_script = os.path.dirname(os.path.abspath(__file__))
        chemins_avatars = sorted(glob.glob(os.path.join(dossier_script, "avatar*.png")))
        self.avatars = []  # liste de (nom_affiche, surface_image ou None)
        for chemin in chemins_avatars:
            try:
                img = pygame.image.load(chemin).convert_alpha()
                nom = os.path.splitext(os.path.basename(chemin))[0].replace("_", " ").upper()
                self.avatars.append((nom, img))
            except pygame.error:
                pass
        # Option "filaire neon" toujours disponible en dernier
        self.avatars.append(("NEON WIREFRAME", None))
        self.index_avatar = 0
        self.couleurs_avatar = [CYAN, MAGENTA, VIOLET, JAUNE_NEON]

        self.etat = self.ETAT_MENU
        self.index_menu = 0
        self.options_menu = ["JOUER", "PERSONNAGE", "QUITTER"]

        self.reinitialiser_partie()

    # ------------------------------------------------------------------
    def reinitialiser_partie(self):
        nom, image = self.avatars[self.index_avatar]
        couleur = self.couleurs_avatar[self.index_avatar % len(self.couleurs_avatar)]
        self.joueur = Joueur(image=image, couleur_neon=couleur)
        self.obstacles = []
        self.vitesse = 8
        self.distance = 0
        self.timer_spawn = 0
        self.rail_offset = 0

    # ------------------------------------------------------------------
    def gerer_evenements(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.etat in (self.ETAT_JEU, self.ETAT_SELECTION):
                        self.etat = self.ETAT_MENU
                    else:
                        pygame.quit()
                        sys.exit()
                    continue

                if self.etat == self.ETAT_MENU:
                    self.gerer_menu(event)
                elif self.etat == self.ETAT_SELECTION:
                    self.gerer_selection(event)
                elif self.etat == self.ETAT_JEU:
                    self.gerer_jeu(event)
                elif self.etat == self.ETAT_GAMEOVER:
                    self.gerer_gameover(event)

    def gerer_menu(self, event):
        if event.key == pygame.K_UP:
            self.index_menu = (self.index_menu - 1) % len(self.options_menu)
        elif event.key == pygame.K_DOWN:
            self.index_menu = (self.index_menu + 1) % len(self.options_menu)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            choix = self.options_menu[self.index_menu]
            if choix == "JOUER":
                self.reinitialiser_partie()
                self.etat = self.ETAT_JEU
            elif choix == "PERSONNAGE":
                self.etat = self.ETAT_SELECTION
            elif choix == "QUITTER":
                pygame.quit()
                sys.exit()

    def gerer_selection(self, event):
        if event.key == pygame.K_LEFT:
            self.index_avatar = (self.index_avatar - 1) % len(self.avatars)
        elif event.key == pygame.K_RIGHT:
            self.index_avatar = (self.index_avatar + 1) % len(self.avatars)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.etat = self.ETAT_MENU

    def gerer_jeu(self, event):
        if event.key == pygame.K_LEFT:
            self.joueur.changer_voie(-1)
        elif event.key == pygame.K_RIGHT:
            self.joueur.changer_voie(1)
        elif event.key in (pygame.K_UP, pygame.K_SPACE):
            self.joueur.sauter()
        elif event.key == pygame.K_DOWN:
            self.joueur.glisser()

    def gerer_gameover(self, event):
        if event.key == pygame.K_r:
            self.reinitialiser_partie()
            self.etat = self.ETAT_JEU
        elif event.key == pygame.K_m:
            self.etat = self.ETAT_MENU

    # ------------------------------------------------------------------
    def spawn_obstacle(self):
        voie = random.randint(0, NB_VOIES - 1)
        type_obstacle = random.choice(["bas", "haut"])
        self.obstacles.append(Obstacle(voie, type_obstacle, 900))

    def maj(self, dt):
        self.temps += dt
        if self.etat != self.ETAT_JEU:
            return

        self.joueur.maj()
        self.rail_offset = (self.rail_offset + self.vitesse) % 40

        self.timer_spawn -= 1
        if self.timer_spawn <= 0:
            self.spawn_obstacle()
            self.timer_spawn = random.randint(35, 60)

        for obs in self.obstacles:
            obs.maj(self.vitesse)
        self.obstacles = [o for o in self.obstacles if not o.hors_ecran()]

        rect_joueur = self.joueur.get_rect()
        for obs in self.obstacles:
            if 100 < obs.z < 220 and obs.voie == self.joueur.voie:
                if rect_joueur.colliderect(obs.get_rect()):
                    if obs.type == "bas" and not self.joueur.en_saut:
                        self.etat = self.ETAT_GAMEOVER
                    elif obs.type == "haut" and not self.joueur.en_glisse:
                        self.etat = self.ETAT_GAMEOVER

        self.distance += self.vitesse * 0.1
        self.vitesse = min(20, 8 + self.distance / 150)

    # ------------------------------------------------------------------
    def dessiner_fond_degrade(self):
        for i in range(HAUTEUR):
            t = i / HAUTEUR
            couleur = [int(FOND_HAUT[c] + (FOND_BAS[c] - FOND_HAUT[c]) * t) for c in range(3)]
            pygame.draw.line(self.ecran, couleur, (0, i), (LARGEUR, i))

    def dessiner_grille_sol(self, calque_glow):
        # Lignes qui convergent vers l'horizon (effet perspective Tron)
        for i in range(-NB_VOIES, NB_VOIES + 1):
            x_bas = LARGEUR // 2 + i * VOIE_LARGEUR
            x_haut = LARGEUR // 2 + i * (VOIE_LARGEUR * 0.12)
            ligne_neon(calque_glow, VIOLET, (x_haut, HORIZON_Y), (x_bas, HAUTEUR), 2)
            pygame.draw.line(self.ecran, (90, 40, 160), (x_haut, HORIZON_Y), (x_bas, HAUTEUR), 1)

        # Lignes horizontales defilantes
        decalage = self.rail_offset
        for k in range(14):
            t = (k * 40 + decalage) / (14 * 40)
            if t <= 0:
                continue
            y = HORIZON_Y + t * t * (HAUTEUR - HORIZON_Y)
            largeur_ligne = 1 + t * 2
            couleur = (90, 40, 160)
            pygame.draw.line(self.ecran, couleur, (0, y), (LARGEUR, y), max(1, int(largeur_ligne)))

    def dessiner_ui(self):
        texte_neon(self.ecran, f"{int(self.distance)}", self.police_grande, (78, 40), CYAN, CYAN, 30)
        label = self.police_petite.render("SCORE", True, GRIS_UI)
        self.ecran.blit(label, (48, 62))

        # barre de vitesse neon
        barre_x, barre_y, barre_w, barre_h = LARGEUR - 150, 25, 120, 14
        pygame.draw.rect(self.ecran, (40, 30, 60), (barre_x, barre_y, barre_w, barre_h), border_radius=7)
        ratio = (self.vitesse - 8) / (20 - 8)
        pygame.draw.rect(self.ecran, MAGENTA, (barre_x, barre_y, int(barre_w * max(0, min(1, ratio))), barre_h), border_radius=7)
        pygame.draw.rect(self.ecran, BLANC, (barre_x, barre_y, barre_w, barre_h), 1, border_radius=7)
        vlabel = self.police_petite.render("VITESSE", True, GRIS_UI)
        self.ecran.blit(vlabel, (barre_x, barre_y + 18))

    def dessiner_jeu(self):
        self.dessiner_fond_degrade()
        self.ville.dessiner(self.ecran)

        calque_glow = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        self.dessiner_grille_sol(calque_glow)

        for obs in sorted(self.obstacles, key=lambda o: -o.z):
            obs.dessiner(calque_glow, self.ecran)
        self.joueur.dessiner(calque_glow, self.ecran)

        bloom = surface_bloom(calque_glow, intensite=200, reduction=5)
        self.ecran.blit(bloom, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.ecran.blit(calque_glow, (0, 0))

        self.dessiner_ui()

        if self.etat == self.ETAT_GAMEOVER:
            overlay = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            overlay.fill((5, 0, 15, 190))
            self.ecran.blit(overlay, (0, 0))
            texte_neon(self.ecran, "GAME OVER", self.police_titre, (LARGEUR // 2, HAUTEUR // 2 - 70), ROUGE_NEON, ROUGE_NEON, 34)
            texte_neon(self.ecran, f"SCORE : {int(self.distance)}", self.police_grande, (LARGEUR // 2, HAUTEUR // 2), BLANC, CYAN, 20)
            self._texte_simple("R : REJOUER    M : MENU", self.police_moyenne, (LARGEUR // 2, HAUTEUR // 2 + 60), JAUNE_NEON)

    def dessiner_menu(self):
        self.dessiner_fond_degrade()
        self.ville.dessiner(self.ecran)
        calque_glow = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        self.dessiner_grille_sol(calque_glow)
        bloom = surface_bloom(calque_glow, intensite=160, reduction=5)
        self.ecran.blit(bloom, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.ecran.blit(calque_glow, (0, 0))

        overlay = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        overlay.fill((5, 0, 15, 120))
        self.ecran.blit(overlay, (0, 0))

        pulse = 20 + int(10 * abs(math.sin(self.temps * 2)))
        texte_neon(self.ecran, "NEON RUNNER", self.police_titre, (LARGEUR // 2, 170), CYAN, MAGENTA, pulse)
        self._texte_simple("NIGHT CITY EDITION", self.police_petite, (LARGEUR // 2, 215), GRIS_UI)

        for i, option in enumerate(self.options_menu):
            y = 340 + i * 60
            selectionne = (i == self.index_menu)
            couleur = JAUNE_NEON if selectionne else BLANC
            couleur_lueur = JAUNE_NEON if selectionne else CYAN
            intensite = 34 if selectionne else 16
            prefixe = "> " if selectionne else "  "
            texte_neon(self.ecran, prefixe + option, self.police_grande, (LARGEUR // 2, y), couleur, couleur_lueur, intensite)

        self._texte_simple("HAUT/BAS : naviguer     ENTREE : valider", self.police_petite, (LARGEUR // 2, HAUTEUR - 40), GRIS_UI)

    def dessiner_selection(self):
        self.dessiner_fond_degrade()
        self.ville.dessiner(self.ecran)

        overlay = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        overlay.fill((5, 0, 15, 140))
        self.ecran.blit(overlay, (0, 0))

        texte_neon(self.ecran, "CHOISIS TON PERSO", self.police_grande, (LARGEUR // 2, 90), CYAN, CYAN, 26)

        nom, image = self.avatars[self.index_avatar]
        couleur = self.couleurs_avatar[self.index_avatar % len(self.couleurs_avatar)]

        calque_glow = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        aperçu = Joueur(image=image, couleur_neon=couleur)
        aperçu.x, aperçu.y = LARGEUR // 2, HAUTEUR // 2 + 120
        aperçu.dessiner(calque_glow, self.ecran)
        bloom = surface_bloom(calque_glow, intensite=200, reduction=5)
        self.ecran.blit(bloom, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.ecran.blit(calque_glow, (0, 0))

        texte_neon(self.ecran, nom, self.police_moyenne, (LARGEUR // 2, HAUTEUR // 2 + 200), BLANC, couleur, 22)
        self._texte_simple(f"< {self.index_avatar + 1} / {len(self.avatars)} >", self.police_petite, (LARGEUR // 2, HAUTEUR // 2 + 230), GRIS_UI)
        self._texte_simple("FLECHES : changer     ENTREE : valider     ECHAP : retour", self.police_petite, (LARGEUR // 2, HAUTEUR - 40), GRIS_UI)

    def _texte_simple(self, texte, police, centre, couleur):
        surf = police.render(texte, True, couleur)
        self.ecran.blit(surf, surf.get_rect(center=centre))

    def dessiner(self):
        if self.etat == self.ETAT_MENU:
            self.dessiner_menu()
        elif self.etat == self.ETAT_SELECTION:
            self.dessiner_selection()
        else:
            self.dessiner_jeu()
        pygame.display.flip()

    def lancer(self):
        while True:
            dt = self.horloge.tick(FPS) / 1000.0
            self.gerer_evenements()
            self.maj(dt)
            self.dessiner()


if __name__ == "__main__":
    jeu = Jeu()
    jeu.lancer()
