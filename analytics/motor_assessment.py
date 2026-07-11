"""
AI-Based Analytics Engine for Motor and Cognitive Assessment
"""
import numpy as np
from typing import Dict, List, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from scipy import stats
import pandas as pd


# 6-Minute Walk Test reference bands by GMFCS level, children with spastic CP.
# Source: Nsenga Leunkeu A, et al. "Six-Minute Walk Test in Children With
# Spastic Cerebral Palsy and Children Developing Typically." Mean distance
# in meters: GMFCS I 439.57, GMFCS II 386.74, GMFCS III 305.28,
# typically developing 528.42. No published reference for GMFCS IV/V
# (largely non-ambulatory; test not typically administered at those levels).
SIX_MWT_REFERENCE_M = {
    1: 439.57,
    2: 386.74,
    3: 305.28,
    4: None,
    5: None,
    "typically_developing": 528.42,
}

# EMG bilateral asymmetry threshold. No pediatric-CP-specific EMG threshold
# was found in the literature; 10-15% is commonly cited as a clinically
# meaningful threshold in sports/biomechanics asymmetry research, which is
# the closest available evidence. Using the more conservative end of that range.
EMG_ASYMMETRY_THRESHOLD_PCT = 15.0

# Static balance hold-time ceiling. 30s is a long-standing convention in
# balance testing protocols; not a clinically validated pediatric cutoff.
BALANCE_HOLD_TARGET_SECONDS = 30.0


class MotorFunctionAnalyzer:
    """Analyzes motor function from EMG and clinical test data"""

    def __init__(self):
        self.scaler = StandardScaler()

    def analyze_emg_data(self, emg_measurements: List[Dict]) -> Dict:
        """
        Analyze EMG measurements to assess muscle function and coordination.

        muscle_strength_score uses a rough amplitude ceiling because raw
        (non-MVC-normalized) EMG amplitude is not standardizable across
        devices/protocols without normalizing to each patient's own maximum
        voluntary contraction (MVC), which this pipeline does not collect.
        """
        if not emg_measurements:
            return {'error': 'No EMG data provided'}

        df = pd.DataFrame(emg_measurements)

        results = {
            'muscle_coordination_score': 0.0,
            'muscle_strength_score': 0.0,
            'muscle_strength_score_caveat': (
                "Not MVC-normalized — not comparable across patients/devices."
            ),
            'muscle_asymmetry': 0.0,
            'muscle_imbalance_detected': False,
            'asymmetry_threshold_pct': EMG_ASYMMETRY_THRESHOLD_PCT,
            'detailed_analysis': {}
        }

        left_muscles = df[df['side'] == 'LT']
        right_muscles = df[df['side'] == 'RT']

        if not left_muscles.empty and not right_muscles.empty:
            results['muscle_asymmetry'] = self._calculate_asymmetry(left_muscles, right_muscles)
            results['muscle_imbalance_detected'] = results['muscle_asymmetry'] > EMG_ASYMMETRY_THRESHOLD_PCT

        if 'mean_value' in df.columns:
            avg_activation = df['mean_value'].mean()
            results['muscle_strength_score'] = min(100, (avg_activation / 300) * 100)

        if 'mean_value' in df.columns and len(df) > 1:
            cv = stats.variation(df['mean_value'])
            results['muscle_coordination_score'] = max(0, 100 - (cv * 50))

        for muscle in df['muscle_name'].unique():
            muscle_data = df[df['muscle_name'] == muscle]
            results['detailed_analysis'][muscle] = {
                'mean_activation': muscle_data['mean_value'].mean(),
                'max_activation': muscle_data['max_value'].max(),
                'consistency': 100 - (muscle_data['mean_value'].std() / muscle_data['mean_value'].mean() * 100)
                if muscle_data['mean_value'].mean() > 0 else 0
            }

        return results

    def _calculate_asymmetry(self, left_df: pd.DataFrame, right_df: pd.DataFrame) -> float:
        """Calculate asymmetry percentage between left and right sides"""
        left_mean = left_df['mean_value'].mean()
        right_mean = right_df['mean_value'].mean()

        if left_mean + right_mean == 0:
            return 0.0

        asymmetry = abs(left_mean - right_mean) / ((left_mean + right_mean) / 2) * 100
        return round(asymmetry, 2)

    def analyze_clinical_tests(self, clinical_data: Dict, gmfcs_level: Optional[int] = None) -> Dict:
        """
        Analyze clinical test results (6MWT, 10MWT, TUG).

        gmfcs_level is used to score the 6MWT against published GMFCS-level
        reference distances rather than a flat, unsourced ceiling. TUG and
        10MWT are reported as raw times only — no validated pediatric
        fall-risk cutoff exists for either in the literature (unlike
        adults, where a 13.5s TUG cutoff is established), so no synthetic
        0-100 score is fabricated for them.
        """
        results = {
            'functional_capacity_score': 0.0,
            'endurance_score': None,
            'six_mwt_raw_distance_m': clinical_data.get('distance_6mwt_meters'),
            'six_mwt_reference_used': None,
            'tug_raw_time_seconds': clinical_data.get('tug_time_seconds'),
        }

        if 'distance_6mwt_meters' in clinical_data:
            distance = clinical_data['distance_6mwt_meters']
            reference = SIX_MWT_REFERENCE_M.get(gmfcs_level) if gmfcs_level else None

            if reference:
                results['endurance_score'] = min(100, (distance / reference) * 100)
                results['six_mwt_reference_used'] = (
                    f"GMFCS level {gmfcs_level} published mean: {reference}m"
                )
            else:
                results['six_mwt_reference_used'] = (
                    "No published 6MWT reference for this GMFCS level "
                    "(or GMFCS not provided) — raw distance only, no score computed."
                )

        if 'time_10mwt_seconds' in clinical_data:
            results['ten_mwt_raw_time_seconds'] = clinical_data['time_10mwt_seconds']

        scores = [v for k, v in results.items() if k.endswith('_score') and v]
        if scores:
            results['functional_capacity_score'] = sum(scores) / len(scores)
        else:
            results['functional_capacity_score'] = None

        return results


