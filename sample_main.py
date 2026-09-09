import sys
import os
import inspect
import cv2

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QTextEdit,
    QLineEdit,
    QLabel,
    QToolBar,
    QInputDialog,
    QPushButton,
)

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# ============================================================
# SCENE SYSTEM
# ============================================================

from app.scene.mesh_cache import MeshCache
from app.scene.primitive_factory import PrimitiveFactory
from app.scene.mesh_generator import MeshGenerator
from app.scene.scene_manager import SceneManager
from app.scene.tool_manager import ToolManager
from app.scene.ray import Ray
from app.scene.raycast import RayCaster

from app.mode_manager import ModeManager
from app.scene_object import SceneObject
from app.viewport import Viewport


# ============================================================
# AI SYSTEM
# ============================================================

from app.ai.command_parser import CommandParser
from app.ai.command_executor import CommandExecutor
from app.ai.ai_engine import AIEngine


# ============================================================
# PROJECT / DATABASE / HISTORY
# ============================================================

from app.database.database import save_model
from app.project.project_manager import ProjectManager
from app.managers.history_manager import HistoryManager


# ============================================================
# HAND TRACKING / GESTURES
# ============================================================

from webcam.hand_tracker_class import HandTracker
from webcam.gesture_controller import GestureController

from interaction.interaction_manager import InteractionManager


# ============================================================
# DEBUG INFORMATION
# ============================================================

print("========================================")
print("        AI3D STUDIO STARTING")
print("========================================")

try:
    print("HandTracker loaded from:")
    print(inspect.getfile(HandTracker))
except Exception as e:
    print("HandTracker path error:", e)


# ============================================================
# AI3D STUDIO
# ============================================================

