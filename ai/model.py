from __future__ import annotations

from typing import Dict, List


def predict_probabilities(features: List[List[float]], labels: List[int], current_features: List[float]) -> Dict[int, float]:
    if not features or not labels:
        raise ValueError("Липсват данни за обучение.")

    try:
        from sklearn.ensemble import RandomForestClassifier
    except Exception as e:
        raise RuntimeError(
            "Липсва зависимост scikit-learn. Инсталирайте с: pip install scikit-learn"
        ) from e

    # Multi-class: 0 home, 1 draw, 2 away
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(features, labels)

    probs = model.predict_proba([current_features])[0]
    class_probs = {int(cls): float(prob) for cls, prob in zip(model.classes_, probs)}
    return {
        0: class_probs.get(0, 0.0),
        1: class_probs.get(1, 0.0),
        2: class_probs.get(2, 0.0),
    }
