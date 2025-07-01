#QApplication : c'est le moteur de l'appli (vu dans MyApp.py).
#QWidget : c'est la fenêtre de base celle que je vais personnaliser, celle que je vais  customiser.
#QVBoxLayout, QHBoxLayout : permettre d' organiser les éléments verticalement ou horizontalement verticalement ou horizontalement.
#QLabel : pour afficher le texte comme le statut ou la batterie. comme le statut ou la batterie.
#QFrame,QPushButton: pour créer des cadres, des boutons, QFileDialog : pour créer des cadres, des boutons et ouvrir des fichiers.
#QFont : pour choisir la police d'écriture .
#QTimer : pour exécuter le code régulièrement , comme la mise à jour de la batterie.
# Qt est comme une grande boîte de constantes et de réglages pour l'interface graphique.
# QKeyEvent est la classe qui décrit une touche du clavier pressée par l'utilisateur .
import sys
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFrame, QPushButton, QFileDialog)
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtCore import Qt, QTimer

# On s´assure  que controleur_marty.py et interface_graphique.py sont dans le même répertoire
from controleur_marty import ControleurRobotMarty
from interface_graphique import BoutonCommandeStyle, dessiner_fleche
from PyQt6.QtWidgets import QLineEdit

class ApplicationControleMarty(QWidget):
    #PREMIER ELEMENT DU SUJET:UNE FENETRE(je donne un nom a cette fenetre et je lui assigne des dimensions)
    # QWidget est utilise en parametre car je me sers de la fenetre que PyQt6 possede deja pour customer la mienne en fonction des exigences du sujet
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contrôle du Robot Marty")
        # 100 px du bord gauche haut horiz,100 vert,750 larg ecran et 600 hauteur ecran
        self.setGeometry(100, 100, 750, 600)
        # DEUXIEME ELEMENT DU SUJET: MENTION INDIQUANT L´ETAT CONNECTE OU PAS(je vais le faire avec QLabel car c´est la fonctionnalite de PyQt6 dedie pour) 

        self.label_statut_connexion = QLabel("Statut : Initialisation...")
        
        self.label_statut_connexion.setFont(QFont("Arial", 12))
        self.label_statut_connexion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # CINQUIEME ELEMENT DU SUJET= au centre on veut le libelle middle_cmd
        
        self.label_tension_batterie = QLabel("middle_cmd")
        self.label_tension_batterie.setFont(QFont("Arial", 12))
        self.label_tension_batterie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #from PyQt6.QtWidgets import QLineEdit j´ai du l´importer pour creer le champ pour l´adresse IP
        
        #TROISIEME ELEMENT DU SUJET SUR LE CHAMP TEXTE
        self.champ_ip = QLineEdit()
        self.champ_ip.setPlaceholderText("Adresse IP de Marty")
        self.champ_ip.setFixedWidth(200)

        #QUATRIEME ELEMENT DU SUJET:BOUTON CONNECTE SI JE SUIS DECONNECTE
        self.bouton_connexion_ip = QPushButton("Connecter à IP")
        self.bouton_connexion_ip.clicked.connect(self.tenter_connexion_depuis_ui)
        self.bouton_deconnexion_ip = QPushButton("Deconnecter à IP")
        #il va falloir implementer plutard la methode tenter_deconnexion_ui,cele de connexion existe deja


        self.controleur_robot = ControleurRobotMarty(parent_ui=self)

        self.charger_icones()
        self.initialiser_ui()

        main_layout = self.layout()
        if main_layout:
            statut_layout = QHBoxLayout()
            statut_layout.addWidget(self.label_statut_connexion)
            statut_layout.addWidget(self.label_tension_batterie)
            statut_layout.addWidget(QLabel("IP :"))
            statut_layout.addWidget(self.champ_ip)
            statut_layout.addWidget(self.bouton_connexion_ip)

            main_layout.insertLayout(0, statut_layout)
        else:
            main_layout = QVBoxLayout(self)
            statut_layout = QHBoxLayout()
            statut_layout.addWidget(self.label_statut_connexion)
            statut_layout.addWidget(self.label_tension_batterie)
            main_layout.addLayout(statut_layout)
            self.setLayout(main_layout)

        self.timer_batterie = QTimer(self)
        self.timer_batterie.timeout.connect(self.rafraichir_statut_batterie)
        self.timer_batterie.start(5000)

    def mettre_a_jour_statut_connexion(self, texte):
        self.label_statut_connexion.setText(f"Statut : {texte}")
        if "Connecté" in texte:
            self.label_statut_connexion.setStyleSheet("color: green;")
        elif "Déconnecté" in texte or "Échec" in texte or "Erreur" in texte:
            self.label_statut_connexion.setStyleSheet("color: red;")
        else:
            self.label_statut_connexion.setStyleSheet("color: orange;")

    def rafraichir_statut_batterie(self):
        if self.controleur_robot.marty:
            try:
                voltage = self.controleur_robot.marty.get_battery_voltage()
                print(f"Tension de la batterie (get_battery_voltage): {voltage:.1f} V")
                self.label_tension_batterie.setText(f"Batterie : {voltage:.1f} V")
                if voltage < 7.0:
                    self.label_tension_batterie.setStyleSheet("color: red;")
                elif voltage < 8.0:
                    self.label_tension_batterie.setStyleSheet("color: orange;")
                else:
                    self.label_tension_batterie.setStyleSheet("color: black;")

                self.mettre_a_jour_statut_connexion("Connecté")

            except Exception as e:
                print(f"Erreur lors de la lecture de la batterie avec get_battery_voltage(): {e}")
                try:
                    remaining = self.controleur_robot.marty.get_battery_remaining()
                    print(f"Pourcentage de batterie (get_battery_remaining): {remaining:.1f} %")
                    self.label_tension_batterie.setText(f"Batterie : {remaining:.1f} %")
                    if remaining < 20:
                        self.label_tension_batterie.setStyleSheet("color: red;")
                    elif remaining < 50:
                        self.label_tension_batterie.setStyleSheet("color: orange;")
                    else:
                        self.label_tension_batterie.setStyleSheet("color: black;")

                    self.mettre_a_jour_statut_connexion("Connecté")
                except Exception as e2:
                    print(f"Erreur lors de la lecture de la batterie avec get_battery_remaining(): {e2}")
                    self.label_tension_batterie.setText("Batterie : Erreur")
                    self.label_tension_batterie.setStyleSheet("color: red;")
                    self.mettre_a_jour_statut_connexion("Déconnecté (Erreur lecture batterie)")
                    # La reconnexion ici est peut-être trop agressive, ça spammera si le Marty n'est pas là
                    # Il est peut-être préférable de laisser l'utilisateur re-tenter la connexion manuellement
                    # self.controleur_robot.tenter_connexion_marty()
        else:
            self.label_tension_batterie.setText("Batterie : -- V (Marty déconnecté)")
            self.label_tension_batterie.setStyleSheet("color: gray;")
            self.mettre_a_jour_statut_connexion("Déconnecté")

    def tenter_connexion_depuis_ui(self):
        ip = self.champ_ip.text()
        if ip:
            self.controleur_robot.changer_ip_et_reconnecter(ip)
        else:
            self.mettre_a_jour_statut_connexion("IP vide. Veuillez entrer une adresse.")        
 
    def charger_icones(self):
        self.taille_bouton_commune = 150
        self.taille_icone_commune = 100

        self.icones = {
            # Les noms ici correspondent aux arguments de dessiner_fleche
            # et sont logiquement liés aux commandes envoyées.
            "tourner_gauche": dessiner_fleche("tourner_gauche", taille=self.taille_bouton_commune),
            "avancer": dessiner_fleche("haut", taille=self.taille_bouton_commune),
            "tourner_droite": dessiner_fleche("tourner_droite", taille=self.taille_bouton_commune),
            "sidestep_gauche": dessiner_fleche("gauche", taille=self.taille_bouton_commune), # Nommage corrigé pour la cohérence
            "sidestep_droite": dessiner_fleche("droite", taille=self.taille_bouton_commune), # Nommage corrigé
            "reculer": dessiner_fleche("bas", taille=self.taille_bouton_commune),
        }

    def initialiser_ui(self):
        mise_en_page_principale = QVBoxLayout()
        mise_en_page_principale.setContentsMargins(50, 50, 50, 50)
        mise_en_page_principale.setSpacing(20)

        mise_en_page_rangee_superieure = QHBoxLayout()
        mise_en_page_rangee_superieure.setSpacing(20)
        # Boutons de rotation
        self.bouton_tourner_gauche = BoutonCommandeStyle(self.icones["tourner_gauche"], "Tourner Gauche", # Texte affiché
                                                         taille_bouton=self.taille_bouton_commune,
                                                         taille_icone=self.taille_icone_commune)
        self.bouton_avancer = BoutonCommandeStyle(self.icones["avancer"], "Avancer",
                                                   taille_bouton=self.taille_bouton_commune,
                                                   taille_icone=self.taille_icone_commune)
        self.bouton_tourner_droite = BoutonCommandeStyle(self.icones["tourner_droite"], "Tourner Droite", # Texte affiché
                                                          taille_bouton=self.taille_bouton_commune,
                                                          taille_icone=self.taille_icone_commune)
        mise_en_page_rangee_superieure.addWidget(self.bouton_tourner_gauche)
        mise_en_page_rangee_superieure.addWidget(self.bouton_avancer)
        mise_en_page_rangee_superieure.addWidget(self.bouton_tourner_droite)
        mise_en_page_principale.addLayout(mise_en_page_rangee_superieure)

        mise_en_page_rangee_milieu = QHBoxLayout()
        mise_en_page_rangee_milieu.setSpacing(20)
        # Boutons de sidestep
        self.bouton_sidestep_gauche = BoutonCommandeStyle(self.icones["sidestep_gauche"], "Pas de Côté Gauche", # Texte affiché
                                                            taille_bouton=self.taille_bouton_commune,
                                                            taille_icone=self.taille_icone_commune)
        emplacement_centre_rond = QFrame()
        emplacement_centre_rond.setFixedSize(self.taille_bouton_commune, self.taille_bouton_commune)
        emplacement_centre_rond.setStyleSheet(f"""
            background-color: #DDDDDD;
            border-radius: {self.taille_bouton_commune // 2}px;
        """)
        self.bouton_sidestep_droite = BoutonCommandeStyle(self.icones["sidestep_droite"], "Pas de Côté Droite", # Texte affiché
                                                             taille_bouton=self.taille_bouton_commune,
                                                             taille_icone=self.taille_icone_commune)
        mise_en_page_rangee_milieu.addWidget(self.bouton_sidestep_gauche)
        mise_en_page_rangee_milieu.addWidget(emplacement_centre_rond)
        mise_en_page_rangee_milieu.addWidget(self.bouton_sidestep_droite)
        mise_en_page_principale.addLayout(mise_en_page_rangee_milieu)

        mise_en_page_rangee_bas = QHBoxLayout()
        mise_en_page_rangee_bas.setSpacing(20)
        mise_en_page_rangee_bas.addStretch()
        self.bouton_reculer = BoutonCommandeStyle(self.icones["reculer"], "Reculer",
                                                   taille_bouton=self.taille_bouton_commune,
                                                   taille_icone=self.taille_icone_commune)
        mise_en_page_rangee_bas.addWidget(self.bouton_reculer)
        mise_en_page_rangee_bas.addStretch()
        mise_en_page_principale.addLayout(mise_en_page_rangee_bas)

        # --- Boutons de Danse ---
        self.bouton_lancer_danse = QPushButton("Lancer une Danse")
        self.bouton_lancer_danse.setFixedSize(200, 50)
        self.bouton_lancer_danse.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Vert */
                color: white;
                font-size: 16px;
                border-radius: 10px;
                border: 2px solid #45a049;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
                border: 2px solid #337a36;
            }
        """)
        self.bouton_lancer_danse.clicked.connect(self.selectionner_et_lancer_danse)
        mise_en_page_principale.addWidget(self.bouton_lancer_danse, alignment=Qt.AlignmentFlag.AlignCenter)

        self.bouton_arreter_danse = QPushButton("Arrêter la Danse")
        self.bouton_arreter_danse.setFixedSize(200, 50)
        self.bouton_arreter_danse.setStyleSheet("""
            QPushButton {
                background-color: #FF5733; /* Rouge-Orange */
                color: white;
                font-size: 16px;
                border-radius: 10px;
                border: 2px solid #DD3311;
            }
            QPushButton:hover {
                background-color: #DD3311;
            }
            QPushButton:pressed {
                background-color: #CC2200;
                border: 2px solid #AA1100;
            }
        """)
        self.bouton_arreter_danse.clicked.connect(self.controleur_robot.arreter_danse)
        mise_en_page_principale.addWidget(self.bouton_arreter_danse, alignment=Qt.AlignmentFlag.AlignCenter)
        # --- Fin des boutons de Danse ---

        # --- Bouton emotion
        self.bouton_lancer_feel = QPushButton("Lancer Feel")
        self.bouton_lancer_feel.setFixedSize(200, 50)
        self.bouton_lancer_feel.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Vert */
                color: white;
                font-size: 16px;
                border-radius: 10px;
                border: 2px solid #45a049;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
                border: 2px solid #337a36;
            }
        """)
        self.bouton_lancer_feel.clicked.connect(self.selectionner_et_lancer_emotion)
        mise_en_page_principale.addWidget(self.bouton_lancer_feel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(mise_en_page_principale)

        # Connexions des boutons aux commandes du contrôleur
        self.bouton_tourner_gauche.clicked.connect(lambda: self.controleur_robot.envoyer_commande("gauche")) # Commande "gauche" pour rotation gauche
        self.bouton_avancer.clicked.connect(lambda: self.controleur_robot.envoyer_commande("avancer"))
        self.bouton_tourner_droite.clicked.connect(lambda: self.controleur_robot.envoyer_commande("droite")) # Commande "droite" pour rotation droite
        self.bouton_sidestep_gauche.clicked.connect(lambda: self.controleur_robot.envoyer_commande("sidestep_gauche")) # Commande sidestep gauche
        self.bouton_sidestep_droite.clicked.connect(lambda: self.controleur_robot.envoyer_commande("sidestep_droite")) # Commande sidestep droite
        self.bouton_reculer.clicked.connect(lambda: self.controleur_robot.envoyer_commande("reculer"))

    def selectionner_et_lancer_danse(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier .dance et lance la danse."""
        chemin_fichier, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier de danse",
                                                         "", "Fichiers de Danse (*.dance);;Tous les fichiers (*)")
        if chemin_fichier:
            self.controleur_robot.executer_danse_fichier(chemin_fichier)
    
    def selectionner_et_lancer_emotion(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier .feel et lance l'émotion associée."""

        chemin_fichier, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier emotion",
                                                        "", "Fichier Emotion (*.feel);;Tous les fichiers (*)")
        if chemin_fichier:
            if self.controleur_robot.marty:
             self.controleur_robot.executer_emotion_fichier(chemin_fichier)
             self.mettre_a_jour_statut_connexion(f"Émotion exécutée depuis {chemin_fichier.split('/')[-1]}")
            else:
             self.mettre_a_jour_statut_connexion("Marty n'est pas connecté — impossible d'exécuter l'émotion.")


    def keyPressEvent(self, event: QKeyEvent):
        # Utilisation de Qt.Key pour une meilleure lisibilité et compatibilité
        if event.key() == Qt.Key.Key_8:
            self.controleur_robot.envoyer_commande("avancer")
            print("Touche 8 pressée : Avancer")
        elif event.key() == Qt.Key.Key_2:
            self.controleur_robot.envoyer_commande("reculer")
            print("Touche 2 pressée : Reculer")
        elif event.key() == Qt.Key.Key_4:
            self.controleur_robot.envoyer_commande("sidestep_gauche") # <<<<< CORRECTION: Maintenant sidestep
            print("Touche 4 pressée : Pas de côté gauche")
        elif event.key() == Qt.Key.Key_6:
            self.controleur_robot.envoyer_commande("sidestep_droite") # <<<<< CORRECTION: Maintenant sidestep
            print("Touche 6 pressée : Pas de côté droite")
        elif event.key() == Qt.Key.Key_7:
            self.controleur_robot.envoyer_commande("gauche") # <<<<< CORRECTION: Envoie "gauche" pour rotation
            print("Touche 7 pressée : Rotation gauche")
        elif event.key() == Qt.Key.Key_9:
            self.controleur_robot.envoyer_commande("droite") # <<<<< CORRECTION: Envoie "droite" pour rotation
            print("Touche 9 pressée : Rotation droite")
        elif event.key() == Qt.Key.Key_5: # Ajout d'une touche pour STOP
            self.controleur_robot.envoyer_commande("stop")
            print("Touche 5 pressée : STOP")
        elif event.key() == Qt.Key.Key_1: # Ajout d'une touche pour GET_READY
            self.controleur_robot.envoyer_commande("pret")
            print("Touche 1 pressée : GET_READY")
        elif event.key() == Qt.Key.Key_3: # Ajout d'une touche pour STAND_STRAIGHT
            self.controleur_robot.envoyer_commande("repos")
            print("Touche 3 pressée : STAND_STRAIGHT")
        else:
            super().keyPressEvent(event)
    





if __name__ == '__main__':
    app = QApplication(sys.argv)
    fenetre = ApplicationControleMarty()
    fenetre.show()
    sys.exit(app.exec())