class AI3DStudio(QMainWindow):

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # Window
        # ----------------------------------------------------

        self.setWindowTitle(
            "AI3D Studio"
        )

        self.resize(
            1400,
            900
        )

        # ----------------------------------------------------
        # Core Managers
        # ----------------------------------------------------

        self.scene_manager = SceneManager()

        self.scene_objects = (
            self.scene_manager.scene_objects
        )

        self.mode_manager = ModeManager()

        self.tool_manager = ToolManager()

        self.history_manager = HistoryManager()

        self.project_manager = ProjectManager()

        self.interaction = InteractionManager()

        # ----------------------------------------------------
        # Selection / Hierarchy
        # ----------------------------------------------------

        self.selected_object = None

        self.pending_parent = None

        self.cube_count = 0

        self.primitive_counts = {}

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        self.command_parser = CommandParser()

        self.command_executor = CommandExecutor(
            self
        )

        self.ai = AIEngine()

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.setup_ui()

        # ----------------------------------------------------
        # Hand Tracking
        # ----------------------------------------------------

        self.tracker = HandTracker()

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

        # ----------------------------------------------------
        # Hand Tracking Timer
        # ----------------------------------------------------

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_hand_control
        )

        self.timer.start(
            8
        )

        print("AI3D Studio initialization complete.")

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        # ----------------------------------------------------
        # Toolbar
        # ----------------------------------------------------

        toolbar = QToolBar(
            "Main Toolbar"
        )

        self.addToolBar(
            toolbar
        )

        # ----------------------------------------------------
        # Tool Buttons
        # ----------------------------------------------------

        self.select_btn = QPushButton(
            "Select"
        )

        self.move_btn = QPushButton(
            "Move"
        )

        self.rotate_btn = QPushButton(
            "Rotate"
        )

        self.scale_btn = QPushButton(
            "Scale"
        )

        # ----------------------------------------------------
        # Primitive Buttons
        # ----------------------------------------------------

        self.cube_btn = QPushButton(
            "Cube"
        )

        self.sphere_btn = QPushButton(
            "Sphere"
        )

        self.cylinder_btn = QPushButton(
            "Cylinder"
        )

        # ----------------------------------------------------
        # Project Buttons
        # ----------------------------------------------------

        self.save_toolbar_btn = QPushButton(
            "Save"
        )

        self.load_toolbar_btn = QPushButton(
            "Load"
        )

        # ----------------------------------------------------
        # Toolbar Layout
        # ----------------------------------------------------

        toolbar.addWidget(
            self.select_btn
        )

        toolbar.addSeparator()

        toolbar.addWidget(
            self.move_btn
        )

        toolbar.addWidget(
            self.rotate_btn
        )

        toolbar.addWidget(
            self.scale_btn
        )

        toolbar.addSeparator()

        toolbar.addWidget(
            self.cube_btn
        )

        toolbar.addWidget(
            self.sphere_btn
        )

        toolbar.addWidget(
            self.cylinder_btn
        )

        toolbar.addSeparator()

        toolbar.addWidget(
            self.save_toolbar_btn
        )

        toolbar.addWidget(
            self.load_toolbar_btn
        )

        # ----------------------------------------------------
        # Connections
        # ----------------------------------------------------

        self.select_btn.clicked.connect(
            self.activate_select_tool
        )

        self.move_btn.clicked.connect(
            self.activate_move_tool
        )

        self.rotate_btn.clicked.connect(
            self.activate_rotate_tool
        )

        self.scale_btn.clicked.connect(
            self.activate_scale_tool
        )

        self.cube_btn.clicked.connect(
            self.create_cube
        )

        self.sphere_btn.clicked.connect(
            self.create_sphere
        )

        self.cylinder_btn.clicked.connect(
            self.create_cylinder
        )

        self.save_toolbar_btn.clicked.connect(
            self.save_scene
        )

        self.load_toolbar_btn.clicked.connect(
            self.load_scene
        )

        # ----------------------------------------------------
        # Central Widget
        # ----------------------------------------------------

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QHBoxLayout()

        # ====================================================
        # LEFT PANEL
        # ====================================================

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

        left_widget.setLayout(
            left_layout
        )

        # ====================================================
        # VIEWPORT
        # ====================================================

        self.viewport = Viewport(
            self
        )

        self.viewport.history_manager = (
            self.history_manager
        )

        self.viewport.setFocusPolicy(
            Qt.StrongFocus
        )

        self.viewport.setFocus()

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right_layout = QVBoxLayout()

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # AI Console
        # ----------------------------------------------------

        self.ai_console = QTextEdit()

        self.ai_console.setReadOnly(
            True
        )

        # ----------------------------------------------------
        # Command Bar
        # ----------------------------------------------------

        self.command_bar = QLineEdit()

        self.command_bar.setPlaceholderText(
            "AI Command... Example: Create Cube"
        )

        self.command_bar.returnPressed.connect(
            self.run_ai_command
        )

        # ----------------------------------------------------
        # Right Layout
        # ----------------------------------------------------

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

        # ====================================================
        # MAIN LAYOUT
        # ====================================================

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

    # ========================================================
    # TOOL MANAGEMENT
    # ========================================================

    def activate_select_tool(self):

        if hasattr(
            ToolManager,
            "SELECT"
        ):

            self.tool_manager.set_tool(
                ToolManager.SELECT
            )

        self.viewport.update()

    def activate_move_tool(self):

        self.tool_manager.set_tool(
            ToolManager.MOVE
        )

        self.viewport.update()

    def activate_rotate_tool(self):

        self.tool_manager.set_tool(
            ToolManager.ROTATE
        )

        self.viewport.update()

    def activate_scale_tool(self):

        self.tool_manager.set_tool(
            ToolManager.SCALE
        )

        self.viewport.update()

    # ========================================================
    # PRIMITIVE CREATION
    # ========================================================

    def create_primitive(
        self,
        primitive_type
    ):

        primitive_type = (
            primitive_type.capitalize()
        )

        if primitive_type not in self.primitive_counts:

            self.primitive_counts[
                primitive_type
            ] = 0

        self.primitive_counts[
            primitive_type
        ] += 1

        name = (
            f"{primitive_type} "
            f"{self.primitive_counts[primitive_type]}"
        )

        obj = PrimitiveFactory.create(
            name,
            primitive_type
        )

        # ----------------------------------------------------
        # Initial Position
        # ----------------------------------------------------

        obj.position = [

            -2.0
            + (
                len(self.scene_objects)
                * 1.5
            ),

            0.0,

            0.0

        ]

        # ----------------------------------------------------
        # Add Object
        # ----------------------------------------------------

        self.scene_objects.append(
            obj
        )

        self.scene_hierarchy.addItem(
            obj.name
        )

        self.scene_hierarchy.setCurrentRow(
            len(self.scene_objects) - 1
        )

        # ----------------------------------------------------
        # Select Object
        # ----------------------------------------------------

        self.selected_object = obj

        self.viewport.set_selected_object(
            obj
        )

        self.viewport.update_scene(
            self.scene_objects
        )

        self.viewport.update()

        # ----------------------------------------------------
        # Database
        # ----------------------------------------------------

        try:

            save_model(
                obj.name,
                primitive_type
            )

        except Exception as e:

            print(
                "Database save error:",
                e
            )

        self.ai_console.append(
            f"Created {obj.name}"
        )

    # --------------------------------------------------------
    # Primitive Shortcuts
    # --------------------------------------------------------

    def create_cube(self):

        self.create_primitive(
            "Cube"
        )

    def create_sphere(self):

        self.create_primitive(
            "Sphere"
        )

    def create_plane(self):

        self.create_primitive(
            "Plane"
        )

    def create_cylinder(self):

        self.create_primitive(
            "Cylinder"
        )

    def create_cone(self):

        self.create_primitive(
            "Cone"
        )

    def create_torus(self):

        self.create_primitive(
            "Torus"
        )

    # ========================================================
    # AI COMMAND SYSTEM
    # ========================================================

    def run_ai_command(self):

        text = (
            self.command_bar
            .text()
            .strip()
        )

        if not text:
            return

        self.ai_console.append(
            f"> {text}"
        )

        try:

            command = self.ai.ask(
                text
            )

            print(
                "AI RESPONSE:",
                command
            )

            self.command_executor.execute(
                command["command"],
                command.get(
                    "argument"
                )
            )

        except Exception as e:

            print(
                "AI unavailable:",
                e
            )

            print(
                "Using Local Command Parser"
            )

            try:

                command, argument = (
                    self.command_parser.parse(
                        text
                    )
                )

                self.command_executor.execute(
                    command,
                    argument
                )

            except Exception as parser_error:

                print(
                    "Command parser error:",
                    parser_error
                )

                self.ai_console.append(
                    "Unable to process command."
                )

        self.command_bar.clear()

    # ========================================================
    # OBJECT DELETION
    # ========================================================

    def delete_selected_object(self):

        if self.selected_object is None:
            return

        obj = self.selected_object

        if obj not in self.scene_objects:
            return

        index = (
            self.scene_objects.index(
                obj
            )
        )

        self.scene_objects.remove(
            obj
        )

        self.scene_hierarchy.takeItem(
            index
        )

        self.selected_object = None

        self.viewport.set_selected_object(
            None
        )

        self.viewport.update_scene(
            self.scene_objects
        )

        self.viewport.update()

        self.ai_console.append(
            f"Deleted {obj.name}"
        )

    # ========================================================
    # OBJECT DUPLICATION
    # ========================================================

    def duplicate_selected_object(self):

        if self.selected_object is None:
            return

        old = self.selected_object

        primitive_type = (
            old.object_type
        )

        if primitive_type not in self.primitive_counts:

            self.primitive_counts[
                primitive_type
            ] = 0

        self.primitive_counts[
            primitive_type
        ] += 1

        new = SceneObject(

            f"{primitive_type} "
            f"{self.primitive_counts[primitive_type]}",

            primitive_type

        )

        # ----------------------------------------------------
        # Duplicate Mesh
        # ----------------------------------------------------

        try:

            new.mesh = MeshCache.get_mesh(
                primitive_type
            )

        except Exception:

            new.mesh = None

        # ----------------------------------------------------
        # Transform
        # ----------------------------------------------------

        new.position = (
            old.position.copy()
        )

        new.rotation = (
            old.rotation.copy()
        )

        new.scale = (
            old.scale.copy()
        )

        # Offset duplicate

        new.position[0] += 0.5

        new.position[1] += 0.5

        # ----------------------------------------------------
        # Add
        # ----------------------------------------------------

        self.scene_objects.append(
            new
        )

        self.scene_hierarchy.addItem(
            new.name
        )

        self.scene_hierarchy.setCurrentRow(
            len(self.scene_objects) - 1
        )

        self.selected_object = new

        self.viewport.set_selected_object(
            new
        )

        self.viewport.update_scene(
            self.scene_objects
        )

        self.viewport.update()

        self.ai_console.append(
            f"Duplicated {old.name}"
        )

    # ========================================================
    # RENAME
    # ========================================================

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

        new_name = new_name.strip()

        if not new_name:
            return

        self.selected_object.name = (
            new_name
        )

        current_row = (
            self.scene_hierarchy.currentRow()
        )

        item = (
            self.scene_hierarchy.item(
                current_row
            )
        )

        if item is not None:

            item.setText(
                new_name
            )

        self.ai_console.append(
            f"Renamed to {new_name}"
        )

    # ========================================================
    # OBJECT SELECTION
    # ========================================================

    def select_object(self, item):

        selected = None

        for obj in self.scene_objects:

            if obj.name == item.text():

                selected = obj

                break

        if selected is None:
            return

        self.selected_object = (
            selected
        )

        self.viewport.set_selected_object(
            selected
        )

        self.viewport.setFocus()

        self.viewport.update()

        self.ai_console.append(
            f"Selected {selected.name}"
        )

    # ========================================================
    # PARENTING
    # ========================================================

    def set_parent_candidate(self):

        if self.selected_object is None:

            self.ai_console.append(
                "No object selected."
            )

            return

        self.pending_parent = (
            self.selected_object
        )

        self.ai_console.append(
            "Parent candidate: "
            + self.selected_object.name
        )

    def parent_selected_object(self):

        if self.pending_parent is None:

            self.ai_console.append(
                "No parent selected."
            )

            return

        if self.selected_object is None:

            self.ai_console.append(
                "No child selected."
            )

            return

        if (
            self.pending_parent
            == self.selected_object
        ):

            self.ai_console.append(
                "Parent and child cannot be the same."
            )

            return

        self.pending_parent.add_child(
            self.selected_object
        )

        self.ai_console.append(

            f"{self.selected_object.name} "
            f"parented to "
            f"{self.pending_parent.name}"

        )

        self.viewport.update()

        print(
            "----------- Scene Graph -----------"
        )

        for obj in self.scene_objects:

            parent = (
                obj.parent.name
                if obj.parent
                else "None"
            )

            print(
                f"{obj.name} -> Parent: {parent}"
            )

    # ========================================================
    # SAVE
    # ========================================================

    def save_scene(self):

        filename = (
            "projects/scene.ai3d"
        )

        try:

            self.project_manager.save_project(

                filename,

                self.scene_objects

            )

            self.ai_console.append(
                "Scene Saved"
            )

        except Exception as e:

            print(
                "Save error:",
                e
            )

            self.ai_console.append(
                "Scene Save Failed"
            )

    # ========================================================
    # LOAD
    # ========================================================

    def load_scene(self):

        filename = (
            "projects/scene.ai3d"
        )

        try:

            loaded_objects = (
                self.project_manager.load_project(
                    filename
                )
            )

            if loaded_objects is None:
                return

            self.scene_objects = (
                loaded_objects
            )

            self.scene_manager.scene_objects = (
                self.scene_objects
            )

            self.scene_hierarchy.clear()

            for obj in self.scene_objects:

                self.scene_hierarchy.addItem(
                    obj.name
                )

            self.selected_object = None

            self.viewport.set_selected_object(
                None
            )

            self.viewport.update_scene(
                self.scene_objects
            )

            self.viewport.update()

            self.ai_console.append(
                "Scene Loaded"
            )

        except Exception as e:

            print(
                "Load error:",
                e
            )

            self.ai_console.append(
                "Scene Load Failed"
            )

    # ========================================================
    # KEYBOARD SHORTCUTS
    # ========================================================

    def keyPressEvent(self, event):

        key = event.key()

        modifiers = (
            event.modifiers()
        )

        print(
            "MAIN KEY:",
            key
        )

        # ----------------------------------------------------
        # Duplicate
        # Ctrl + D
        # ----------------------------------------------------

        if (
            key == Qt.Key_D
            and modifiers & Qt.ControlModifier
        ):

            self.duplicate_selected_object()

            return

        # ----------------------------------------------------
        # Object / Edit Mode
        # Tab
        # ----------------------------------------------------

        if key == Qt.Key_Tab:

            self.mode_manager.toggle()

            print(
                "MODE:",
                self.mode_manager.get_mode()
            )

            self.viewport.update()

            return

        # ----------------------------------------------------
        # Parent Candidate
        # Ctrl + P
        # ----------------------------------------------------

        if (
            key == Qt.Key_P
            and modifiers == Qt.ControlModifier
        ):

            self.set_parent_candidate()

            return

        # ----------------------------------------------------
        # Parent Object
        # Ctrl + Shift + P
        # ----------------------------------------------------

        if (
            key == Qt.Key_P
            and modifiers
            == (
                Qt.ControlModifier
                | Qt.ShiftModifier
            )
        ):

            self.parent_selected_object()

            return

        # ----------------------------------------------------
        # Delete
        # ----------------------------------------------------

        if key == Qt.Key_Delete:

            self.delete_selected_object()

            return

        # ----------------------------------------------------
        # Rename
        # Ctrl + R
        # ----------------------------------------------------

        if (
            key == Qt.Key_R
            and modifiers & Qt.ControlModifier
        ):

            self.rename_selected_object()

            return

        # ----------------------------------------------------
        # F1 = Move
        # ----------------------------------------------------

        if key == Qt.Key_F1:

            self.activate_move_tool()

            return

        # ----------------------------------------------------
        # F2 = Rotate
        # ----------------------------------------------------

        if key == Qt.Key_F2:

            self.activate_rotate_tool()

            return

        # ----------------------------------------------------
        # F3 = Scale
        # ----------------------------------------------------

        if key == Qt.Key_F3:

            self.activate_scale_tool()

            return

        # ----------------------------------------------------
        # Pass Other Keys
        # ----------------------------------------------------

        super().keyPressEvent(
            event
        )

    # ========================================================
    # HAND TRACKING
    # ========================================================

    def update_hand_control(self):

        if not hasattr(
            self,
            "tracker"
        ):

            return

        success, frame = (
            self.cap.read()
        )

        if not success:
            return

        # ----------------------------------------------------
        # Mirror Camera
        # ----------------------------------------------------

        frame = cv2.flip(
            frame,
            1
        )

        # ----------------------------------------------------
        # Hand Detection
        # ----------------------------------------------------

        self.tracker.get_hand_position(
            frame
        )

        palm = (
            self.tracker.get_palm_position()
        )

        # ----------------------------------------------------
        # Debug Frame
        # ----------------------------------------------------

        debug_frame = (
            frame.copy()
        )

        if (
            self.tracker.last_result
            and
            self.tracker.last_result.hand_landmarks
        ):

            hand = (
                self.tracker
                .last_result
                .hand_landmarks[0]
            )

            h, w, _ = (
                debug_frame.shape
            )

            # ------------------------------------------------
            # Landmarks
            # ------------------------------------------------

            for landmark in hand:

                px = int(
                    landmark.x * w
                )

                py = int(
                    landmark.y * h
                )

                cv2.circle(

                    debug_frame,

                    (
                        px,
                        py
                    ),

                    5,

                    (
                        0,
                        255,
                        0
                    ),

                    -1

                )

            # ------------------------------------------------
            # Connections
            # ------------------------------------------------

            connections = [

                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),

                (0, 5),
                (5, 6),
                (6, 7),
                (7, 8),

                (5, 9),
                (9, 10),
                (10, 11),
                (11, 12),

                (9, 13),
                (13, 14),
                (14, 15),
                (15, 16),

                (13, 17),
                (17, 18),
                (18, 19),
                (19, 20),

                (0, 17)

            ]

            for start, end in connections:

                p1 = hand[start]

                p2 = hand[end]

                cv2.line(

                    debug_frame,

                    (
                        int(p1.x * w),
                        int(p1.y * h)
                    ),

                    (
                        int(p2.x * w),
                        int(p2.y * h)
                    ),

                    (
                        255,
                        0,
                        0
                    ),

                    2

                )

        # ----------------------------------------------------
        # Send Webcam Frame to Viewport
        # ----------------------------------------------------

        self.viewport.update_webcam_frame(
            debug_frame
        )

        # ----------------------------------------------------
        # Hand Cursor
        # ----------------------------------------------------

        if palm is not None:

            x, y, z = palm

            world_x = (
                x - 0.5
            ) * 2

            world_y = -(
                y - 0.5
            ) * 2

            self.viewport.update_cursor(

                world_x,

                world_y

            )

        # ----------------------------------------------------
        # Pinch / Grab
        # ----------------------------------------------------

        pinching = (
            self.tracker.is_pinching()
        )

        grab_event = (
            self.interaction.update_grab(
                pinching
            )
        )

        if grab_event:

            if self.interaction.is_holding:

                axes = (
                    self.tracker
                    .get_palm_axes()
                )

                if (
                    axes is not None
                    and
                    self.viewport.selected_object
                ):

                    self.gesture.grab(

                        self.viewport.selected_object,

                        axes

                    )

                    self.gesture.grab_pinch_distance = (

                        self.tracker
                        .get_pinch_distance()

                    )

            else:

                self.gesture.release()

        # ----------------------------------------------------
        # Move / Rotate / Scale With Hand
        # ----------------------------------------------------

        if (
            self.interaction.is_holding
            and
            self.viewport.selected_object
            and
            palm is not None
        ):

            smooth = 0.20

            obj = (
                self.viewport.selected_object
            )

            # ------------------------------------------------
            # Position
            # ------------------------------------------------

            obj.position[0] += (

                world_x
                - obj.position[0]

            ) * smooth

            obj.position[1] += (

                world_y
                - obj.position[1]

            ) * smooth

            # ------------------------------------------------
            # Palm Orientation
            # ------------------------------------------------

            axes = (
                self.tracker
                .get_palm_axes()
            )

            if axes is not None:

                right, up, forward = axes

                obj.rotation[0] = (
                    up[1] * 180
                )

                obj.rotation[1] = (
                    right[0] * 180
                )

                obj.rotation[2] = (
                    forward[2] * 180
                )

                # ------------------------------------------------
                # Pinch Scaling
                # ------------------------------------------------

                current_distance = (
                    self.tracker
                    .get_pinch_distance()
                )

                if (
                    current_distance is not None
                    and
                    self.gesture.grab_pinch_distance is not None
                ):

                    scale_factor = (

                        current_distance
                        /
                        self.gesture.grab_pinch_distance

                    )

                    scale_factor = max(
                        0.3,
                        min(
                            scale_factor,
                            3.0
                        )
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

    # ========================================================
    # MOUSE FOCUS
    # ========================================================

    def mousePressEvent(self, event):

        if hasattr(
            self,
            "viewport"
        ):

            self.viewport.setFocus()

        super().mousePressEvent(
            event
        )

    # ========================================================
    # APPLICATION EVENT HANDLING
    # ========================================================

    def event(self, event):

        try:

            return super().event(
                event
            )

        except Exception as e:

            print(
                "EVENT ERROR:",
                e
            )

            raise

    # ========================================================
    # APPLICATION SHUTDOWN
    # ========================================================

    def closeEvent(self, event):

        # ----------------------------------------------------
        # Stop Camera
        # ----------------------------------------------------

        if hasattr(
            self,
            "cap"
        ):

            self.cap.release()

        # ----------------------------------------------------
        # Close OpenCV
        # ----------------------------------------------------

        cv2.destroyAllWindows()

        event.accept()


# ============================================================
# FUTURE AI3D STUDIO FEATURE REGISTRY
# ============================================================
#
# These are the planned functional areas of AI3D Studio.
# They are intentionally kept as architecture documentation
# here rather than calling modules that do not yet exist.
#
# 1. Advanced Object Editing
#    - Vertex editing
#    - Edge editing
#    - Face editing
#    - Extrusion
#    - Inset
#    - Loop cuts
#    - Mesh subdivision
#
# 2. Advanced Transform System
#    - Move gizmo
#    - Rotation gizmo
#    - Scale gizmo
#    - Local / Global transforms
#    - Transform snapping
#
# 3. Selection System
#    - Object selection
#    - Vertex selection
#    - Edge selection
#    - Face selection
#    - Box selection
#    - Ray-based selection
#
# 4. AI Creation System
#    - Natural-language object creation
#    - AI scene generation
#    - AI modeling commands
#    - AI material generation
#    - AI scene organization
#
# 5. Voice System
#    - Voice commands
#    - Speech-to-text
#    - Voice-controlled modeling
#
# 6. Hand / Gesture System
#    - Hand tracking
#    - Pinch selection
#    - Hand movement
#    - Gesture transforms
#    - Future holographic interaction
#
# 7. Scene Management
#    - Scene hierarchy
#    - Parenting
#    - Object duplication
#    - Object deletion
#    - Object renaming
#
# 8. Rendering
#    - Solid rendering
#    - Wireframe rendering
#    - Face highlighting
#    - Materials
#    - Lighting
#    - Shadows
#
# 9. Project System
#    - Save project
#    - Load project
#    - Scene serialization
#    - Project metadata
#
# 10. Future Holographic Interface
#     - Camera-based spatial interaction
#     - Gesture-controlled 3D UI
#     - Spatial gizmos
#     - Holographic-style viewport
#
# 11. Future Professional Features
#     - Undo / Redo
#     - Asset browser
#     - Material editor
#     - Camera controls
#     - Lighting controls
#     - Export / Import
#
# ============================================================


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    window = AI3DStudio()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()