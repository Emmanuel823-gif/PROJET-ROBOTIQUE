# marty_controller.py
from martypy import Marty
import time
from PyQt6.QtWidgets import QMessageBox
from config import Ipaddress 
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer 
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from ReadSequence import DanceFileParser # Importe la classe depuis ReadSequence.py
from calibrage_couleur import couleurs_mesurees
import math

def couleur_proche_capteur(r, g, b):
    def distance(c1, c2):
        return math.sqrt(sum((e1 - e2) ** 2 for e1, e2 in zip(c1, c2)))

    couleur_min = None
    dist_min = float('inf')

    for nom, (r_ref, g_ref, b_ref) in couleurs_mesurees.items():
        d = distance((r, g, b), (r_ref, g_ref, b_ref))
        if d < dist_min:
            dist_min = d
            couleur_min = nom

    return couleur_min

class DanceWorker(QObject):
    """
    Worker pour exécuter la danse dans un thread séparé afin de ne pas bloquer l'UI.
    """
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    dance_finished = pyqtSignal() # Ce signal indique que la méthode run du worker est terminée.

    def __init__(self, marty_instance, dance_file_path, base_move_time_for_dance_unit=1500, delay_between_commands_ms=300):
        super().__init__()
        self.marty = marty_instance
        self.dance_file_path = dance_file_path
        self._stop_requested = False # Drapeau pour demander l'arrêt de la danse de manière coopérative.
        
        self.base_move_time_for_dance_unit = base_move_time_for_dance_unit 
        self.delay_between_commands_s = delay_between_commands_ms / 1000.0
        
        try:
            self.dance_parser = DanceFileParser(move_time_per_dance_unit=self.base_move_time_for_dance_unit)
            print(f"DanceWorker créé pour {self.dance_file_path}. Thread parent: {QThread.currentThread().objectName()}")
        except Exception as e:
            print(f"Erreur lors de l'initialisation de DanceFileParser : {e}")
            raise 

    def request_stop(self):
        """Demande au worker d'arrêter l'exécution de la danse."""
        print(f"DanceWorker.request_stop() - Signal d'arrêt reçu par DanceWorker dans le thread {QThread.currentThread().objectName()}.")
        self._stop_requested = True

    def run(self):
        """
        Méthode principale exécutée dans le thread séparé pour piloter Marty.
        Exécute les commandes de danse parsées sur l'instance de Marty.
        """
        self.thread().setObjectName("DanceWorkerThread")
        print(f"DanceWorker.run() - Démarré dans le thread : {QThread.currentThread().objectName()} pour {self.dance_file_path}")

        if not self.marty:
            self.error_occurred.emit("Marty n'est pas connecté pour exécuter la danse.")
            self.dance_finished.emit()
            print("DanceWorker.run() - Marty non connecté, fin de l'exécution.")
            return

        commands = []
        try:
            # Appelle le parseur externe pour obtenir les commandes
            # Utilise _stop_requested pour le drapeau d'interruption
            commands = self.dance_parser.parse_dance_file(
                self.dance_file_path,
                is_running_flag=lambda: not self._stop_requested,
                status_callback=self.status_updated.emit,
                error_callback=self.error_occurred.emit
            )
        except Exception as e:
            self.error_occurred.emit(f"Erreur critique lors du parsing du fichier de danse : {e}")
            self.dance_finished.emit()
            print(f"DanceWorker.run() - Erreur de parsing : {e}, fin de l'exécution.")
            return

        if not commands:
            self.status_updated.emit("Aucune commande à exécuter ou erreur de parsing. (Vérifiez le fichier .dance)")
            self.dance_finished.emit()
            print("DanceWorker.run() - Aucune commande ou erreur de parsing, fin de l'exécution.")
            return

        self.status_updated.emit(f"Exécution de la danse '{self.dance_file_path}'...")
        
        print("DanceWorker.run() - Ajout d'une petite pause (0.5s) avant le premier mouvement pour stabilisation de Marty.")
        time.sleep(0.5) 

        for i, cmd in enumerate(commands):
            if self._stop_requested: # Vérifie si un arrêt a été demandé
                self.status_updated.emit("Danse interrompue par l'utilisateur.")
                print("DanceWorker.run() - Interruption demandée, arrêt de l'exécution.")
                break

            action = cmd.get("action")
            steps = cmd.get("steps") 
            move_time = cmd.get("move_time")
            original_quantity = cmd.get("original_quantity", 0) 

            # Vérifications des paramètres essentiels
            if not isinstance(move_time, (int, float)) or move_time <= 0:
                self.error_occurred.emit(f"Erreur: 'move_time' invalide pour l'action '{action}' à la ligne {i+1}. Valeur: {move_time}")
                self.status_updated.emit("Danse interrompue (Erreur de temps)")
                print(f"DanceWorker.run() - Erreur: 'move_time' invalide pour action '{action}', arrêt.")
                # Arrête Marty en cas d'erreur critique
                if self.marty: self.marty.stop()
                break

            if not isinstance(steps, (int)) or steps is None:
                self.error_occurred.emit(f"Erreur : Le nombre de pas physiques est manquant ou invalide pour l'action '{action}' à la ligne {i+1}. Valeur: {steps}")
                self.status_updated.emit("Danse interrompue (Données manquantes)")
                print(f"DanceWorker.run() - Erreur : 'steps' est None ou non entier pour l'action '{action}', arrêt.")
                if self.marty: self.marty.stop()
                break
            
            steps = int(steps) 

            self.status_updated.emit(f"Exécution : {action} {original_quantity} unité(s) ({steps} pas physiques) en {move_time}ms ({i+1}/{len(commands)})")

            try:
                if action == "walk":
                    step_length = cmd.get("step_length", 15) 
                    if not isinstance(step_length, (int, float)):
                         self.error_occurred.emit(f"Erreur: 'step_length' invalide pour l'action '{action}' à la ligne {i+1}.")
                         self.status_updated.emit("Danse interrompue (Erreur de longueur de pas)")
                         print(f"DanceWorker.run() - Erreur: 'step_length' invalide pour action '{action}', arrêt.")
                         if self.marty: self.marty.stop()
                         break
                    self.marty.walk(num_steps=steps, step_length=step_length, move_time=move_time)
                elif action == "sidestep":
                    side = cmd.get("side")
                    if side not in ["left", "right"]:
                         self.error_occurred.emit(f"Erreur: 'side' invalide pour l'action 'sidestep' à la ligne {i+1}.")
                         self.status_updated.emit("Danse interrompue (Erreur de côté)")
                         print(f"DanceWorker.run() - Erreur: 'side' invalide pour action 'sidestep', arrêt.")
                         if self.marty: self.marty.stop()
                         break
                    self.marty.sidestep(side=side, steps=steps, move_time=move_time)
                else:
                    self.error_occurred.emit(f"Action inconnue '{action}' à la ligne {i+1}.")
                    self.status_updated.emit("Danse interrompue (Action inconnue)")
                    print(f"DanceWorker.run() - Action inconnue '{action}', arrêt.")
                    if self.marty: self.marty.stop()
                    break
                
                if self.delay_between_commands_s > 0 and not self._stop_requested: # Vérifie le drapeau avant le délai aussi
                    time.sleep(self.delay_between_commands_s) 

            except Exception as e:
                self.error_occurred.emit(f"Erreur lors de l'exécution de '{action}' par Marty : {e}")
                self.status_updated.emit("Danse interrompue (Erreur Marty)")
                print(f"DanceWorker.run() - Erreur lors de l'exécution de '{action}' : {e}, arrêt.")
                if self.marty: self.marty.stop()
                break
        
        # S'assurer que Marty est arrêté après la danse ou en cas d'interruption
        if self.marty:
            try:
                self.marty.stop() 
                print("Marty arrêté.")
            except Exception as e:
                print(f"Erreur lors de l'arrêt de Marty: {e}")

        self.status_updated.emit("Danse terminée.")
        self.dance_finished.emit() # Émet le signal pour indiquer la fin du travail du worker.
        print(f"DanceWorker.run() - Danse terminée, signal 'dance_finished' émis. Thread : {QThread.currentThread().objectName()}")


