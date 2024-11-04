# Bake Normals To Vertex Colors
lilToonのOutline用に法線を頂点カラーとしてベイクするBlenderアドオンです。
![Bake_Normals_To_Vertex_Colors](https://github.com/user-attachments/assets/88823d00-2071-4d31-a381-83c38efed411)

## 動作説明
選択したオブジェクトのアクティブなVertexColorに対して、各ポリゴンの各頂点に対する法線を頂点毎に平均化した法線をベイクします。
選択したオブジェクトにVertexColorが存在しなければ、NormalColorsという名前で追加した上でベイクします。

lilToonの輪郭線の頂点カラーにて`RGBA -> Normal & Width`を選択して使うことを想定しています。
![image](https://github.com/user-attachments/assets/618e4e60-4eb8-416e-bf90-ba90d03f7e76)


## 動作確認環境
* Blender 4.2.3

## インストール方法
1. このリポジトリをZIPでダウンロードします。
2. Blenderを起動し、`Edit > Preferences... > Add-ons`の右上の`v`マークから、`Install From Disk...`にてダウンロードしたZIPファイルを選択します。
3. Bake Normals To Vertex Colors アドオンを有効化します。

## 使用方法
1. オブジェクトモードにて、法線をベイクしたいオブジェクトを選択します。(複数選択可)
2. `3D Viewport > Object > Bake Normals To Vertex Colors`を実行します。
3. Fbxとしてエクスポートする際は、GeometryのVertex ColorsをLinearに設定してください。

## パラメーターの説明
### adjust normal length
チェックを入れた場合、法線の長さ(輪郭線の太さ)を調整する。

チェックがない場合、法線の長さは1.0固定。

### length limit
法線の長さの最大値。制限をかけたくない場合は10等の大き目の値を設定。

直方体の角を綺麗に出したければ、$`\sqrt{3} \simeq 1.7320508`$ 以上の値を設定する。

### normalize normal length
チェックを入れた場合、法線の長さを計算した結果の最大値が1となるように全体を正規化。

## 注意
Auto Smoothモディファイアで法線が変更されている場合、その結果が反映されません。
実行する前にAuto SmoothモディファイアをApplyしてください。

color_attributeでアクセスしているため、sRGBではなくlinearで格納されます。エクスポート時の設定に注意してください。