class BalanceAnalyzer:
    """Analyzes balance and stability data"""

    def analyze_balance_data(self, balance_metrics: Dict) -> Dict:
        """
        Analyze balance test metrics.

        total_stability_index thresholds (the /10 normalization and the
        <2/<4 fall-risk cutoffs) could not be traced to public clinical
        literature — given this pipeline's equipment is TecnoBody, these
        are most likely manufacturer-specific reference values and should
        be verified against TecnoBody's documentation before clinical use.
        """
        results = {
            'balance_score': 0.0,
            'stability_score': 0.0,
            'fall_risk_level': 'unknown',
            'postural_control_score': 0.0,
        }

        if 'total_stability_index' in balance_metrics:
            stability_index = balance_metrics['total_stability_index']
            results['stability_score'] = max(0, 100 - (stability_index / 10 * 100))

        if 'time_seconds' in balance_metrics:
            time_seconds = balance_metrics['time_seconds']
            results['balance_score'] = min(100, (time_seconds / BALANCE_HOLD_TARGET_SECONDS) * 100)

        if 'total_stability_index' in balance_metrics:
            stability_index = balance_metrics['total_stability_index']
            if stability_index < 2:
                results['fall_risk_level'] = 'low'
            elif stability_index < 4:
                results['fall_risk_level'] = 'medium'
            else:
                results['fall_risk_level'] = 'high'

        trunk_sway_keys = [k for k in balance_metrics.keys() if 'trunk_sway' in k]
        if trunk_sway_keys:
            trunk_sway_values = [abs(balance_metrics[k]) for k in trunk_sway_keys if balance_metrics[k] is not None]
            if trunk_sway_values:
                avg_sway = sum(trunk_sway_values) / len(trunk_sway_values)
                results['postural_control_score'] = max(0, 100 - avg_sway)

        return results


class DisabilityQuantifier:
    """Quantifies disability severity based on comprehensive assessment"""

    def calculate_disability_index(self,
                                   motor_analysis: Dict,
                                   balance_analysis: Dict,
                                   clinical_analysis: Dict,
                                   gmfcs_level: Optional[int] = None) -> Dict:
        """
        Calculate comprehensive disability index.

        Component weights (0.35/0.30/0.25/0.10) are heuristic — no
        published composite index for this exact combination of measures
        was found; this is the clearest candidate for replacement with a
        supervised model trained on real outcome data.

        GMFCS is published as an ordinal scale (Palisano et al.) — the
        functional gap between adjacent levels is not equal. The linear
        conversion `(6 - level) * 20` below is a known simplification,
        not a validated conversion.
        """
        weights = {
            'motor': 0.35,
            'balance': 0.30,
            'functional': 0.25,
            'clinical': 0.10
        }

        scores = []

        if motor_analysis.get('muscle_coordination_score'):
            scores.append(motor_analysis['muscle_coordination_score'] * weights['motor'])

        if balance_analysis.get('balance_score'):
            scores.append(balance_analysis['balance_score'] * weights['balance'])

        if clinical_analysis.get('functional_capacity_score'):
            scores.append(clinical_analysis['functional_capacity_score'] * weights['functional'])

        gmfcs_score = None
        if gmfcs_level:
            gmfcs_score = (6 - gmfcs_level) * 20
            scores.append(gmfcs_score * weights['clinical'])

        disability_index = sum(scores) if scores else 0
        severity_index = 100 - disability_index

        if severity_index < 20:
            severity = 'mild'
        elif severity_index < 40:
            severity = 'moderate'
        elif severity_index < 70:
            severity = 'severe'
        else:
            severity = 'profound'

        return {
            'disability_index': round(disability_index, 2),
            'severity_index': round(severity_index, 2),
            'disability_severity': severity,
            'component_scores': {
                'motor_function': motor_analysis.get('muscle_coordination_score', 0),
                'balance': balance_analysis.get('balance_score', 0),
                'functional_capacity': clinical_analysis.get('functional_capacity_score', 0),
                'gmfcs_score': gmfcs_score
            },
            'confidence_score': min(100, len(scores) / 4 * 100),
        }


class CognitiveAssessor:
    """Assess cognitive function indicators from motor patterns"""

    def assess_cognitive_indicators(self,
                                    emg_data: List[Dict],
                                    balance_data: Dict,
                                    clinical_data: Dict) -> Dict:
        """
        Assess cognitive function based on motor-cognitive correlations.

        This inference approach (cognition from balance/EMG consistency)
        is a plausibility heuristic, not a validated clinical assessment
        methodology — the least evidence-grounded component of this module.
        """
        results = {
            'cognitive_function_score': 0.0,
            'attention_score': 0.0,
            'motor_planning_score': 0.0,
        }

        if 'total_stability_index' in balance_data:
            stability = balance_data['total_stability_index']
            results['attention_score'] = max(0, 100 - (stability / 5 * 100))

        if emg_data:
            df = pd.DataFrame(emg_data)
            if 'mean_value' in df.columns and len(df) > 1:
                consistency = 100 - (df['mean_value'].std() / df['mean_value'].mean() * 100) \
                    if df['mean_value'].mean() > 0 else 0
                results['motor_planning_score'] = max(0, min(100, consistency))

        scores = [v for k, v in results.items() if k.endswith('_score') and v > 0]
        if scores:
            results['cognitive_function_score'] = sum(scores) / len(scores)

        return results