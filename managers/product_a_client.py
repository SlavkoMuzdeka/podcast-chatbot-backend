import os
import logging
import requests

from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)


class ProductAClient:
    """Client for interacting with Product A API"""

    def __init__(self):
        self.base_url = os.getenv("PRODUCT_A_BASE_URL", "http://localhost:8000")
        self.api_key = os.getenv("PRODUCT_A_API_KEY", "")
        self.timeout = 300  # 5 minutes timeout for processing

    def process_episode(self, url: str, episode_id: str) -> Dict[str, Any]:
        """
        Send episode URL to Product A for processing

        Args:
            url: Episode URL (YouTube or RSS)
            episode_id: Unique identifier for the episode

        Returns:
            Dict containing transcript, summary, and metadata
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            }

            payload = {
                "url": url,
                "episode_id": episode_id,
                "include_transcript": True,
                "include_summary": True,
                "include_timestamps": True,
            }

            logger.info(f"Sending episode {episode_id} to Product A for processing")

            response = requests.post(
                f"{self.base_url}/api/process-episode",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully processed episode {episode_id}")
                return {
                    "success": True,
                    "transcript": data.get("transcript", ""),
                    "summary": data.get("summary", ""),
                    "title": data.get("title", ""),
                    "duration": data.get("duration"),
                    "timestamps": data.get("timestamps", []),
                    "metadata": data.get("metadata", {}),
                }
            else:
                logger.error(
                    f"Product A returned error {response.status_code}: {response.text}"
                )
                return {
                    "success": False,
                    "error": f"Processing failed with status {response.status_code}",
                }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout processing episode {episode_id}")
            return {
                "success": False,
                "error": "Processing timeout - episode may be too long",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error processing episode {episode_id}: {str(e)}")
            return {
                "success": False,
                "error": "Network error connecting to processing service",
            }
        except Exception as e:
            logger.error(f"Unexpected error processing episode {episode_id}: {str(e)}")
            return {"success": False, "error": "Unexpected error during processing"}

    def get_processing_status(self, episode_id: str) -> Dict[str, Any]:
        """
        Check the processing status of an episode

        Args:
            episode_id: Unique identifier for the episode

        Returns:
            Dict containing processing status and progress
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
            }

            response = requests.get(
                f"{self.base_url}/api/episode-status/{episode_id}",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"Status check failed with status {response.status_code}",
                }

        except Exception as e:
            logger.error(f"Error checking status for episode {episode_id}: {str(e)}")
            return {"success": False, "error": "Error checking processing status"}
