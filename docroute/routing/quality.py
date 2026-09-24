"""Quality Assessment Engine for Document Text Layers."""
import re
import string
from typing import Dict, Any
from docroute.models.quality import QualityScore

class QualityAssessor:
    """Calculates objective text quality scores and garbage ratios for extracted content."""

    PRINTABLE_SET = set(string.printable)

    @classmethod
    def calculate_garbage_ratio(cls, text: str) -> float:
        """Calculates ratio of unprintable or unusual non-alphanumeric noise symbols."""
        if not text:
            return 1.0
        
        total_len = len(text)
        unusual_count = 0
        for char in text:
            # Characters outside standard ASCII/Unicode printable set or control chars
            if char not in cls.PRINTABLE_SET and not char.isalpha():
                unusual_count += 1

        return float(unusual_count) / float(total_len)

    @classmethod
    def calculate_printable_ratio(cls, text: str) -> float:
        """Calculates ratio of standard printable characters."""
        if not text:
            return 0.0
        printable_count = sum(1 for c in text if c in cls.PRINTABLE_SET)
        return float(printable_count) / float(len(text))

    @classmethod
    def calculate_word_quality(cls, text: str) -> float:
        """Evaluates proportion of coherent words (alphanumeric sequences >= 2 chars)."""
        words = text.split()
        if not words:
            return 0.0
        
        valid_words = 0
        for w in words:
            clean_w = re.sub(r"[^\w]", "", w)
            if len(clean_w) >= 2 and any(c.isalpha() for c in clean_w):
                valid_words += 1

        return float(valid_words) / float(len(words))

    @classmethod
    def assess_native_quality(
        cls, text: str, char_count: int, page_area_sq_pt: float, threshold: float = 0.5
    ) -> QualityScore:
        """Calculates composite quality score for a native text layer.
        
        Args:
            text: Extracted text string
            char_count: Native character count
            page_area_sq_pt: Page surface area in square points
            threshold: Applied quality threshold
            
        Returns:
            Structured QualityScore model
        """
        if not text or char_count < 10:
            return QualityScore(
                native_text_density=0.0,
                garbage_ratio=1.0,
                printable_char_ratio=0.0,
                dictionary_word_ratio=0.0,
                overall_score=0.0,
                threshold_applied=threshold,
                extraction_route="native",
                fallback_triggered=False,
                reasoning="Native text length < 10 chars. Document appears scanned or image-only."
            )

        density = (float(char_count) / (page_area_sq_pt / 1000.0)) if page_area_sq_pt > 0 else 0.0
        garbage_ratio = cls.calculate_garbage_ratio(text)
        printable_ratio = cls.calculate_printable_ratio(text)
        word_ratio = cls.calculate_word_quality(text)

        # Composite overall score formula (0.0 to 1.0)
        # Higher weight on word validity and low garbage ratio
        score = (0.4 * min(1.0, density / 2.0)) + (0.4 * word_ratio) + (0.2 * printable_ratio) - (0.5 * garbage_ratio)
        normalized_score = max(0.0, min(1.0, score))

        reasoning = (
            f"Native quality score {normalized_score:.2f} calculated from density={density:.2f}, "
            f"word_ratio={word_ratio:.2f}, garbage_ratio={garbage_ratio:.2f}."
        )

        return QualityScore(
            native_text_density=density,
            garbage_ratio=garbage_ratio,
            printable_char_ratio=printable_ratio,
            dictionary_word_ratio=word_ratio,
            overall_score=normalized_score,
            threshold_applied=threshold,
            extraction_route="native",
            fallback_triggered=False,
            reasoning=reasoning
        )
