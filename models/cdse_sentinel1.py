"""Cloud-only Sentinel-1 discovery through Copernicus Data Space OData."""
import datetime as _dt
import requests

CDSE_PRODUCTS = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
EVEREST_BBOX = "POLYGON ((86.55 27.72, 87.05 27.72, 87.05 28.10, 86.55 28.10, 86.55 27.72))"


def discover_sentinel1_slc_pair(days_back=60):
    """Return the newest two AOI-intersecting Sentinel-1 SLC products.

    This only discovers remote products; it never downloads SAFE archives.
    Downstream processing must provide a matching cloud InSAR result.
    """
    since = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    area = f"geography'SRID=4326;{EVEREST_BBOX}'"
    filt = (
        "Collection/Name eq 'SENTINEL-1' and "
        f"OData.CSC.Intersects(area={area}) and "
        "(startswith(Name,'S1A_IW_SLC') or startswith(Name,'S1B_IW_SLC') "
        "or startswith(Name,'S1C_IW_SLC') or startswith(Name,'S1D_IW_SLC')) and "
        f"ContentDate/Start ge {since}"
    )
    params = {"$filter": filt, "$orderby": "ContentDate/Start desc", "$top": "50"}
    response = requests.get(CDSE_PRODUCTS, params=params, headers={"User-Agent": "Everest-Pipeline/5.1", "Accept": "application/json"}, timeout=45)
    response.raise_for_status()
    products = response.json().get("value", [])
    if len(products) < 2:
        raise RuntimeError(f"CDSE returned only {len(products)} AOI Sentinel-1 SLC product(s); refusing stale fallback")
    unique = {}
    for p in products:
        start = p.get("ContentDate", {}).get("Start")
        if start and start[:10] not in unique:
            unique[start[:10]] = {
                "id": p.get("Id"), "name": p.get("Name"), "date": start[:10],
                "content_start": start, "s3_path": p.get("S3Path"),
                "online": p.get("Online"), "footprint": p.get("GeoFootprint")
            }
    if len(unique) < 2:
        raise RuntimeError("CDSE returned fewer than two distinct acquisition dates; refusing stale fallback")
    pair = list(unique.values())[:2]
    return {"latest": pair[0], "previous": pair[1], "source": "Copernicus Data Space OData Products", "query_type": "AOI_INTERSECTING_SENTINEL1_SLC"}

def discover_burst_pair(burst_id=23790, swath="IW1", rel_orbit=12, direction="ASCENDING", platform="D", days_back=60):
    """同一条带（同一 burst、同一相对轨道、同一卫星）上相隔 12 天的最新一对影像。

    以前取的是“与珠峰范围相交的最新两景”，会把不同轨道的影像凑成一对（例如 10-06 和 10-10 相隔 4 天，
    10-06 根本不在 23790 条带上）。干涉只能用同一轨道的影像，所以改为和云端干涉（cloud_insar_pipeline.py）同一个查询。
    """
    since = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
    flt = (f"BurstId eq {burst_id} and SwathIdentifier eq '{swath}' and PolarisationChannels eq 'VV' and "
           f"RelativeOrbitNumber eq {rel_orbit} and OrbitDirection eq '{direction}' and PlatformSerialIdentifier eq '{platform}' and "
           f"ContentDate/Start ge {since}")
    r = requests.get("https://catalogue.dataspace.copernicus.eu/odata/v1/Bursts",
                     params={"$filter": flt, "$orderby": "ContentDate/Start desc", "$top": 100},
                     headers={"User-Agent": "Everest-Pipeline/5.2", "Accept": "application/json"}, timeout=60)
    r.raise_for_status()
    dates = {}
    for it in r.json().get("value", []):
        dates.setdefault(it["ContentDate"]["Start"][:10], it)
    for latest in sorted(dates, reverse=True):
        prev = (_dt.date.fromisoformat(latest) - _dt.timedelta(days=12)).isoformat()
        if prev in dates:
            mk = lambda d: {"date": d, "id": dates[d].get("Id"), "name": dates[d].get("ParentProductName") or dates[d].get("Name"), "content_start": dates[d]["ContentDate"]["Start"]}
            return {"latest": mk(latest), "previous": mk(prev), "source": "Copernicus Data Space OData Bursts",
                    "query_type": f"BURST_{burst_id}_{swath}_VV_ORBIT{rel_orbit}_{direction}_S1{platform}_12DAY"}
    raise RuntimeError(f"No complete 12-day S1{platform}/Burst{burst_id}/{swath}/VV/orbit{rel_orbit} pair in the last {days_back} days")
