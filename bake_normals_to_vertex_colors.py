import bpy
import mathutils
from mathutils import Vector

class BakeNormalsToVertexColors(bpy.types.Operator):
    bl_idname = "object.bake_normals_to_vertex_colors"
    bl_label = "Bake Normals To Vertex Colors"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Bake normals to vertex colors."

    adjust_length: bpy.props.BoolProperty(
        name="adjust normal length",
        description="adjust normals length.",
        default=True,
    )

    length_limit : bpy.props.FloatProperty(
        name="length limit",
        description="法線の長さの最大値。立方体を綺麗に出すならsqrt(3)以上。",
        default=2,
        min = 1,
    )

    normalize_length: bpy.props.BoolProperty(
        name="normalize normal length",
        description="normalize normal max length to 1.",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
        )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "adjust_length")
        if self.adjust_length:
            layout.prop(self, "length_limit")
            layout.prop(self, "normalize_length")

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            bake_normals_to_vertex_colors(obj, self.adjust_length, self.length_limit, self.normalize_length)
        return {"FINISHED"}

def bake_normals_to_vertex_colors(obj:bpy.types.Object, adjust_length:bool, length_limit:float, normalize_length:bool):
    if obj.type != "MESH":
        raise Exception("This object's type is not a MESH")

    mesh:bpy.types.Mesh = obj.data
    mesh.calc_tangents()

    # 法線を取得
    vertex_normals:list[bpy.types.MeshNormalValue] = mesh.vertex_normals
    vert_nors_dir = [n.vector for n in vertex_normals] # 法線の方向
    vert_nors_length = [1.0,] * len(mesh.vertices) # 法線の長さ

    if adjust_length:
        # 鋭角で輪郭が細らないように調整
        verts:list[bpy.types.MeshVertex] = mesh.vertices
        vert_length_accum = [0.0,] * len(verts)
        vert_angle_accum = [0.0,] * len(verts)
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
                vert_angle_accum[vidx] += angle
                # 面の法線と頂点の法線の間の角度によって法線の長さを調整 1/cos(angle)
                # 45°の場合、sqrt(2)となり立方体が綺麗になる。
                # vertex_normalとface_normalの成す角度なので、90°を超えないはず。一応絶対値をとる。
                angle_cos = abs(vert_nors_dir[vidx].dot(polygon.normal))
                # 限りなく尖った頂点の場合、長さが発散してしまうのを防ぐ。
                angle_cos = max(angle_cos, 1.0e-8)
                vert_length_accum[vidx] += (1.0/angle_cos) * angle
                # 次の頂点にそなえて更新
                loop_prev = loop_curr
                loop_curr = loop_next
        
        # 頂点の法線として格納
        for i in range(len(verts)):
            # lengthについて、重みつき平均をとる
            vert_nors_length[i] = (vert_length_accum[i] / vert_angle_accum[i])

        # length_limitで制限
        for i in range(len(vert_nors_length)):
            vert_nors_length[i] = min(vert_nors_length[i], length_limit)
        
        # 最大の長さが1となるように正規化
        if normalize_length:
            max_length = max(vert_nors_length)
            if max_length > 0:
                coef = 1.0 / max_length
                for i in range(len(vert_nors_length)):
                    vert_nors_length[i] = vert_nors_length[i] * coef

    # 頂点カラーを取得
    color_attribute:bpy.types.ByteColorAttribute
    if not mesh.color_attributes:
        color_attribute = mesh.color_attributes.new(
                                                 name="NormalColors",
                                                 type="BYTE_COLOR",
                                                 domain="CORNER")
    else:
        color_attribute = mesh.attributes.active_color
    vc:list[bpy.types.ByteColorAttributeValue] = color_attribute.data

    # 頂点カラーに書き込み
    for i, loop in enumerate(mesh.loops):
        loop:bpy.types.MeshLoop
        vert_idx = loop.vertex_index
        world_normal = vert_nors_dir[vert_idx]
        local_normal = Vector((
            Vector.dot(world_normal, loop.tangent.xyz),
            Vector.dot(world_normal, loop.bitangent.xyz),
            Vector.dot(world_normal, loop.normal.xyz)
        )).normalized()
        color = Vector((
            local_normal.x * 0.5 + 0.5,
            local_normal.y * 0.5 + 0.5,
            local_normal.z * 0.5 + 0.5,
            vert_nors_length[vert_idx],
        ))
        vc[i].color = color
    mesh.update()
