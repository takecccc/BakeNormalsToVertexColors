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
        default="ANGLE_WEIGHT",
        items=[
            ("AVERAGE", "Average", "各頂点が関わるLoopの法線の平均"),
            ("CROSS", "Cross", "各法線と垂直な平面の交点"),
            ("VERTEX_NORMALS", "Vertex Normal", "各法線と垂直な平面の交点"),
            ("ANGLE_WEIGHT", "Angle Weight", "Angle weighted length."),
        ],
    )

    length_is_one: bpy.props.BoolProperty(
        name="set all length to 1",
        description="法線の長さを1に正規化するかどうか",
        default=False,
    )

    length_limit : bpy.props.FloatProperty(
        name="length limit",
        description="法線の長さの最大値。立方体を綺麗に出すならsqrt(3)以上。",
        default=2,
        min = 0,
    )

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
        )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "method")
        layout.prop(self, "length_is_one")
        if not self.length_is_one:
            layout.prop(self, "length_limit")

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bake_normals_to_vertex_colors(obj, self.method, self.length_is_one, self.length_limit)
        return {"FINISHED"}

def bake_normals_to_vertex_colors(obj:bpy.types.Object, method, length_is_one:bool, length_limit:float):
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
        
    elif method == "VERTEX_NORMALS":
        print("VERTEX_NORMALS")
        for i in range(len(mesh.vertices)):
            vertex_normals[i] = mesh.vertex_normals[i].vector

    elif method == "ANGLE_WEIGHT":
        print("ANGLE_WEIGHT")
        verts:list[bpy.types.MeshVertex] = mesh.vertices
        vert_dist = [0.0,] * len(verts)
        vert_accum = [0.0,] * len(verts)
        vert_normals:list[bpy.types.MeshNormalValue] = mesh.vertex_normals
        vert_nors:list[Vector] = [vert_normal.vector for vert_normal in vert_normals]
        for polygon in mesh.polygons:
            polygon:bpy.types.MeshPolygon
            # 最後のloopから処理する
            loop_prev:bpy.types.MeshLoop = mesh.loops[polygon.loop_indices[-2]]
            loop_curr:bpy.types.MeshLoop = mesh.loops[polygon.loop_indices[-1]]
            nor_prev:Vector = verts[loop_prev.vertex_index].co - verts[loop_curr.vertex_index].co
            for loop_index in polygon.loop_indices:
                loop_next:bpy.types.MeshLoop = mesh.loops[loop_index]
                nor_next:Vector = verts[loop_curr.vertex_index].co - verts[loop_next.vertex_index].co
                # loopの前後のエッジが成す角度を計算(0°は存在しない前提)
                angle = nor_prev.angle(-nor_next)
                vidx = loop_curr.vertex_index
                # 影響度を、エッジの成す角度とする
                vert_accum[vidx] += angle
                # 面の法線と頂点の法線の間の角度によって法線の長さを調整 1/cos(angle)
                # 45°の場合、sqrt(2)となり立方体が綺麗になる。
                # vertex_normalとface_normalの成す角度なので、90°を超えないはず。一応絶対値をとる。
                angle_cos = abs(vert_nors[vidx].dot(polygon.normal))
                # 限りなく尖った頂点の場合、長さが発散してしまうのを防ぐ。
                angle_cos = max(angle_cos, 1.0e-8)
                vert_dist[vidx] += (1.0/angle_cos) * angle
                # 次の頂点にそなえて更新
                loop_prev = loop_curr
                loop_curr = loop_next
        
        # 頂点の法線として格納
        for i in range(len(verts)):
            # distanceについて、重みつき平均をとる
            vertex_normals[i] = vert_nors[i] * (vert_dist[i] / vert_accum[i])
    else:
        raise Exception(f"not supported method : {method}")

    if length_is_one:
        for i in range(len(vertex_normals)):
            vertex_normals[i] = vertex_normals[i].normalized()    
    else:
        # dist_limitで制限
        for i in range(len(vertex_normals)):
            dist = vertex_normals[i].length
            normal = vertex_normals[i].normalized()
            dist = min(dist, length_limit)
            vertex_normals[i] = normal * dist

    # 最大の長さが1となるように正規化
    max_length = max([n.length for n in vertex_normals])
    if max_length > 0:
        coef = 1.0 / max_length
    else:
        coef = 1.0
    for i in range(len(vertex_normals)):
        vertex_normals[i] = vertex_normals[i] * coef

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
        world_normal = vertex_normals[loop.vertex_index]
        local_normal = Vector((
            Vector.dot(world_normal, loop.tangent.xyz),
            Vector.dot(world_normal, loop.bitangent.xyz),
            Vector.dot(world_normal, loop.normal.xyz)
        )).normalized()
        color = Vector((
            local_normal.x * 0.5 + 0.5,
            local_normal.y * 0.5 + 0.5,
            local_normal.z * 0.5 + 0.5,
            world_normal.length,
        ))
        vc[i].color = color
    mesh.update()
