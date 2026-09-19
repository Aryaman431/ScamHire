from typing import Dict, Any
from app.ai.schemas import JobExtraction
from .rules import get_signal_score, RiskLevel, get_risk_level


class RiskEngine:
    @staticmethod
    def calculate_risk(extraction: JobExtraction) -> Dict[str, Any]:
        """
        Calculates the final deterministic risk score and confidence.
        """
        base_score = 0
        signal_details = []
        seen_signals = set()

        # 1. Evaluate Suspicious Signals from AI
        for signal in extraction.suspicious_signals:
            signal_type = getattr(signal.signal_type, "value", signal.signal_type)
            signal_identity = (signal_type, signal.evidence.strip())
            if signal_identity in seen_signals:
                continue
            seen_signals.add(signal_identity)

            score = get_signal_score(signal_type)
            base_score += score

            signal_details.append({
                "signal_type": signal_type,
                "score_contribution": score,
                "evidence": signal.evidence,
                "reasoning": signal.reasoning,
                "confidence": signal.confidence,
            })

        # 2. Clamp score between 0 and 100
        final_score = max(0, min(100, base_score))

        # 3. Determine Risk Level
        risk_level = get_risk_level(final_score)

        # 4. Calculate deterministic confidence
        confidence_penalties = 0
        if extraction.missing_information:
            confidence_penalties += len(extraction.missing_information) * 5

        for signal in extraction.suspicious_signals:
            if signal.confidence < 80:
                confidence_penalties += 5

        final_confidence = max(0, min(100, 100 - confidence_penalties))

        return {
            "risk_score": final_score,
            "risk_level": risk_level.value if isinstance(risk_level, RiskLevel) else risk_level,
            "confidence": final_confidence,
            "signal_details": signal_details,
        }
