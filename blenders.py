import bpy
import requests
from threading import Thread

# Server URL
SERVER_URL = "http://localhost:8000"

# Register properties
bpy.types.Scene.selected_object = bpy.props.PointerProperty(
    type=bpy.types.Object,  # Property type (Blender object)
    name="Selected Object"  # Property name
)

bpy.types.Scene.selected_endpoint = bpy.props.EnumProperty(
    items=[
        ("transform", "Transform", "Send position, rotation, and scale"),
        ("translation", "Translation", "Send only position"),
        ("rotation", "Rotation", "Send only rotation"),
        ("scale", "Scale", "Send only scale"),
        ("file-path", "File Path", "Get DCC file or project path"),
        ("add-item", "Add Item", "Add an item to the database"),
        ("remove-item", "Remove Item", "Remove an item from the database"),
        ("update-quantity", "Update Quantity", "Update an item's quantity"),
    ],
    name="Endpoint",  # Property name
    description="Select a server endpoint"  # Property description
)

bpy.types.Scene.object_to_create = bpy.props.EnumProperty(
    items=[
        ("CUBE", "Cube", "Create a cube"),
        ("SPHERE", "Sphere", "Create a sphere"),
        ("CONE", "Cone", "Create a cone"),
        ("CYLINDER", "Cylinder", "Create a cylinder"),
    ],
    name="Object to Create",  # Property name
    description="Select the type of object to create"  # Property description
)

bpy.types.Scene.item_name = bpy.props.StringProperty(
    name="Item Name",
    description="Name of the item to add/remove/update"
)

bpy.types.Scene.item_quantity = bpy.props.IntProperty(
    name="Item Quantity",
    description="Quantity of the item",
    default=1,
    min=1
)

# Function to send data to the server in a separate thread
def send_data_to_server(endpoint, data=None):
    # Construct the URL correctly
    url = f"{SERVER_URL}/{endpoint}"
    print(f"Sending data to {url}: {data}")  # Debugging line
    try:
        if data:
            print(f"Data being sent: {data}")  # Debugging line
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        if response.status_code == 200:
            print(f"Server response: {response.json()}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to the server: {e}")

# Plugin UI Panel
class OBJECT_PT_TransformPlugin(bpy.types.Panel):
    bl_label = "Transform Plugin"  # Title of the panel
    bl_space_type = 'VIEW_3D'  # Show the panel in the 3D Viewport
    bl_region_type = 'UI'  # Show the panel in the UI region
    bl_category = "new_Tool"  # Category under which the panel will appear

    def draw(self, context):
        layout = self.layout  # Layout manager for organizing UI elements
        scene = context.scene  # Current Blender scene

        # Object Selection
        row = layout.row()
        row.prop_search(scene, "selected_object", scene, "objects", text="Object")

        # Dropdown to Select Object Type to Create
        row = layout.row()
        row.prop(scene, "object_to_create", text="")  # Dropdown for object type

        # Button to Create New Object
        row.operator("object.create_new_object", text="Create", icon="ADD")

        # Transform Controls
        if scene.selected_object:  # Check if an object is selected
            obj = scene.selected_object
            layout.prop(obj, "location", text="Position")  # Position controls
            layout.prop(obj, "rotation_euler", text="Rotation")  # Rotation controls
            layout.prop(obj, "scale", text="Scale")  # Scale controls

        # Endpoint Dropdown
        layout.prop(scene, "selected_endpoint", text="Endpoint")

        # Additional UI for specific endpoints
        if scene.selected_endpoint in ["add-item", "remove-item", "update-quantity"]:
            layout.prop(scene, "item_name", text="Item Name")
            if scene.selected_endpoint in ["add-item", "update-quantity"]:
                layout.prop(scene, "item_quantity", text="Quantity")

        # Submit Button
        layout.operator("object.send_transform_data", text="Submit")

# Operator to Create New Object
class OBJECT_OT_CreateNewObject(bpy.types.Operator):
    bl_idname = "object.create_new_object"  # Unique identifier for the operator
    bl_label = "Create New Object"  # Label for the operator
    bl_options = {'REGISTER', 'UNDO'}  # Allow undo

    def execute(self, context):
        scene = context.scene

        # Create the selected object type
        if scene.object_to_create == "CUBE":
            bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        elif scene.object_to_create == "SPHERE":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        elif scene.object_to_create == "CONE":
            bpy.ops.mesh.primitive_cone_add(radius1=1, radius2=0, depth=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        elif scene.object_to_create == "CYLINDER":
            bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))

        new_object = context.active_object  # Get the newly created object
        scene.selected_object = new_object  # Set it as the selected object
        return {'FINISHED'}  # Indicate successful execution

# Operator to Send Transform Data
class OBJECT_OT_SendTransformData(bpy.types.Operator):
    bl_idname = "object.send_transform_data"  # Unique identifier for the operator
    bl_label = "Send Transform Data"  # Label for the operator

    def execute(self, context):
        scene = context.scene
        endpoint = scene.selected_endpoint

        if endpoint in ["transform", "translation", "rotation", "scale"] and not scene.selected_object:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}

        # Prepare data based on the selected endpoint
        data = None
        if endpoint == "transform":
            obj = scene.selected_object
            data = {
                "position": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale),
            }
        elif endpoint == "translation":
            obj = scene.selected_object
            data = {"position": list(obj.location)}
        elif endpoint == "rotation":
            obj = scene.selected_object
            data = {"rotation": list(obj.rotation_euler)}
        elif endpoint == "scale":
            obj = scene.selected_object
            data = {"scale": list(obj.scale)}
        elif endpoint == "add-item":
            data = {"name": scene.item_name, "quantity": scene.item_quantity}
        elif endpoint == "remove-item":
            data = {"name": scene.item_name}
        elif endpoint == "update-quantity":
            data = {"name": scene.item_name, "new_quantity": scene.item_quantity}

        print(f"Prepared data for {endpoint}: {data}")  # Debugging line

        # Send data to the server in a separate thread
        Thread(target=send_data_to_server, args=(endpoint, data)).start()

        self.report({'INFO'}, f"Data sent to {endpoint} endpoint!")
        return {'FINISHED'}

# Register and unregister functions
def register():
    bpy.utils.register_class(OBJECT_PT_TransformPlugin)  # Register the panel
    bpy.utils.register_class(OBJECT_OT_CreateNewObject)  # Register the create object operator
    bpy.utils.register_class(OBJECT_OT_SendTransformData)  # Register the send data operator

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_TransformPlugin)  # Unregister the panel
    bpy.utils.unregister_class(OBJECT_OT_CreateNewObject)  # Unregister the create object operator
    bpy.utils.unregister_class(OBJECT_OT_SendTransformData)  # Unregister the send data operator

    # Unregister properties
    del bpy.types.Scene.selected_object
    del bpy.types.Scene.selected_endpoint
    del bpy.types.Scene.object_to_create
    del bpy.types.Scene.item_name
    del bpy.types.Scene.item_quantity

# Run the script
if __name__ == "__main__":
    register()