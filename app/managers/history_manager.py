import copy

class HistoryManager:
    def __init__(self):
        self.undo_stack=[]
        self.redo_stack=[]
        self.operation_state=None

    def _capture_mesh_state(self,mesh):
        if mesh is None:return None
        s={"vertices":copy.deepcopy(getattr(mesh,"vertices",[])),"faces":copy.deepcopy(getattr(mesh,"faces",[])),"edges":copy.deepcopy(getattr(mesh,"edges",[])),"normals":copy.deepcopy(getattr(mesh,"normals",[])),"uvs":copy.deepcopy(getattr(mesh,"uvs",[]))}
        for a in ("selected_face","selected_vertex","selected_edge"):
            if hasattr(mesh,a):s[a]=copy.deepcopy(getattr(mesh,a))
        return s

    def _capture_object_state(self,obj):
        if obj is None:return None
        s={"object":obj,"name":copy.deepcopy(getattr(obj,"name","")),"object_type":copy.deepcopy(getattr(obj,"object_type",None)),"position":copy.deepcopy(getattr(obj,"position",[0.,0.,0.])),"rotation":copy.deepcopy(getattr(obj,"rotation",[0.,0.,0.])),"scale":copy.deepcopy(getattr(obj,"scale",[1.,1.,1.])),"mesh":self._capture_mesh_state(getattr(obj,"mesh",None))}
        if hasattr(obj,"bounding_box"):s["bounding_box"]=copy.deepcopy(obj.bounding_box)
        return s

    def _capture_scene_state(self,objects,selected=None):
        objs=list(objects or [])
        return {"objects":[self._capture_object_state(o) for o in objs if o is not None],"parents":{id(o):getattr(o,"parent",None) for o in objs if getattr(o,"parent",None) is not None},"selected_object":selected}

    def _restore_mesh_state(self,mesh,s):
        if mesh is None or s is None:return
        for a in ("vertices","faces","edges","normals","uvs"):
            setattr(mesh,a,copy.deepcopy(s.get(a,[])))
        for a in ("selected_face","selected_vertex","selected_edge"):
            if a in s:setattr(mesh,a,copy.deepcopy(s[a]))

    def _restore_object_state(self,s):
        if not s:return None
        o=s.get("object")
        if o is None:return None
        for a,d in (("name",o.name),("object_type",o.object_type),("position",[0.,0.,0.]),("rotation",[0.,0.,0.]),("scale",[1.,1.,1.])):
            setattr(o,a,copy.deepcopy(s.get(a,d)))
        ms=s.get("mesh")
        if ms is None:o.mesh=None
        else:
            if o.mesh is None:
                try:
                    from app.scene.mesh import Mesh; o.mesh=Mesh()
                except Exception: pass
            self._restore_mesh_state(o.mesh,ms)
        if "bounding_box" in s:o.bounding_box=copy.deepcopy(s["bounding_box"])
        return o

    def _restore_scene_state(self,objects,s):
        restored=[]
        for os in s.get("objects",[]):
            o=os.get("object")
            if o is not None:self._restore_object_state(os); restored.append(o)
        objects[:]=restored
        for o in restored:
            if hasattr(o,"parent"):o.parent=None
            if hasattr(o,"children"):o.children=[]
        for o in restored:
            parent=s.get("parents",{}).get(id(o))
            if parent in restored and parent is not o:
                if hasattr(parent,"add_child"):parent.add_child(o)
                else:o.parent=parent; parent.children.append(o)
        sel=s.get("selected_object")
        return sel if sel in restored else (restored[-1] if restored else None)

    def save_state(self,obj):
        if obj is not None:
            self.undo_stack.append({"type":"object","state":self._capture_object_state(obj)}); self.redo_stack.clear()

    def save_scene_state(self,objects,selected=None):
        self.undo_stack.append({"type":"scene","state":self._capture_scene_state(objects,selected)}); self.redo_stack.clear()

    def undo(self,objects=None):
        if not self.undo_stack:return None
        e=self.undo_stack.pop(); s=e["state"]
        if e["type"]=="scene":
            if objects is None:self.undo_stack.append(e); return None
            cur=self._capture_scene_state(objects); sel=self._restore_scene_state(objects,s); cur["selected_object"]=sel; self.redo_stack.append({"type":"scene","state":cur}); return sel
        o=s.get("object") if s else None
        if o is None:return None
        self.redo_stack.append({"type":"object","state":self._capture_object_state(o)}); self._restore_object_state(s); return o

    def redo(self,objects=None):
        if not self.redo_stack:return None
        e=self.redo_stack.pop(); s=e["state"]
        if e["type"]=="scene":
            if objects is None:self.redo_stack.append(e); return None
            cur=self._capture_scene_state(objects); sel=self._restore_scene_state(objects,s); cur["selected_object"]=sel; self.undo_stack.append({"type":"scene","state":cur}); return sel
        o=s.get("object") if s else None
        if o is None:return None
        self.undo_stack.append({"type":"object","state":self._capture_object_state(o)}); self._restore_object_state(s); return o

    def begin_action(self,obj):self.operation_state=self._capture_object_state(obj) if obj is not None else None
    def commit_action(self,obj):
        if self.operation_state is not None:
            self.undo_stack.append({"type":"object","state":self.operation_state}); self.redo_stack.clear()
        self.operation_state=None
    def cancel_action(self):
        if self.operation_state is None:return None
        o=self.operation_state.get("object"); self._restore_object_state(self.operation_state); self.operation_state=None; return o
    def has_operation(self):return self.operation_state is not None
    def can_undo(self):return bool(self.undo_stack)
    def can_redo(self):return bool(self.redo_stack)
    def undo_count(self):return len(self.undo_stack)
    def redo_count(self):return len(self.redo_stack)
    def clear(self):self.undo_stack.clear(); self.redo_stack.clear(); self.operation_state=None
