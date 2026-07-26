import sys
import os
from matplotlib.pylab import angle
project_root = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
sys.path.append(project_root)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QTextEdit,
    QLineEdit, 
    QLabel, 
    QToolBar, 
    QInputDialog, 
    QPushButton,
    QVBoxLayout
)
from PySide6.QtCore import Qt, QTimer
from app.ai.command_parser import CommandParser
from app.ai.command_executor import CommandExecutor
import cv2
from app.ai.ai_engine import AIEngine
from scene_object import SceneObject
from database.database import save_model
from app.viewport import Viewport
from webcam.hand_tracker_class import HandTracker
import webcam.hand_tracker_class
import inspect
from webcam.gesture_controller import GestureController
from interaction.interaction_manager import InteractionManager
from app.project.project_manager import ProjectManager
from app.tools.tool_manager import ToolManager
from scene.ray import Ray
from scene.raycast import RayCaster
print("OK")
print("HandTracker loaded from:")
print(inspect.getfile(HandTracker))
print("Methods:")
print(dir(HandTracker))
print(
    webcam.hand_tracker_class.__file__
)
ray = Ray(
    origin=[0, 0, 5],
    direction=[2, 0, -4]
)
print("Origin:", ray.origin)
print("Direction:", ray.direction)
from scene.scene_manager import SceneManager
from scene.tool_manager import ToolManager
from managers.history_manager import HistoryManager

