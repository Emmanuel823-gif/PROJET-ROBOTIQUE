# ui_elements.py
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QPointF

class BoutonCommandeStyle(QPushButton):
    def __init__(self, pixmap_icone, commande, taille_bouton, taille_icone, parent=None):
        super().__init__("", parent)
        self.commande = commande
        self.setFixedSize(taille_bouton, taille_bouton)
        self.setStyleSheet("""
            QPushButton {
                background-color: #66CCFF;
                border: 2px solid #3399FF;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #99DDFF;
            }
            QPushButton:pressed {
                background-color: #3399FF;
                border: 2px solid #0066CC;
            }
        """)

        if pixmap_icone:
            pixmap_mise_a_echelle = pixmap_icone.scaled(QSize(taille_icone, taille_icone), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setIcon(QIcon(pixmap_mise_a_echelle))
            self.setIconSize(QSize(taille_icone, taille_icone))

def dessiner_fleche(direction, taille, epaisseur_trait=4, ratio_taille_pointe_fleche=0.15):
    pixmap = QPixmap(taille, taille)
    pixmap.fill(Qt.GlobalColor.transparent)
    peintre = QPainter(pixmap)
    peintre.setRenderHint(QPainter.RenderHint.Antialiasing)
    peintre.setPen(QColor(0, 0, 0))
    peintre.setBrush(QColor(0, 0, 0))

    if direction == "haut":
        points = [
            QPointF(taille * 0.5, taille * 0.2),
            QPointF(taille * 0.3, taille * 0.5),
            QPointF(taille * 0.45, taille * 0.5),
            QPointF(taille * 0.45, taille * 0.8),
            QPointF(taille * 0.55, taille * 0.8),
            QPointF(taille * 0.55, taille * 0.5),
            QPointF(taille * 0.7, taille * 0.5)
        ]
    elif direction == "bas":
        points = [
            QPointF(taille * 0.5, taille * 0.8),
            QPointF(taille * 0.3, taille * 0.5),
            QPointF(taille * 0.45, taille * 0.5),
            QPointF(taille * 0.45, taille * 0.2),
            QPointF(taille * 0.55, taille * 0.2),
            QPointF(taille * 0.55, taille * 0.5),
            QPointF(taille * 0.7, taille * 0.5)
        ]
    elif direction == "gauche":
        points = [
            QPointF(taille * 0.2, taille * 0.5),
            QPointF(taille * 0.5, taille * 0.3),
            QPointF(taille * 0.5, taille * 0.45),
            QPointF(taille * 0.8, taille * 0.45),
            QPointF(taille * 0.8, taille * 0.55),
            QPointF(taille * 0.5, taille * 0.55),
            QPointF(taille * 0.5, taille * 0.7)
        ]
    elif direction == "droite":
        points = [
            QPointF(taille * 0.8, taille * 0.5),
            QPointF(taille * 0.5, taille * 0.3),
            QPointF(taille * 0.5, taille * 0.45),
            QPointF(taille * 0.2, taille * 0.45),
            QPointF(taille * 0.2, taille * 0.55),
            QPointF(taille * 0.5, taille * 0.55),
            QPointF(taille * 0.5, taille * 0.7)
        ]
    elif direction == "tourner_gauche":
        peintre.setPen(QColor(0,0,0))
        peintre.setFont(QFont("Arial", int(taille * 0.4)))
        peintre.drawText(QPointF(taille * 0.15, taille * 0.7), "↺")
    elif direction == "tourner_droite":
        peintre.setPen(QColor(0,0,0))
        peintre.setFont(QFont("Arial", int(taille * 0.4)))
        peintre.drawText(QPointF(taille * 0.4, taille * 0.7), "↻")

    if direction not in ["tourner_gauche", "tourner_droite"]:
        peintre.drawPolygon(*points)

    peintre.end()
    return pixmap