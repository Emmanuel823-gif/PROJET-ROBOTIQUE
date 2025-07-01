# ReadSequence.py

class DanceFileParser:
    """
    Classe utilitaire pour lire et parser les fichiers de danse (.dance).
    Contient la logique d'extraction des instructions et de traduction en commandes structurées.
    """
    def __init__(self, move_time_per_dance_unit=1500):
        # move_time_per_dance_unit: Temps alloué pour UNE unité de mouvement (quantite=1) du fichier .dance
        # Note: Ce paramètre est maintenu mais n'est plus la seule source de temps pour garantir
        # une vitesse constante basée sur 'time_per_actual_marty_step_ms'.
        self.move_time_per_dance_unit = move_time_per_dance_unit
        
        # Définissons le nombre de PAS PHYSIQUES réels que Marty fera
        # pour chaque "unité" de danse (quantite=1) dans le fichier .dance.
        self.actual_steps_per_T_unit = 8   # 7 pas avant pour une unité 'T'
        self.actual_steps_per_B_unit = 5   # 4 pas arrière pour une unité 'B'
        self.actual_steps_per_F_unit = 8   # 1 pas de côté gauche pour une unité 'L'
        self.actual_steps_per_W_unit = 7   # 1 pas de côté droit pour une unité 'R'
        self.actual_steps_per_T_unit = 8   # 7 pas avant pour une unité 'T'
        self.actual_steps_per_B_unit = 5   # 4 pas arrière pour une unité 'B'
        self.actual_steps_per_L_unit = 8   # 1 pas de côté gauche pour une unité 'L'
        self.actual_steps_per_W_unit = 7   # 1 pas de côté droit pour une unité 'R'
        self.actual_steps_per_R_unit = 7   # 1 pas de côté droit pour une unité 'R'



        # Temps en millisecondes que Marty prendra pour faire UN pas PHYSIQUE (réel).
        # C'est la valeur clé pour contrôler la vitesse GLOBALE et CONSTANTE.
        # Plus cette valeur est petite, plus Marty se déplacera rapidement.
        self.time_per_actual_marty_step_ms = 200 # Ex: 300ms par pas physique. Ajustez selon vos besoins.


    def _extraire_instruction(self, instruction):
        """
        Extrait la quantité (nombre de répétitions) et la direction à partir d'une instruction (ex: '2R' → (2, 'R')).
        """
        nombre = ""
        direction = ""
        for c in instruction:
            if c.isdigit():
                nombre += c
            else:
                direction += c.upper() # Convertit en majuscule pour la cohérence ('l' -> 'L')

        if not nombre: # S'assurer qu'il y a un nombre (ex: 'U' sans '1' devant)
            nombre = "1" # Par défaut, une unité si aucun nombre n'est spécifié

        if direction not in {"L", "R", "U", "B","T", "F", "W"}:
            raise ValueError(f"Direction inconnue : {direction}. Les directions valides sont L, R, U, B;T,F,W,.")

        return int(nombre), direction

    def parse_dance_file(self, dance_file_path, is_running_flag=None, status_callback=None, error_callback=None):
        parsed_commands = []
        try:
            with open("survey.traj", "r", encoding="utf-8") as f:
                lignes = [l.strip().upper() for l in f if l.strip()]

            
            if status_callback:
                status_callback(f"Mode de lecture : {lignes[0]}. Début du parsing des instructions.")
            instructions = lignes[1:]

            for i, instr_str in enumerate(instructions, 1):
                if is_running_flag and not is_running_flag():
                    if status_callback:
                        status_callback("Parsing interrompu par l'utilisateur.")
                    return []
                try:
                    quantite, direction_code = self._extraire_instruction(instr_str)
                    
                    num_steps_actual = 0
                    current_step_length = 0
                    current_side = None
                    action_type = ""

                    # Détermine le nombre de pas physiques réels et le type d'action
                    if direction_code == "L":
                        num_steps_actual = self.actual_steps_per_L_unit * quantite
                        current_step_length = 15 # Longueur de pas pour la marche avant
                        action_type = "walk"
                    elif direction_code == "T":
                        num_steps_actual = self.actual_steps_per_T_unit * quantite
                        current_step_length = -25 # Longueur de pas pour la marche arrière
                        action_type = "walk"
                    elif direction_code == "F":
                        num_steps_actual = self.actual_steps_per_F_unit * quantite
                        current_side = "left"
                        action_type = "sidestep"
                    elif direction_code == "R":
                        num_steps_actual = self.actual_steps_per_R_unit * quantite
                        current_side = "right"
                        action_type = "sidestep"
                    elif direction_code == "W":
                        num_steps_actual = self.actual_steps_per_W_unit * quantite
                        current_side = "right"
                        action_type = "sidestep"
                    else:
                        # Ce cas ne devrait normalement pas être atteint grâce à _extraire_instruction
                        if error_callback:
                            error_callback(f"Ligne {i} : Direction inconnue '{direction_code}' dans l'instruction '{instr_str}'. Ignorée.")
                        continue

                    # Calcul du move_time total basé sur le nombre de pas réels et le temps par pas réel
                    # C'est ce qui garantit une vitesse constante (temps par pas réel est fixe)
                    total_move_time = int(num_steps_actual * self.time_per_actual_marty_step_ms)

                    # Construire la commande pour parsed_commands, incluant la quantité d'origine
                    command = {
                        "action": action_type,
                        "steps": num_steps_actual, # Nombre de pas physiques réels
                        "move_time": total_move_time,
                        "original_quantity": quantite # La quantité spécifiée dans le fichier .dance
                    }
                    if action_type == "walk":
                        command["step_length"] = current_step_length
                    elif action_type == "sidestep":
                        command["side"] = current_side
                    
                    parsed_commands.append(command)

                except ValueError as ve:
                    if error_callback:
                        error_callback(f"Ligne {i} : Erreur de format d'instruction '{instr_str}' : {ve}")
                except Exception as e:
                    if error_callback:
                        error_callback(f"Ligne {i} : Erreur inattendue lors du parsing de '{instr_str}' : {e}")
            
            if status_callback:
                status_callback(f"Parsing du fichier terminé. {len(parsed_commands)} commandes de danse détectées.")
            return parsed_commands

        except FileNotFoundError:
            error_msg = f"Erreur : Le fichier de danse '{dance_file_path}' n'a pas été trouvé."
            if error_callback:
                error_callback(error_msg)
            return []
        except ValueError as ve:
            if error_callback:
                error_callback(f"Erreur de format de fichier de danse : {ve}")
            return []
        except Exception as e:
            error_msg = f"Une erreur inattendue est survenue lors de la lecture du fichier de danse : {e}"
            if error_callback:
                error_callback(error_msg)
            return []
        
