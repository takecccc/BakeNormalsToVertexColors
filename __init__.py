from . import bake_normals_to_vertex_colors

if "bpy" in locals():
    # 2回目以降の読み込みではモジュールをリロード
    import importlib
    importlib.reload(bake_normals_to_vertex_colors)

import bpy

BakeNormalsToVertexColors = bake_normals_to_vertex_colors.BakeNormalsToVertexColors

bl_info = {
    "name" : "Bake Normals To Vertex Colors",
    "author" : "takec",
    "description" : "Bake normals to vertex colors.",
    "blender" : (4, 2, 0),
    "version" : (1, 2, 0),
    "location" : "View3D > Object",
    "warning" : "",
    "category" : "Object"
}

classes = (
    BakeNormalsToVertexColors,
)

def menu_fn(self, context):
    self.layout.operator(BakeNormalsToVertexColors.bl_idname, text="Bake Normals to Vertex Colors", icon='PLUGIN')

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_object.append(menu_fn)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_fn)
    for c in classes:
        bpy.utils.unregister_class(c)
