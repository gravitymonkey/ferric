from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np


logger = logging.getLogger("ferric.metadata")


def _mean(x: np.ndarray) -> float:
    return float(np.mean(x)) if x.size else 0.0


def _std(x: np.ndarray) -> float:
    return float(np.std(x)) if x.size else 0.0


def extract_track_metadata(audio_path: Path) -> dict[str, Any] | None:
    try:
        import librosa
    except Exception:
        logger.warning("librosa not installed; skipping metadata extraction for %s", audio_path)
        return None

    try:
        y, sr = librosa.load(str(audio_path), sr=None, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)[0]
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        flatness = librosa.feature.spectral_flatness(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)

        return {
            "analysis_version": "librosa_v1",
            "sample_rate_hz": int(sr),
            "duration_sec": duration,
            "tempo_bpm": float(tempo) if np.isfinite(tempo) else None,
            "beat_count": int(len(beats)),
            "onset_strength_mean": _mean(onset_env),
            "rms_mean": _mean(rms),
            "rms_std": _std(rms),
            "spectral_centroid_mean": _mean(centroid),
            "spectral_centroid_std": _std(centroid),
            "spectral_bandwidth_mean": _mean(bandwidth),
            "spectral_rolloff_mean": _mean(rolloff),
            "spectral_flatness_mean": _mean(flatness),
            "zero_crossing_rate_mean": _mean(zcr),
            "mfcc_mean_json": json.dumps(np.mean(mfcc, axis=1).tolist()),
            "chroma_mean_json": json.dumps(np.mean(chroma, axis=1).tolist()),
            "tonnetz_mean_json": json.dumps(np.mean(tonnetz, axis=1).tolist()),
            "metadata_json": json.dumps({"extractor": "librosa", "n_samples": int(y.size)}),
        }
    except Exception as exc:
        logger.warning("metadata extraction failed for %s: %s", audio_path, exc)
        return None