class ControleurRobotMarty(QObject):
    # si tu veux detecter une couleur,emotion ,faire une action avec une certaine vitesse,il faut ajouter la suite mettre les instru,chercher
    # def envoyer_commande_avec_vitesse(self, commande: str, delai_ms: int):
    # self.envoyer_commande(commande)  # commande existante, déjà gérée
    # time.sleep(delai_ms / 1000)  # temporisation avant autre action (ou prochaine étape)

    def __init__(self, parent_ui=None):
        super().__init__()
        self.marty = None
        self.parent_ui = parent_ui
        self.dance_thread = None 
        self.dance_worker = None
        self.tenter_connexion_marty()
        print("ControleurRobotMarty initialisé.")

    def tenter_connexion_marty(self):
        print("Tentative de connexion à Marty...")
        if self.parent_ui:
            self.parent_ui.mettre_a_jour_statut_connexion("Connexion en cours...")
        
        try:
            self.marty = Marty('wifi', Ipaddress) 
            if self.parent_ui:
                self.parent_ui.mettre_a_jour_statut_connexion("Connecté")
        except Exception as e:
            print(f"Échec de la connexion à Marty : {e}")
            if self.parent_ui:
                QMessageBox.critical(self.parent_ui, "Échec de Connexion",
                                     f"Impossible de se connecter à Marty. Veuillez vérifier l'adresse IP et la connexion Wi-Fi.\nErreur : {e}")
                self.parent_ui.mettre_a_jour_statut_connexion("Déconnecté (Échec connexion)")
            self.marty = None 

    def changer_ip_et_reconnecter(self, nouvelle_ip):
      if self.parent_ui:
        self.parent_ui.mettre_a_jour_statut_connexion(f"Tentative de connexion à {nouvelle_ip}...")
      try:
        self.marty = Marty('wifi', nouvelle_ip)
        print(f"Connexion réussie à l'IP : {nouvelle_ip}")
        if self.parent_ui:
            self.parent_ui.mettre_a_jour_statut_connexion(f"Connecté à {nouvelle_ip}")
      except Exception as e:
        print(f"Erreur de connexion à {nouvelle_ip} :", e)
        if self.parent_ui:
            self.parent_ui.mettre_a_jour_statut_connexion(f"Échec de connexion : {e}")
            QMessageBox.critical(self.parent_ui, "Échec de Connexion",
                                 f"Impossible de se connecter à Marty à l'adresse {nouvelle_ip}.\nErreur : {e}")
        self.marty = None

    def envoyer_commande(self, commande):
        if not self.marty:
            print("Marty n'est pas initialisé. Tentative de reconnexion.")
            if self.parent_ui:
                QMessageBox.warning(self.parent_ui, "Marty Déconnecté",
                                    "Le robot Marty n'est pas connecté. Veuillez vérifier la connexion ou l'adresse IP.")
            self.tenter_connexion_marty()
            if not self.marty:
                return

        # Si une danse est en cours, ne pas envoyer de commande directe pour éviter les conflits
        if self.dance_thread and self.dance_thread.isRunning():
            self.parent_ui.mettre_a_jour_statut_connexion("Une danse est en cours. Commandes directes désactivées.")
            print("Commande directe ignorée car une danse est en cours.")
            return

        print(f"Envoi de la commande à Marty : {commande}")
        try:
            if commande == "avancer":
                self.marty.walk(num_steps=1, step_length=15) 
            elif commande == "reculer":
                self.marty.walk(num_steps=1, step_length=-25)
            elif commande == "tourner_gauche":
                self.marty.walk(turn=15) 
            elif commande == "tourner_droite":
                self.marty.walk(turn=-15) 
            elif commande == "gauche":
                self.marty.walk(turn=15)
                self.marty.walk(num_steps=1)
                self.marty.walk(turn=15)
                self.marty.walk(num_steps=1)
            elif commande == "droite":
                self.marty.walk(turn=-15)
                self.marty.walk(num_steps=1)
                self.marty.walk(turn=-15)
                self.marty.walk(num_steps=1)
            
            if self.parent_ui:
                self.parent_ui.mettre_a_jour_statut_connexion("Connecté")

        except Exception as e:
            print(f"Erreur lors de l'envoi de la commande '{commande}' : {e}")
            if self.parent_ui:
                QMessageBox.warning(self.parent_ui, "Erreur Commande Marty",
                                    f"Une erreur est survenue lors de l'envoi de la commande '{commande}'.\nErreur : {e}")
            self.tenter_connexion_marty()


    def executer_danse_fichier(self, chemin_fichier_danse):
        """
        Lance l'exécution d'une danse à partir d'un fichier .dance dans un thread séparé.
        Crée de nouvelles instances de QThread et DanceWorker à chaque appel.
        """
        print("\n--- 'executer_danse_fichier()' appelé. ---")
        
        if self.dance_thread and self.dance_thread.isRunning():
            self.parent_ui.mettre_a_jour_statut_connexion("Une danse est déjà en cours. Veuillez l'arrêter avant d'en lancer une nouvelle.")
            print("executer_danse_fichier() - Danse déjà en cours, annulation du lancement.")
            return
        
        # Si un thread existe mais n'est pas en cours d'exécution, on suppose qu'il a terminé
        # et on peut le nettoyer avant de créer un nouveau thread.
        # Ceci est important pour éviter des threads zombies ou des objets orphelins.
        elif self.dance_thread: 
            print("executer_danse_fichier() - L'ancien thread de danse n'était pas en cours. Nettoyage avant de relancer.")
            # Déconnecter le signal finished de l'ancien thread avant de le nettoyer
            try:
                self.dance_thread.finished.disconnect(self._cleanup_dance_thread)
            except (TypeError, RuntimeError, AttributeError):
                pass # Already disconnected or invalid, which is fine
            
            self._cleanup_dance_thread_immediate() # Nettoyage direct car nous allons en recréer un
            
        if not self.marty:
            self.parent_ui.mettre_a_jour_statut_connexion("Marty non connecté. Impossible de lancer la danse.")
            self.tenter_connexion_marty() 
            if not self.marty: 
                print("executer_danse_fichier() - Marty non connecté après la tentative, annulation.")
                return

        self.parent_ui.mettre_a_jour_statut_connexion(f"Préparation de la danse : {chemin_fichier_danse}...")
        print("executer_danse_fichier() - Création de nouveaux thread et worker.")
        
        try:
            self.dance_thread = QThread()
            self.dance_worker = DanceWorker(self.marty, chemin_fichier_danse, 
                                            base_move_time_for_dance_unit=1500, 
                                            delay_between_commands_ms=300) # Revert delay to 300ms as per initial code
            
            self.dance_worker.moveToThread(self.dance_thread)

            # Connexions des signaux
            self.dance_worker.status_updated.connect(self.parent_ui.mettre_a_jour_statut_connexion)
            self.dance_worker.error_occurred.connect(lambda msg: QMessageBox.warning(self.parent_ui, "Erreur de Danse", msg))
            
            # Quand le worker a fini son travail (run() est terminé), le thread doit quitter.
            self.dance_worker.dance_finished.connect(self.dance_thread.quit)
            
            # Quand le thread a quitté (quit() est appelé), on nettoie les ressources.
            self.dance_thread.finished.connect(self._cleanup_dance_thread_final) 
            
            # Démarrage du thread et exécution de la méthode run du worker
            self.dance_thread.started.connect(self.dance_worker.run) 
            self.dance_thread.start() 
            self.parent_ui.mettre_a_jour_statut_connexion("Danse lancée.")
            print(f"executer_danse_fichier() - Thread démarré. ID du thread : {self.dance_thread.currentThreadId()}")
        
        except Exception as e:
            error_msg = f"Erreur critique lors du lancement de la danse : {e}\nVotre application va tenter de continuer."
            print(error_msg)
            if self.parent_ui:
                QMessageBox.critical(self.parent_ui, "Erreur de Lancement de Danse", error_msg)
            # Tenter un nettoyage même en cas d'erreur de lancement.
            # Pas besoin d'attendre ici, on se contente de déconnecter et deleteLater
            self._cleanup_dance_thread_immediate()
            self.parent_ui.mettre_a_jour_statut_connexion("Échec du lancement de la danse.")



    def executer_emotion_fichier(self, chemin_fichier):
        
        donnees = []
        with open(chemin_fichier, "r", errors="ignore") as f: #ignore les espaces entre les lignes du fichier real.feels
            for ligne in f:
                elements = ligne.strip().split(";")
                if len(elements) == 3:
                    couleur, emotion, code_hex = elements
                    donnees.append({
                        "couleur": couleur,
                        "emotion": emotion,
                        "code_hex": code_hex
                        })
        if not self.marty:
            print("Marty n'est pas initialisé. Tentative de reconnexion.")
            if self.parent_ui:
                QMessageBox.warning(self.parent_ui, "Marty Déconnecté",
                                "Le robot Marty n'est pas connecté. Veuillez vérifier la connexion ou l'adresse IP.")
            self.tenter_connexion_marty()
            if not self.marty:
                return
        r = self.marty.get_color_sensor_value_by_channel('LeftColorSensor', channel='red')
        g = self.marty.get_color_sensor_value_by_channel('LeftColorSensor', channel='green')
        b = self.marty.get_color_sensor_value_by_channel('LeftColorSensor', channel='blue')


        couleur_detectee = couleur_proche_capteur(r, g, b)
        for entree in donnees:
            if entree["couleur"].lower() == couleur_detectee.lower():
                emotion = entree["emotion"]
                code_hex = entree["code_hex"]
                self.marty.eyes(pose_or_angle= emotion)
                self.marty.disco_color(color= code_hex)
                #voici...si tu veux ajouter des actions specifiques a des couleurs detectees
                #if couleur_detectee == "red":
                 #self.envoyer_commande_avec_vitesse("avancer", 150)
                #elif couleur_detectee == "blue":
                 #self.envoyer_commande_avec_vitesse("reculer", 350)
                #elif couleur_detectee == "yellow":
                # self.envoyer_commande_avec_vitesse("gauche", 250)

                return emotion, code_hex
        
        return None
        

    def _cleanup_dance_thread_immediate(self):
        """
        Nettoie immédiatement les références du thread et du worker, sans attendre la fin du thread.
        Utilisé avant de recréer un nouveau thread.
        """
        print(f"_cleanup_dance_thread_immediate() appelé. Thread de danse actuel : {self.dance_thread}, worker : {self.dance_worker}")

        if self.dance_worker:
            try: 
                # Déconnecte explicitement tous les signaux
                self.dance_worker.status_updated.disconnect(self.parent_ui.mettre_a_jour_statut_connexion) 
            except (TypeError, RuntimeError, AttributeError): 
                pass
            try: 
                self.dance_worker.error_occurred.disconnect() 
            except (TypeError, RuntimeError, AttributeError): 
                pass
            try:
                self.dance_worker.dance_finished.disconnect(self.dance_thread.quit)
            except (TypeError, RuntimeError, AttributeError):
                pass
            
            print("Marquage de 'dance_worker' pour suppression immédiate.")
            self.dance_worker.deleteLater()
            self.dance_worker = None 

        if self.dance_thread:
            # S'assurer que le signal finished du thread est déconnecté de cette méthode
            try:
                self.dance_thread.finished.disconnect(self._cleanup_dance_thread_final)
            except (TypeError, RuntimeError, AttributeError):
                pass
            
            # Si le thread est toujours en cours d'exécution, demander à le quitter ou le terminer
            if self.dance_thread.isRunning():
                print("_cleanup_dance_thread_immediate() - Thread est toujours en cours, demande d'arrêt (quit).")
                self.dance_thread.quit()
                if not self.dance_thread.wait(500): # Attendre un court instant
                    print("_cleanup_dance_thread_immediate() - Le thread ne s'est pas terminé, terminaison forcée.")
                    self.dance_thread.terminate()
                    self.dance_thread.wait(100)
            
            print("Marquage de 'dance_thread' pour suppression immédiate.")
            self.dance_thread.deleteLater()
            self.dance_thread = None 
        
        print("Nettoyage immédiat terminé. 'dance_thread' et 'dance_worker' sont maintenant à None.")


    def _cleanup_dance_thread_final(self):
        """
        Nettoie les références du thread et du worker de danse.
        Cette méthode est appelée UNIQUEMENT lorsque le thread a émis son signal 'finished'.
        """
        print(f"_cleanup_dance_thread_final() appelé (via finished signal). Thread de danse actuel : {self.dance_thread}, worker : {self.dance_worker}")

        if self.dance_worker:
            try: 
                # Déconnecte explicitement tous les signaux
                self.dance_worker.status_updated.disconnect(self.parent_ui.mettre_a_jour_statut_connexion) 
            except (TypeError, RuntimeError, AttributeError): 
                pass
            try: 
                self.dance_worker.error_occurred.disconnect() 
            except (TypeError, RuntimeError, AttributeError): 
                pass
            try:
                self.dance_worker.dance_finished.disconnect(self.dance_thread.quit)
            except (TypeError, RuntimeError, AttributeError):
                pass
            
            print("Marquage de 'dance_worker' pour suppression ultérieure.")
            self.dance_worker.deleteLater()
            self.dance_worker = None 

        if self.dance_thread:
            # Déconnecter le signal finished du thread de cette méthode pour éviter des boucles
            try:
                self.dance_thread.finished.disconnect(self._cleanup_dance_thread_final)
            except (TypeError, RuntimeError, AttributeError):
                pass
            
            print("Marquage de 'dance_thread' pour suppression ultérieure.")
            self.dance_thread.deleteLater()
            self.dance_thread = None 
        
        print("Nettoyage final terminé. 'dance_thread' et 'dance_worker' sont maintenant à None.")


    def arreter_danse(self):
        """Demande au worker d'arrêter la danse et initie le processus de terminaison du thread."""
        print("\n--- 'arreter_danse()' appelé. ---")
        
        if self.dance_worker and self.dance_thread and self.dance_thread.isRunning():
            self.parent_ui.mettre_a_jour_statut_connexion("Arrêt de la danse demandé. Initialisation de l'arrêt...")
            print("arreter_danse() - Demande d'arrêt envoyée au worker.")
            
            # Demander au worker d'arrêter sa boucle
            self.dance_worker.request_stop() 
            
            # Demander au thread de quitter sa boucle d'événements
            self.dance_thread.quit()
            
            # Attendre que le thread ait réellement terminé.
            # Cela bloque l'UI TANT QUE le thread ne s'est pas terminé (jusqu'à 5s).
            # Cependant, c'est le seul moyen sûr de s'assurer que le thread est mort
            # avant que l'utilisateur ne puisse en relancer un ou cliquer à nouveau.
            if not self.dance_thread.wait(5000): # Attendre max 5 secondes
                print("arreter_danse() - Le thread ne s'est pas terminé à temps (timeout), terminaison forcée.")
                self.dance_thread.terminate() # Terminaison plus brutale si nécessaire
                self.dance_thread.wait(500) # Petite attente pour la terminaison effective
            
            self.parent_ui.mettre_a_jour_statut_connexion("Danse arrêtée.")
            print("arreter_danse() - Processus d'arrêt terminé.")

        elif self.dance_thread and not self.dance_thread.isRunning():
            # Cas où le thread existe mais a déjà terminé naturellement.
            # On peut forcer un nettoyage si _cleanup_dance_thread_final n'a pas encore eu lieu.
            self.parent_ui.mettre_a_jour_statut_connexion("La danse était déjà terminée ou en cours de nettoyage.")
            print("arreter_danse() - Le thread existe mais n'est pas actif. Probablement déjà terminé.")
            # S'assurer que le nettoyage final est déclenché si ce n'est pas déjà fait
            self._cleanup_dance_thread_final() 
        else:
            self.parent_ui.mettre_a_jour_statut_connexion("Aucune danse n'est en cours à arrêter.")
            print("arreter_danse() - Aucun worker/thread de danse actif.")