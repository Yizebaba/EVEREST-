"""Cloud InSAR acquisition, resumable processing and phase export.

Runs on the authenticated CDSE host or any runner with an OpenEO refresh-token
store. Does not derive displacement from coherence or reuse legacy matrices.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
import openeo
import requests

NAMESPACE = 'https://raw.githubusercontent.com/ESA-APEx/apex_algorithms/refs/heads/main/algorithm_catalog/eurac/sentinel1_sar_interferogram/openeo_udp/sentinel1_sar_interferogram.json'


def discover(session=None):
    session = session or requests.Session()
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=60)).strftime('%Y-%m-%dT00:00:00Z')
    response = session.get(
        'https://catalogue.dataspace.copernicus.eu/odata/v1/Bursts',
        params={'$filter': "BurstId eq 23790 and SwathIdentifier eq 'IW1' and PolarisationChannels eq 'VV' and RelativeOrbitNumber eq 12 and OrbitDirection eq 'ASCENDING' and PlatformSerialIdentifier eq 'D' and ContentDate/Start ge " + since,
                '$orderby': 'ContentDate/Start desc', '$top': 100}, timeout=60,
    )
    response.raise_for_status()
    dates = {}
    for item in response.json()['value']:
        date = item['ContentDate']['Start'][:10]
        dates.setdefault(date, item)
    ordered = sorted(dates, reverse=True)
    for latest in ordered:
        previous = (datetime.date.fromisoformat(latest) - datetime.timedelta(days=12)).isoformat()
        if previous in dates:
            return [previous, latest], [dates[previous], dates[latest]]
    raise RuntimeError('No complete 12-day S1D/Burst23790/IW1/VV/orbit12 pair available')


def safe_metadata(value):
    """Signed asset URLs stay private; omit authentication-bearing query strings."""
    if isinstance(value, dict):
        return {k: safe_metadata(v) for k, v in value.items()}
    if isinstance(value, list):
        return [safe_metadata(v) for v in value]
    if isinstance(value, str) and value.startswith(('https://', 'http://')):
        return value.split('?', 1)[0]
    return value


def export(tif, output, pair, job_id):
    import rasterio
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    with rasterio.open(tif) as dataset:
        if dataset.count != 3:
            raise RuntimeError('Expected wrapped phase, unwrapped phase and coherence bands')
        wrapped = dataset.read(1, masked=True)
        phase = dataset.read(2, masked=True)
        coherence = dataset.read(3, masked=True)
        valid = (~np.ma.getmaskarray(phase) & ~np.ma.getmaskarray(coherence)
                 & np.isfinite(phase.data) & np.isfinite(coherence.data)
                 & (coherence.data >= 0.3) & (coherence.data <= 1))
        if not valid.any():
            raise RuntimeError('No phase pixels pass the coherence quality filter')
        # Raw conversion only. A validated stable-ground reference is still
        # required before claiming glacier displacement or hazard conclusions.
        los = np.where(valid, phase.data * (-0.055465 * 1000 / (4 * np.pi)), np.nan)
        np.save(output / 'los_unreferenced_mm.npy', los)
        np.save(output / 'coherence.npy', coherence.filled(np.nan))
        summary = {
            'product': 'Sentinel-1 unwrapped phase and coherence',
            'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'insar_pair': {'master': pair[0], 'slave': pair[1]},
            'job_id': job_id, 'processing_status': 'finished',
            'burst_id': 23790, 'swath': 'IW1', 'polarization': 'VV',
            'relative_orbit': 12, 'orbit_direction': 'ASCENDING',
            'shape': list(phase.shape), 'crs': str(dataset.crs),
            'bounds': list(dataset.bounds), 'transform': list(dataset.transform),
            'valid_phase_pixels': int(valid.sum()),
            'coherence_threshold': 0.3,
            # skip NaN (masked array still holds NaN pixels, mean became NaN)
            'coherence_mean': float(np.ma.masked_invalid(coherence).mean()),
            'displacement_status': 'UNREFERENCED_NOT_FOR_HAZARD_DECISIONS',
            'reference': None,
            'source_sha256': hashlib.sha256(Path(tif).read_bytes()).hexdigest(),
        }
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        arrays = [wrapped, coherence, np.ma.masked_invalid(los)]
        titles = ['Wrapped phase (rad)', 'Coherence', 'Unreferenced phase-to-LOS (mm)']
        for ax, array, title in zip(axes, arrays, titles):
            # skip NaN, otherwise percentiles are NaN and the colour stretch collapses
            lo, hi = np.percentile(np.ma.masked_invalid(array).compressed(), [2, 98])
            image = ax.imshow(array, vmin=lo, vmax=hi)
            ax.set_title(title)
            ax.axis('off')
            fig.colorbar(image, ax=ax, shrink=0.6)
        fig.suptitle(f'Sentinel-1D {pair[0]} to {pair[1]} | Burst 23790 IW1 VV')
        fig.tight_layout()
        fig.savefig(output / 'insar_preview.png', dpi=130)
        plt.close(fig)
    (output / 'product.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


def run(root, export_only=False):
    pair, products = discover()
    output = root / ('_'.join(d.replace('-', '') for d in pair))
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / 'job.json'
    if (output / 'product.json').exists() and not export_only:
        # Pair already exported; large rasters are git-ignored, so do not re-download every run
        print('ALREADY_EXPORTED', output)
        return
    connection = openeo.connect('https://openeo.dataspace.copernicus.eu')
    connection.authenticate_oidc_refresh_token()
    title = 'Everest_InSAR_' + output.name
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state['pair'] != pair:
            raise RuntimeError('Saved job pair does not match discovery')
        job = connection.job(state['job_id'])
    else:
        matches = [j for j in connection.list_jobs() if j.get('title') == title]
        if matches:
            job = connection.job(max(matches, key=lambda j: j.get('created', ''))['id'])
        elif export_only:
            raise RuntimeError('No existing job to export')
        else:
            graph = {
                'interferogram': {'process_id': 'sentinel1_sar_interferogram', 'namespace': NAMESPACE,
                                 'arguments': {'InSAR_pairs': [pair], 'burst_id': 23790,
                                               'sub_swath': 'IW1', 'polarization': 'VV',
                                               'coherence_window_az': 2, 'coherence_window_rg': 10,
                                               'n_az_looks': 1, 'n_rg_looks': 4}, 'result': True},
            }
            job = connection.create_job(process_graph=graph, title=title)
        state = {'pair': pair, 'job_id': job.job_id}
        state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
    description = job.describe()
    status = description['status']
    print('JOB', job.job_id, status, 'PAIR', pair, flush=True)
    if status in ('error', 'canceled'):
        logs = safe_metadata(list(job.logs()))
        (output / 'failure.json').write_text(json.dumps(logs, indent=2), encoding='utf-8')
        raise RuntimeError('Cloud job failed; no stale output will be published')
    if status != 'finished':
        if export_only:
            raise RuntimeError('Existing job is not finished')
        if status == 'created':
            job.start()
        # Return promptly; subsequent schedule polls the same job, avoiding
        # long-running runners and duplicate paid jobs.
        print('PENDING: next scheduled invocation will resume this job')
        return
    result = job.get_results()
    metadata = result.get_metadata()
    names = [name for name in metadata.get('assets', {}) if name.endswith('.tif')]
    if len(names) != 1 or not all(d.replace('-', '') in names[0] for d in pair):
        raise RuntimeError('Result asset dates do not match the requested pair')
    tif = output / names[0]
    if not tif.exists():
        result.get_asset(names[0]).download(tif)
    summary = export(tif, output, pair, job.job_id)
    (output / 'provenance.json').write_text(json.dumps(safe_metadata(metadata), indent=2), encoding='utf-8')
    (root / 'latest.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('PRODUCT_READY', str(output), 'PIXELS', summary['valid_phase_pixels'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('data/cloud_insar'))
    parser.add_argument('--export-only', action='store_true')
    args = parser.parse_args()
    run(args.output, args.export_only)
