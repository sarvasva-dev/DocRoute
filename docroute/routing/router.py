"""Adaptive OCR Fallback Router."""
import logging
from typing import Tuple
from docroute.models.profile import PageProfile
from docroute.models.quality import QualityScore

logger = logging.getLogger(__name__)

class OCRRouter:
    """Evaluates page profile signals and native quality scores to decide extraction routing."""

    def __init__(self, default_threshold: float = 0.5):
        """Initializes router with quality threshold.
        
        Args:
            default_threshold: Minimum acceptable quality score (0.0 to 1.0)
        """
        self.default_threshold = default_threshold

    def decide_route(
        self, profile: PageProfile, native_quality: QualityScore, threshold: float = None
    ) -> Tuple[bool, str]:
        """Decides whether to accept native text or invoke OCR fallback.
        
        Args:
            profile: PageProfile for target page
            native_quality: QualityScore from native text assessment
            threshold: Custom threshold override if provided
            
        Returns:
            Tuple of (should_invoke_ocr: bool, decision_reasoning: str)
        """
        target_threshold = threshold if threshold is not None else self.default_threshold

        # Signal 1: Extremely low character count or density
        if profile.native_char_count < 15:
            reason = (
                f"OCR Fallback Triggered: Page contains only {profile.native_char_count} native characters. "
                f"High scan likelihood ({profile.scan_likelihood:.2f})."
            )
            logger.info(f"Page {profile.page_number} route decision: OCR ({reason})")
            return True, reason

        # Signal 2: High scan likelihood score from image area coverage
        if profile.scan_likelihood > 0.75 and native_quality.overall_score < 0.6:
            reason = (
                f"OCR Fallback Triggered: Page scan likelihood ({profile.scan_likelihood:.2f}) exceeds 0.75 "
                f"with native quality ({native_quality.overall_score:.2f}) < 0.60."
            )
            logger.info(f"Page {profile.page_number} route decision: OCR ({reason})")
            return True, reason

        # Signal 3: Quality score below defined threshold
        if native_quality.overall_score < target_threshold:
            reason = (
                f"OCR Fallback Triggered: Native text quality score ({native_quality.overall_score:.2f}) "
                f"is below configured threshold ({target_threshold:.2f}). "
                f"Garbage ratio = {native_quality.garbage_ratio:.2f}."
            )
            logger.info(f"Page {profile.page_number} route decision: OCR ({reason})")
            return True, reason

        # Accept Native route
        reason = (
            f"Native Text Accepted: Quality score ({native_quality.overall_score:.2f}) meets "
            f"threshold ({target_threshold:.2f}). Scan likelihood = {profile.scan_likelihood:.2f}."
        )
        logger.info(f"Page {profile.page_number} route decision: Native ({reason})")
        return False, reason
