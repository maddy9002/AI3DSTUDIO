import json

from scene_object import SceneObject


class ProjectManager:

    def save_project(self, filename, scene_objects):

        data = []

        for obj in scene_objects:

            data.append({

                "name": obj.name,

                "type": obj.object_type,

                "position": obj.position,

                "rotation": obj.rotation,

                "scale": obj.scale

            })

        with open(filename, "w") as file:

            json.dump(data, file, indent=4)


    def load_project(self, filename):

        with open(filename, "r") as file:

            data = json.load(file)

        scene_objects = []

        for item in data:

            obj = SceneObject(

                item["name"],

                item["type"]

            )

            obj.position = item["position"]

            obj.rotation = item["rotation"]

            obj.scale = item["scale"]

            scene_objects.append(obj)

        return scene_objects