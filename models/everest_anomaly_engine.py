"""
Everest Anomaly Engine (L4 珠峰多源异常分析引擎).
Implements the 6 Core Operational Pillars:
1. Persistence (持续性时间演变)
2. Spatial Consistency (空间聚集度与地形相干)
3. Cross-Source Validation (多源交叉验证: S1 + S2 + DEM + Weather + Seismic)
4. Physics Constraint (DEM 物理门禁裁决)
5. Confidence (多模态置信度评分 0.0 - 1.0)
6. Uncertainty (不确定性指标与来源归因)

Adheres to: Detection != Warning (Anomaly -> Event Candidate -> Human Review -> Alert)
"""
from typing import Dict, List, Optional

class EverestAnomalyEngine:
    def __init__(self):
        pass

    def evaluate_multi_source_candidate(self,
                                        insar_state: Dict,
                                        optical_state: Dict,
                                        velocity_state: Dict,
                                        glof_state: Dict,
                                        avalanche_state: Dict,
                                        physics_state: Dict,
                                        weather_state: Dict,
                                        seismic_state: Dict) -> Dict:
        """
        全源加权聚合推理与状态机综合裁决
        """
        uncertainty_factors = []
        confidence_penalties = 0.0

        # 1. 检查物理门禁 (Physics Constraint Veto)
        if not physics_state.get("is_valid_candidate", True):
            return {
                "decision": "SUPPRESSED_PHYSICAL_VETO",
                "is_event_candidate": False,
                "confidence_score": 0.0,
                "uncertainty_score": 1.0,
                "veto_reason": physics_state.get("veto_reason"),
                "recommended_action": "ARCHIVE_AS_FALSE_POSITIVE"
            }

        # 2. 不确定性归因 (Uncertainty Attribution)
        coherence = insar_state.get("coherence_mean") or insar_state.get("bedrock_anchor", {}).get("coherence", 0.0)
        if coherence < 0.60:
            uncertainty_factors.append("LOW_INSAR_COHERENCE_NOISE")
            confidence_penalties += 0.20

        cloud_coverage = optical_state.get("cloud_gap_percent", 0.0)
        if cloud_coverage > 20.0:
            uncertainty_factors.append("OPTICAL_CLOUD_OCCLUSION")
            confidence_penalties += 0.15

        # 3. 持续性与空间一致性量化 (Persistence & Spatial Consistency)
        disp_mm = insar_state.get("median_mm") or 0.0   # 没有参考点时位移为 None，不作为证据
        is_accelerating = velocity_state.get("is_velocity_accelerating", False)
        is_crevasse = optical_state.get("is_crevasse_detected", False)
        
        persistence_score = 0.90 if is_accelerating else 0.40
        spatial_consistency = 0.95 if insar_state.get("evaluated_candidate_pixels", 0) > 5000 else 0.50

        # 4. 多源证据交叉加权 (Cross Validation)
        evidence_score = 0.0
        active_evidences = []

        if disp_mm > 0.0:
            evidence_score += min(0.35, (disp_mm / 5.0) * 0.35)
            active_evidences.append(f"InSAR LOS creep ({disp_mm} mm)")

        if is_accelerating:
            evidence_score += 0.30
            active_evidences.append(f"ITS_LIVE flow acceleration (Z={velocity_state.get('velocity_anomaly_z_score')})")

        if is_crevasse:
            evidence_score += 0.25
            active_evidences.append("Optical surface crevasse fracturing")

        if weather_state.get("is_heavy_rain_or_melt"):
            evidence_score += 0.15
            active_evidences.append("High freezing-level snowmelt driver")

        if seismic_state.get("nearby_earthquake_detected"):
            evidence_score += 0.20
            active_evidences.append("Seismic vibration ground motion trigger")

        overall_confidence = max(0.1, min(1.0, (1.0 - confidence_penalties) * (0.6 * persistence_score + 0.4 * spatial_consistency)))
        uncertainty_score = round(1.0 - overall_confidence, 2)
        
        # 5. 阶梯判定: Normal / Candidate / Alert
        is_candidate = (evidence_score >= 0.50) and (overall_confidence >= 0.70)
        
        if is_candidate:
            decision = "EVENT_CANDIDATE_REQUIRES_HUMAN_REVIEW"
            status = "PENDING_EXPERT_VERIFICATION"
        else:
            decision = "ROUTINE_BACKGROUND_MONITORING"
            status = "NORMAL_PHYSICAL_CREEP"

        return {
            "decision": decision,
            "status": status,
            "is_event_candidate": is_candidate,
            "overall_confidence": round(overall_confidence, 2),
            "uncertainty_score": uncertainty_score,
            "uncertainty_reasons": uncertainty_factors,
            "active_evidences": active_evidences,
            "persistence_index": round(persistence_score, 2),
            "spatial_consistency_index": round(spatial_consistency, 2),
            "evidence_score": round(evidence_score, 2),
            "human_verification_required": is_candidate,
            "alert_dispatched": False
        }