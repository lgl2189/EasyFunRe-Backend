import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class RecommendParam:
    alpha: float = 0.5
    wDiv: float = 0.0
    wBound: float = 0.0
    topN: int = 10

    def validate(self):
        self.alpha = max(0.0, min(1.0, self.alpha))
        self.wDiv = max(0.0, min(1.0, self.wDiv))
        self.wBound = max(0.0, min(1.0, self.wBound))


class HybridFusionService:
    """
    模块3：算法融合与用户可控模块
    """

    @staticmethod
    def _normalize(scores: Dict[int, float]) -> Dict[int, float]:
        if not scores:
            return {}
        minV = min(scores.values())
        maxV = max(scores.values())
        if maxV == minV:
            return {k: 0.5 for k in scores}
        return {k: (v - minV) / (maxV - minV + 1e-8) for k, v in scores.items()}

    @staticmethod
    def _cosineSimilarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def fuseAndRecommend(self,
                         params: RecommendParam,
                         cfScores: Dict[int, float],
                         contentScores: Dict[int, float],
                         postFeatures: Dict[int, np.ndarray]) -> List[Dict[str, Any]]:
        """核心融合接口"""
        params.validate()

        normCf = self._normalize(cfScores)
        normContent = self._normalize(contentScores)

        allCandidates = set(normCf.keys()) | set(normContent.keys())

        fusedScores = {}
        for vid in allCandidates:
            sCf = normCf.get(vid, 0.0)
            sCt = normContent.get(vid, 0.0)
            baseScore = params.alpha * sCf + (1.0 - params.alpha) * sCt
            explorationBonus = params.wBound * (1.0 - sCt) * 0.5
            fusedScores[vid] = baseScore + explorationBonus

        lambdaVal = 1.0 - params.wDiv
        candidates = list(fusedScores.items())
        selectedList = []

        while len(selectedList) < params.topN and candidates:
            bestMmr = -float('inf')
            bestVid = None
            bestHybridScore = 0.0

            for vid, hScore in candidates:
                penalty = 0.0
                if selectedList:
                    vecCurrent = postFeatures.get(vid, np.zeros(1))
                    penalty = max(
                        self._cosineSimilarity(vecCurrent,
                                               postFeatures.get(s.get('postId', s.get('post_id')), np.zeros(1)))
                        for s in selectedList
                    )

                mmrScore = lambdaVal * hScore - (1.0 - lambdaVal) * penalty

                if mmrScore > bestMmr:
                    bestMmr = mmrScore
                    bestVid = vid
                    bestHybridScore = hScore

            selectedList.append({
                "postId": bestVid,
                "finalScore": round(bestMmr, 4),
                "hybridScore": round(bestHybridScore, 4)
            })

            candidates = [c for c in candidates if c[0] != bestVid]

        return selectedList
