import bpy
import mathutils

class BakeNormalsToVertexColors(bpy.types.Operator):
    bl_idname = "object.bake_normals_to_vertex_colors"
    bl_label = "Bake Normals To Vertex Colors"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Bake normals to vertex colors."

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
        )

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bake_normals_to_vertex_colors(obj)

        return {"FINISHED"}

def bake_normals_to_vertex_colors(obj:bpy.types.Object):
    if obj.type != "MESH":
        raise Exception("This object's type is not a MESH")

    mesh:bpy.types.Mesh = obj.data
    mesh.calc_tangents()

    vertex_normals = [mathutils.Vector.Fill(3, 0.0) for _ in range(len(mesh.vertices))]
    vertex_loop_count = [0] * len(mesh.vertices)

    # 各頂点の法線情報を収集
    for loop in mesh.loops:
        loop:bpy.types.MeshLoop
        vert_idx = loop.vertex_index
        vertex_normals[vert_idx] += loop.normal
        vertex_loop_count[vert_idx] += 1

    # 平均を計算
    for i, normal in enumerate(vertex_normals):
        if vertex_loop_count[i] == 0:
            raise Exception("vertex loop count is 0")
            continue
        vertex_normals[i] /= vertex_loop_count[i]
        vertex_normals[i].normalize()

    # 頂点カラーを取得
    if not mesh.vertex_colors:
        mesh.vertex_colors.new(name="NormalColors")
    vertex_colors:bpy.types.MeshLoopColorLayer = mesh.vertex_colors.active

    # 頂点カラーに書き込み
    for i, loop in enumerate(mesh.loops):
        loop:bpy.types.MeshLoop
        vert_idx = loop.vertex_index
        loop_tangent = loop.tangent
        loop_bitangent = loop.bitangent
        loop_normal = loop.normal
        world_normal = vertex_normals[vert_idx]
        local_normal = mathutils.Vector((
            mathutils.Vector.dot(world_normal, loop_tangent.xyz),
            mathutils.Vector.dot(world_normal, loop_bitangent.xyz),
            mathutils.Vector.dot(world_normal, loop_normal.xyz)
        )).normalized()
        color = mathutils.Vector((
            local_normal.x * 0.5 + 0.5,
            local_normal.y * 0.5 + 0.5,
            local_normal.z * 0.5 + 0.5,
            1.0
        ))
        vert_color:bpy.types.MeshVertColor = vertex_colors.data[i]
        vert_color.color = color
    
    mesh.update()
    