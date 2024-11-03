import bpy
import mathutils
from mathutils import Vector

class BakeNormalsToVertexColors(bpy.types.Operator):
    bl_idname = "object.bake_normals_to_vertex_colors"
    bl_label = "Bake Normals To Vertex Colors"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Bake normals to vertex colors."

    method: bpy.props.EnumProperty(
        name="Method",
        description="method of normal calculation.",
        default="VERTEX_NORMALS",
        items=[
            ("AVERAGE", "Average", "各頂点が関わるLoopの法線の平均"),
            ("CROSS", "Cross", "各法線と垂直な平面の交点"),
            ("VERTEX_NORMALS", "Vertex Normal", "各法線と垂直な平面の交点"),
        ]
    )

    normalize_distance : bpy.props.BoolProperty(
        name="Normalize_distance",
        description="CROSS選択時に法線の長さを正規化するかどうか",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
        )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "method")
        if(self.method == "CROSS"):
            layout.prop(self, "normalize_distance")

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bake_normals_to_vertex_colors(obj, self.method, self.normalize_distance)
        return {"FINISHED"}

def bake_normals_to_vertex_colors(obj:bpy.types.Object, method, normalize_distance:bool):
    if obj.type != "MESH":
        raise Exception("This object's type is not a MESH")

    mesh:bpy.types.Mesh = obj.data
    mesh.calc_tangents()

    vertex_normals = [Vector.Fill(3, 0.0) for _ in range(len(mesh.vertices))]
    if method == "AVERAGE":
        print("AVERAGE")
        vertex_loop_count = [0] * len(mesh.vertices)

        # 各頂点の法線情報を収集
        for loop in mesh.loops:
            loop:bpy.types.MeshLoop
            vert_idx = loop.vertex_index
            vertex_normals[vert_idx] += loop.normal
            vertex_loop_count[vert_idx] += 1

        # 平均を計算
        for i in range(len(vertex_normals)):
            if vertex_loop_count[i] == 0:
                raise Exception("vertex loop count is 0")
            vertex_normals[i] /= vertex_loop_count[i]
            vertex_normals[i].normalize()

    elif method == "CROSS":
        print("CROSS")
        def make_new_normal(n1:Vector, n2:Vector):
            line_a, line_b = mathutils.geometry.intersect_plane_plane(n1,n1,n2,n2)
            if line_a is None:
                return (n1 + n2) * 0.5
            plane_co = Vector()
            plane_n = n1.cross(n2)
            normal = mathutils.geometry.intersect_line_plane(line_a, line_b, plane_co, plane_n)
            if normal is None:
                return (n1 + n2) * 0.5
            return normal

        vertex_normals = [None] * len(mesh.vertices)
        for loop in mesh.loops:
            loop:bpy.types.MeshLoop
            vert_idx = loop.vertex_index
            if vertex_normals[vert_idx] is None:
                vertex_normals[vert_idx] = loop.normal
            else:
                vertex_normals[vert_idx] = make_new_normal(vertex_normals[vert_idx], loop.normal)
        
        if normalize_distance:
            for i in range(len(vertex_normals)):
                vertex_normals[i] = vertex_normals[i].normalized()
        else:
            # 最大の長さが1となるように正規化
            max_length = 0
            for n in vertex_normals:
                if max_length < n.length:
                    max_length = n.length
            if max_length > 0:
                coef = 1.0 / max_length
            else:
                coef = 1.0
            for i in range(len(vertex_normals)):
                vertex_normals[i] = vertex_normals[i] * coef
                if vertex_normals[i] > 1.0:
                    vertex_normals[i] = 1.0
    
    elif method == "VERTEX_NORMALS":
        print("VERTEX_NORMALS")
        for i in range(len(mesh.vertices)):
            vertex_normals[i] = mesh.vertex_normals[i].vector
    else:
        raise Exception(f"not supported method : {method}")

    # 頂点カラーを取得
    if not mesh.color_attributes:
        vertex_color = mesh.color_attributes.new(
                                                 name="NormalColors",
                                                 type="BYTE_COLOR",
                                                 domain="CORNER")
    else:
        vertex_color = mesh.attributes.active_color


    vc = vertex_color.data
    # 頂点カラーに書き込み
    for i, loop in enumerate(mesh.loops):
        loop:bpy.types.MeshLoop
        vert_idx = loop.vertex_index
        loop_tangent = loop.tangent
        loop_bitangent = loop.bitangent
        loop_normal = loop.normal
        world_normal = vertex_normals[vert_idx]
        local_normal = Vector((
            Vector.dot(world_normal, loop_tangent.xyz),
            Vector.dot(world_normal, loop_bitangent.xyz),
            Vector.dot(world_normal, loop_normal.xyz)
        )).normalized()
        color = Vector((
            local_normal.x * 0.5 + 0.5,
            local_normal.y * 0.5 + 0.5,
            local_normal.z * 0.5 + 0.5,
            world_normal.length,
        ))
        vc[i].color = color
    mesh.update()
