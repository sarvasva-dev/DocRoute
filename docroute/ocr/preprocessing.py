"""OpenCV Image Preprocessing Pipeline for Document OCR."""
import logging
from typing import Tuple, Dict, Any
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Provides OpenCV image transformations to enhance text clarity for OCR engines."""

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """Converts BGR/RGB image to single-channel grayscale."""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    @staticmethod
    def binarize_otsu(gray_img: np.ndarray) -> np.ndarray:
        """Applies Otsu's automatic thresholding to produce binary image."""
        _, binary = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    @staticmethod
    def binarize_adaptive(gray_img: np.ndarray) -> np.ndarray:
        """Applies Gaussian adaptive thresholding for unevenly illuminated pages."""
        return cv2.adaptiveThreshold(
            gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

    @staticmethod
    def denoise(gray_img: np.ndarray) -> np.ndarray:
        """Applies Non-Local Means Denoising to reduce noise artifacts."""
        return cv2.fastNlMeansDenoising(gray_img, h=10)

    @classmethod
    def deskew(cls, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Detects document skew angle using minAreaRect on text contours and rotates back to 0 degrees.
        
        Returns:
            Tuple of (deskewed_image, detected_angle_degrees)
        """
        try:
            gray = cls.to_grayscale(image)
            # Invert image: text is white, background is black
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find non-zero pixel coordinates
            pts = cv2.findNonZero(binary)
            if pts is None or len(pts) == 0:
                return image, 0.0

            rect = cv2.minAreaRect(pts)
            angle = rect[-1]

            # Normalize angle to range [-45, 45]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle

            # If angle is negligible, return original
            if abs(angle) < 0.5:
                return image, 0.0

            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
            logger.info(f"Deskewed document by {angle:.2f} degrees")
            return rotated, float(angle)
        except Exception as e:
            logger.warning(f"Deskew operation failed: {e}")
            return image, 0.0

    @classmethod
    def preprocess_for_ocr(
        cls, image: np.ndarray, apply_deskew: bool = True, apply_denoise: bool = False
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Full document preprocessing pipeline.
        
        Args:
            image: Input image array (BGR or Gray)
            apply_deskew: Enable automatic deskew correction
            apply_denoise: Enable noise reduction filter
            
        Returns:
            Tuple of (preprocessed_image, pipeline_metadata)
        """
        metadata = {
            "original_shape": image.shape,
            "deskew_angle": 0.0,
            "denoised": False,
            "thresholding": "otsu"
        }

        processed = image.copy()
        if apply_deskew:
            processed, angle = cls.deskew(processed)
            metadata["deskew_angle"] = angle

        gray = cls.to_grayscale(processed)
        if apply_denoise:
            gray = cls.denoise(gray)
            metadata["denoised"] = True

        binary = cls.binarize_otsu(gray)
        metadata["final_shape"] = binary.shape
        return binary, metadata
