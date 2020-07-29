import os
import math
import json

# メッシュコード生成範囲
ORIGIN_MIN_LON = 122.00
ORIGIN_MAX_LON = 154.00
ORIGIN_MIN_LAT = 20.00
ORIGIN_MAX_LAT = 46.00


def get_start_offset(meshnum: int, lonlat: list) -> tuple:
    """[summary]
    メッシュ次数と経緯度に対し、原点（左下）から数えて何個のメッシュをスキップするか計算
    Args:
        meshnum (int): メッシュ次数
        lonlat ([float, float]): [経度, 緯度]

    Returns:
        tuple: (x方向のオフセット、y方向のオフセット)
    """
    x_mesh_dist, y_mesh_dist = get_mesh_size(meshnum)

    x_offset = 0
    while lonlat[0] >= ORIGIN_MIN_LON + x_mesh_dist * (x_offset + 1):
        x_offset += 1

    y_offset = 0
    while lonlat[1] >= ORIGIN_MIN_LAT + y_mesh_dist * (y_offset + 1):
        y_offset += 1

    return x_offset, y_offset


def get_end_offset(meshnum: int, lonlat: list) -> tuple:
    """[summary]
    メッシュ次数と経緯度に対し、終点（右上）から数えて何個のメッシュをスキップするか計算
    Args:
        meshnum (int): メッシュ次数
        lonlat ([float, float]): [経度, 緯度]

    Returns:
        tuple: (x方向のオフセット、y方向のオフセット)
    """
    x_mesh_dist, y_mesh_dist = get_mesh_size(meshnum)

    x_offset = 0
    while lonlat[0] <= ORIGIN_MAX_LON - x_mesh_dist * (x_offset + 1):
        x_offset += 1

    y_offset = 0
    while lonlat[1] <= ORIGIN_MAX_LAT - y_mesh_dist * (y_offset + 1):
        y_offset += 1

    return x_offset, y_offset


def get_mesh_size(meshnum: int) -> tuple:
    """[summary]
    メッシュ次数ごとのメッシュサイズを返す

    Args:
        meshnum (int): メッシュ次数

    Returns:
        tuple: 1メッシュあたりの(経度サイズ, 緯度サイズ)
    """
    x_size = 0
    y_size = 0

    if meshnum == 1:
        x_size = 1
        y_size = 2/3
    elif meshnum == 2:
        x_size = 1/8
        y_size = 1/12
    elif meshnum == 3:
        x_size = 1/80
        y_size = 1/120
    elif meshnum == 4:
        x_size = 1/160
        y_size = 1/240
    elif meshnum == 5:
        x_size = 1/320
        y_size = 1/480
    elif meshnum == 6:
        x_size = 1/640
        y_size = 1/960
    elif meshnum == 7:
        x_size = 1/1600
        y_size = 1/2400

    return x_size, y_size


def get_meshes(meshnum, extent=None) -> list:
    """[summary]
    メッシュ次数および領域から、その領域に重なる全てのメッシュの頂点の経緯度のリストを返す

    Args:
        meshnum ([type]): メッシュ次数
        extent (list, optional):  経緯度のペアのリストで領域指定

    Returns:
        list: [ {"geometry":<メッシュのジオメトリ>, "code":<メッシュコード>}... ]
    """

    # メッシュのx方向y方向それぞれの数
    x_size, y_size = get_mesh_size(meshnum)
    x_mesh_count = math.ceil((ORIGIN_MAX_LON - ORIGIN_MIN_LON) / x_size)
    y_mesh_count = math.ceil((ORIGIN_MAX_LAT - ORIGIN_MIN_LAT) / y_size)

    # スキップすべきメッシュの数＝オフセットを計算
    start_offset = [0, 0]
    end_offset = [0, 0]
    if extent:
        start_offset = get_start_offset(meshnum, extent[0])
        end_offset = get_end_offset(meshnum, extent[1])

    meshes = []
    for y in range(start_offset[1], y_mesh_count - end_offset[1]):
        for x in range(start_offset[0], x_mesh_count - end_offset[0]):
            leftbottom = [ORIGIN_MIN_LON + x * x_size,
                          ORIGIN_MIN_LAT + y * y_size]
            righttop = [ORIGIN_MIN_LON + (x + 1) * x_size,
                        ORIGIN_MIN_LAT + (y + 1) * y_size]
            mesh = {
                "geometry": [[
                    leftbottom,
                    [leftbottom[0], righttop[1]],
                    righttop,
                    [righttop[0], leftbottom[1]],
                    leftbottom
                ]],
                "code": get_meshcode(meshnum, x, y)
            }
            meshes.append(mesh)
    return meshes


