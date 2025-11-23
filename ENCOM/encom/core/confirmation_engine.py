"""
Confirmation Engine - Multi-layer confirmation logic
"""

from typing import List, Dict, Any
import pandas as pd
from encom.core.signal_registry import BaseSignal


class ConfirmationLayer:
    """
    Manages confirmation signals with AND/OR logic
    """

    def __init__(self, layer_id: int, required: bool = True):
        self.layer_id = layer_id
        self.required = required
        self.signals: List[BaseSignal] = []
        self.logic = "AND"  # AND or OR

    def add_signal(self, signal: BaseSignal):
        """Add a confirmation signal to this layer"""
        self.signals.append(signal)

    def evaluate(self, df: pd.DataFrame, current_idx: int) -> bool:
        """
        Evaluate all signals in this layer

        Returns:
            True if confirmation passes, False otherwise
        """
        if not self.signals:
            # No signals = pass through (don't block entry)
            return True

        results = [sig.evaluate(df, current_idx) for sig in self.signals]

        if self.logic == "AND":
            return all(results)
        else:  # OR
            return any(results)

    def get_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """Calculate weighted confirmation strength"""
        if not self.signals:
            return 0.0

        strengths = [sig.get_strength(df, current_idx) for sig in self.signals]
        return sum(strengths) / len(strengths)


class ConfirmationEngine:
    """
    Manages multiple confirmation layers
    """

    def __init__(self):
        self.layer1 = ConfirmationLayer(layer_id=1, required=True)
        self.layer2 = ConfirmationLayer(layer_id=2, required=False)

    def evaluate_all(self, df: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        Evaluate all confirmation layers

        Returns:
            Dict with layer results and overall confirmation status
        """
        layer1_pass = self.layer1.evaluate(df, current_idx)
        layer2_pass = self.layer2.evaluate(df, current_idx)

        layer1_strength = self.layer1.get_strength(df, current_idx)
        layer2_strength = self.layer2.get_strength(df, current_idx)

        # Overall confirmation: Layer 1 must pass
        confirmed = layer1_pass

        return {
            "layer1_pass": layer1_pass,
            "layer2_pass": layer2_pass,
            "layer1_strength": layer1_strength,
            "layer2_strength": layer2_strength,
            "confirmed": confirmed,
            "total_strength": (layer1_strength + layer2_strength) / 2
        }
