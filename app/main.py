import sys
import os
import inspect
import cv2
import copy 

from PySide6.QtCore import Qt, QTimer, QEvent
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

project_root = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if project_root not in sys.path:
    sys.path.append(project_root)

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

from app.ai.command_parser import CommandParser
from app.ai.command_executor import CommandExecutor
from app.ai.ai_engine import AIEngine

from app.database.database import save_model
from app.project.project_manager import ProjectManager
from app.managers.history_manager import HistoryManager

from webcam.hand_tracker_class import HandTracker
import webcam.hand_tracker_class
from webcam.gesture_controller import GestureController

from interaction.interaction_manager import InteractionManager

import time

print("OK")
print("HandTracker loaded from:")
print(inspect.getfile(HandTracker))
print("Methods:")
print(dir(HandTracker))
print(webcam.hand_tracker_class.__file__)


ray = Ray(
    origin=[0, 0, 5],
    direction=[2, 0, -4]
)

print("Origin:", ray.origin)
print("Direction:", ray.direction)


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

        self.pending_parent = None

        self.cube_count = 0

        self.command_parser = CommandParser()

        self.command_executor = CommandExecutor(self)

        print("INIT COMPLETE")
        print("Parser:", self.command_parser)
        print("Executor:", self.command_executor)

        self.project_manager = ProjectManager()

        self.mode_manager = ModeManager()

        self.tool_manager = ToolManager()

        print(self.tool_manager)

        self.ai = AIEngine()

        self.setup_ui()

        self.tracker = HandTracker()

        print(inspect.getfile(HandTracker))

        print(dir(self.tracker))

        self.gesture = GestureController()

        self.first_start_time = None
        self.edit_mode_activated = False

        # Tracks one continuous hand-gesture transform as a single
        # undoable history operation.
        self._hand_history_active = False
        self._hand_history_object = None

        self.open_hand_holding = False
        self.open_hand_object = None
        self.open_hand_start_position = None

        self.pinch_rotating = False
        self.pinch_rotation_object = None
        self.pinch_previous_palm = None

        self.gesture_mode_start_time = None
        self.gesture_mode_activated = False
        self.last_gesture_mode = None

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

        # ========================================================
        # GLOBAL KEYBOARD EVENT FILTER
        # ========================================================
        #
        # This allows Ctrl+Z / Ctrl+Y to work even when the
        # Viewport has keyboard focus.
        #
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event):

        if event.type() == QEvent.KeyPress:

            # ----------------------------------------------------
            # Do not intercept Ctrl+Z / Ctrl+Y while typing
            # into the AI command bar.
            # ----------------------------------------------------

            if watched == self.command_bar:

                return super().eventFilter(
                    watched,
                    event
                )

            # ----------------------------------------------------
            # ESC - CANCEL ACTIVE HAND GESTURE
            # ----------------------------------------------------

            if event.key() == Qt.Key_Escape:

                if self._hand_history_active:

                    history_object = self._hand_history_object

                    if history_object is not None:
                        restored_object = (
                            self.history_manager.cancel_action()
                        )

                        if restored_object is not None:
                            self.selected_object = restored_object

                            self.viewport.set_selected_object(
                                restored_object
                            )

                    self._hand_history_active = False
                    self._hand_history_object = None

                    self.gesture.release()

                    # Reset the grab state so the next pinch starts
                    # a fresh history operation.
                    self.interaction.is_holding = False

                    self.viewport.update_scene(
                        self.scene_objects
                    )

                    self.viewport.update()

                    print("ESC - HAND GESTURE CANCELLED")

                    return True

                # No hand operation is active. Returning False allows
                # the focused widget/viewport to process ESC normally.
                return False

            # ----------------------------------------------------
            # UNDO
            # ----------------------------------------------------

            if (
                event.key() == Qt.Key_Z
                and event.modifiers() & Qt.ControlModifier
                and not (
                    event.modifiers()
                    & Qt.ShiftModifier
                )
            ):

                print("UNDO SHORTCUT")

                restored_object = (
                    self.history_manager.undo(
                        self.scene_objects
                    )
                )

                if restored_object is not None:

                    self._refresh_scene_from_history(
                        restored_object
                    )

                    self.ai_console.append(
                        "Undo"
                    )

                else:

                    print(
                        "Nothing to undo."
                    )

                return True

            # ----------------------------------------------------
            # REDO
            # ----------------------------------------------------

            if (
                event.key() == Qt.Key_Y
                and event.modifiers() & Qt.ControlModifier
            ):

                print("REDO SHORTCUT")

                restored_object = (
                    self.history_manager.redo(
                        self.scene_objects
                    )
                )

                if restored_object is not None:

                    self._refresh_scene_from_history(
                        restored_object
                    )

                    self.ai_console.append(
                        "Redo"
                    )

                else:

                    print(
                        "Nothing to redo."
                    )

                return True

        return super().eventFilter(
            watched,
            event
        )

    def setup_ui(self):

        # ==========================
        # Toolbar
        # ==========================

        toolbar = QToolBar(
            "Main Toolbar"
        )

        self.addToolBar(
            toolbar
        )

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

        self.cube_btn = QPushButton(
            "Cube"
        )

        self.sphere_btn = QPushButton(
            "Sphere"
        )

        self.cylinder_btn = QPushButton(
            "Cylinder"
        )

        self.save_toolbar_btn = QPushButton(
            "Save"
        )

        self.load_toolbar_btn = QPushButton(
            "Load"
        )

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

        self.setCentralWidget(
            central
        )

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

        left_widget.setLayout(
            left_layout
        )

        # ==========================
        # Viewport
        # ==========================

        self.history_manager = HistoryManager()

        self.viewport = Viewport(
            self
        )

        self.viewport.setFocus()

        self.viewport.history_manager = (
            self.history_manager
        )

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

        self.ai_console.setReadOnly(
            True
        )

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

    def create_primitive(
        self,
        primitive_type
    ):

        primitive_type = (
            primitive_type.capitalize()
        )

        if not hasattr(
            self,
            "primitive_counts"
        ):

            self.primitive_counts = {}

        if primitive_type not in (
            self.primitive_counts
        ):

            self.primitive_counts[
                primitive_type
            ] = 0

        self.primitive_counts[
            primitive_type
        ] += 1

        self.history_manager.save_scene_state(
            self.scene_objects,
            self.selected_object
        )

        obj = PrimitiveFactory.create(

            f"{primitive_type} "
            f"{self.primitive_counts[primitive_type]}",

            primitive_type

        )

        obj.position = [

            -2.0
            + (
                len(self.scene_objects)
                * 1.5
            ),

            0.0,

            0.0

        ]

        self.scene_objects.append(
            obj
        )

        self.scene_hierarchy.addItem(
            obj.name
        )

        self.scene_hierarchy.setCurrentRow(
            len(self.scene_objects) - 1
        )

        self.viewport.set_selected_object(
            obj
        )

        self.selected_object = obj

        self.viewport.update_scene(
            self.scene_objects
        )

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

    def run_ai_command(self):

        text = self.command_bar.text().strip()

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
                command.get("argument")
            )

        except Exception:

            print(
                "Using Local Command Parser"
            )

            command, argument = (
                self.command_parser.parse(
                    text
                )
            )

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

            self.history_manager.save_scene_state(
                self.scene_objects,
                self.selected_object
            )

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

            self.viewport.set_selected_object(
                None
            )

            self.selected_object = None

            self.viewport.update_scene(
                self.scene_objects
            )

            self.viewport.update()

            self.ai_console.append(
                f"Deleted {obj.name}"
            )

    def duplicate_selected_object(self):

        if self.selected_object is None:
            return

        self.history_manager.save_scene_state(
            self.scene_objects,
            self.selected_object
        )

        self.cube_count += 1

        old = self.selected_object

        new = SceneObject(

            f"Cube {self.cube_count}",

            old.object_type

        )

        new.position = (
            old.position.copy()
        )

        new.rotation = (
            old.rotation.copy()
        )

        new.scale = (
            old.scale.copy()
        )

        if old.mesh is not None:
            new.mesh = copy.deepcopy(
                old.mesh
            )

        new.position[0] += 0.5
        new.position[1] += 0.5

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

    def save_scene(self):

        filename = (
            "projects/scene.ai3d"
        )

        self.project_manager.save_project(

            filename,

            self.scene_objects

        )

        self.ai_console.append(
            "Scene Saved"
        )

    def load_scene(self):

        filename = (
            "projects/scene.ai3d"
        )

        self.scene_objects = (
            self.project_manager.load_project(
                filename
            )
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

    def _refresh_scene_from_history(self, selected_object):

        self.scene_manager.scene_objects = self.scene_objects

        self.scene_hierarchy.clear()

        selected_row = -1

        for index, obj in enumerate(self.scene_objects):

            self.scene_hierarchy.addItem(obj.name)

            if obj is selected_object:

                selected_row = index

        self.selected_object = selected_object

        self.viewport.set_selected_object(selected_object)

        if selected_row >= 0:

            self.scene_hierarchy.setCurrentRow(selected_row)

        self.viewport.update_scene(self.scene_objects)

        self.viewport.update()

    def select_object(
        self,
        item
    ):

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

        self.ai_console.append(
            f"Selected {selected.name}"
        )

    def set_parent_candidate(self):

        if self.selected_object is None:
            return

        self.pending_parent = (
            self.selected_object
        )

        self.ai_console.append(
            "Parent candidate: "
            f"{self.selected_object.name}"
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
                "Parent and child cannot "
                "be the same."
            )

            return

        self.pending_parent.add_child(
            self.selected_object
        )

        self.ai_console.append(
            f"{self.selected_object.name} "
            "parented to "
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
                f"{obj.name} -> "
                f"Parent: {parent}"
            )

    def keyPressEvent(
        self,
        event
    ):

        print(
            "MAIN KEY:",
            event.key()
        )

        # --------------------------------------------------------
        # Ctrl + D
        # --------------------------------------------------------

        if (
            event.key() == Qt.Key_D
            and event.modifiers()
            & Qt.ControlModifier
        ):

            self.duplicate_selected_object()

            return

        # --------------------------------------------------------
        # TAB
        # --------------------------------------------------------

        if event.key() == Qt.Key_Tab:

            self.mode_manager.toggle()

            print(
                "Mode:",
                self.mode_manager.get_mode()
            )

            self.viewport.update()

            return

        # --------------------------------------------------------
        # Ctrl + P
        # --------------------------------------------------------

        if (
            event.key() == Qt.Key_P
            and event.modifiers()
            == Qt.ControlModifier
        ):

            self.set_parent_candidate()

            return

        # --------------------------------------------------------
        # Ctrl + Shift + P
        # --------------------------------------------------------

        if (
            event.key() == Qt.Key_P
            and event.modifiers()
            == (
                Qt.ControlModifier
                | Qt.ShiftModifier
            )
        ):

            self.parent_selected_object()

            return

        # --------------------------------------------------------
        # Delete
        # --------------------------------------------------------

        if event.key() == Qt.Key_Delete:

            self.delete_selected_object()

            return

        # --------------------------------------------------------
        # Ctrl + R
        # --------------------------------------------------------

        if (
            event.key() == Qt.Key_R
            and event.modifiers()
            & Qt.ControlModifier
        ):

            self.rename_selected_object()

            return

        # --------------------------------------------------------
        # F1
        # --------------------------------------------------------

        if event.key() == Qt.Key_F1:

            print(
                "F1 BLOCK ENTERED"
            )

            self.viewport.tool_manager.set_tool(
                ToolManager.MOVE
            )

            self.viewport.update()

            return

        # --------------------------------------------------------
        # F2
        # --------------------------------------------------------

        if event.key() == Qt.Key_F2:

            print(
                "F2 BLOCK ENTERED"
            )

            self.viewport.tool_manager.set_tool(
                ToolManager.ROTATE
            )

            self.viewport.update()

            return

        # --------------------------------------------------------
        # F3
        # --------------------------------------------------------

        if event.key() == Qt.Key_F3:

            print(
                "F3 BLOCK ENTERED"
            )

            self.viewport.tool_manager.set_tool(
                ToolManager.SCALE
            )

            self.viewport.update()

            return

        # --------------------------------------------------------
        # Selected object information
        # --------------------------------------------------------

        if self.selected_object is None:

            super().keyPressEvent(
                event
            )

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

        new_name, ok = (
            QInputDialog.getText(
                self,
                "Rename Object",
                "New Name:",
                text=self.selected_object.name
            )
        )

        if not ok:
            return

        if not new_name.strip():
            return

        self.selected_object.name = (
            new_name.strip()
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
                self.selected_object.name
            )

        self.ai_console.append(
            f"Renamed to "
            f"{self.selected_object.name}"
        )

    def update_hand_control(self):

        success, frame = self.cap.read()

        if not success:
            return

        frame = cv2.flip(frame, 1)

        self.tracker.get_hand_position(frame)

        palm = self.tracker.get_palm_position()

        debug_frame = frame.copy()

        if (
            self.tracker.last_result
            and self.tracker.last_result.hand_landmarks
        ):

            for hand in self.tracker.last_result.hand_landmarks:

                h, w, _ = debug_frame.shape

                for landmark in hand:

                    px = int(landmark.x * w)
                    py = int(landmark.y * h)

                    cv2.circle(
                        debug_frame,
                        (px, py),
                        5,
                        (0, 255, 0),
                        -1
                    )

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
                        (255, 0, 0),
                        2
                    )

        self.viewport.update_webcam_frame(
            debug_frame
        )

        world_x = None
        world_y = None

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

        gesture = self.tracker.get_gesture()

        print(
            "HAND GESTURE:",
            gesture
        )

        edit_mode = (
            self.viewport.main_window
            .mode_manager
            .get_mode()
            == "EDIT"
        )

        if edit_mode and gesture in (
            "ONE_FINGER",
            "TWO_FINGERS",
            "THREE_FINGERS"
        ):

            if self.last_gesture_mode != gesture:

                self.gesture_mode_start_time = time.time()
                self.gesture_mode_activated = False
                self.last_gesture_mode = gesture

            elif (
                time.time()
                - self.gesture_mode_start_time
                >= 1.0
                and not self.gesture_mode_activated
            ):

                if gesture == "ONE_FINGER":

                    self.viewport.set_vertex_mode()

                    self.ai_console.append(
                        "HAND GESTURE: Vertex Mode"
                    )

                elif gesture == "TWO_FINGERS":

                    self.viewport.set_edge_mode()

                    self.ai_console.append(
                        "HAND GESTURE: Edge Mode"
                    )

                elif gesture == "THREE_FINGERS":

                    self.viewport.set_face_mode()

                    self.ai_console.append(
                        "HAND GESTURE: Face Mode"
                    )

                self.gesture_mode_activated = True

        else:

            self.gesture_mode_start_time = None
            self.gesture_mode_activated = False
            self.last_gesture_mode = None

        if gesture == "FIST":

            if self.fist_start_time is None:

                self.fist_start_time = time.time()

            elif (
                time.time()
                - self.fist_start_time
                >= 1.0
                and not self.edit_mode_activated
            ):

                self.viewport.main_window.mode_manager.toggle()

                new_mode = (
                    self.viewport.main_window
                    .mode_manager
                    .get_mode()
                )

                print(
                    "MODE:",
                    new_mode
                )

                if new_mode == "EDIT":

                    self.ai_console.append(
                        "HAND GESTURE: Edit Mode activated"
                    )

                else:

                    self.ai_console.append(
                        "HAND GESTURE: Object Mode activated"
                    )

                self.viewport.update()

                self.edit_mode_activated = True

        else:

            self.fist_start_time = None
            self.edit_mode_activated = False

        if gesture == "TWO_HAND_PINCH":

            obj = self.viewport.selected_object

            if obj is None:
                return

            edit_mode = (
                self.viewport.main_window
                .mode_manager
                .get_mode()
                == "EDIT"
            )

            selected_vertices = set(
                getattr(
                    self.viewport,
                    "selected_vertices",
                    set()
                )
            )

            if edit_mode and selected_vertices:

                positions = (
                    self.tracker
                    .get_two_hand_palm_positions()
                )

                if len(positions) != 2:
                    return

                center_x = (
                    positions[0][0]
                    + positions[1][0]
                ) / 2.0

                center_y = (
                    positions[0][1]
                    + positions[1][1]
                ) / 2.0

                if not hasattr(
                    self,
                    "_two_hand_vertex_active"
                ):

                    self._two_hand_vertex_active = False

                if not self._two_hand_vertex_active:

                    self.history_manager.begin_action(
                        obj
                    )

                    self._two_hand_vertex_active = True

                    self._two_hand_vertex_object = obj

                    self._two_hand_vertex_previous = (
                        center_x,
                        center_y
                    )

                previous_x, previous_y = (
                    self._two_hand_vertex_previous
                )

                dx = center_x - previous_x
                dy = center_y - previous_y

                move_x = dx * 2.0
                move_y = -dy * 2.0

                mesh = obj.mesh

                if mesh is None:
                    return

                for vertex_index in selected_vertices:

                    if (
                        vertex_index < 0
                        or vertex_index >= len(mesh.vertices)
                    ):
                        continue

                    mesh.vertices[
                        vertex_index
                    ][0] += move_x

                    mesh.vertices[
                        vertex_index
                    ][1] += move_y

                mesh.build_edges()

                self._two_hand_vertex_previous = (
                    center_x,
                    center_y
                )

                self.viewport.update()

                return

            if hasattr(
                self,
                "_two_hand_vertex_active"
            ):

                if self._two_hand_vertex_active:

                    vertex_object = getattr(
                        self,
                        "_two_hand_vertex_object",
                        None
                    )

                    if vertex_object is not None:

                        self.history_manager.commit_action(
                            vertex_object
                        )

                    self._two_hand_vertex_active = False
                    self._two_hand_vertex_object = None
                    self._two_hand_vertex_previous = None

            distance = (
                self.tracker
                .get_two_hand_distance()
            )

            if distance is not None:

                if not hasattr(
                    self,
                    "_two_hand_scale_active"
                ):

                    self._two_hand_scale_active = False

                if not self._two_hand_scale_active:

                    self.history_manager.begin_action(
                        obj
                    )

                    self._two_hand_scale_active = True

                    self._two_hand_scale_object = obj

                    self._two_hand_scale_distance = (
                        distance
                    )

                    self._two_hand_scale_start = (
                        obj.scale.copy()
                    )

                start_distance = (
                    self._two_hand_scale_distance
                )

                if start_distance > 0:

                    scale_factor = (
                        distance
                        / start_distance
                    )

                    scale_factor = max(
                        0.3,
                        min(
                            scale_factor,
                            3.0
                        )
                    )

                    start_scale = (
                        self._two_hand_scale_start
                    )

                    obj.scale[0] = (
                        start_scale[0]
                        * scale_factor
                    )

                    obj.scale[1] = (
                        start_scale[1]
                        * scale_factor
                    )

                    obj.scale[2] = (
                        start_scale[2]
                        * scale_factor
                    )

                    self.viewport.update()

            return

        if hasattr(
            self,
            "_two_hand_vertex_active"
        ):

            if self._two_hand_vertex_active:

                vertex_object = getattr(
                    self,
                    "_two_hand_vertex_object",
                    None
                )

                if vertex_object is not None:

                    self.history_manager.commit_action(
                        vertex_object
                    )

                self._two_hand_vertex_active = False
                self._two_hand_vertex_object = None
                self._two_hand_vertex_previous = None

        if hasattr(
            self,
            "_two_hand_scale_active"
        ):

            if self._two_hand_scale_active:

                scale_object = getattr(
                    self,
                    "_two_hand_scale_object",
                    None
                )

                if scale_object is not None:

                    self.history_manager.commit_action(
                        scale_object
                    )

                self._two_hand_scale_active = False
                self._two_hand_scale_object = None
                self._two_hand_scale_distance = None
                self._two_hand_scale_start = None

        if gesture == "OPEN_HAND":

            obj = self.viewport.selected_object

            if obj is not None and palm is not None:

                if not self.open_hand_holding:

                    self.history_manager.begin_action(
                        obj
                    )

                    self.open_hand_holding = True
                    self.open_hand_object = obj

                smooth = 0.20

                obj.position[0] += (
                    world_x
                    - obj.position[0]
                ) * smooth

                obj.position[1] += (
                    world_y
                    - obj.position[1]
                ) * smooth

                self.viewport.update()

            return

        if self.open_hand_holding:

            if self.open_hand_object is not None:

                self.history_manager.commit_action(
                    self.open_hand_object
                )

            self.open_hand_holding = False
            self.open_hand_object = None

        if gesture == "PINCH":

            obj = self.viewport.selected_object

            if obj is not None and palm is not None:

                if not self.pinch_rotating:

                    self.history_manager.begin_action(
                        obj
                    )

                    self.pinch_rotating = True
                    self.pinch_rotation_object = obj
                    self.pinch_previous_palm = palm

                else:

                    previous_x, previous_y, previous_z = (
                        self.pinch_previous_palm
                    )

                    current_x, current_y, current_z = palm

                    dx = current_x - previous_x
                    dy = current_y - previous_y

                    obj.rotation[1] += (
                        dx * 300
                    )

                    obj.rotation[0] += (
                        dy * 300
                    )

                    self.pinch_previous_palm = palm

                    self.viewport.update()

            return

        if self.pinch_rotating:

            if self.pinch_rotation_object is not None:

                self.history_manager.commit_action(
                    self.pinch_rotation_object
                )

            self.pinch_rotating = False
            self.pinch_rotation_object = None
            self.pinch_previous_palm = None

    def closeEvent(
        self,
        event
    ):

        if self._hand_history_active:

            history_object = self._hand_history_object

            if history_object is not None:

                self.history_manager.commit_action(
                    history_object
                )

            self._hand_history_active = False
            self._hand_history_object = None

        if hasattr(
            self,
            "cap"
        ):

            self.cap.release()

        cv2.destroyAllWindows()

        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)

        event.accept()

    def event(
        self,
        event
    ):

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


if __name__ == "__main__":

    app = QApplication([])

    window = AI3DStudio()

    window.show()

    app.exec()