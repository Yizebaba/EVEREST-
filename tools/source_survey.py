"""候选数据源实测：逐个请求，记录 HTTP 状态、耗时、返回条数和样本，写 survey.json。在 GitHub 运行器上跑（本地网络受限）。"""
import json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

NOW = datetime.now(timezone.utc)
D = lambda n: (NOW - timedelta(days=n)).strftime("%Y-%m-%d")
UA = {"user-agent": "everest-source-survey (github.com/Yizebaba/EVEREST-)", "accept": "application/json, */*"}
BB = "79.5,26.3,92.5,31.5"   # 喜马拉雅范围 w,s,e,n

C = {
 "bipad_hazard": "https://bipadportal.gov.np/api/v1/hazard/?format=json&limit=200",
 "bipad_incident": "https://bipadportal.gov.np/api/v1/incident/?format=json&ordering=-incident_on&limit=100&expand=loss",
 "bipad_alert": "https://bipadportal.gov.np/api/v1/alert/?format=json&ordering=-started_on&limit=50",
 "bipad_pollution": "https://bipadportal.gov.np/api/v1/pollution-stations/?format=json&limit=5",
 "bipad_rain": "https://bipadportal.gov.np/api/v1/rain-stations/?format=json&limit=5",
 "eonet": f"https://eonet.gsfc.nasa.gov/api/v3/events?bbox=79.5,31.5,92.5,26.3&days=120&status=all",
 "eonet_global": "https://eonet.gsfc.nasa.gov/api/v3/events?days=10&status=all&limit=50",
 "eonet_categories": "https://eonet.gsfc.nasa.gov/api/v3/categories",
 "swpc_alerts": "https://services.swpc.noaa.gov/products/alerts.json",
 "swpc_kp": "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
 "swpc_xray_flares": "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json",
 "swpc_protons": "https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json",
 "cneos_fireball": f"https://ssd-api.jpl.nasa.gov/fireball.api?date-min={D(365)}",
 "cneos_cad": f"https://ssd-api.jpl.nasa.gov/cad.api?date-min={D(30)}&date-max={D(-30)}&dist-max=0.05",
 "celestrak_decayed": "https://celestrak.org/NORAD/elements/gp.php?GROUP=last-30-days&FORMAT=json",
 "who_don": "https://www.who.int/api/news/diseaseoutbreaknews?sf_culture=en&$orderby=PublicationDateAndTime%20desc&$top=20",
 "who_flunet_npl": "https://xmart-api-public.who.int/FLUMART/VIW_FNT?$filter=COUNTRY_CODE%20eq%20%27NPL%27&$orderby=ISO_WEEKSTARTDATE%20desc&$top=5",
 "wahis_events": "https://wahis.woah.org/api/v1/pi/event/filtered-list?language=en",
 "fao_locust": "https://services5.arcgis.com/sjP4Ugu5s0dZWLjd/arcgis/rest/services/Swarms_Public/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=5&orderByFields=STARTDATE%20DESC&f=json",
 "ghcn_kathmandu": f"https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&stations=NPM00044454&startDate={D(40)}&endDate={D(0)}&format=json&units=metric",
 "ghcn_stations_np": "https://www.ncei.noaa.gov/access/services/search/v1/data?dataset=daily-summaries&bbox=31.5,79.5,26.3,92.5&startDate=" + D(30) + "&endDate=" + D(0) + "&limit=50",
 "isd_np": f"https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-hourly&stations=44454099999&startDate={D(3)}&endDate={D(0)}&format=json",
 "ncei_tsunami": "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events?minYear=2025",
 "ncei_volcano": "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes?minYear=2025",
 "ncei_eq": "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes?minYear=2025&country=NEPAL",
 "gvp_weekly": "https://volcano.si.edu/news/WeeklyVolcanoRSS.xml",
 "ptwc_atom": "https://www.tsunami.gov/events/xml/PHEBAtom.xml",
 "ioc_stations": "https://www.ioc-sealevelmonitoring.org/service.php?query=stationlist&showall=all",
 "ndbc_dart": "https://www.ndbc.noaa.gov/data/realtime2/21413.dart",
 "nsidc_seaice": "https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v3.0.csv",
 "ibtracs_active": "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.ACTIVE.list.v04r01.csv",
 "gbif_np": f"https://api.gbif.org/v1/occurrence/search?country=NP&eventDate={D(60)},{D(0)}&limit=1",
 "safecast_np": "https://api.safecast.org/measurements.json?latitude=27.7&longitude=85.3&distance=200000&per_page=5",
 "cisa_kev": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
 "hibp_breaches": "https://haveibeenpwned.com/api/v3/breaches",
 "nrb_forex": f"https://www.nrb.org.np/api/forex/v1/rates?from={D(10)}&to={D(0)}&per_page=10&page=1",
 "ucdp_candidate": "https://ucdpapi.pcr.uu.se/api/gedevents/25.0.10?pagesize=5&Country=779",
 "openfda_food": "https://api.fda.gov/food/enforcement.json?sort=report_date:desc&limit=3",
 "openfda_drug": "https://api.fda.gov/drug/enforcement.json?sort=report_date:desc&limit=3",
 "s5p_stac": "https://planetarycomputer.microsoft.com/api/stac/v1/search?collections=sentinel-5p-l2-netcdf&bbox=" + BB + "&datetime=" + D(3) + "T00:00:00Z/" + D(0) + "T23:59:59Z&limit=50",
 "gdacs_all": f"https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?fromdate={D(60)}&todate={D(0)}&alertlevel=green;orange;red",
 "reliefweb_noapp": "https://api.reliefweb.int/v2/disasters?appname=test&limit=1",
 "gfw_noauth": "https://data-api.globalforestwatch.org/datasets",
 "openaq_noauth": "https://api.openaq.org/v3/locations?countries_id=126&limit=1",
 "gdelt_theme": "https://api.gdeltproject.org/api/v2/doc/doc?query=theme:NATURAL_DISASTER%20Nepal&mode=artlist&maxrecords=5&format=json&timespan=7d",
 "nepse": "https://www.nepalstock.com/api/nots/nepse-index",
 # —— 参考数据（历史同类事件、文献数据检索），2026-10-14 加 ——
 "ref_zenodo_glof": "https://zenodo.org/api/records/7330344",
 "ref_zenodo_glof_latest": "https://zenodo.org/api/records/7330344/versions/latest",
 "ref_coolr_points": "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer/0/query?where=1%3D1&geometry=79.5,26.3,92.5,31.5&geometryType=esriGeometryEnvelope&inSR=4326&outFields=*&resultRecordCount=3&f=json",
 "ref_coolr_count": "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer/0/query?where=1%3D1&geometry=79.5,26.3,92.5,31.5&geometryType=esriGeometryEnvelope&inSR=4326&returnCountOnly=true&f=json",
 "ref_coolr_layers": "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer/layers?f=json",
 "ref_icimod_ckan": "https://rds.icimod.org/api/3/action/package_search?q=glacial%20lake&rows=5",
 "ref_crossref_datajournal": "https://api.crossref.org/works?query.bibliographic=glacial+lake+outburst+flood&filter=issn:1866-3516,issn:2052-4463,issn:2049-6060,issn:2352-3409,issn:1866-3508&rows=3&select=DOI,title,container-title,issued,is-referenced-by-count",
 "ref_crossref_top": "https://api.crossref.org/works?query.bibliographic=glacial+lake+outburst+flood&filter=from-pub-date:2020-01-01,type:journal-article&rows=20&select=DOI,title,container-title,issued,is-referenced-by-count",
 "ref_datacite": "https://api.datacite.org/dois?query=%22glacial%20lake%20outburst%22&resource-type-id=dataset&page%5Bsize%5D=5",
 "ref_openalex_ratelimit": "https://api.openalex.org/rate-limit",
 "ref_emdat_doc": "https://doc.emdat.be/docs/",
 "ref2_hma_glof_csv": "https://raw.githubusercontent.com/fidelsteiner/HMAGLOFDB/main/Database/GLOFs/HMAGLOFDB.csv",
 "ref2_hma_glof_meta": "https://raw.githubusercontent.com/fidelsteiner/HMAGLOFDB/main/Database/GLOFs/HMAGLOFDB_Metadata.yml",
 "ref2_hma_glof_zenodo": "https://zenodo.org/api/records/7271187/versions/latest",
 "ref2_glof_global_files": "https://zenodo.org/api/records/7924369/files",
 "ref2_coolr_q1": "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer/0/query?where=country_code%3D%27NP%27&outFields=event_date,event_title,landslide_category,landslide_trigger,latitude,longitude,source_name,source_link&resultRecordCount=3&f=json",
 "ref2_coolr_q2": "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer/0/query?where=1%3D1&returnCountOnly=true&f=json",
 "ref2_coolr_nccs": "https://maps.nccs.nasa.gov/mapping/rest/services/COOLR/COOLR_Events_Point/FeatureServer/0/query?where=1%3D1&returnCountOnly=true&f=json",
 "ref2_glc_disasters": "https://maps.disasters.nasa.gov/ags01/rest/services/Hosted/nasa_glc_poly_point/FeatureServer/0/query?where=1%3D1&returnCountOnly=true&f=json",
 "ref2_crossref_top": "https://api.crossref.org/works?query.bibliographic=glacial+lake+outburst+flood&filter=from-pub-date:2020-01-01,type:journal-article&rows=20&select=DOI,title,container-title,issued,is-referenced-by-count",
 # —— 实时源候选（2026-10-14 第三轮）——
 "rt_metar_np": "https://aviationweather.gov/api/data/metar?ids=VNKT,VNLK,VNPK,VNBW,ZULS&format=json&hours=3",
 "rt_metar_cache": "https://aviationweather.gov/data/cache/metars.cache.csv.gz",
 "rt_isigmet": "https://aviationweather.gov/api/data/isigmet?format=json",
 "rt_spc_today": "https://www.spc.noaa.gov/climo/reports/today.csv",
 "rt_spc_yday": "https://www.spc.noaa.gov/climo/reports/yesterday.csv",
 "rt_nws_observed": "https://api.weather.gov/alerts/active?certainty=Observed",
 "rt_usgs_volcano": "https://volcanoes.usgs.gov/hans-public/api/volcano/getElevatedVolcanoes",
 "rt_nifc_fires": "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0/query?where=1%3D1&outFields=IncidentName,FireDiscoveryDateTime,IncidentSize,POOState&resultRecordCount=3&orderByFields=FireDiscoveryDateTime%20DESC&f=json",
 "rt_urlhaus": "https://urlhaus.abuse.ch/downloads/json_recent/",
 "rt_threatfox": "https://threatfox.abuse.ch/export/json/recent/",
 "rt_feodo": "https://feodotracker.abuse.ch/downloads/ipblocklist.json",
 "rt_openphish": "https://openphish.com/feed.txt",
 "rt_adsb_7700": "https://api.adsb.lol/v2/sqk/7700",
 "rt_airplaneslive_7700": "https://api.airplanes.live/v2/sqk/7700",
 "rt_cems_rapid": "https://emergency.copernicus.eu/mapping/activations-rapid/feed",
 "rt_cems_api": "https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/?limit=3",
 "rt_coralreef": "https://coralreefwatch.noaa.gov/product/5km/v3.1_op/data/",
 "rt_eurdep": "https://remap.jrc.ec.europa.eu/api/maps/RadiationLevels",
 "rt_waqi_demo": "https://api.waqi.info/feed/kathmandu/?token=demo",
 "rt_noaa_coops": "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?date=latest&station=8518750&product=water_level&datum=MLLW&units=metric&time_zone=gmt&format=json",
 "rt_usgs_water_flood": "https://waterservices.usgs.gov/nwis/iv/?format=json&stateCd=ny&parameterCd=00065&siteStatus=active&period=PT1H",
 "rt_ga_quakes": "https://earthquakes.ga.gov.au/geoserver/earthquakes/wfs?service=WFS&request=getfeature&typeNames=earthquakes:earthquakes_seven_days&outputFormat=application/json&count=2",
 "rt_bmkg": "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json",
 "rt_jma_quake": "https://www.jma.go.jp/bosai/quake/data/list.json",
 "rt_cenc": "https://www.ceic.ac.cn/ajax/speedsearch?num=1&page=1",
 # —— 摄像头候选 ——
 "cam_evk2_page": "https://evk2minoprio.org/webcam/",
 "cam_evk2_home": "https://evk2minoprio.org/",
 "cam_hev_home": "https://hoteleverestview.com/",
 "cam_oembed_everest_pyramid": "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=tz3VTxlq9l4&format=json",
 "cam_thumb_everest_pyramid": "https://i.ytimg.com/vi/tz3VTxlq9l4/maxresdefault_live.jpg",
 "cam_oembed_lukla": "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=am9KDRSZQ-0&format=json",
 "cam_thumb_lukla": "https://i.ytimg.com/vi/am9KDRSZQ-0/maxresdefault_live.jpg",
 "cam_oembed_lobuche": "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=AFUTlak8wcA&format=json",
 "cam_thumb_lobuche": "https://i.ytimg.com/vi/AFUTlak8wcA/maxresdefault_live.jpg",
 "cam_oembed_namche": "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=uQsntMlx8ZY&format=json",
 "cam_thumb_namche": "https://i.ytimg.com/vi/uQsntMlx8ZY/maxresdefault_live.jpg",
 "cam_oembed_khare": "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=PAIpsIJ_7AE&format=json",
 "cam_thumb_khare": "https://i.ytimg.com/vi/PAIpsIJ_7AE/maxresdefault_live.jpg",
 "cam_oembed_everest_yt2": "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=AD4-Z-ONsIc&format=json",
 "cam_thumb_everest_yt2": "https://i.ytimg.com/vi/AD4-Z-ONsIc/maxresdefault_live.jpg",
 "cam2_pwc": "https://ftp.mountaingenius.org/PYRCEOP/PWC.jpg",
 "cam2_dir": "https://ftp.mountaingenius.org/PYRCEOP/",
 "cam2_root": "https://ftp.mountaingenius.org/",
 "cam3_everest_pyramid": "https://www.youtube.com/watch?v=tz3VTxlq9l4",
 "cam3_lukla": "https://www.youtube.com/watch?v=am9KDRSZQ-0",
 "cam3_lobuche": "https://www.youtube.com/watch?v=AFUTlak8wcA",
 "cam3_namche": "https://www.youtube.com/watch?v=uQsntMlx8ZY",
 "cam3_khare": "https://www.youtube.com/watch?v=PAIpsIJ_7AE",
 "cam3_everest_yt2": "https://www.youtube.com/watch?v=AD4-Z-ONsIc",
 "cam4_everest_pyramid": "https://i.ytimg.com/vi/tz3VTxlq9l4/maxresdefault_live.jpg",
 "cam4_hq_everest_pyramid": "https://i.ytimg.com/vi/tz3VTxlq9l4/hqdefault_live.jpg",
 "cam4_lukla": "https://i.ytimg.com/vi/am9KDRSZQ-0/maxresdefault_live.jpg",
 "cam4_hq_lukla": "https://i.ytimg.com/vi/am9KDRSZQ-0/hqdefault_live.jpg",
 "cam4_lobuche": "https://i.ytimg.com/vi/AFUTlak8wcA/maxresdefault_live.jpg",
 "cam4_hq_lobuche": "https://i.ytimg.com/vi/AFUTlak8wcA/hqdefault_live.jpg",
 "cam4_namche": "https://i.ytimg.com/vi/uQsntMlx8ZY/maxresdefault_live.jpg",
 "cam4_hq_namche": "https://i.ytimg.com/vi/uQsntMlx8ZY/hqdefault_live.jpg",
 "cam4_khare": "https://i.ytimg.com/vi/PAIpsIJ_7AE/maxresdefault_live.jpg",
 "cam4_hq_khare": "https://i.ytimg.com/vi/PAIpsIJ_7AE/hqdefault_live.jpg",
 "cam4_everest_yt2": "https://i.ytimg.com/vi/AD4-Z-ONsIc/maxresdefault_live.jpg",
 "cam4_hq_everest_yt2": "https://i.ytimg.com/vi/AD4-Z-ONsIc/hqdefault_live.jpg",
 "cam4_channel_streams": "https://www.youtube.com/@webcamnepallive/streams",
 "cam4_channel_live": "https://www.youtube.com/channel/UCCCVkU6r9ZTD8E4z7AtuOIw/live",
 "ref_rekor": "https://rekor.sigstore.dev/api/v1/log",
}
out = {}
import os
ONLY = os.environ.get("SURVEY_ONLY", "")
for k, u in C.items():
    if ONLY and not k.startswith(ONLY): continue
    t = time.time(); r = {"url": u}
    try:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as f:
            b = f.read(); r["status"] = f.status; r["bytes"] = len(b); r["ctype"] = f.headers.get("content-type"); r["last_modified"] = f.headers.get("last-modified")
        txt = b.decode("utf-8", "ignore")
        try:
            j = json.loads(txt)
            if isinstance(j, list): r["n"] = len(j); r["sample"] = json.dumps(j[:2], ensure_ascii=False)[:1500]
            else:
                for key in ("results", "events", "value", "data", "features", "vulnerabilities", "articles", "categories"):
                    if isinstance(j.get(key), list): r["n"] = len(j[key]); r["key"] = key; r["sample"] = json.dumps(j[key][:2], ensure_ascii=False)[:1500]; break
                else: r["sample"] = json.dumps(j, ensure_ascii=False)[:1500]
                r["keys"] = list(j.keys())[:20]
        except Exception:
            r["sample"] = txt[:800]
        if k.startswith("cam") and "html" in (r.get("ctype") or ""):
            import re as _re
            r["imgs"] = sorted(set(_re.findall(r'(?:src|href|data-src)=["\']([^"\']+\.(?:jpe?g|png|webp|m3u8)[^"\']*)', txt)))[:60]
            r["frames"] = sorted(set(_re.findall(r'<iframe[^>]+src=["\']([^"\']+)', txt)))[:20]
        if k.startswith("cam4_channel"):
            import re as _re
            r["video_ids"] = list(dict.fromkeys(_re.findall(r'"videoId":"([\w-]{11})"', txt)))[:30]
            r["titles"] = list(dict.fromkeys(_re.findall(r'"title":\{"runs":\[\{"text":"([^"]{5,120})"', txt)))[:30]
            r["live_badges"] = len(_re.findall(r'BADGE_STYLE_TYPE_LIVE_NOW|"LIVE"', txt))
            r["sample"] = ""
        if k.startswith("cam3_"):
            import re as _re
            for f in ("isLiveNow", "isLive", "playableInEmbed", "isLiveContent"):
                m = _re.search('"' + f + '":(true|false)', txt); r[f] = m.group(1) if m else None
            for f in ("title", "ownerChannelName", "channelId", "startTimestamp", "endTimestamp", "uploadDate"):
                m = _re.search('"' + f + '":"([^"]{0,120})"', txt); r[f] = m.group(1) if m else None
            m = _re.search('"status":"(OK|UNPLAYABLE|ERROR|LOGIN_REQUIRED|LIVE_STREAM_OFFLINE)"', txt); r["play_status"] = m.group(1) if m else None
            r["sample"] = ""
        if k == "bipad_hazard":
            r["all"] = [(h.get("id"), h.get("title")) for h in (json.loads(txt).get("results") or [])]
    except Exception as e:
        r["err"] = str(e)[:200]
    r["sec"] = round(time.time() - t, 1); out[k] = r
    print(k, r.get("status"), r.get("n"), r.get("err", "")[:80], flush=True)
    if k.startswith("gdelt") or k.startswith("ref"): time.sleep(3)
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "survey.json", "w"), ensure_ascii=False, indent=1)