def get_meshcode(meshnum: int, x_count: int, y_count: int) -> str:
    """[summary]
    メッシュ次数、対象メッシュの左下の点の経緯度、原点から数えたメッシュ番号からメッシュコードを生成
    Args:
        meshnum (int): メッシュ次数
        leftbottom_lonlat (list): 対象メッシュの左下の経緯度
        x_count (int): 原点からx方向に数えたメッシュ番号
        y_count (int): 原点からy方向に数えたメッシュ番号

    Raises:
        Exception: 適切なメッシュ次数が与えられなければ例外をスロー

    Returns:
        str: メッシュコード
    """

    x_size, y_size = get_mesh_size(meshnum)
    left_lon = ORIGIN_MIN_LON + x_count * x_size
    bottom_lat = ORIGIN_MIN_LAT + y_count * y_size

    meshcode = ""
    # 緯度を1.5倍した整数値
    meshcode += str(int(bottom_lat * 1.5))
    # 経度の整数部分の下2桁
    meshcode += str(int(left_lon))[1:]
    if meshnum == 1:
        return meshcode
    elif meshnum == 2:
        meshcode += str(y_count % 8)
        meshcode += str(x_count % 8)
        return meshcode
    elif meshnum == 3:
        meshcode += str(int((y_count % 80) / 10))
        meshcode += str(int((x_count % 80) / 10))
        meshcode += str(y_count % 10)
        meshcode += str(x_count % 10)
        return meshcode
    elif meshnum == 4:
        meshcode += str(int((y_count % 160) / 20))
        meshcode += str(int((x_count % 160) / 20))
        meshcode += str(int((y_count % 20) / 2))
        meshcode += str(int((x_count % 20) / 2))
        meshcode += str(y_count % 2)
        meshcode += str(x_count % 2)
        return meshcode
    elif meshnum == 5:
        meshcode += str(int((y_count % 320) / 40))
        meshcode += str(int((x_count % 320) / 40))
        meshcode += str(int((y_count % 40) / 4))
        meshcode += str(int((x_count % 40) / 4))
        meshcode += str(int((y_count % 4) / 2))
        meshcode += str(int((x_count % 4) / 2))
        meshcode += str(y_count % 2)
        meshcode += str(x_count % 2)
        return meshcode
    elif meshnum == 6:
        meshcode += str(int((y_count % 640) / 80))
        meshcode += str(int((x_count % 640) / 80))
        meshcode += str(int((y_count % 80) / 8))
        meshcode += str(int((x_count % 80) / 8))
        meshcode += str(int((y_count % 8) / 4))
        meshcode += str(int((x_count % 8) / 4))
        meshcode += str(int((y_count % 4) / 2))
        meshcode += str(int((x_count % 4) / 2))
        meshcode += str(y_count % 2)
        meshcode += str(x_count % 2)
        return meshcode
    elif meshnum == 7:
        meshcode += str(int((y_count % 1600) / 200))
        meshcode += str(int((x_count % 1600) / 200))
        meshcode += str(int((y_count % 200) / 20))
        meshcode += str(int((x_count % 200) / 20))
        meshcode += str(int((y_count % 20) / 10))
        meshcode += str(int((x_count % 20) / 10))
        meshcode += str(int((y_count % 10) / 5))
        meshcode += str(int((x_count % 10) / 5))
        meshcode += str(y_count % 5)
        meshcode += str(x_count % 5)
        return meshcode


if __name__ == "__main__":
    import argschems

    print("initializing...")
    # コマンド初期化
    args = argschems.ARGSCHEME.parse_args()

    # メッシュ番号
    try:
        meshnum = int(args.meshnum)
    except ValueError:
        raise ValueError(
            "Input Integer for meshnum, your input:" + str(args.meshnum))

    # 別称での指定を次数に置き換え
    if meshnum == 500:
        meshnum = 4
    elif meshnum == 250:
        meshnum = 5
    elif meshnum == 125:
        meshnum = 6
    elif meshnum == 50:
        meshnum = 7

    if meshnum < 1 or 7 < meshnum:
        raise ValueError("正しいメッシュ次数を指定してください。入力:" + str(args.meshnum))

    extent_texts = args.extent
    target_dir = args.target_dir

    # 保存先未指定なら実行ディレクトリに保存
    if target_dir is None:
        target_dir = ''

    # 領域が指定されているならパース
    extent = None
    if extent_texts:
        extent = [list(map(float, extent_texts[0].split(","))),
                  list(map(float, extent_texts[1].split(",")))]

    print("making meshes...")
    # メッシュ生成
    meshes = get_meshes(meshnum, extent)

    # geojsonl文字列を生成
    geojsonl_txt = ""
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": []
        },
        "properties": {
            "code": 0
        }
    }
    for mesh in meshes:
        feature["geometry"]["coordinates"] = mesh["geometry"]
        feature["properties"]["code"] = mesh["code"]
        geojsonl_txt += json.dumps(feature) + "\n"

    print("writing file...")
    # geojsonl書き出し
    with open(os.path.join(target_dir, "mesh_" + str(meshnum) + ".geojsonl"), mode="w") as f:
        f.write(geojsonl_txt)

    print("done")