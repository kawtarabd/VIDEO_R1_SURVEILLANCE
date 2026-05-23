"""
Interface en ligne de commande pour Video-R1 Surveillance Analyzer.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import json
import os

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Video-R1 Surveillance Analyzer - Analyse de vidéos par IA."""
    pass


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.argument("question")
@click.option("--frames", "-f", default=32, help="Nombre max de frames par segment (défaut: 32)")
@click.option("--resolution", "-r", default=560, help="Résolution des frames en pixels (défaut: 560)")
@click.option("--output", "-o", type=click.Path(), help="Fichier de sortie JSON (optionnel)")
@click.option("--start", "-s", type=float, default=None, help="Temps de début en secondes")
@click.option("--end", "-e", type=float, default=None, help="Temps de fin en secondes (défaut: fin de vidéo)")
@click.option("--start-frame", type=int, default=None, help="Frame de début")
@click.option("--end-frame", type=int, default=None, help="Frame de fin (défaut: fin de vidéo)")
@click.option("--smart", is_flag=True, help="Extraction intelligente (priorité au mouvement)")
def analyze(video_path: str, question: str, frames: int, resolution: int, output: str, 
            start: float, end: float, start_frame: int, end_frame: int, smart: bool):
    """Analyse une vidéo avec une question en langage naturel.

    Exemples:
        python -m src.cli analyze video.mp4 "Que se passe-t-il?"
        python -m src.cli analyze video.mp4 "Y a-t-il un vol?" --frames 128 --resolution 560
    """
    from src.client import create_client
    from src.video_utils import get_video_info

    # Obtenir les infos vidéo pour convertir temps -> frames
    info = get_video_info(video_path)
    fps = info['fps']
    total_frames = info['total_frames']

    # Calculer les frames de début/fin
    calc_start_frame = 0
    calc_end_frame = None

    # Priorité: start-frame/end-frame > start/end
    if start_frame is not None:
        calc_start_frame = start_frame
    elif start is not None:
        calc_start_frame = int(start * fps)

    if end_frame is not None:
        calc_end_frame = end_frame
    elif end is not None:
        calc_end_frame = int(end * fps)

    # Afficher l'info de plage
    range_info = ""
    if calc_start_frame > 0 or calc_end_frame is not None:
        time_start = calc_start_frame / fps if fps > 0 else 0
        time_end = (calc_end_frame / fps if calc_end_frame else total_frames / fps) if fps > 0 else 0
        range_info = f"\nPlage: {time_start:.1f}s - {time_end:.1f}s (frames {calc_start_frame}-{calc_end_frame or total_frames})"

    title = f"[bold blue]🔍 Analyse Video-R1[/]\nQuestion: {question}{range_info}"
    title += f"\n[dim]Frames: {frames} | Résolution: {resolution}px[/]"
    if smart:
        title += "\n[cyan]🧠 Mode Smart: Activé[/]"

    console.print(Panel.fit(title, border_style="blue"))
    console.print()

    try:
        client = create_client()
        result = client.analyze(
            video_path, 
            question, 
            max_frames=frames,
            start_frame=calc_start_frame,
            end_frame=calc_end_frame,
            smart=smart,
            resolution=resolution
        )

        # Afficher le raisonnement
        if result.get("thinking"):
            console.print(Panel(
                result["thinking"],
                title="[yellow]💭 Raisonnement[/]",
                border_style="yellow"
            ))
            console.print()

        # Afficher la réponse
        console.print(Panel(
            Markdown(result.get("answer", result.get("raw_output", "Pas de réponse"))),
            title="[green]✅ Réponse[/]",
            border_style="green"
        ))

        # Sauvegarder si demandé
        if output:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            console.print(f"\n[cyan]📄 Résultat sauvegardé: {output}[/]")

    except Exception as e:
        console.print(f"[red]❌ Erreur: {e}[/]")
        raise click.Abort()


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option(
    "--type", "-t", "detection_type",
    type=click.Choice(["shoplifting", "suspicious_behavior", "checkout_interactions", "timeline", "crowd_analysis", "general"]),
    default="general",
    help="Type de détection à effectuer"
)
@click.option("--frames", "-f", default=32, help="Nombre max de frames par segment (défaut: 32)")
@click.option("--resolution", "-r", default=560, help="Résolution des frames en pixels (défaut: 560)")
@click.option("--overlap", is_flag=False, flag_value=16, default=0, help="Chevauchement entre segments (sans valeur: 16, sinon: valeur spécifiée)")
@click.option("--span", type=float, default=None, help="Répartir les frames sur X secondes (ex: --span 10)")
@click.option("--cumulative", is_flag=True, help="Contexte cumulatif entre segments")
@click.option("--multipass", is_flag=True, help="Analyse multi-passes: scan rapide puis focus sur moments suspects")
@click.option("--pass1-frames", type=int, default=16, help="Frames pour pass 1 - scan rapide (défaut: 16)")
@click.option("--pass2-frames", type=int, default=64, help="Frames pour pass 2 - analyse détaillée (défaut: 64)")
@click.option("--pass2-window", type=float, default=8.0, help="Fenêtre temporelle pass 2 en secondes (défaut: 8.0)")
@click.option("--output", "-o", type=click.Path(), help="Fichier de sortie JSON")
@click.option("--start", "-s", type=float, default=None, help="Temps de début en secondes")
@click.option("--end", "-e", type=float, default=None, help="Temps de fin en secondes")
@click.option("--start-frame", type=int, default=None, help="Frame de début")
@click.option("--end-frame", type=int, default=None, help="Frame de fin")
@click.option("--smart", is_flag=True, help="Extraction intelligente (priorité au mouvement)")
def detect(video_path: str, detection_type: str, frames: int, resolution: int, overlap: int, span: float, 
           cumulative: bool, multipass: bool, pass1_frames: int, pass2_frames: int, pass2_window: float,
           output: str, start: float, end: float, start_frame: int, end_frame: int, smart: bool):
    """Détection d'événements prédéfinis dans une vidéo.

    Types disponibles:
    - shoplifting: Détection de vol à l'étalage
    - suspicious_behavior: Comportements suspects
    - checkout_interactions: Interactions à la caisse
    - timeline: Chronologie des événements
    - crowd_analysis: Analyse de foule
    - general: Description générale

    Exemples:
        python -m src.cli detect video.mp4 --type shoplifting --smart
        python -m src.cli detect video.mp4 -t shoplifting --frames 128 --resolution 560
    """
    from src.client import create_client
    from src.prompts import get_prompt
    from src.video_utils import get_video_info

    # Obtenir les infos vidéo pour convertir temps -> frames
    info = get_video_info(video_path)
    fps = info['fps']
    total_frames = info['total_frames']

    # Calculer les frames de début/fin
    calc_start_frame = 0
    calc_end_frame = None

    if start_frame is not None:
        calc_start_frame = start_frame
    elif start is not None:
        calc_start_frame = int(start * fps)

    if end_frame is not None:
        calc_end_frame = end_frame
    elif end is not None:
        calc_end_frame = int(end * fps)

    # Afficher l'info de plage
    range_info = ""
    if calc_start_frame > 0 or calc_end_frame is not None:
        time_start = calc_start_frame / fps if fps > 0 else 0
        time_end = (calc_end_frame / fps if calc_end_frame else total_frames / fps) if fps > 0 else 0
        range_info = f"\nPlage: {time_start:.1f}s - {time_end:.1f}s"

    # Construire le panneau d'info
    title = f"[bold blue]🎯 Détection: {detection_type}[/]"
    title += f"\n[cyan]📹 Vidéo:[/] {info['filename']}"
    title += f"\n[cyan]⏱️  Durée:[/] {info['duration_formatted']} | [cyan]📐 Résolution:[/] {info['width']}x{info['height']}"
    title += f"\n[cyan]🎞️  Total Frames:[/] {total_frames} | [cyan]FPS:[/] {fps:.2f}"
    if range_info:
        title += f"\n[yellow]{range_info}[/]"
    title += f"\n[dim]Frames/segment: {frames} | Résolution traitement: {resolution}px[/]"
    if span:
        title += f"\n[magenta]📊 Span temporel: {span}s (frames réparties sur {span} secondes)[/]"
    if cumulative:
        title += "\n[yellow]🔗 Contexte Cumulatif: Activé[/]"
    if multipass:
        title += f"\n[cyan]🔍 Multi-Pass: Activé (P1:{pass1_frames}f, P2:{pass2_frames}f, fenêtre:{pass2_window}s)[/]"
    if smart:
        title += "\n[green]🧠 Mode Smart: Activé[/]"

    console.print(Panel.fit(
        title,
        border_style="blue"
    ))
    console.print()

    try:
        question = get_prompt(detection_type)
        client = create_client()
        
        # Mode Multi-Pass: utiliser analyze_multipass()
        if multipass:
            result = client.analyze_multipass(
                video_path,
                question=question,
                pass1_frames=pass1_frames,
                pass2_frames=pass2_frames,
                pass2_window=pass2_window,
                resolution=resolution,
                start_time=start,
                end_time=end,
                smart=smart,
            )
        else:
            # Mode standard
            result = client.analyze(
                video_path, 
                question, 
                max_frames=frames,
                start_frame=calc_start_frame,
                end_frame=calc_end_frame,
                smart=smart,
                resolution=resolution,
                overlap=overlap,
                span=span,
                cumulative=cumulative
            )

        # Afficher le raisonnement
        if result.get("thinking"):
            console.print(Panel(
                result["thinking"][:500] + "..." if len(result.get("thinking", "")) > 500 else result.get("thinking", ""),
                title="[yellow]💭 Raisonnement (extrait)[/]",
                border_style="yellow"
            ))
            console.print()

        # Afficher la réponse
        console.print(Panel(
            Markdown(result.get("answer", result.get("raw_output", "Pas de réponse"))),
            title=f"[green]✅ Résultat - {detection_type}[/]",
            border_style="green"
        ))

        # Sauvegarder si demandé
        if output:
            with open(output, "w", encoding="utf-8") as f:
                json.dump({
                    "detection_type": detection_type,
                    "video_path": video_path,
                    **result
                }, f, ensure_ascii=False, indent=2)
            console.print(f"\n[cyan]📄 Résultat sauvegardé: {output}[/]")

    except Exception as e:
        console.print(f"[red]❌ Erreur: {e}[/]")
        raise click.Abort()


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.argument("question")
@click.option("--frames-per-segment", "-f", default=64, help="Frames par segment (défaut: 64)")
@click.option("--output", "-o", type=click.Path(), help="Fichier de sortie JSON")
def scan(video_path: str, question: str, frames_per_segment: int, output: str):
    """Analyse complète d'une vidéo par segments.

    Divise la vidéo en segments de N frames et analyse chaque segment.
    Utile pour ne manquer aucun événement dans une vidéo longue.

    Exemples:
        python -m src.cli scan video.mp4 "Y a-t-il un vol?" --frames-per-segment 64
        python -m src.cli scan surveillance.mp4 "Détecter tout comportement suspect"
    """
    from src.client import create_client

    console.print(Panel.fit(
        f"[bold blue]🔍 Scan Complet Video-R1[/]\n"
        f"Question: {question}\n"
        f"Frames par segment: {frames_per_segment}",
        border_style="blue"
    ))
    console.print()

    try:
        client = create_client()
        results = client.analyze_full_video(
            video_path, 
            question, 
            frames_per_segment=frames_per_segment
        )

        # Résumé
        console.print(Panel.fit(
            f"[bold green]📊 Analyse terminée[/]\n"
            f"Segments analysés: {len(results)}",
            border_style="green"
        ))
        console.print()

        # Afficher les résultats avec détection positive
        detections = []
        for result in results:
            if "error" not in result:
                answer = result.get("answer", "").lower()
                # Chercher des indices de détection positive
                if any(word in answer for word in ["oui", "yes", "vol", "theft", "suspicious", "suspect"]):
                    detections.append(result)

        if detections:
            console.print("[bold red]⚠️ ÉVÉNEMENTS DÉTECTÉS:[/]")
            for d in detections:
                console.print(Panel(
                    f"[bold]Segment {d['segment']}[/] ({d['time_range']})\n\n"
                    f"{d.get('answer', 'Pas de réponse')}",
                    border_style="red"
                ))
        else:
            console.print("[green]✅ Aucun événement suspect détecté dans l'ensemble de la vidéo[/]")

        # Sauvegarder si demandé
        if output:
            with open(output, "w", encoding="utf-8") as f:
                json.dump({
                    "video_path": video_path,
                    "question": question,
                    "total_segments": len(results),
                    "detections": len(detections),
                    "segments": results
                }, f, ensure_ascii=False, indent=2)
            console.print(f"\n[cyan]📄 Résultat sauvegardé: {output}[/]")

    except Exception as e:
        console.print(f"[red]❌ Erreur: {e}[/]")
        raise click.Abort()


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
def info(video_path: str):
    """Affiche les informations sur une vidéo.

    Exemple:
        python -m src.cli info video.mp4
    """
    from src.video_utils import get_video_info

    try:
        info = get_video_info(video_path)

        console.print(Panel.fit(
            f"[bold]📹 {info['filename']}[/]\n\n"
            f"Durée: {info['duration_formatted']}\n"
            f"Résolution: {info['width']} x {info['height']}\n"
            f"FPS: {info['fps']:.2f}\n"
            f"Total frames: {info['total_frames']}",
            title="Informations vidéo",
            border_style="cyan"
        ))

    except Exception as e:
        console.print(f"[red]❌ Erreur: {e}[/]")


