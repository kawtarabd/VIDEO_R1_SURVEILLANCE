"""
Client pour communiquer avec l'endpoint RunPod Video-R1.
"""

import requests
import os
import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()

console = Console()


class VideoR1Client:
    """Client pour l'API Video-R1 déployée sur RunPod Serverless."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint_id: Optional[str] = None,
    ):
        """
        Initialise le client RunPod.

        Args:
            api_key: Clé API RunPod (ou variable RUNPOD_API_KEY)
            endpoint_id: ID de l'endpoint (ou variable RUNPOD_ENDPOINT_ID)
        """
        self.api_key = api_key or os.getenv("RUNPOD_API_KEY")
        self.endpoint_id = endpoint_id or os.getenv("RUNPOD_ENDPOINT_ID")

        if not self.api_key:
            raise ValueError(
                "RUNPOD_API_KEY non définie. "
                "Créez un fichier .env ou passez api_key en paramètre."
            )

        if not self.endpoint_id:
            raise ValueError(
                "RUNPOD_ENDPOINT_ID non défini. "
                "Créez un fichier .env ou passez endpoint_id en paramètre."
            )

        self.base_url = f"https://api.runpod.ai/v2/{self.endpoint_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def analyze(
        self,
        video_path: str,
        question: str,
        max_frames: int = 32,
        problem_type: str = "free-form",
        timeout: int = 300,
        start_frame: int = 0,
        end_frame: int = None,
        smart: bool = False,
        resolution: int = 560,
        overlap: int = 0,
        span: float = None,
        cumulative: bool = False,
    ) -> dict:
        """
        Analyse une vidéo avec une question.
        Si la plage dépasse max_frames, segmente automatiquement.

        Args:
            video_path: Chemin vers la vidéo
            question: Question à poser
            max_frames: Nombre max de frames par segment (défaut: 32)
            problem_type: Type de réponse attendue
            timeout: Timeout en secondes
            start_frame: Frame de début (optionnel)
            end_frame: Frame de fin (optionnel)
            smart: Utiliser l'extraction intelligente basée sur le mouvement
            resolution: Résolution des frames en pixels (défaut: 560)
            overlap: Chevauchement entre segments en frames (défaut: 0)
            span: Répartir les frames sur X secondes (extraction temporelle élargie)
            cumulative: Utiliser le contexte cumulatif entre segments

        Returns:
            Résultat de l'analyse avec 'thinking', 'answer', 'raw_output'
            Si segmenté, retourne un dict avec 'segments' contenant tous les résultats
        """
        from src.video_utils import extract_frames, get_video_info

        info = get_video_info(video_path)
        total_frames = info['total_frames']
        fps = info['fps']
        
        # Déterminer la plage effective
        effective_start = start_frame
        effective_end = end_frame if end_frame is not None else total_frames
        range_frames = effective_end - effective_start
        
        # Si la plage dépasse max_frames, segmenter automatiquement
        if range_frames > max_frames:
            console.print(f"[yellow]⚠️ Plage de {range_frames} frames > {max_frames} max[/]")
            console.print(f"[yellow]   → Segmentation automatique avec chevauchement de {overlap} frames[/]")
            console.print()
            
            return self._analyze_segmented(
                video_path=video_path,
                question=question,
                max_frames=max_frames,
                problem_type=problem_type,
                timeout=timeout,
                start_frame=effective_start,
                end_frame=effective_end,
                smart=smart,
                overlap=overlap,
                resolution=resolution,
                span=span,
                cumulative=cumulative
            )

        # Afficher les informations vidéo
        console.print(f"[cyan]📹 Vidéo:[/] {info['filename']}")
        console.print(f"[cyan]⏱️  Durée:[/] {info['duration_formatted']}")
        console.print(f"[cyan]📐 Résolution:[/] {info['width']}x{info['height']}")
        if start_frame > 0 or end_frame is not None:
            time_start = effective_start / fps if fps > 0 else 0
            time_end = effective_end / fps if fps > 0 else 0
            console.print(f"[cyan]📍 Plage:[/] {time_start:.1f}s - {time_end:.1f}s ({range_frames} frames)")
        else:
            console.print(f"[cyan]🎞️  Frames:[/] {total_frames} ({fps:.1f} fps)")
        
        if smart:
            console.print("[cyan]🧠 Mode Smart:[/] Activé (priorité au mouvement)")
        if span:
            console.print(f"[cyan]📊 Span:[/] {span}s (frames réparties sur {span} secondes)")
        
        console.print()

        # Extraire les frames
        with console.status("[bold green]Extraction des frames..."):
            frames = extract_frames(
                video_path, 
                max_frames=max_frames,
                start_frame=start_frame,
                end_frame=end_frame,
                smart_extraction=smart,
                target_size=(resolution, resolution),
                span_seconds=span
            )
            console.print(f"[green]✓[/] {len(frames)} frames extraites ({resolution}x{resolution}px)")

        # Envoyer la requête à RunPod
        max_pixels = resolution * resolution
        payload = {
            "input": {
                "video_frames": frames,
                "question": question,
                "problem_type": problem_type,
                "max_frames": max_frames,
                "resolution": resolution,
                "max_pixels": max_pixels,
            }
        }

        with console.status("[bold green]Envoi vers RunPod..."):
            response = requests.post(
                f"{self.base_url}/run",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            job_data = response.json()

        job_id = job_data.get("id")
        console.print(f"[green]✓[/] Job créé: {job_id}")

        # Attendre le résultat
        with console.status("[bold green]Analyse en cours sur RunPod (GPU)..."):
            result = self._wait_for_result(job_id, timeout)

        return result

    def _analyze_segmented(
        self,
        video_path: str,
        question: str,
        max_frames: int,
        problem_type: str,
        timeout: int,
        start_frame: int,
        end_frame: int,
        smart: bool = False,
        overlap: int = 16,
        resolution: int = 560,
        span: float = None,
        cumulative: bool = False,
    ) -> dict:
        """Analyse une plage en plusieurs segments avec chevauchement et contexte cumulatif optionnel."""
        from src.video_utils import get_video_info, extract_frames, get_video_segments
        from src.prompts import build_cumulative_prompt, extract_summary_from_response
        
        info = get_video_info(video_path)
        fps = info['fps']
        
        console.print(f"[cyan]📹 Vidéo:[/] {info['filename']}")
        console.print(f"[cyan]📍 Plage:[/] frames {start_frame}-{end_frame}")
        
        # Obtenir les segments avec chevauchement manuellement ici ou via video_utils
        # Pour une sous-plage, on doit calculer nous-mêmes ou adapter get_video_segments
        # On va le faire manuellement ici pour la sous-plage
        
        segments = []
        step = max_frames - overlap
        current = start_frame
        while current < end_frame:
            seg_end = min(current + max_frames, end_frame)
            segments.append((current, seg_end))
            if seg_end == end_frame:
                break
            current += step
            
        console.print(f"[cyan]📊 Segments:[/] {len(segments)} segments (overlap {overlap})")
        console.print(f"[cyan]📐 Résolution:[/] {resolution}x{resolution}px")
        if smart:
            console.print("[cyan]🧠 Mode Smart:[/] Activé")
        if span:
            console.print(f"[cyan]📊 Span:[/] {span}s par segment")
        if cumulative:
            console.print("[cyan]🔗 Contexte Cumulatif:[/] Activé")
        console.print()
        
        results = []
        max_pixels = resolution * resolution
        previous_summaries = []  # Pour le contexte cumulatif
        
        for i, (seg_start, seg_end) in enumerate(segments):
            time_start = seg_start / fps if fps > 0 else 0
            time_end = seg_end / fps if fps > 0 else 0
            
            console.print(f"[bold yellow]═══ Segment {i+1}/{len(segments)} ═══[/]")
            console.print(f"[dim]Frames {seg_start}-{seg_end} ({time_start:.1f}s - {time_end:.1f}s)[/]")
            
            try:
                # Extraire les frames du segment
                with console.status("[bold green]Extraction..."):
                    frames = extract_frames(
                        video_path,
                        max_frames=max_frames,
                        start_frame=seg_start,
                        end_frame=seg_end,
                        smart_extraction=smart,
                        target_size=(resolution, resolution),
                        span_seconds=span
                    )
                    console.print(f"[green]✓[/] {len(frames)} frames extraites")
                
                # Construire le prompt (avec ou sans contexte cumulatif)
                segment_question = question
                if cumulative and previous_summaries:
                    segment_question = build_cumulative_prompt(question, previous_summaries)
                    console.print(f"[dim]  📝 Contexte: {len(previous_summaries)} segments précédents[/]")
                
                # Envoyer à RunPod
                payload = {
                    "input": {
                        "video_frames": frames,
                        "question": segment_question,
                        "problem_type": problem_type,
                        "max_frames": max_frames,
                        "resolution": resolution,
                        "max_pixels": max_pixels,
                    }
                }
                
                with console.status("[bold green]Envoi vers RunPod..."):
                    response = requests.post(
                        f"{self.base_url}/run",
                        headers=self.headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    job_data = response.json()
                
                job_id = job_data.get("id")
                console.print(f"[green]✓[/] Job créé: {job_id}")
                
                with console.status("[bold green]Analyse en cours..."):
                    result = self._wait_for_result(job_id, timeout)
                
                result["segment"] = i + 1
                result["start_frame"] = seg_start
                result["end_frame"] = seg_end
                result["time_range"] = f"{time_start:.1f}s - {time_end:.1f}s"
                results.append(result)
                
                answer = result.get("answer", "")
                
                # Stocker le résumé pour le contexte cumulatif
                if cumulative:
                    summary = extract_summary_from_response(answer)
                    previous_summaries.append(f"({time_start:.1f}s-{time_end:.1f}s) {summary}")
                
                console.print(f"[green]✓[/] Réponse: {answer[:80]}...")
                console.print()
                
            except Exception as e:
                console.print(f"[red]✗[/] Erreur: {e}")
                results.append({
                    "segment": i + 1,
                    "error": str(e),
                    "start_frame": seg_start,
                    "end_frame": seg_end,
                })
                console.print()
        
        # Combiner les résultats
        combined_answer = "\n\n".join([
            f"**Segment {r['segment']} ({r['time_range']}):** {r.get('answer', 'Erreur')}"
            for r in results if "error" not in r
        ])
        
        return {
            "segmented": True,
            "total_segments": len(segments),
            "cumulative_mode": cumulative,
            "segments": results,
            "answer": combined_answer,
            "thinking": "Analyse segmentée" + (" avec contexte cumulatif" if cumulative else "") + " - voir détails",
        }

    def analyze_full_video(
        self,
        video_path: str,
        question: str,
        frames_per_segment: int = 64,
        problem_type: str = "free-form",
        timeout: int = 300,
    ) -> list:
        """
        Analyse une vidéo complète par segments.

        Args:
            video_path: Chemin vers la vidéo
            question: Question à poser
            frames_per_segment: Nombre de frames par segment
            problem_type: Type de réponse attendue
            timeout: Timeout par segment

        Returns:
            Liste des résultats pour chaque segment
        """
        from src.video_utils import get_video_info, get_video_segments

        info = get_video_info(video_path)
        segments = get_video_segments(video_path, frames_per_segment)
        
        console.print(f"[cyan]📹 Vidéo:[/] {info['filename']}")
        console.print(f"[cyan]⏱️  Durée:[/] {info['duration_formatted']}")
        console.print(f"[cyan]📐 Résolution:[/] {info['width']}x{info['height']}")
        console.print(f"[cyan]🎞️  Frames totales:[/] {info['total_frames']} ({info['fps']:.1f} fps)")
        console.print(f"[cyan]📊 Segments:[/] {len(segments)} segments de {frames_per_segment} frames")
        console.print()

        results = []
        
        for i, (start, end) in enumerate(segments):
            segment_time_start = start / info['fps'] if info['fps'] > 0 else 0
            segment_time_end = end / info['fps'] if info['fps'] > 0 else 0
            
            console.print(f"[bold yellow]═══ Segment {i+1}/{len(segments)} ═══[/]")
            console.print(f"[dim]Frames {start}-{end} ({segment_time_start:.1f}s - {segment_time_end:.1f}s)[/]")
            
            try:
                result = self.analyze(
                    video_path=video_path,
                    question=question,
                    max_frames=frames_per_segment,
                    problem_type=problem_type,
                    timeout=timeout,
                    start_frame=start,
                    end_frame=end,
                )
                result["segment"] = i + 1
                result["start_frame"] = start
                result["end_frame"] = end
                result["time_range"] = f"{segment_time_start:.1f}s - {segment_time_end:.1f}s"
                results.append(result)
                
                # Afficher un résumé rapide
                answer = result.get("answer", "")[:100]
                console.print(f"[green]✓[/] Réponse: {answer}...")
                console.print()
                
            except Exception as e:
                console.print(f"[red]✗[/] Erreur segment {i+1}: {e}")
                results.append({
                    "segment": i + 1,
                    "error": str(e),
                    "start_frame": start,
                    "end_frame": end,
                })
                console.print()

        return results

    def analyze_multipass(
        self,
        video_path: str,
        question: str = None,
        pass1_frames: int = 16,
        pass2_frames: int = 64,
        pass2_window: float = 8.0,
        resolution: int = 560,
        timeout: int = 300,
        start_time: float = None,
        end_time: float = None,
        smart: bool = False,
    ) -> dict:
        """
        Analyse multi-passes: scan rapide puis analyse détaillée des moments suspects.
        
        Pass 1: Scan rapide de la plage spécifiée (ou toute la vidéo)
        Pass 2: Analyse détaillée pour chaque moment suspect avec une fenêtre élargie
        
        Args:
            video_path: Chemin vers la vidéo
            question: Question personnalisée (utilise MULTIPASS_PASS2_PROMPT si None)
            pass1_frames: Frames pour le scan rapide (défaut: 16)
            pass2_frames: Frames pour l'analyse détaillée (défaut: 64)
            pass2_window: Fenêtre temporelle autour du moment suspect en secondes (défaut: 8.0)
            resolution: Résolution des frames (défaut: 560)
            timeout: Timeout par requête (défaut: 300)
            start_time: Temps de début en secondes (None = début de la vidéo)
            end_time: Temps de fin en secondes (None = fin de la vidéo)
            smart: Si True, utilise l'extraction intelligente basée sur le mouvement pour le Pass 1
            
        Returns:
            Dict avec les résultats des deux passes et conclusions finales
        """
        from src.video_utils import get_video_info, extract_frames
        from src.prompts import (
            MULTIPASS_PASS1_PROMPT, 
            MULTIPASS_PASS2_PROMPT, 
            parse_pass1_frames
        )
        
        info = get_video_info(video_path)
        total_frames = info['total_frames']
        fps = info['fps']
        full_duration = info['duration_seconds']
        
        # Calculer la plage effective
        range_start = start_time if start_time is not None else 0
        range_end = end_time if end_time is not None else full_duration
        range_duration = range_end - range_start
        
        # Calculer les frames correspondantes
        start_frame = int(range_start * fps)
        end_frame = int(range_end * fps)
        
        range_info = ""
        if start_time is not None or end_time is not None:
            range_info = f"\n[cyan]📍 Plage:[/] {range_start:.1f}s - {range_end:.1f}s ({range_duration:.1f}s)"
            
        smart_info = ""
        if smart:
            smart_info = "\n[green]🧠 Mode Smart: Activé (Scan mouvement)[/]"
        
        console.print(Panel.fit(
            f"[bold cyan]🔍 ANALYSE MULTI-PASS[/]\n"
            f"[cyan]📹 Vidéo:[/] {info['filename']}\n"
            f"[cyan]⏱️  Durée:[/] {info['duration_formatted']}{range_info}\n"
            f"[cyan]Pass 1:[/] Scan rapide ({pass1_frames} frames){smart_info}\n"
            f"[cyan]Pass 2:[/] Analyse détaillée ({pass2_frames} frames, fenêtre {pass2_window}s)",
            border_style="cyan"
        ))
        console.print()
        
        # ═══════════════════════════════════════════════════════════════
        # PASS 1: Scan rapide pour identifier les moments suspects
        # ═══════════════════════════════════════════════════════════════
        console.print("[bold yellow]═══ PASS 1: SCAN RAPIDE ═══[/]")
        console.print(f"[dim]Extraction de {pass1_frames} frames sur la plage {range_start:.1f}s - {range_end:.1f}s...[/]")
        
        try:
            # Extraire des frames réparties sur la plage spécifiée
            with console.status("[bold green]Extraction pass 1..."):
                frames = extract_frames(
                    video_path,
                    max_frames=pass1_frames,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    target_size=(resolution, resolution),
                    smart_extraction=smart,
                )
                actual_frames_count = len(frames)
                console.print(f"[green]✓[/] {actual_frames_count} frames extraites")
            
            # Formater le prompt Pass 1 avec le nombre de frames
            pass1_prompt_formatted = MULTIPASS_PASS1_PROMPT.format(total_frames=actual_frames_count)
            
            # Envoyer pour scan rapide
            max_pixels = resolution * resolution
            payload = {
                "input": {
                    "video_frames": frames,
                    "question": pass1_prompt_formatted,
                    "problem_type": "free-form",
                    "max_frames": pass1_frames,
                    "resolution": resolution,
                    "max_pixels": max_pixels,
                }
            }
            
            with console.status("[bold green]Envoi pass 1 vers RunPod..."):
                response = requests.post(
                    f"{self.base_url}/run",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                job_data = response.json()
            
            job_id = job_data.get("id")
            console.print(f"[green]✓[/] Job pass 1: {job_id}")
            
            with console.status("[bold green]Analyse pass 1 en cours..."):
                pass1_result = self._wait_for_result(job_id, timeout)
            
            pass1_answer = pass1_result.get("answer", "")
            console.print(f"[green]✓[/] Pass 1 terminé")
            console.print(f"[dim]Réponse: {pass1_answer[:200]}...[/]")
            
            # Parser les numéros de frames et convertir en timestamps (relatifs à la plage)
            relative_timestamps, confidence_score = parse_pass1_frames(pass1_answer, actual_frames_count, range_duration)
            # Ajouter l'offset de début de plage pour obtenir les timestamps absolus
            suspicious_timestamps = [round(range_start + t, 1) for t in relative_timestamps]
            
            console.print(f"[dim]Confiance Pass 1: {confidence_score}[/]")
            
        except Exception as e:
            console.print(f"[red]✗[/] Erreur pass 1: {e}")
            return {
                "multipass": True,
                "pass1_error": str(e),
                "suspicious_timestamps": [],
                "pass2_results": [],
                "answer": f"Erreur lors du scan rapide: {e}",
            }
        
        # Vérifier si des moments suspects ont été trouvés
        if not suspicious_timestamps:
            console.print("\n[green]✓ Aucun moment suspect détecté lors du scan rapide.[/]")
            return {
                "multipass": True,
                "pass1_result": pass1_result,
                "suspicious_timestamps": [],
                "pass2_results": [],
                "answer": "NO SUSPICIOUS ACTIVITY DETECTED - Le scan rapide n'a identifié aucun moment suspect.",
                "thinking": "Analyse multi-pass terminée: Pass 1 n'a détecté aucune activité suspecte.",
            }
        
        # Seuil de confiance: skip Pass 2 si confiance trop basse
        if confidence_score == "low" and len(suspicious_timestamps) > 0:
            console.print("\n[yellow]⚠️ Confiance faible - Pass 2 optionnel[/]")
        
        # Filtrer les timestamps qui dépassent la durée de la vidéo
        valid_timestamps = [t for t in suspicious_timestamps if t <= full_duration]
        if len(valid_timestamps) < len(suspicious_timestamps):
            invalid_count = len(suspicious_timestamps) - len(valid_timestamps)
            console.print(f"[dim]  ℹ️ {invalid_count} timestamp(s) ignoré(s) (au-delà de la durée vidéo)[/]")
        
        console.print(f"\n[yellow]⚠️ {len(valid_timestamps)} moment(s) suspect(s) à analyser: {valid_timestamps}[/]")
        console.print()
        
        # ═══════════════════════════════════════════════════════════════
        # PASS 2: Analyse détaillée pour chaque moment suspect
        # ═══════════════════════════════════════════════════════════════
        console.print("[bold yellow]═══ PASS 2: ANALYSE DÉTAILLÉE ═══[/]")
        
        pass2_results = []
        pass2_prompt = question if question else MULTIPASS_PASS2_PROMPT
        
        for i, timestamp in enumerate(valid_timestamps):
            console.print(f"\n[bold cyan]── Moment suspect #{i+1}: {timestamp}s ──[/]")
            
            # Calculer la fenêtre autour du timestamp
            window_start = max(0, timestamp - pass2_window / 2)
            window_end = min(full_duration, timestamp + pass2_window / 2)
            
            # Validation: la fenêtre doit être valide
            if window_end <= window_start:
                console.print(f"[yellow]  ⚠️ Fenêtre invalide, ignoré[/]")
                continue
                
            start_frame = int(window_start * fps)
            end_frame = min(int(window_end * fps), total_frames)
            
            console.print(f"[dim]Fenêtre: {window_start:.1f}s - {window_end:.1f}s (frames {start_frame}-{end_frame})[/]")
            
            try:
                # Extraire les frames de la fenêtre
                # Haute résolution pour Pass 2 (1.5x la résolution de base)
                pass2_resolution = min(int(resolution * 1.5), 896)  # Cap à 896px
                
                with console.status("[bold green]Extraction pass 2 (haute résolution)..."):
                    frames = extract_frames(
                        video_path,
                        max_frames=pass2_frames,
                        start_frame=start_frame,
                        end_frame=end_frame,
                        target_size=(pass2_resolution, pass2_resolution),
                    )
                    console.print(f"[green]✓[/] {len(frames)} frames extraites ({pass2_resolution}px)")
                
                # Envoyer pour analyse détaillée
                payload = {
                    "input": {
                        "video_frames": frames,
                        "question": pass2_prompt,
                        "problem_type": "free-form",
                        "max_frames": pass2_frames,
                        "resolution": resolution,
                        "max_pixels": max_pixels,
                    }
                }
                
                with console.status("[bold green]Envoi pass 2 vers RunPod..."):
                    response = requests.post(
                        f"{self.base_url}/run",
                        headers=self.headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    job_data = response.json()
                
                job_id = job_data.get("id")
                console.print(f"[green]✓[/] Job pass 2: {job_id}")
                
                with console.status("[bold green]Analyse pass 2 en cours..."):
                    pass2_result = self._wait_for_result(job_id, timeout)
                
                pass2_result["suspicious_timestamp"] = timestamp
                pass2_result["window"] = f"{window_start:.1f}s - {window_end:.1f}s"
                pass2_results.append(pass2_result)
                
                answer = pass2_result.get("answer", "")
                console.print(f"[green]✓[/] Analyse terminée")
                console.print(f"[dim]Réponse: {answer[:150]}...[/]")
                
            except Exception as e:
                console.print(f"[red]✗[/] Erreur: {e}")
                pass2_results.append({
                    "suspicious_timestamp": timestamp,
                    "error": str(e),
                })
        
        # Combiner les résultats
        combined_answer = "MULTI-PASS ANALYSIS RESULTS:\n\n"
        combined_answer += f"Pass 1 (Scan rapide): {len(suspicious_timestamps)} moment(s) suspect(s) identifié(s)\n\n"
        
        for i, result in enumerate(pass2_results):
            timestamp = result.get("suspicious_timestamp", "?")
            window = result.get("window", "?")
            answer = result.get("answer", result.get("error", "Non analysé"))
            combined_answer += f"**Moment suspect #{i+1} ({timestamp}s, fenêtre {window}):**\n{answer}\n\n"
        
        console.print()
        
        return {
            "multipass": True,
            "pass1_result": pass1_result,
            "suspicious_timestamps": suspicious_timestamps,
            "pass2_results": pass2_results,
            "answer": combined_answer,
            "thinking": f"Analyse multi-pass: {len(suspicious_timestamps)} moments suspects analysés en détail.",
        }

    def _wait_for_result(self, job_id: str, timeout: int) -> dict:
        """Attend et récupère le résultat d'un job RunPod."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.base_url}/status/{job_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            status_data = response.json()

            status = status_data.get("status")

            if status == "COMPLETED":
                output = status_data.get("output", {})
                if isinstance(output, dict) and "error" in output:
                    error_msg = output.get("error", "Unknown error")
                    traceback = output.get("traceback", "")
                    raise RuntimeError(f"Erreur du worker: {error_msg}\n{traceback}")
                return output

            elif status == "FAILED":
                # Afficher toutes les infos disponibles pour debug
                error = status_data.get("error")
                output = status_data.get("output")
                
                # Construire le message d'erreur complet
                error_parts = []
                if error:
                    error_parts.append(f"Error: {error}")
                if output and isinstance(output, dict):
                    if "error" in output:
                        error_parts.append(f"Output error: {output.get('error')}")
                    if "traceback" in output:
                        error_parts.append(f"Traceback: {output.get('traceback')}")
                elif output:
                    error_parts.append(f"Output: {output}")
                    
                if not error_parts:
                    error_parts.append(f"Full response: {status_data}")
                    
                raise RuntimeError(f"Job échoué: {chr(10).join(error_parts)}")

            elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                time.sleep(2)  # Attendre 2 secondes entre les checks

            else:
                raise RuntimeError(f"Status inconnu: {status}")

        raise TimeoutError(f"Timeout après {timeout} secondes")

    def check_endpoint_health(self) -> dict:
        """Vérifie l'état de l'endpoint RunPod."""
        response = requests.get(
            f"{self.base_url}/health",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()


def create_client(
    api_key: Optional[str] = None,
    endpoint_id: Optional[str] = None,
) -> VideoR1Client:
    """Factory pour créer un client Video-R1."""
    return VideoR1Client(api_key=api_key, endpoint_id=endpoint_id)
