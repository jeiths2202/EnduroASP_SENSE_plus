#!/usr/bin/env python3
"""
BitNet B1.58 Service for Chat API
Handles BitNet model inference with fallback to mock responses
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class BitNetService:
    def __init__(self):
        self.bitnet_dir = Path("/home/aspuser/app/models/bitnet/BitNet")
        self.model_path = self.bitnet_dir / "models" / "BitNet-b1.58-2B-4T" / "ggml-model-i2_s.gguf"
        self.venv_path = self.bitnet_dir / ".venv"
        self.is_available = self._check_availability()
        
        logger.info(f"BitNet Service initialized - Available: {self.is_available}")
        
    def _check_availability(self) -> bool:
        """Check if BitNet is properly installed and configured"""
        try:
            # Check if BitNet directory exists
            if not self.bitnet_dir.exists():
                logger.warning(f"BitNet directory not found: {self.bitnet_dir}")
                return False
                
            # Check if model file exists
            if not self.model_path.exists():
                logger.warning(f"BitNet model not found: {self.model_path}")
                return False
                
            # Check if virtual environment exists
            if not self.venv_path.exists():
                logger.warning(f"BitNet venv not found: {self.venv_path}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking BitNet availability: {e}")
            return False
    
    def generate_response(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response using BitNet model"""
        if options is None:
            options = {}
            
        try:
            if not self.is_available:
                return self._mock_response(prompt)
                
            return self._call_bitnet(prompt, options)
            
        except Exception as e:
            logger.error(f"BitNet generation error: {e}")
            return self._mock_response(prompt, error=str(e))
    
    def _call_bitnet(self, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Call actual BitNet inference"""
        try:
            # Prepare BitNet inference command
            cmd = [
                str(self.venv_path / "bin" / "python"),
                str(self.bitnet_dir / "run_inference.py"),
                "-m", str(self.model_path),
                "-p", prompt,
                "-t", str(options.get("threads", 4)),
                "--temp", str(options.get("temperature", 0.7))
            ]
            
            if options.get("conversational", True):
                cmd.append("-cnv")
            
            # Set working directory to BitNet directory
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=str(self.bitnet_dir),
                capture_output=True,
                text=True,
                timeout=options.get("timeout", 30)
            )
            
            inference_time = time.time() - start_time
            
            if result.returncode == 0:
                response_text = result.stdout.strip()
                return {
                    "success": True,
                    "response": response_text,
                    "model": "BitNet B1.58 2B",
                    "inference_time": inference_time,
                    "tokens_per_second": self._estimate_tokens_per_second(response_text, inference_time)
                }
            else:
                logger.error(f"BitNet inference failed: {result.stderr}")
                return self._mock_response(prompt, error=result.stderr)
                
        except subprocess.TimeoutExpired:
            logger.error("BitNet inference timeout")
            return self._mock_response(prompt, error="Inference timeout")
            
        except Exception as e:
            logger.error(f"BitNet call error: {e}")
            return self._mock_response(prompt, error=str(e))
    
    def _mock_response(self, prompt: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Generate mock response when BitNet is not available"""
        mock_responses = [
            "I'm a lightweight BitNet B1.58 2B model. How can I help you with coding tasks?",
            "Here's a code example for your request:\n\n```python\n# Example implementation\nprint('Hello from BitNet!')\n```",
            "As a 2-bit quantized model, I'm optimized for efficient inference while maintaining good performance.",
            "I can help you with coding, debugging, and technical explanations. What would you like to work on?",
            "BitNet B1.58 offers excellent performance-to-efficiency ratio for coding tasks."
        ]
        
        # Simple hash-based selection for consistent responses
        response_index = hash(prompt.lower()) % len(mock_responses)
        response_text = mock_responses[response_index]
        
        # Add code block for coding-related prompts
        if any(keyword in prompt.lower() for keyword in ['code', 'function', 'class', 'implement', 'write']):
            response_text += "\n\n```javascript\n// Sample code implementation\nfunction example() {\n    return 'Generated by BitNet B1.58';\n}\n```"
        
        return {
            "success": not bool(error),
            "response": response_text,
            "model": "BitNet B1.58 2B (Mock)" if error else "BitNet B1.58 2B",
            "inference_time": 0.5,  # Mock timing
            "tokens_per_second": 20.0,  # Mock performance
            "mock": True,
            "error": error
        }
    
    def _estimate_tokens_per_second(self, text: str, inference_time: float) -> float:
        """Estimate tokens per second based on response length"""
        if inference_time <= 0:
            return 0.0
        
        # Rough estimation: ~4 characters per token
        estimated_tokens = len(text) / 4
        return estimated_tokens / inference_time
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get BitNet model information"""
        return {
            "name": "bitnet-b1.58:2b",
            "friendly_name": "BitNet B1.58 2B",
            "size": 2.0,  # Billions of parameters
            "quantization": "2-bit (i2_s)",
            "architecture": "BitNet",
            "available": self.is_available,
            "description": "Microsoft BitNet B1.58 2B model with 2-bit quantization for efficient inference",
            "capabilities": ["code_generation", "text_completion", "conversational"],
            "optimized_for": "coding_tasks"
        }
    
    def download_model(self) -> Dict[str, Any]:
        """Download BitNet model if not available"""
        try:
            if self.model_path.exists():
                return {"success": True, "message": "Model already exists"}
            
            # Create models directory
            models_dir = self.bitnet_dir / "models"
            models_dir.mkdir(exist_ok=True)
            
            # Download using huggingface-cli
            cmd = [
                str(self.venv_path / "bin" / "huggingface-cli"),
                "download",
                "microsoft/bitnet-b1.58-2B-4T-gguf",
                "--local-dir",
                str(self.bitnet_dir / "models" / "BitNet-b1.58-2B-4T")
            ]
            
            logger.info("Starting BitNet model download...")
            result = subprocess.run(
                cmd,
                cwd=str(self.bitnet_dir),
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                self.is_available = self._check_availability()
                return {
                    "success": True,
                    "message": "Model downloaded successfully",
                    "available": self.is_available
                }
            else:
                return {
                    "success": False,
                    "error": f"Download failed: {result.stderr}",
                    "available": False
                }
                
        except Exception as e:
            logger.error(f"Model download error: {e}")
            return {
                "success": False,
                "error": str(e),
                "available": False
            }

# Global BitNet service instance
bitnet_service = BitNetService()