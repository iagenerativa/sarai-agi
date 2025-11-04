"""
Vision Agent - Visual Analysis with Qwen3-VL-4B-GGUF

High-performance vision agent for multimodal input processing using Qwen3-VL-4B
in GGUF format for efficient CPU inference.

Capabilities
------------
- Image analysis (OCR, object detection, scene description)
- Visual reasoning (answering questions about visual content)
- Diagram and chart interpretation
- Video analysis (frame-by-frame, temporal understanding)

Performance Benchmarks (Qwen3-VL-4B Q6_K)
------------------------------------------
- MMMU: 60.1% (visual understanding)
- MVBench: 71.9% (video analysis)
- Video-MME: 65.8% (video reasoning)

Memory Management
-----------------
- Load on demand when input_type in ["image", "video"]
- Auto-release after 60s TTL (Time-To-Live)
- Auto-unload if available RAM < 4GB
- Swapping with LFM2 for memory optimization

Architecture
------------
- Model: Qwen3-VL-4B-Instruct.Q6_K.gguf (~3.1GB)
- Backend: llama-cpp-python (CPU-optimized)
- Context: 2048 tokens
- Integration: CASCADE Oracle System compatible

Usage
-----
>>> from sarai_agi.agents.specialized import create_vision_agent
>>> from sarai_agi.model import get_model_pool
>>>
>>> pool = get_model_pool()
>>> agent = create_vision_agent(pool)
>>>
>>> # Analyze image
>>> result = agent.analyze_image("diagram.png", "Explain this diagram")
>>> print(result['text'])
>>>
>>> # OCR
>>> text = agent.extract_text_ocr("screenshot.png")
>>>
>>> # Diagram description
>>> desc = agent.describe_diagram("architecture.png")

Version: v3.5.1
Author: SARAi Project
"""

import base64
from pathlib import Path
from typing import Any, Dict, Union


