import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal, QObject, QRect, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QCursor, QKeySequence
import pyautogui
import cv2
import numpy as np
from pynput import keyboard  # Para la escucha global de teclas

# Definir el archivo de configuración
CONFIG_FILE = "zoom_config.json"

class Communicate(QObject):
    # Señal personalizada para toggle del zoom
    toggle_zoom = pyqtSignal()

class ConfigWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Configuraciones de Zoom")
        self.setGeometry(200, 200, 400, 300)
        self.captured_key = None  # Para almacenar el código de la tecla

        layout = QVBoxLayout()

        # Deslizador para nivel de zoom
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Nivel de Zoom:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(5)  # Limitar el zoom máximo a 5
        self.zoom_slider.setValue(self.parent.zoom_level)
        self.zoom_slider.valueChanged.connect(self.update_zoom_level)
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(self.zoom_slider)

        # Detección de tecla
        key_layout = QHBoxLayout()
        key_label = QLabel("Tecla Toggle Zoom:")
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Presiona una tecla")
        self.key_input.setReadOnly(True)
        self.key_input.installEventFilter(self)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)

        # Botón de aplicar
        apply_button = QPushButton("Aplicar")
        apply_button.clicked.connect(self.apply_settings)

        # Botón para seleccionar área de zoom
        select_area_button = QPushButton("Seleccionar Área de Zoom")
        select_area_button.clicked.connect(self.parent.open_selection_window)

        layout.addLayout(zoom_layout)
        layout.addLayout(key_layout)
        layout.addWidget(apply_button)
        layout.addWidget(select_area_button)

        self.setLayout(layout)

    def eventFilter(self, source, event):
        if source == self.key_input and event.type() == QEvent.KeyPress:
            key = event.key()
            key_text = QKeySequence(key).toString()
            if key_text:
                self.key_input.setText(key_text)
                self.captured_key = key  # Almacenar el código de la tecla
            return True
        return super().eventFilter(source, event)

    def update_zoom_level(self):
        self.parent.zoom_level = self.zoom_slider.value()
        print(f"Nivel de zoom actualizado: {self.parent.zoom_level}")

    def apply_settings(self):
        print("Aplicando configuraciones...")
        if self.captured_key is None:
            print("Error: No se ha configurado una tecla de zoom válida.")
            return

        # Guardar configuraciones válidas
        self.parent.zoom_key = self.captured_key  # Guardar el código de la tecla
        self.parent.save_settings()
        print(f"Nuevas configuraciones aplicadas: Tecla Toggle Zoom = {self.parent.zoom_key}, Nivel de Zoom = {self.parent.zoom_level}")

        # Reiniciar el listener de teclas para usar la nueva tecla
        self.parent.restart_key_listener()

        # Cerrar solo la ventana de configuración
        self.close()

class SelectionWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Seleccionar Área de Zoom")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.parent_app = parent

        # Variables para mover y redimensionar
        self.dragging = False
        self.resizing = False
        self.resize_direction = None
        self.rect = QRect(100, 100, 300, 200)  # Rectángulo inicial
        self.setMouseTracking(True)

        # Layout para el botón "Guardar"
        self.button_widget = QWidget(self)
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_selection)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_button)
        self.button_widget.setLayout(self.button_layout)
        self.button_widget.setGeometry(10, 10, 100, 40)  # Posición y tamaño del botón

        # Verificar dimensiones de pantalla
        screen_geometry = QApplication.primaryScreen().geometry()
        print(f"Resolución de pantalla en SelectionWindow: {screen_geometry.width()}x{screen_geometry.height()}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.SolidLine))
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.drawRect(self.rect)

        # Dibujar pequeños cuadrados en las esquinas para redimensionar
        handle_size = 10
        corners = [
            self.rect.topLeft(),
            self.rect.topRight(),
            self.rect.bottomLeft(),
            self.rect.bottomRight()
        ]
        painter.setBrush(QColor(255, 0, 0))
        for corner in corners:
            painter.drawRect(corner.x() - handle_size // 2, corner.y() - handle_size // 2, handle_size, handle_size)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            handle_size = 10
            # Verificar si el clic está en alguna esquina para redimensionar
            corners = [
                self.rect.topLeft(),
                self.rect.topRight(),
                self.rect.bottomLeft(),
                self.rect.bottomRight()
            ]
            for corner in corners:
                handle_rect = QRect(corner.x() - handle_size // 2, corner.y() - handle_size // 2, handle_size, handle_size)
                if handle_rect.contains(pos):
                    self.resizing = True
                    if corner == self.rect.topLeft():
                        self.resize_direction = 'top_left'
                    elif corner == self.rect.topRight():
                        self.resize_direction = 'top_right'
                    elif corner == self.rect.bottomLeft():
                        self.resize_direction = 'bottom_left'
                    elif corner == self.rect.bottomRight():
                        self.resize_direction = 'bottom_right'
                    return
            # Si no está en una esquina, iniciar el movimiento
            if self.rect.contains(pos):
                self.dragging = True
                self.drag_start_pos = pos
                self.rect_start_pos = QPoint(self.rect.x(), self.rect.y())

    def mouseMoveEvent(self, event):
        pos = event.pos()
        handle_size = 10
        # Cambiar el cursor si está sobre una esquina
        corners = [
            self.rect.topLeft(),
            self.rect.topRight(),
            self.rect.bottomLeft(),
            self.rect.bottomRight()
        ]
        on_corner = False
        for corner in corners:
            handle_rect = QRect(corner.x() - handle_size // 2, corner.y() - handle_size // 2, handle_size, handle_size)
            if handle_rect.contains(pos):
                on_corner = True
                if corner == self.rect.topLeft() or corner == self.rect.bottomRight():
                    self.setCursor(QCursor(Qt.SizeFDiagCursor))
                else:
                    self.setCursor(QCursor(Qt.SizeBDiagCursor))
                break
        if not on_corner:
            if self.rect.contains(pos):
                self.setCursor(QCursor(Qt.SizeAllCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))

        if self.dragging:
            delta = pos - self.drag_start_pos
            new_x = self.rect_start_pos.x() + delta.x()
            new_y = self.rect_start_pos.y() + delta.y()
            # Asegurarse de que el rectángulo no salga de la pantalla
            screen_rect = QApplication.primaryScreen().geometry()
            new_x = max(0, min(new_x, screen_rect.width() - self.rect.width()))
            new_y = max(0, min(new_y, screen_rect.height() - self.rect.height()))
            self.rect.moveTo(new_x, new_y)
            self.update()

        if self.resizing:
            if self.resize_direction == 'top_left':
                new_x = pos.x()
                new_y = pos.y()
                new_width = self.rect.right() - new_x
                new_height = self.rect.bottom() - new_y
                if new_width >= 100 and new_height >= 100:
                    self.rect.setTopLeft(QPoint(new_x, new_y))
            elif self.resize_direction == 'top_right':
                new_y = pos.y()
                new_width = pos.x() - self.rect.x()
                new_height = self.rect.bottom() - new_y
                if new_width >= 100 and new_height >= 100:
                    self.rect.setTopRight(QPoint(pos.x(), new_y))
            elif self.resize_direction == 'bottom_left':
                new_x = pos.x()
                new_width = self.rect.right() - new_x
                new_height = pos.y() - self.rect.y()
                if new_width >= 100 and new_height >= 100:
                    self.rect.setBottomLeft(QPoint(new_x, pos.y()))
            elif self.resize_direction == 'bottom_right':
                new_width = pos.x() - self.rect.x()
                new_height = pos.y() - self.rect.y()
                if new_width >= 100 and new_height >= 100:
                    self.rect.setBottomRight(QPoint(pos.x(), pos.y()))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.resizing or self.dragging:
                self.resizing = False
                self.dragging = False
                self.resize_direction = None
                # No cerramos la ventana aquí

    def save_selection(self):
        if self.parent_app:
            # Usar directamente el rectángulo seleccionado, ya que SelectionWindow está en pantalla completa
            global_rect = self.rect
            print(f"Área de zoom establecida (global): x={global_rect.x()}, y={global_rect.y()}, width={global_rect.width()}, height={global_rect.height()}")

            # Pasar el rectángulo global a la aplicación principal
            self.parent_app.set_zoom_area(global_rect)
        self.close()

class ZoomApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.communicate = Communicate()
        self.communicate.toggle_zoom.connect(self.toggle_zoom)

        self.load_settings()
        self.setGeometry(100, 100, 300, 300)
        self.setWindowTitle("Zoom Tool")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 255, 0, 0.2); border: 2px solid green;")

        # Permitir que la ventana sea draggable
        self.setFocusPolicy(Qt.StrongFocus)  # Asegurar que la ventana puede recibir eventos de teclas

        self.start_pos = None
        self.zoom_window = QLabel()
        self.zoom_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.zoom_window.setStyleSheet("background: black; color: white; border: 2px solid red;")
        self.zoom_window.setAttribute(Qt.WA_TransparentForMouseEvents)  # Hacerla transparente a eventos del ratón
        # Set attributes to reduce flickering
        self.zoom_window.setAttribute(Qt.WA_NoSystemBackground, True)
        self.zoom_window.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.zoom_window.hide()

        # Temporizador para actualizar el zoom
        self.zoom_timer = QTimer()
        self.zoom_timer.timeout.connect(self.update_zoom)

        # Añadir ventana de configuración
        self.config_window = ConfigWindow(self)
        self.show_config_window()

        # Iniciar el listener global de teclas
        self.listener = None
        self.zoom_active_flag = False  # Para manejar el estado de zoom
        self.start_key_listener()

        # Área de zoom por defecto
        self.zoom_area = QRect(100, 100, self.rect_size, self.rect_size)

    def show_config_window(self):
        self.config_window.show()

    def open_selection_window(self):
        self.selection_window = SelectionWindow(parent=self)
        self.selection_window.show()

    def set_zoom_area(self, rect):
        self.zoom_area = rect
        print(f"Área de zoom actualizada a: {self.zoom_area}")
        if self.zoom_active_flag:
            self.update_zoom()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            self.move(self.pos() + event.pos() - self.start_pos)

    def mouseReleaseEvent(self, event):
        self.start_pos = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.zoom_window.isVisible():
            self.update_zoom()

    def toggle_zoom(self):
        if not self.zoom_active_flag:
            self.start_zoom()
        else:
            self.stop_zoom()

    def start_zoom(self):
        if not self.zoom_active_flag:
            print("Iniciando zoom...")
            self.zoom_active_flag = True

            rect = self.zoom_area

            # Asegurarse de que las coordenadas están dentro de los límites de la pantalla
            screen_geometry = QApplication.primaryScreen().geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            adjusted_x = max(0, min(rect.x(), screen_width - rect.width()))
            adjusted_y = max(0, min(rect.y(), screen_height - rect.height()))
            adjusted_width = rect.width()
            adjusted_height = rect.height()

            zoom_level = max(1, min(self.zoom_level, 5))
            zoomed_width = adjusted_width * zoom_level
            zoomed_height = adjusted_height * zoom_level

            # Evitar que el zoom exceda las dimensiones de la pantalla
            zoomed_width = min(zoomed_width, screen_width - 20)  # 10 píxeles de margen a cada lado
            zoomed_height = min(zoomed_height, screen_height - 20)

            print(f"Zoom Level aplicado: {zoom_level}")
            print(f"Tamaño de la ventana de zoom: {int(zoomed_width)}x{int(zoomed_height)}")

            # Establecer tamaño de la ventana de zoom
            self.zoom_window.resize(int(zoomed_width), int(zoomed_height))

            # Posicionar la ventana de zoom cerca del área seleccionada
            desired_x = rect.x() + rect.width() + 10  # 10 píxeles de margen a la derecha
            desired_y = rect.y()

            print(f"Posición antes de verificar: x={desired_x}, y={desired_y}")

            # Verificar si la ventana de zoom excede el ancho de la pantalla
            if desired_x + zoomed_width > screen_width:
                desired_x = rect.x() - zoomed_width - 10  # 10 píxeles de margen a la izquierda
                if desired_x < 0:
                    desired_x = 10  # Fallback a 10 píxeles de margen desde la izquierda
            if desired_y + zoomed_height > screen_height:
                desired_y = screen_height - zoomed_height - 10  # 10 píxeles de margen desde arriba

            print(f"Posición final de la ventana de zoom: x={int(desired_x)}, y={int(desired_y)}")

            # Mover la ventana de zoom
            self.zoom_window.move(int(desired_x), int(desired_y))

            # Mostrar la ventana de zoom
            self.zoom_window.show()

            # Capturar y mostrar la primera imagen
            self.update_zoom()

            # Iniciar el temporizador para actualizaciones
            self.zoom_timer.start(300)  # 300ms de intervalo

    def stop_zoom(self):
        if self.zoom_active_flag:
            print("Deteniendo zoom...")
            self.zoom_active_flag = False
            self.zoom_timer.stop()
            self.zoom_window.hide()

    def update_zoom(self):
        if not self.zoom_active_flag:
            return

        print("Actualizando zoom...")
        print(f"Nivel de zoom actual: {self.zoom_level}")
        rect = self.zoom_area
        print(f"Coordenadas del rectángulo de zoom (Global): x={rect.x()}, y={rect.y()}, width={rect.width()}, height={rect.height()}")

        # Calcular el zoom
        zoom_level = max(1, min(self.zoom_level, 5))
        zoomed_width = rect.width() * zoom_level
        zoomed_height = rect.height() * zoom_level

        # Evitar que el zoom exceda las dimensiones de la pantalla
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        zoomed_width = min(zoomed_width, screen_width - 20)
        zoomed_height = min(zoomed_height, screen_height - 20)

        print(f"Zoom Level aplicado: {zoom_level}")
        print(f"Tamaño de la ventana de zoom: {int(zoomed_width)}x{int(zoomed_height)}")

        # Capturar la región seleccionada de la pantalla
        try:
            # Usando pyautogui
            screenshot = pyautogui.screenshot(region=(
                int(rect.x()),
                int(rect.y()),
                int(rect.width()),
                int(rect.height())
            ))
            print("Capturando pantalla en la región especificada.")

            # Guardar la captura para verificar visualmente
            screenshot.save("captura_de_zoom.png")
            print("Captura de pantalla guardada como 'captura_de_zoom.png'.")

            # Convertir la captura a formato OpenCV
            screenshot = np.array(screenshot)
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

            # Aplicar el zoom (escalado)
            zoomed = cv2.resize(screenshot, (int(zoomed_width), int(zoomed_height)), interpolation=cv2.INTER_LINEAR)

            # Convertir la imagen a QPixmap y mostrarla
            h, w, ch = zoomed.shape
            bytes_per_line = ch * w
            zoomed_qimage = QImage(zoomed.data, w, h, bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(zoomed_qimage)
            self.zoom_window.setPixmap(pixmap)
            print("Zoom actualizado correctamente.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error durante la actualización del zoom: {e}")

    def load_settings(self):
        try:
            with open(CONFIG_FILE, "r") as file:
                config = json.load(file)
                # Capping zoom_level to [1,5] to prevent excessive values
                self.zoom_level = max(1, min(config.get("zoom_level", 2), 5))
                self.rect_size = config.get("rect_size", 300)
                self.zoom_key = config.get("zoom_key", Qt.Key_Shift)
                print(f"Configuración cargada: zoom_level={self.zoom_level}, rect_size={self.rect_size}, zoom_key={self.zoom_key}")
        except FileNotFoundError:
            # Valores predeterminados si no se encuentra el archivo de configuración
            self.zoom_level = 2
            self.rect_size = 300
            self.zoom_key = Qt.Key_Shift
            print("Archivo de configuración no encontrado. Usando valores predeterminados.")

    def save_settings(self):
        print("Guardando configuraciones...")
        config = {
            "zoom_level": self.zoom_level,
            "rect_size": self.rect_size,
            "zoom_key": self.zoom_key
        }
        try:
            with open(CONFIG_FILE, "w") as file:
                json.dump(config, file)
            print("Configuraciones guardadas exitosamente.")
        except Exception as e:
            print(f"Error al guardar configuraciones: {e}")

    def start_key_listener(self):
        if self.listener:
            self.listener.stop()

        def on_press(key):
            # Manejar la pulsación de tecla para togglear zoom
            if key in self.pynput_key:
                print("Tecla de zoom presionada detectada por el listener.")
                self.communicate.toggle_zoom.emit()

        # Mapear la tecla de Qt a la tecla de pynput
        self.pynput_key = self.map_qt_key_to_pynput(self.zoom_key)
        if self.pynput_key is not None:
            # Asegurarse de que es una lista
            if isinstance(self.pynput_key, keyboard.Key):
                self.pynput_key = [self.pynput_key]
            elif isinstance(self.pynput_key, list):
                pass
            else:
                self.pynput_key = [self.pynput_key]

            self.listener = keyboard.Listener(
                on_press=on_press
            )
            self.listener.start()
            print("Listener global de teclas iniciado.")
        else:
            print("Tecla de zoom no soportada para el listener global.")

    def restart_key_listener(self):
        print("Reiniciando el listener de teclas con nuevas configuraciones...")
        self.start_key_listener()

    def map_qt_key_to_pynput(self, qt_key):
        # Mapeo de teclas comunes de Qt a teclas de pynput
        key_mapping = {
            Qt.Key_Shift: [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r],
            Qt.Key_Control: [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r],
            Qt.Key_Alt: [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r],
            Qt.Key_Meta: [keyboard.Key.cmd],
            Qt.Key_A: [keyboard.KeyCode.from_char('a')],
            Qt.Key_B: [keyboard.KeyCode.from_char('b')],
            Qt.Key_C: [keyboard.KeyCode.from_char('c')],
            Qt.Key_D: [keyboard.KeyCode.from_char('d')],
            Qt.Key_E: [keyboard.KeyCode.from_char('e')],
            Qt.Key_F: [keyboard.KeyCode.from_char('f')],
            Qt.Key_G: [keyboard.KeyCode.from_char('g')],
            Qt.Key_H: [keyboard.KeyCode.from_char('h')],
            Qt.Key_I: [keyboard.KeyCode.from_char('i')],
            Qt.Key_J: [keyboard.KeyCode.from_char('j')],
            Qt.Key_K: [keyboard.KeyCode.from_char('k')],
            Qt.Key_L: [keyboard.KeyCode.from_char('l')],
            Qt.Key_M: [keyboard.KeyCode.from_char('m')],
            Qt.Key_N: [keyboard.KeyCode.from_char('n')],
            Qt.Key_O: [keyboard.KeyCode.from_char('o')],
            Qt.Key_P: [keyboard.KeyCode.from_char('p')],
            Qt.Key_Q: [keyboard.KeyCode.from_char('q')],
            Qt.Key_R: [keyboard.KeyCode.from_char('r')],
            Qt.Key_S: [keyboard.KeyCode.from_char('s')],
            Qt.Key_T: [keyboard.KeyCode.from_char('t')],
            Qt.Key_U: [keyboard.KeyCode.from_char('u')],
            Qt.Key_V: [keyboard.KeyCode.from_char('v')],
            Qt.Key_W: [keyboard.KeyCode.from_char('w')],
            Qt.Key_X: [keyboard.KeyCode.from_char('x')],
            Qt.Key_Y: [keyboard.KeyCode.from_char('y')],
            Qt.Key_Z: [keyboard.KeyCode.from_char('z')],
            # Añadir más mapeos según sea necesario
        }
        return key_mapping.get(qt_key, None)

    def closeEvent(self, event):
        # Asegurar que el listener se detenga al cerrar la aplicación
        if self.listener:
            self.listener.stop()
        event.accept()

if __name__ == "__main__":
    # Habilitar atributos de alta DPI antes de crear QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    zoom_app = ZoomApp()
    zoom_app.show()
    sys.exit(app.exec())
