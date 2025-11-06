"""Video analysis module for video advertisements."""

import logging
import os
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path
import cv2
import base64
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Analyzes video advertisements by extracting and analyzing key frames."""

    def __init__(self):
        """Initialize video analyzer."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def analyze_video(self, video_path: str, num_frames: int = 5) -> Dict[str, Any]:
        """Analyze a video advertisement.

        Args:
            video_path: Path to video file
            num_frames: Number of key frames to extract and analyze

        Returns:
            Dictionary containing video analysis
        """
        logger.info(f"Analyzing video: {video_path}")

        try:
            # Extract key frames
            frames = self._extract_key_frames(video_path, num_frames)

            if not frames:
                return {'error': 'Failed to extract frames from video'}

            # Analyze frames
            frame_analyses = []
            for idx, frame_path in enumerate(frames):
                analysis = self._analyze_frame(frame_path, idx, num_frames)
                frame_analyses.append(analysis)

            # Get video metadata
            metadata = self._get_video_metadata(video_path)

            # Perform overall video analysis
            overall_analysis = self._analyze_video_progression(frame_analyses, metadata)

            # Clean up temporary files
            self._cleanup_frames(frames)

            return {
                'video_path': video_path,
                'metadata': metadata,
                'frame_analyses': frame_analyses,
                'overall_analysis': overall_analysis,
                'num_frames_analyzed': len(frames)
            }

        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            return {
                'error': str(e),
                'video_path': video_path
            }

    def _extract_key_frames(self, video_path: str, num_frames: int) -> List[str]:
        """Extract key frames from video.

        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract

        Returns:
            List of paths to extracted frame images
        """
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                logger.error(f"Failed to open video: {video_path}")
                return []

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            logger.info(f"Video has {total_frames} frames at {fps} FPS")

            # Calculate frame indices to extract (evenly spaced)
            frame_indices = [int(total_frames * i / num_frames) for i in range(num_frames)]

            # Extract frames
            extracted_frames = []
            temp_dir = tempfile.mkdtemp(prefix='video_frames_')

            for idx, frame_num in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if ret:
                    frame_path = os.path.join(temp_dir, f'frame_{idx:03d}.jpg')
                    cv2.imwrite(frame_path, frame)
                    extracted_frames.append(frame_path)
                    logger.debug(f"Extracted frame {frame_num} to {frame_path}")
                else:
                    logger.warning(f"Failed to read frame {frame_num}")

            cap.release()

            logger.info(f"Extracted {len(extracted_frames)} frames from video")
            return extracted_frames

        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            return []

    def _analyze_frame(self, frame_path: str, frame_index: int, total_frames: int) -> Dict[str, Any]:
        """Analyze a single video frame.

        Args:
            frame_path: Path to frame image
            frame_index: Index of this frame
            total_frames: Total number of frames being analyzed

        Returns:
            Frame analysis dictionary
        """
        try:
            # Read and encode image
            with open(frame_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            # Determine position in video
            position = 'beginning' if frame_index == 0 else \
                      'end' if frame_index == total_frames - 1 else \
                      'middle'

            # Analyze with Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""Analyze this frame from a video advertisement (frame {frame_index + 1} of {total_frames}, {position} of video).

Describe:
1. What's happening in this frame
2. Key visual elements
3. Text or messaging visible
4. Emotional tone/mood
5. Call-to-action if present

Be concise (2-3 sentences)."""
                        }
                    ]
                }]
            )

            analysis_text = response.content[0].text

            return {
                'frame_index': frame_index,
                'position': position,
                'analysis': analysis_text,
                'frame_path': frame_path
            }

        except Exception as e:
            logger.error(f"Error analyzing frame {frame_index}: {e}")
            return {
                'frame_index': frame_index,
                'error': str(e)
            }

    def _analyze_video_progression(self, frame_analyses: List[Dict[str, Any]],
                                   metadata: Dict[str, Any]) -> str:
        """Analyze the overall video progression and narrative.

        Args:
            frame_analyses: List of individual frame analyses
            metadata: Video metadata

        Returns:
            Overall analysis text
        """
        try:
            # Combine frame analyses
            frames_summary = "\n\n".join([
                f"Frame {a['frame_index'] + 1} ({a['position']}): {a.get('analysis', 'N/A')}"
                for a in frame_analyses if 'analysis' in a
            ])

            # Get overall analysis
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Based on these frame analyses from a video ad, provide an overall analysis:

{frames_summary}

Video Duration: {metadata.get('duration', 'Unknown')} seconds

Analyze:
1. Narrative structure and progression
2. Visual consistency and branding
3. Pacing and timing
4. Emotional journey
5. Effectiveness of the video format
6. Key recommendations for video ads

Be specific and actionable."""
                }]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error analyzing video progression: {e}")
            return f"Error: {str(e)}"

    def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract metadata from video file.

        Args:
            video_path: Path to video file

        Returns:
            Metadata dictionary
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                return {}

            metadata = {
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'format': Path(video_path).suffix
            }

            cap.release()

            return metadata

        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {}

    def _cleanup_frames(self, frame_paths: List[str]):
        """Clean up temporary frame files.

        Args:
            frame_paths: List of frame file paths to delete
        """
        try:
            for frame_path in frame_paths:
                if os.path.exists(frame_path):
                    os.remove(frame_path)

            # Remove temporary directory if empty
            if frame_paths:
                temp_dir = os.path.dirname(frame_paths[0])
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)

            logger.debug("Cleaned up temporary frame files")

        except Exception as e:
            logger.warning(f"Error cleaning up frames: {e}")

    def extract_audio_transcript(self, video_path: str) -> Optional[str]:
        """Extract audio and transcribe (requires additional dependencies).

        Note: This is a placeholder. Full implementation would require:
        - ffmpeg for audio extraction
        - speech-to-text service (e.g., Whisper API)

        Args:
            video_path: Path to video file

        Returns:
            Transcribed text or None
        """
        logger.info("Audio transcription not yet implemented")
        # TODO: Implement with Whisper API or similar
        return None