class VisionAgent:
    """
    Vision agent using Qwen3-VL-4B-GGUF for efficient visual analysis.

    Loading Policy
    --------------
    - On-demand loading when input_type in ["image", "video"]
    - TTL: 60 seconds (auto-release for memory)
    - Auto-release if available RAM < 4GB
    - Integrated with ModelPool for efficient swapping

    Parameters
    ----------
    model_pool : ModelPool
        Instance of ModelPool for model lifecycle management

    Attributes
    ----------
    model_name : str
        Identifier for Qwen3-VL model in ModelPool
    model_pool : ModelPool
        Reference to the model pool instance

    Methods
    -------
    analyze_image(image_input, question, max_tokens)
        Analyze image and answer questions about it
    analyze_video(video_path, question, sample_fps, max_frames)
        Analyze video frame-by-frame (requires opencv)
    describe_diagram(image_path)
        Helper for technical diagram description
    extract_text_ocr(image_path)
        Helper for OCR text extraction

    Examples
    --------
    >>> agent = VisionAgent(model_pool)
    >>> result = agent.analyze_image(
    ...     "screenshot.png",
    ...     "What programming language is shown?"
    ... )
    >>> print(result['text'])
    'This is Python code...'
    """

    def __init__(self, model_pool):
        """
        Initialize Vision Agent.

        Parameters
        ----------
        model_pool : ModelPool
            Instance of ModelPool for model management
        """
        self.model_pool = model_pool
        self.model_name = "qwen3_vl"  # Updated to match config

    def analyze_image(
        self,
        image_input: Union[str, bytes],
        question: str = "¿Qué hay en esta imagen?",
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        """
        Analyze an image and answer questions about its content.

        Parameters
        ----------
        image_input : str or bytes
            Image path, raw bytes, or base64-encoded string
        question : str, optional
            Question to ask about the image (default: "¿Qué hay en esta imagen?")
        max_tokens : int, optional
            Maximum tokens in response (default: 512)

        Returns
        -------
        dict
            Analysis result with keys:
            - text (str): Textual response
            - confidence (float or None): Confidence score if available
            - metadata (dict): Additional info (model, question, tokens)

        Raises
        ------
        FileNotFoundError
            If image_input is a path and file doesn't exist
        RuntimeError
            If image analysis fails

        Examples
        --------
        >>> result = agent.analyze_image("diagram.png", "Explain this UML diagram")
        >>> print(result['text'])
        'This diagram shows a class hierarchy...'

        >>> # Using image bytes
        >>> with open("image.jpg", "rb") as f:
        ...     result = agent.analyze_image(f.read(), "Describe the scene")
        """
        # Load model (automatic memory management by ModelPool)
        print(f"[VisionAgent] Loading {self.model_name} for image analysis...")
        model = self.model_pool.get(self.model_name)

        # Prepare image
        if isinstance(image_input, str):
            # It's a file path
            image_path = Path(image_input)
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_input}")

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            # Encode to base64 for the model
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        elif isinstance(image_input, bytes):
            # Already bytes
            image_b64 = base64.b64encode(image_input).decode('utf-8')

        else:
            # Assume it's already base64
            image_b64 = image_input

        # Build multimodal prompt (Qwen-VL format)
        prompt = f"""<|im_start|>system
You are a helpful vision assistant that analyzes images accurately.<|im_end|>
<|im_start|>user
<img>{image_b64}</img>
{question}<|im_end|>
<|im_start|>assistant
"""

        # Generate response
        try:
            response = model.create_completion(
                prompt,
                max_tokens=max_tokens,
                temperature=0.4,  # Moderate for balance precision/creativity
                stop=["<|im_end|>", "<|endoftext|>"]
            )

            response_text = response["choices"][0]["text"].strip()

            # Auto-release if low RAM
            self._auto_release_if_low_ram()

            return {
                "text": response_text,
                "confidence": None,  # GGUF doesn't provide scores directly
                "metadata": {
                    "model": self.model_name,
                    "question": question,
                    "tokens_generated": len(response_text.split())
                }
            }

        except Exception as e:
            # Ensure release on error
            self.model_pool.release(self.model_name)
            raise RuntimeError(f"Image analysis error: {e}") from e

    def analyze_video(
        self,
        video_path: str,
        question: str = "Describe qué sucede en este video",
        sample_fps: int = 1,  # Frames per second to analyze
        max_frames: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze video frame-by-frame.

        Parameters
        ----------
        video_path : str
            Path to video file
        question : str, optional
            Question about the video (default: "Describe qué sucede en este video")
        sample_fps : int, optional
            Sampling FPS (1 = 1 frame/second, default: 1)
        max_frames : int, optional
            Maximum frames to analyze (default: 10)

        Returns
        -------
        dict
            Temporal video analysis

        Raises
        ------
        NotImplementedError
            Video analysis requires opencv-python (not yet implemented)

        Notes
        -----
        TODO: Implement frame extraction with opencv-python
        Install with: pip install opencv-python
        """
        # TODO: Implement frame extraction with opencv
        # For now, placeholder for interface
        raise NotImplementedError(
            "Video analysis requires opencv-python. "
            "Install with: pip install opencv-python"
        )

    def _auto_release_if_low_ram(self):
        """
        Auto-release model if available RAM < 4GB.

        Defensive policy to avoid OOM (Out Of Memory) conditions.
        Monitors system RAM and proactively releases the vision model
        if memory pressure is detected.

        Notes
        -----
        Uses psutil to check available memory.
        Threshold: 4GB free RAM (conservative for safety)
        """
        import psutil

        available_ram_gb = psutil.virtual_memory().available / (1024**3)

        if available_ram_gb < 4.0:
            print(f"[VisionAgent] Available RAM: {available_ram_gb:.1f}GB < 4GB. "
                  f"Releasing {self.model_name}...")
            self.model_pool.release(self.model_name)

    def describe_diagram(self, image_path: str) -> str:
        """
        Helper: Describe a technical diagram.

        Parameters
        ----------
        image_path : str
            Path to diagram image

        Returns
        -------
        str
            Textual description of diagram

        Examples
        --------
        >>> desc = agent.describe_diagram("architecture.png")
        >>> print(desc)
        'This diagram shows a microservices architecture with...'
        """
        result = self.analyze_image(
            image_path,
            question="Describe this technical diagram in detail. "
                     "Identify components, connections, and data flow."
        )
        return result["text"]

    def extract_text_ocr(self, image_path: str) -> str:
        """
        Helper: Extract text from image (OCR).

        Parameters
        ----------
        image_path : str
            Path to image with text

        Returns
        -------
        str
            Extracted text

        Examples
        --------
        >>> text = agent.extract_text_ocr("screenshot.png")
        >>> print(text)
        'def main():\n    print("Hello, world!")'
        """
        result = self.analyze_image(
            image_path,
            question="Extract all visible text from this image. "
                     "Preserve formatting and structure."
        )
        return result["text"]


def create_vision_agent(model_pool) -> VisionAgent:
    """
    Factory function to create a vision agent instance.

    Parameters
    ----------
    model_pool : ModelPool
        Instance of ModelPool for model management

    Returns
    -------
    VisionAgent
        Configured vision agent ready for use

    Examples
    --------
    >>> from sarai_agi.model import get_model_pool
    >>> from sarai_agi.agents.specialized import create_vision_agent
    >>>
    >>> pool = get_model_pool()
    >>> agent = create_vision_agent(pool)
    >>> result = agent.analyze_image("image.jpg", "What's in this image?")
    """
    return VisionAgent(model_pool)


# Exports
__all__ = ["VisionAgent", "create_vision_agent"]