class AI3DStudio(QMainWindow):

    def mousePressEvent(self, event):

        self.viewport.setFocus()

        super().mousePressEvent(event)
    
    def __init__(self):
        super().__init__()

        self.interaction = InteractionManager()

        self.setWindowTitle("AI3D Studio")
        self.resize(1400, 900)

        self.scene_manager = SceneManager()
        self.scene_objects = self.scene_manager.scene_objects
        self.selected_object = None
        self.cube_count = 0

        self.command_parser = CommandParser()

        self.command_executor = CommandExecutor(self)

        print("INIT COMPLETE")
        print("Parser:", self.command_parser)
        print("Executor:", self.command_executor)

        self.project_manager = ProjectManager()

        self.tool_manager = ToolManager()

        print(self.tool_manager)

        self.ai = AIEngine()

        self.setup_ui()

        self.tracker = HandTracker()

        print(inspect.getfile(HandTracker))

        print(dir(self.tracker))

        self.gesture = GestureController()

        self.cap = cv2.VideoCapture(0)

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            1280
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            720
        )

        print(
            self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        self.timer = QTimer()
        self.timer.timeout.connect(
            self.update_hand_control
        )
        self.timer.start(8)

    def setup_ui(self):

        # ==========================
        # Toolbar
        # ==========================

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.select_btn = QPushButton("Select")
        self.move_btn = QPushButton("Move")
        self.rotate_btn = QPushButton("Rotate")
        self.scale_btn = QPushButton("Scale")

        self.cube_btn = QPushButton("Cube")
        self.sphere_btn = QPushButton("Sphere")
        self.cylinder_btn = QPushButton("Cylinder")

        self.save_toolbar_btn = QPushButton("Save")
        self.load_toolbar_btn = QPushButton("Load")

        toolbar.addWidget(self.select_btn)

        toolbar.addSeparator()

        toolbar.addWidget(self.move_btn)
        toolbar.addWidget(self.rotate_btn)
        toolbar.addWidget(self.scale_btn)

        toolbar.addSeparator()

        toolbar.addWidget(self.cube_btn)
        toolbar.addWidget(self.sphere_btn)
        toolbar.addWidget(self.cylinder_btn)

        toolbar.addSeparator()

        toolbar.addWidget(self.save_toolbar_btn)
        toolbar.addWidget(self.load_toolbar_btn)

        self.cube_btn.clicked.connect(
            self.create_cube
        )

        self.save_toolbar_btn.clicked.connect(
            self.save_scene
        )

        self.load_toolbar_btn.clicked.connect(
            self.load_scene
        )

        self.select_btn.clicked.connect(
            lambda: self.tool_manager.set_tool(
                ToolManager.SELECT
            )
        )

        self.move_btn.clicked.connect(
            lambda: self.tool_manager.set_tool(
                ToolManager.MOVE
            )
        )

        self.rotate_btn.clicked.connect(
            lambda: self.tool_manager.set_tool(
                ToolManager.ROTATE
            )
        )

        self.scale_btn.clicked.connect(
            lambda: self.tool_manager.set_tool(
                ToolManager.SCALE
            )
        )

        # ==========================
        # Central Widget
        # ==========================

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()

        # ==========================
        # Scene Hierarchy
        # ==========================

        self.scene_hierarchy = QListWidget()

        self.scene_hierarchy.itemClicked.connect(
            self.select_object
        )

        left_layout = QVBoxLayout()

        left_layout.addWidget(
            QLabel("Scene")
        )

        left_layout.addWidget(
            self.scene_hierarchy
        )

        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # ==========================
        # Viewport
        # ==========================

        self.history_manager = HistoryManager()

        self.viewport = Viewport()

        self.viewport.history_manager = self.history_manager

        self.viewport.setFocusPolicy(
            Qt.StrongFocus
        )

        self.viewport.setFocus()

        # ==========================
        # Right Panel
        # ==========================

        right_layout = QVBoxLayout()

        self.create_cube_btn = QPushButton(
            "Create Cube"
        )

        self.save_btn = QPushButton(
            "Save Scene"
        )

        self.load_btn = QPushButton(
            "Load Scene"
        )

        self.create_cube_btn.clicked.connect(
            self.create_cube
        )

        self.save_btn.clicked.connect(
            self.save_scene
        )

        self.load_btn.clicked.connect(
            self.load_scene
        )

        self.ai_console = QTextEdit()

        self.ai_console.setReadOnly(True)

        self.command_bar = QLineEdit()

        self.command_bar.setPlaceholderText(
            "AI Command... (Example: Create Cube)"
        )

        self.command_bar.returnPressed.connect(
            self.run_ai_command
        )

        right_layout.addWidget(
            self.create_cube_btn
        )

        right_layout.addWidget(
            self.save_btn
        )

        right_layout.addWidget(
            self.load_btn
        )

        right_layout.addWidget(
            self.ai_console
        )

        right_layout.addWidget(
            self.command_bar
        )

        right_widget = QWidget()

        right_widget.setLayout(
            right_layout
        )

        # ==========================
        # Main Layout
        # ==========================

        main_layout.addWidget(
            left_widget,
            1
        )

        main_layout.addWidget(
            self.viewport,
            4
        )

        main_layout.addWidget(
            right_widget,
            2
        )

        central.setLayout(
            main_layout
        )

        self.ai_console.append(
            "AI3D Studio Started"
        )

    def create_primitive(self, primitive_type):

        primitive_type = primitive_type.capitalize()

        if not hasattr(self, "primitive_counts"):
            self.primitive_counts = {}

        if primitive_type not in self.primitive_counts:
            self.primitive_counts[primitive_type] = 0

        self.primitive_counts[primitive_type] += 1

        obj = SceneObject(

            f"{primitive_type} {self.primitive_counts[primitive_type]}",

            primitive_type

        )

        obj.position = [

            -2.0 + ((len(self.scene_objects)) * 1.5),

            0.0,

            0.0

        ]

        self.scene_objects.append(obj)

        self.scene_hierarchy.addItem(obj.name)

        self.scene_hierarchy.setCurrentRow(
            len(self.scene_objects) - 1
        )

        self.viewport.set_selected_object(obj)

        self.viewport.update_scene(self.scene_objects)

        self.viewport.update()

        try:

            save_model(
                obj.name,
                primitive_type
            )

        except Exception:
            pass

        self.ai_console.append(

            f"Created {obj.name}"

        )

    def create_cube(self):

        self.create_primitive("Cube")

    def create_sphere(self):

        self.create_primitive("Sphere")

    def create_plane(self):

        self.create_primitive("Plane")

    def create_cylinder(self):

        self.create_primitive("Cylinder")

    def create_cone(self):

        self.create_primitive("Cone")

    def create_torus(self):

        self.create_primitive("Torus")
    
    def run_ai_command(self):

        text = self.command_bar.text().strip()

        if not text:
            return

        self.ai_console.append(f"> {text}")

        try:

            command = self.ai.ask(text)

            print("AI RESPONSE:", command)

            self.command_executor.execute(
                command["command"],
                command.get("argument")
            )

        except Exception:

            print("Using Local Command Parser")

            command, argument = self.command_parser.parse(text)

            self.command_executor.execute(
                command,
                argument
            )

        self.command_bar.clear()

    def delete_selected_object(self):

        if self.selected_object is None:

            return

        obj = self.selected_object

        if obj in self.scene_objects:

            index = self.scene_objects.index(obj)

            self.scene_objects.remove(obj)

            self.scene_hierarchy.takeItem(index)

            self.viewport.set_selected_object(None)

            self.selected_object = None

            self.viewport.update_scene(
                self.scene_objects
            )

            self.ai_console.append(
                f"Deleted {obj.name}"
            )

    def duplicate_selected_object(self):

        if self.selected_object is None:
            return

        self.cube_count += 1

        old = self.selected_object

        new = SceneObject(

            f"Cube {self.cube_count}",

            old.object_type

        )

        new.position = old.position.copy()
        new.rotation = old.rotation.copy()
        new.scale = old.scale.copy()

        # Offset slightly so it isn't exactly on top
        new.position[0] += 0.5
        new.position[1] += 0.5

        self.scene_objects.append(new)

        self.scene_hierarchy.addItem(new.name)

        self.scene_hierarchy.setCurrentRow(
            len(self.scene_objects) - 1
        )

        self.selected_object = new

        self.viewport.set_selected_object(new)

        self.viewport.update_scene(
            self.scene_objects
        )

        self.ai_console.append(
            f"Duplicated {old.name}"
        )

    def save_scene(self):

        filename = "projects/scene.ai3d"

        self.project_manager.save_project(

            filename,

            self.scene_objects

        )

        self.ai_console.append(

            "Scene Saved"

        )

    def load_scene(self):

        filename = "projects/scene.ai3d"

        self.scene_objects = self.project_manager.load_project(

            filename

        )

        self.scene_hierarchy.clear()

        for obj in self.scene_objects:

            self.scene_hierarchy.addItem(

                obj.name

            )

        self.viewport.update_scene(

            self.scene_objects

        )

        self.ai_console.append(

            "Scene Loaded"

        )

    def select_object(self, item):

        selected = None

        for obj in self.scene_objects:

            if obj.name == item.text():

                selected = obj
                break

        if selected is None:
            return

        self.selected_object = selected

        self.viewport.set_selected_object(
            selected
        )

        self.viewport.setFocus()

        self.ai_console.append(
            f"Selected {selected.name}"
        )
        
    def keyPressEvent(self, event):

        print("MAIN KEY:", event.key())

        print("KEY:", event.key())

        # ---------- Global Shortcuts ----------

        if (
            event.key() == Qt.Key_D
            and event.modifiers() & Qt.ControlModifier
        ):

            self.duplicate_selected_object()
            return

        elif event.key() == Qt.Key_Delete:

            self.delete_selected_object()
            return

        elif (
            event.key() == Qt.Key_R
            and event.modifiers() & Qt.ControlModifier
        ):

            self.rename_selected_object()
            return

        # ----------------------------
        # Tool Switching
        # ----------------------------

        if event.key() == Qt.Key_F1:

            print("F1 BLOCK ENTERED")

            print("Before:", self.viewport.tool_manager.get_tool())

            self.viewport.tool_manager.set_tool(
                ToolManager.MOVE
            )

            print("After:", self.viewport.tool_manager.get_tool())

            self.viewport.update()

            return


        elif event.key() == Qt.Key_F2:

            print("F2 BLOCK ENTERED")

            print("Before:", self.viewport.tool_manager.get_tool())

            self.viewport.tool_manager.set_tool(
                ToolManager.ROTATE
            )

            print("After:", self.viewport.tool_manager.get_tool())

            self.viewport.update()

            return


        elif event.key() == Qt.Key_F3:

            print("F3 BLOCK ENTERED")

            print("Before:", self.viewport.tool_manager.get_tool())

            self.viewport.tool_manager.set_tool(
                ToolManager.SCALE
            )

            print("After:", self.viewport.tool_manager.get_tool())

            self.viewport.update()

            return

        # ---------- Object Required ----------

        if self.selected_object is None:

            super().keyPressEvent(event)
            return
    
        print(
            "Position:",
            self.selected_object.position,
            "Rotation:",
            self.selected_object.rotation
        )
        
        self.viewport.update()

    def rename_selected_object(self):

        if self.selected_object is None:
            return

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Object",
            "New Name:",
            text=self.selected_object.name
        )

        if not ok:
            return

        if not new_name.strip():
            return

        self.selected_object.name = new_name.strip()

        current_row = self.scene_hierarchy.currentRow()

        self.scene_hierarchy.item(current_row).setText(
            self.selected_object.name
        )

        self.ai_console.append(
            f"Renamed to {self.selected_object.name}"
        )

    def update_hand_control(self):

        success, frame = self.cap.read()

        if not success:
            return

        frame = cv2.flip(frame, 1)

        # -----------------------------------
        # Detect hand FIRST
        # -----------------------------------

        self.tracker.get_hand_position(frame)

        palm = self.tracker.get_palm_position()

        # -----------------------------------
        # Debug window
        # -----------------------------------

        debug_frame = frame.copy()

        if (
            self.tracker.last_result
            and self.tracker.last_result.hand_landmarks
        ):

            hand = self.tracker.last_result.hand_landmarks[0]

            h, w, _ = debug_frame.shape

            for landmark in hand:

                px = int(landmark.x * w)
                py = int(landmark.y * h)

                cv2.circle(
                    debug_frame,
                    (px, py),
                    5,
                    (0,255,0),
                    -1
                )

            connections = [

                (0,1),(1,2),(2,3),(3,4),

                (0,5),(5,6),(6,7),(7,8),

                (5,9),(9,10),(10,11),(11,12),

                (9,13),(13,14),(14,15),(15,16),

                (13,17),(17,18),(18,19),(19,20),

                (0,17)

            ]

            for start,end in connections:

                p1 = hand[start]
                p2 = hand[end]

                cv2.line(

                    debug_frame,

                    (
                        int(p1.x*w),
                        int(p1.y*h)
                    ),

                    (
                        int(p2.x*w),
                        int(p2.y*h)
                    ),

                    (255,0,0),

                    2

                )

        self.viewport.update_webcam_frame(
            debug_frame
        )

        # -----------------------------------
        # Cursor
        # -----------------------------------

        if palm is not None:

            x, y, z = palm

            world_x = (x - 0.5) * 2
            world_y = -(y - 0.5) * 2

            self.viewport.update_cursor(
                world_x,
                world_y
            )

        # -----------------------------------
        # Grabbed object
        # -----------------------------------

        pinching = self.tracker.is_pinching()

        grab_event = self.interaction.update_grab(pinching)

        if grab_event:

            if self.interaction.is_holding:

                axes = self.tracker.get_palm_axes()

                if (
                    axes is not None
                    and self.viewport.selected_object
                ):

                    self.gesture.grab(
                        self.viewport.selected_object,
                        axes
                    )

                    self.gesture.grab_pinch_distance = (
                        self.tracker.get_pinch_distance()
                    )

            else:

                self.gesture.release()


        if (
            self.interaction.is_holding
            and self.viewport.selected_object
            and palm is not None
        ):

            smooth = 0.20

            obj = self.viewport.selected_object

            obj.position[0] += (
                world_x - obj.position[0]
            ) * smooth

            obj.position[1] += (
                world_y - obj.position[1]
            ) * smooth

            axes = self.tracker.get_palm_axes()

            if axes is not None:

                right, up, forward = axes

                obj.rotation[0] = up[1] * 180
                obj.rotation[1] = right[0] * 180
                obj.rotation[2] = forward[2] * 180
                
                current_distance = self.tracker.get_pinch_distance()

                if (
                    current_distance is not None
                    and self.gesture.grab_pinch_distance is not None
                ):

                    scale_factor = (
                        current_distance /
                        self.gesture.grab_pinch_distance
                    )

                    scale_factor = max(
                        0.3,
                        min(scale_factor, 3.0)
                    )

                    obj.scale[0] = (
                        self.gesture.grab_scale[0]
                        * scale_factor
                    )

                    obj.scale[1] = (
                        self.gesture.grab_scale[1]
                        * scale_factor
                    )

                    obj.scale[2] = (
                        self.gesture.grab_scale[2]
                        * scale_factor
                    )

            self.viewport.update()

    def closeEvent(self, event):

        if hasattr(
            self,
            "cap"
        ):
            self.cap.release()

        cv2.destroyAllWindows()

        event.accept()

if __name__ == "__main__":

    app = QApplication([])

    window = AI3DStudio()

    window.show()

    app.exec()