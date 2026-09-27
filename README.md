# AI3DSTUDIO

## AI-Powered 3D Designing Environment

AI3DSTUDIO is an AI-powered 3D designing application designed to make 3D modeling more accessible through a combination of traditional 3D interaction, AI commands, hand gestures, and an interactive web-based studio.

The project combines a Python desktop application with a browser-based version so that the core idea of AI-assisted 3D design can be explored both as a desktop application and as an accessible web application.

---

## Project Overview

Traditional 3D modeling applications often require users to learn a large number of tools, menus, shortcuts, and interaction techniques.

AI3DSTUDIO explores a different approach.

The goal is to allow users to interact with 3D objects using:

- Mouse
- Keyboard
- AI commands
- Hand gestures
- 3D transformation tools
- Object selection
- Scene hierarchy
- Web-based interaction

The system is being developed as an experimental AI-assisted 3D design environment.

---

# Main Features

## 1. 3D Viewport

AI3DSTUDIO provides an interactive 3D viewport for working with objects.

The viewport supports:

- 3D camera navigation
- Orbit
- Zoom
- Grid
- Coordinate axes
- Object selection
- Object transformations
- Real-time scene updates

---

## 2. Primitive Creation

The application supports basic 3D primitives.

Current primitives include:

- Cube
- Sphere
- Cylinder

These objects can be selected and transformed inside the scene.

---

## 3. Object Selection

Objects can be selected through the viewport or through the scene hierarchy.

The selection system is designed to provide the foundation for more advanced object interaction.

Selection is important because future AI and gesture-based operations can act directly on the selected object.

---

## 4. Transformation Tools

AI3DSTUDIO includes transformation tools inspired by professional 3D applications.

Current transformation modes include:

- Select
- Move
- Rotate
- Scale

The desktop version also contains interactive transformation gizmos.

The web version provides equivalent transformation functionality through browser-based controls.

---

# AI Command System

AI3DSTUDIO includes an AI command interface that allows users to describe simple operations using text.

Examples include:

```text
Create cube
Create sphere
Create cylinder
Delete object
Move object
Rotate object
Scale object
