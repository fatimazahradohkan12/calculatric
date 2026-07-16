"""
Calculatrice avec Tkinter - Thème féminin (rose/pastel)
Projet scolaire - OFPPT
"""

import tkinter as tk


class Calculatrice:
    def __init__(self, fenetre):
        self.fenetre = fenetre
        self.fenetre.title("✨ Calculatrice ✨")
        self.fenetre.resizable(False, False)
        self.fenetre.configure(bg="#ffe6f2")

        self.expression = ""
        self.texte_saisie = tk.StringVar()

        self.creer_ecran()
        self.creer_boutons()

    def creer_ecran(self):
        """Crée l'écran d'affichage en haut de la calculatrice"""
        cadre_ecran = tk.Frame(self.fenetre, bg="#ffe6f2")
        cadre_ecran.grid(row=0, column=0, columnspan=4, padx=15, pady=(15, 5), sticky="nsew")

        tk.Label(
            cadre_ecran, text="♡ Calculatrice ♡",
            font=("Segoe UI", 12, "italic"),
            bg="#ffe6f2", fg="#d16ba5"
        ).pack(anchor="w")

        ecran = tk.Entry(
            cadre_ecran,
            textvariable=self.texte_saisie,
            font=("Segoe UI", 26),
            justify="right",
            bd=0,
            relief=tk.FLAT,
            bg="#fff0f7",
            fg="#8e3b6e",
            insertbackground="#d16ba5",
        )
        ecran.pack(fill="x", ipady=15, pady=(5, 0))

    def creer_boutons(self):
        """Crée tous les boutons de la calculatrice (chiffres + opérations)"""
        # Palette pastel : rose poudré, lavande, rose vif pour les actions
        ROSE_CLAIR = "#ffd1e8"
        LAVANDE = "#e5d4f0"
        ROSE_VIF = "#f2789f"
        ROUGE_DOUX = "#f4a6b7"
        VERT_MENTHE = "#a8e6cf"

        boutons = [
            ("C", 1, 0, ROUGE_DOUX, "#7a2e3d"), ("(", 1, 1, LAVANDE, "#5b4b6b"),
            (")", 1, 2, LAVANDE, "#5b4b6b"), ("÷", 1, 3, ROSE_VIF, "white"),

            ("7", 2, 0, ROSE_CLAIR, "#7a2e3d"), ("8", 2, 1, ROSE_CLAIR, "#7a2e3d"),
            ("9", 2, 2, ROSE_CLAIR, "#7a2e3d"), ("×", 2, 3, ROSE_VIF, "white"),

            ("4", 3, 0, ROSE_CLAIR, "#7a2e3d"), ("5", 3, 1, ROSE_CLAIR, "#7a2e3d"),
            ("6", 3, 2, ROSE_CLAIR, "#7a2e3d"), ("−", 3, 3, ROSE_VIF, "white"),

            ("1", 4, 0, ROSE_CLAIR, "#7a2e3d"), ("2", 4, 1, ROSE_CLAIR, "#7a2e3d"),
            ("3", 4, 2, ROSE_CLAIR, "#7a2e3d"), ("+", 4, 3, ROSE_VIF, "white"),

            ("0", 5, 0, ROSE_CLAIR, "#7a2e3d"), (".", 5, 1, ROSE_CLAIR, "#7a2e3d"),
            ("⌫", 5, 2, LAVANDE, "#5b4b6b"), ("=", 5, 3, VERT_MENTHE, "#1f5c4a"),
        ]

        cadre_boutons = tk.Frame(self.fenetre, bg="#ffe6f2")
        cadre_boutons.grid(row=1, column=0, columnspan=4, padx=15, pady=(5, 15))

        for (texte, ligne, colonne, couleur, couleur_texte) in boutons:
            bouton = tk.Button(
                cadre_boutons,
                text=texte,
                font=("Segoe UI", 16, "bold"),
                bg=couleur,
                fg=couleur_texte,
                bd=0,
                relief=tk.FLAT,
                width=5,
                height=2,
                activebackground="#f7b8d2",
                cursor="hand2",
                command=lambda t=texte: self.on_click(t),
            )
            bouton.grid(row=ligne, column=colonne, padx=5, pady=5)

    def on_click(self, valeur):
        """Gère le clic sur un bouton"""
        # On traduit les symboles jolis en symboles compréhensibles par Python
        symboles = {"÷": "/", "×": "*", "−": "-"}

        if valeur == "C":
            self.expression = ""
        elif valeur == "⌫":
            self.expression = self.expression[:-1]
        elif valeur == "=":
            try:
                expression_calculable = self.expression
                for joli, reel in symboles.items():
                    expression_calculable = expression_calculable.replace(joli, reel)
                resultat = str(eval(expression_calculable))
                self.expression = resultat
            except Exception:
                self.expression = "Erreur"
        else:
            self.expression += valeur

        self.texte_saisie.set(self.expression)


if __name__ == "__main__":
    fenetre = tk.Tk()
    app = Calculatrice(fenetre)
    fenetre.mainloop()
