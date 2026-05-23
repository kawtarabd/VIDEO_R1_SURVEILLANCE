"""
Utilitaires pour le traitement vidéo.
"""

import base64
import os
from typing import List, Tuple
from pathlib import Path


def extract_frames(
    video_path: str,
    max_frames: int = 32,
    target_size: Tuple[int, int] = (448, 448),
    start_frame: int = 0,
    end_frame: int = None,
    smart_extraction: bool = False,
    span_seconds: float = None,
) -> List[str]:
    """
    Extrait les frames d'une vidéo et les encode en base64.

    Args:
        video_path: Chemin vers le fichier vidéo
        max_frames: Nombre maximum de frames à extraire
        target_size: Taille cible pour redimensionner les frames (width, height)
        start_frame: Frame de début (incluse)
        end_frame: Frame de fin (exclue), None = jusqu'à la fin
        smart_extraction: Si True, priorise les frames avec du mouvement
        span_seconds: Si spécifié, répartit les frames sur cette durée (en secondes)
                      au lieu d'extraire des frames consécutives

    Returns:
        Liste de frames encodées en base64
    """
    import cv2
    import numpy as np
    from PIL import Image
    from io import BytesIO

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    
    # Définir la plage de frames
    if end_frame is None:
        end_frame = total_frames
    end_frame = min(end_frame, total_frames)
    start_frame = max(0, start_frame)
    
    segment_frames = end_frame - start_frame

    frame_indices = []

    # Mode SPAN : répartir les frames sur une durée spécifiée
    if span_seconds is not None and span_seconds > 0:
        span_frames = int(span_seconds * fps)
        # Centrer le span sur la plage demandée
        center_frame = start_frame + segment_frames // 2
        span_start = max(0, center_frame - span_frames // 2)
        span_end = min(total_frames, span_start + span_frames)
        
        # Répartir max_frames uniformément sur le span
        actual_span = span_end - span_start
        if actual_span <= max_frames:
            frame_indices = list(range(span_start, span_end))
        else:
            step = actual_span / max_frames
            frame_indices = [int(span_start + i * step) for i in range(max_frames)]

    elif smart_extraction and segment_frames > max_frames:
        # Extraction intelligente basée sur le mouvement
        diff_scores = []
        prev_frame = None
        
        # Sous-échantillonnage pour calculer le mouvement (1 frame sur 2 ou 3 pour la vitesse)
        step_analysis = max(1, segment_frames // 200) # Analyser max 200 frames pour les scores
        
        for i in range(start_frame, end_frame, step_analysis):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (128, 128)) # Petit pour la vitesse
            
            if prev_frame is not None:
                score = cv2.absdiff(gray, prev_frame).mean()
                diff_scores.append((i, score))
            else:
                diff_scores.append((i, 0))
            prev_frame = gray
            
        # Sélectionner les frames avec le plus de mouvement, tout en gardant une distribution temporelle
        # On divise le segment en 'max_frames' sous-segments et on prend le max de mouvement dans chacun
        if diff_scores:
            chunk_size = len(diff_scores) / max_frames
            for k in range(max_frames):
                chunk_start = int(k * chunk_size)
                chunk_end = int((k + 1) * chunk_size)
                chunk = diff_scores[chunk_start:chunk_end]
                if chunk:
                    # Prendre la frame avec le score max dans ce chunk
                    best_frame_idx, _ = max(chunk, key=lambda x: x[1])
                    frame_indices.append(best_frame_idx)
        
        # Si pas assez de frames trouvées via mouvement, compléter uniformément
        if len(frame_indices) < max_frames:
            current_indices = set(frame_indices)
            needed = max_frames - len(frame_indices)
            step = segment_frames / needed
            for i in range(needed):
                idx = int(start_frame + i * step)
                if idx not in current_indices:
                    frame_indices.append(idx)
                    
        frame_indices.sort()
        
    else:
        # Extraction uniforme classique
        if segment_frames <= max_frames:
            frame_indices = list(range(start_frame, end_frame))
        else:
            step = segment_frames / max_frames
            frame_indices = [int(start_frame + i * step) for i in range(max_frames)]

    frames_b64 = []

    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()

        if not ret:
            continue

        # Convertir BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convertir en PIL Image
        img = Image.fromarray(frame_rgb)

        # Redimensionner
        img = img.resize(target_size, Image.Resampling.LANCZOS)

        # Encoder en base64
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        frame_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        frames_b64.append(frame_b64)

    cap.release()

    return frames_b64


def get_video_segments(
    video_path: str, 
    frames_per_segment: int = 64, 
    overlap_frames: int = 16
) -> List[Tuple[int, int]]:
    """
    Divise une vidéo en segments avec chevauchement.

    Args:
        video_path: Chemin vers le fichier vidéo
        frames_per_segment: Nombre de frames par segment
        overlap_frames: Nombre de frames de chevauchement entre segments

    Returns:
        Liste de tuples (start_frame, end_frame)
    """
    import cv2

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    segments = []
    step = frames_per_segment - overlap_frames
    
    if step <= 0:
        step = frames_per_segment # Pas de boucle infinie si overlap >= frames

    start = 0
    while start < total_frames:
        end = min(start + frames_per_segment, total_frames)
        segments.append((start, end))
        
        if end == total_frames:
            break
            
        start += step

    return segments


def get_video_info(video_path: str) -> dict:
    """
    Récupère les informations sur une vidéo.

    Args:
        video_path: Chemin vers le fichier vidéo

    Returns:
        Dictionnaire avec les informations vidéo
    """
    import cv2

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    info = {
        "path": video_path,
        "filename": Path(video_path).name,
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }

    # Calculer la durée
    if info["fps"] > 0:
        info["duration_seconds"] = info["total_frames"] / info["fps"]
        info["duration_formatted"] = format_duration(info["duration_seconds"])
    else:
        info["duration_seconds"] = 0
        info["duration_formatted"] = "Unknown"

    cap.release()

    return info


def format_duration(seconds: float) -> str:
    """Formate une durée en secondes en HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"
