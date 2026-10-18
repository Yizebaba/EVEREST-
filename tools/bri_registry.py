"""一带一路样品项目清单：从 AidData《全球中国发展融资地理数据集》第 3 版取项目的真实范围，简化后存成 bri/projects.json。
数据：https://github.com/aiddata/gcdf-geospatial-data （AidData，ODC-By；OSM 部分 ODbL）。范围是 AidData 按 OSM 要素画的（线状项目是沿线缓冲带）。
用法：python3 tools/bri_registry.py <gcdf 仓库目录> bri/projects.json
只做一次（项目位置不常变）；新增项目在 PROJ 里加一行再跑。
"""
import csv, json, sys
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

SRC, OUT = sys.argv[1], sys.argv[2]
# AidData 记录号 → 中文名、英文名、国家、类别、备注（同一项目多笔融资只取一条记录的范围）
PROJ = [
    (38360, "沙布鲁贝西—热索瓦加迪公路", "Syaphrubesi–Rasuwagadhi Highway", "NPL", "公路", ""),
    (53125, "热索瓦加迪（Timure）口岸边检站", "Timure (Rasuwagadhi) Frontier Inspection Station", "NPL", "口岸", ""),
    (53716, "上特里苏利 3A 水电站（60 MW）", "Upper Trishuli 3A Hydroelectric Project (60 MW)", "NPL", "水电", ""),
    (38705, "上特里苏利 3A—加德满都 220 kV 输电线", "Upper Trishuli 3A–Kathmandu 220 kV Transmission Line", "NPL", "输电", ""),
    (72338, "吉隆—加德满都跨境铁路（规划）", "Kerung–Kathmandu Cross-border Railway (planned)", "NPL", "铁路", "规划中；AidData 只有大致范围（县级）"),
    (85304, "中老铁路", "China–Laos Railway", "LAO", "铁路", ""),
    (63762, "南欧江梯级水电站（一期）", "Nam Ou Hydropower Project (Phase 1)", "LAO", "水电", ""),
    (35739, "喀喇昆仑公路改扩建（雷科特—红其拉甫）", "Karakoram Highway Improvement (Raikot–Khunjerab)", "PAK", "公路", "中巴经济走廊"),
    (54424, "喀喇昆仑公路二期（塔科特—哈维连）", "KKH Phase 2 (Thakot–Havelian)", "PAK", "公路", "中巴经济走廊；AidData 标为大致位置"),
    (37233, "卡洛特水电站（720 MW）", "Karot Hydropower Project (720 MW)", "PAK", "水电", "中巴经济走廊"),
    (92475, "瓜达尔港", "Gwadar Port", "PAK", "港口", "中巴经济走廊"),
]
CTRY = {"NPL": ["尼泊尔", "Nepal"], "LAO": ["老挝", "Laos"], "PAK": ["巴基斯坦", "Pakistan"]}

rows = {}
for r in csv.DictReader(open(f"{SRC}/input_data/gcdf_v3/final_input.csv", encoding="utf-8")):
    rows.setdefault(int(r["AidData.Record.ID"]), r)

out = []
for pid, zh, en, iso, kind, note in PROJ:
    r = rows[pid]
    g = unary_union([shape(f["geometry"]) for f in json.load(open(f"{SRC}/latest/geojsons/{pid}.geojson"))["features"]])
    s = g.simplify(0.002, preserve_topology=True)   # 约 200 m，页面和距离计算够用
    m = mapping(s)
    polys = [m["coordinates"]] if m["type"] == "Polygon" else list(m["coordinates"])
    rings = [[[round(x, 4), round(y, 4)] for x, y in p[0]] for p in polys]   # 只留外环
    c = g.centroid; b = g.bounds
    out.append({"id": f"aiddata-{pid}", "aiddata_id": pid, "name": zh, "name_en": en, "country": iso, "country_name": CTRY[iso], "kind": kind,
                "title": r["Title"], "status": r["Status"], "commit_year": r["Commitment.Year"], "precision": r["Level.of.precision"],
                "osm": r["OSM.link"], "centroid": [round(c.y, 4), round(c.x, 4)], "bbox": [round(b[1], 4), round(b[0], 4), round(b[3], 4), round(b[2], 4)],
                "rings": rings, "note": note,
                "source": "AidData Global Chinese Development Finance Dataset v3.0 (geospatial), https://github.com/aiddata/gcdf-geospatial-data"})
json.dump({"generated_from": "AidData GCDF v3.0 geospatial (ODC-By; OSM features ODbL)", "projects": out}, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "projects", sum(len(x) for p in out for x in p["rings"]), "vertices")