@cli.command()
def prompts():
    """Liste les types de prompts de surveillance disponibles."""
    from src.prompts import SURVEILLANCE_PROMPTS

    console.print(Panel.fit(
        "[bold]Types de détection disponibles[/]",
        border_style="blue"
    ))

    for name, prompt in SURVEILLANCE_PROMPTS.items():
        console.print(f"\n[cyan]{name}[/]")
        # Afficher les 100 premiers caractères du prompt
        preview = prompt[:100].replace("\n", " ") + "..."
        console.print(f"  {preview}")


@cli.command()
def deploy():
    """Instructions pour déployer le worker sur RunPod."""
    console.print(Panel(
        Markdown("""
# Déploiement sur RunPod

## 1. Créer un compte RunPod
Allez sur https://runpod.io et créez un compte.

## 2. Build et push l'image Docker
```bash
cd runpod_worker
docker build -t votre-dockerhub/video-r1-worker:latest .
docker push votre-dockerhub/video-r1-worker:latest
```

## 3. Créer l'endpoint
1. Console RunPod → Serverless → New Endpoint
2. Sélectionnez "Custom"
3. Image: `votre-dockerhub/video-r1-worker:latest`
4. GPU: A100 80GB
5. Cliquez "Create Endpoint"

## 4. Configurer le client
```bash
cp .env.example .env
# Éditez .env avec votre API key et endpoint ID
```

## 5. Utiliser
```bash
python -m src.cli analyze video.mp4 "Votre question"
```

## Coûts estimés
- GPU A100: ~$1.99/heure
- Scale-to-zero automatique
- Paiement à la seconde
"""),
        title="[bold green]Guide de déploiement RunPod[/]",
        border_style="green"
    ))


if __name__ == "__main__":
    cli()
