"""
app.py — Punto de entrada del Mini CRM de servicio al cliente.
Ejecuta la interfaz gráfica conectada al controlador.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from controller import ControladorPQRS
from gui import VentanaPrincipal


def main():
    ctrl = ControladorPQRS()
    app = VentanaPrincipal(ctrl)
    app.iniciar()


if __name__ == "__main__":
    main()
