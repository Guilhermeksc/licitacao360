from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSize
import pandas as pd
from pathlib import Path

def start_color_blink(widget, label):
    start_color = QColor(252, 194, 0)  # Cor inicial (amarelo)
    mid_color = QColor(0, 0, 0)  # Cor intermediária (preto)
    end_color = QColor(252, 194, 0)  # Cor de retorno (amarelo)

    # Criar animações para duas piscadas
    animation1 = QVariantAnimation(widget)
    animation1.setStartValue(start_color)
    animation1.setEndValue(mid_color)
    animation1.setDuration(200)
    animation1.setEasingCurve(QEasingCurve.Type.InOutSine)

    animation2 = QVariantAnimation(widget)
    animation2.setStartValue(mid_color)
    animation2.setEndValue(end_color)
    animation2.setDuration(200)
    animation2.setEasingCurve(QEasingCurve.Type.InOutSine)

    # Repetir a criação para a segunda piscada
    animation3 = QVariantAnimation(widget)
    animation3.setStartValue(start_color)
    animation3.setEndValue(mid_color)
    animation3.setDuration(200)
    animation3.setEasingCurve(QEasingCurve.Type.InOutSine)

    animation4 = QVariantAnimation(widget)
    animation4.setStartValue(mid_color)
    animation4.setEndValue(end_color)
    animation4.setDuration(200)
    animation4.setEasingCurve(QEasingCurve.Type.InOutSine)

    # Grupo de animação para sequenciar as quatro animações
    color_animation = QSequentialAnimationGroup(widget)
    color_animation.addAnimation(animation1)  # Ida 1
    color_animation.addAnimation(animation2)  # Volta 1
    color_animation.addAnimation(animation3)  # Ida 2
    color_animation.addAnimation(animation4)  # Volta 2
    color_animation.addAnimation(animation3)  # Ida 2

    # Conectar mudança de cor ao método de atualização
    animation1.valueChanged.connect(lambda color: update_background_color(label, color))
    animation2.valueChanged.connect(lambda color: update_background_color(label, color))
    animation3.valueChanged.connect(lambda color: update_background_color(label, color))
    animation4.valueChanged.connect(lambda color: update_background_color(label, color))

    # Definir o loop count como 1 para que a animação complete uma vez e pare
    color_animation.setLoopCount(1)

    # Iniciar animação
    color_animation.start()

def update_background_color(label, color):
    label.setStyleSheet(f"background-color: {color.name()}; color: white; font-size: 14pt; padding: 5px;")

def start_blink_effect(button, interval_ms=100):
    color1 = QColor(252, 194, 0)  # Yellow
    color2 = QColor(0, 0, 0)      # Black
    animate_blink(button, color1, color2, interval_ms, max_blinks=10)

def stop_blink_effect(button):
    if hasattr(button, 'blink_timer'):
        button.blink_timer.stop()
    button.setStyleSheet("""
        QPushButton {
            background-color: rgb(0, 0, 0);
            color: white;
            font-size: 12pt;
            min-height: 35px;
            padding: 5px;
            border-radius: 4px;
            border: 1px solid white;
        }
        QPushButton:hover {
            background-color: rgb(252, 194, 0);
            color: black;
        }
        QPushButton:pressed {
            background-color: rgb(252, 194, 0);
        }
        QPushButton:focus {
            border: 1px solid white;
        }
    """)
    
def animate_blink(button, color1, color2, interval_ms=100, max_blinks=10):
    """Animate button background color blinking between two colors."""
    is_color1 = True  # Toggle flag
    blink_count = 0  # Count the number of blinks

    def update_style():
        nonlocal is_color1, blink_count
        if blink_count >= max_blinks:
            button.blink_timer.stop()
            return
        # Determine the current color
        color = color1 if is_color1 else color2
        text_color = "black" if color == color1 else "white"
        # Update the button style with the current color
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                color: {text_color};
                font-size: 12pt;
                min-height: 35px;
                padding: 5px;
                border-radius: 4px; 
                border: 1px solid white; 
            }}
            QPushButton:hover {{
                background-color: rgb(252, 194, 0);
                color: black;
            }}
            QPushButton:pressed {{
                background-color: rgb(252, 194, 0);
                color: black;
            }}
            QPushButton:focus {{
                border: 1px solid white; 
            }}
        """)
        is_color1 = not is_color1  # Toggle the flag
        blink_count += 1  # Increment the blink count

    # Create and start the timer
    timer = QTimer(button)
    timer.timeout.connect(update_style)
    timer.start(interval_ms)
    button.blink_timer = timer  

def create_button(text, icon, callback, tooltip_text, icon_size=QSize(40, 40), parent=None, animate=False):
    btn = QPushButton(text, parent)
    if icon:
        btn.setIcon(icon)
    btn.setIconSize(icon_size)
    btn.clicked.connect(callback)
    btn.setToolTip(tooltip_text)
    # Set initial background color to the desired yellow color
    btn.setStyleSheet("""
        QPushButton {
            background-color: rgb(0, 0, 0);
            color: white;
            font-size: 12pt;
            min-height: 35px;
            padding: 5px;
            border-radius: 4px;
            border: 1px solid white;
        }
        QPushButton:hover {
            background-color: #555;
            border: 1px solid white;
        }
        QPushButton:pressed {
            background-color: rgb(252, 194, 0);
            color: black;
        }
        QPushButton:focus {
            border: 1px solid white;
        }
    """)

    if animate:
        # Define the colors for blinking
        color1 = QColor(252, 194, 0)  # Yellow
        color2 = QColor(0, 0, 0)      # Black
        # animate_blink(btn, color1, color2, 500)  # Start blinking

    return btn

def load_icons(icons_dir):
    icons = {}
    for icon_file in Path(icons_dir).glob("*.png"):  # Procura por arquivos .png no diretório
        icon_name = icon_file.stem  # Obtém o nome do arquivo sem a extensão
        icons[icon_name] = QIcon(str(icon_file))  # Cria o QIcon e adiciona ao dicionário
    return icons

def apply_standard_style(widget):
    widget.setStyleSheet("""
        QWidget {
            background-color: #f0f0f0;
            color: #333;
        }
    """)