# backend/services/video_r1.py
"""
Service d'intégration du CLI Video-R1 avec le backend FastAPI
"""

import subprocess
import json
import tempfile
import os
import sys
from typing import Dict
import logging

from backend.models import Video, Detection
from backend.config import settings

logger = logging.getLogger(__name__)


class VideoR1Service:
    """
    Service pour exécuter les analyses Video-R1 via CLI
    """

    @staticmethod
    def run_detection_task(
        video_id: int,
        video_path: str,
        params: dict
    ) -> None:
        """
        Exécuter une détection vidéo avec les paramètres utilisateur.
        """

        logger.info(f"Début de l'analyse pour video_id={video_id}")

        from backend.database import SessionLocal

        db = SessionLocal()
        output_file = None

        logger.info("Session database créée pour la tâche background")

        try:
            # Créer fichier temporaire de sortie
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                output_file = f.name

            logger.info(f"Fichier temporaire créé: {output_file}")

            # Déterminer la question
            if params.get("custom_question"):
                question = params["custom_question"]
                logger.info(f"💬 Question personnalisée: {question[:50]}...")
            else:
                try:
                    from src.prompts import get_prompt
                    question = get_prompt(params["detection_type"])
                    logger.info(f"Prompt prédéfini pour: {params['detection_type']}")

                except ImportError as e:
                    logger.error(f"Module prompts non chargé: {e}")
                    question = "Describe what you see in this video."

                except Exception as e:
                    logger.error(f"Erreur récupération prompt: {e}")
                    question = "Describe what you see in this video."

            # Python executable utilisé
            python_executable = sys.executable
            logger.info(f"Python utilisé: {python_executable}")

            # Construire la commande CLI
            cmd = [
                python_executable,
                "-m", "src.cli",
                "detect",
                video_path,
                "--type", params["detection_type"],
                "--frames", str(params["frames"]),
                "--resolution", str(params["resolution"]),
                "--output", output_file
            ]

            # Smart Mode
            if params.get("smart"):
                cmd.append("--smart")
                logger.info("✓ --smart activé")

            # Multi-pass
            if params.get("multipass"):
                cmd.append("--multipass")
                logger.info("✓ --multipass activé")

                if params.get("pass1_frames"):
                    cmd.extend(["--pass1-frames", str(params["pass1_frames"])])

                if params.get("pass2_frames"):
                    cmd.extend(["--pass2-frames", str(params["pass2_frames"])])

                if params.get("pass2_window"):
                    cmd.extend(["--pass2-window", str(params["pass2_window"])])

            # Cumulative
            if params.get("cumulative"):
                cmd.append("--cumulative")
                logger.info("✓ --cumulative activé")

            # Span
            if params.get("span") is not None:
                cmd.extend(["--span", str(params["span"])])

            # Overlap
            if params.get("overlap") and params["overlap"] > 0:
                cmd.extend(["--overlap", str(params["overlap"])])

            # Plage temporelle
            if params.get("start_frame") is not None:
                cmd.extend(["--start-frame", str(params["start_frame"])])
            elif params.get("start") is not None:
                cmd.extend(["--start", str(params["start"])])

            if params.get("end_frame") is not None:
                cmd.extend(["--end-frame", str(params["end_frame"])])
            elif params.get("end") is not None:
                cmd.extend(["--end", str(params["end"])])

            logger.info("=" * 70)
            logger.info("COMMANDE CLI CONSTRUITE:")
            logger.info("=" * 70)
            logger.info(" ".join(cmd))
            logger.info("=" * 70)

            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            logger.info(f"Répertoire de travail: {project_root}")

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            logger.info("Exécution du CLI Video-R1...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=settings.VIDEO_R1_TIMEOUT,
                cwd=project_root,
                env=env
            )

            logger.info(f"CLI terminé avec code: {result.returncode}")

            if result.stdout:
                logger.info(f"STDOUT: {result.stdout[:500]}")

            if result.stderr:
                logger.warning(f"STDERR: {result.stderr[:500]}")

            if result.returncode != 0:
                logger.error(f"CLI a échoué avec code {result.returncode}")
                raise subprocess.CalledProcessError(
                    result.returncode,
                    cmd,
                    output=result.stdout,
                    stderr=result.stderr
                )

            if not output_file or not os.path.exists(output_file):
                logger.error(f"Fichier de sortie non trouvé: {output_file}")
                raise FileNotFoundError("Le CLI n'a pas créé le fichier de sortie")

            file_size = os.path.getsize(output_file)
            logger.info(f"Fichier de sortie: {file_size} bytes")

            if file_size == 0:
                logger.error("Le fichier de sortie est vide")
                raise ValueError("Le CLI a créé un fichier de sortie vide")

            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    file_content = f.read()

                detection_result = json.loads(file_content)

                logger.info("✅ JSON parsé avec succès")
                logger.debug(f"Clés du résultat: {detection_result.keys()}")

            except json.JSONDecodeError as e:
                logger.error(f"❌ Erreur de parsing JSON: {e}")
                logger.error(f"Contenu du fichier: {file_content[:500]}")
                raise

            video = db.query(Video).filter(Video.id == video_id).first()

            if video:
                detection = Detection(
                    video_id=video_id,
                    detection_type=params.get("detection_type", "unknown"),
                    result=detection_result,
                    confidence=detection_result.get("confidence"),
                    timestamp_start=params.get("start"),
                    timestamp_end=params.get("end")
                )

                db.add(detection)
                video.status = "completed"
                db.commit()

                logger.info(
                    f"Détection sauvegardée "
                    f"(video_id={video_id}, detection_id={detection.id})"
                )

            else:
                logger.error(f"Vidéo id={video_id} non trouvée en base")

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout après {settings.VIDEO_R1_TIMEOUT} secondes")

            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"

            detection = Detection(
                video_id=video_id,
                detection_type=params.get("detection_type", "unknown"),
                result={
                    "error": f"Timeout: Analysis took more than {settings.VIDEO_R1_TIMEOUT} seconds"
                }
            )

            db.add(detection)
            db.commit()

        except subprocess.CalledProcessError as e:
            logger.error(f"Échec du CLI: {e.stderr}")

            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"

            detection = Detection(
                video_id=video_id,
                detection_type=params.get("detection_type", "unknown"),
                result={
                    "error": f"CLI Error: {str(e.stderr)}"
                }
            )

            db.add(detection)
            db.commit()

        except Exception as e:
            logger.error(f"Erreur inattendue: {str(e)}")
            logger.exception("Unexpected error during Video-R1 execution")

            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"

            detection = Detection(
                video_id=video_id,
                detection_type=params.get("detection_type", "unknown"),
                result={
                    "error": str(e)
                }
            )

            db.add(detection)
            db.commit()

        finally:
            db.close()
            logger.info("Session database fermée")

            if output_file and os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                    logger.info(f"Fichier temporaire supprimé: {output_file}")
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")

            logger.info(f"Fin de la tâche pour video_id={video_id}")

    @staticmethod
    def get_video_info(video_path: str) -> Dict:
        """
        Obtenir les informations d'une vidéo.
        """
        try:
            from src.video_utils import get_video_info

            info = get_video_info(video_path)
            logger.info(f"Métadonnées extraites: {video_path}")
            return info

        except ImportError as e:
            logger.error(f"Module video_utils non disponible: {e}")
            return {"error": f"Module unavailable: {str(e)}"}

        except Exception as e:
            logger.error(f"Erreur extraction métadonnées: {e}")
            return {"error": str(e)}