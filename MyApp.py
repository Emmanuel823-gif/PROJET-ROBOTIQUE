#j´importe les elements du systeme qui pourraient etre utiles a mon application
import sys
#ici je mets la lumiere sur le spectacle qui est mon application 
from PyQt6.QtWidgets import QApplication
from Application import ApplicationControleMarty # Importer votre classe d'interface


#je m´assure que le fichier ne soit execute qu´a partir d´ici
if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = ApplicationControleMarty()
    fenetre.show()
    #ici on va permettre la lecture automatique du fichier survey.traj 
    try:
        fichier = open("survey.traj",'rt')
        texte = fichier.read()
        print(texte)
        fichier.close()
    except Exception as e:
                print(f"Le fichier survey:traj n´a pas pu etre lu: {e}")    

    sys.exit(app.exec())