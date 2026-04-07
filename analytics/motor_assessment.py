"""
AI-Based Analytics Engine for Motor and Cognitive Assessment
"""
import numpy as np
from typing import Dict, List, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from scipy import stats
import pandas as pd


class MotorFunctionAnalyzer:
    """Analyzes motor function from EMG and clinical test data"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def analyze_emg_data(self, emg_measurements: List[Dict]) -> Dict:
        """
        Analyze EMG measurements to assess muscle function and coordination
        
        Args:
            emg_measurements: List of EMG data points with muscle readings
        
        Returns:
            Dictionary with motor function metrics
        """
        if not emg_measurements:
            return {'error': 'No EMG data provided'}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(emg_measurements)
        
        results = {
            'muscle_coordination_score': 0.0,
            'muscle_strength_score': 0.0,
            'muscle_asymmetry': 0.0,
            'muscle_imbalance_detected': False,
            'detailed_analysis': {}
        }
        
        # Analyze muscle pairs (left vs right)
        left_muscles = df[df['side'] == 'LT']
        right_muscles = df[df['side'] == 'RT']
        
        if not left_muscles.empty and not right_muscles.empty:
            results['muscle_asymmetry'] = self._calculate_asymmetry(left_muscles, right_muscles)
            results['muscle_imbalance_detected'] = results['muscle_asymmetry'] > 20.0  # >20% asymmetry
        
        # Calculate muscle strength score based on mean EMG values
        if 'mean_value' in df.columns:
            avg_activation = df['mean_value'].mean()
            # Normalize to 0-100 scale (assuming max EMG value around 300)
            results['muscle_strength_score'] = min(100, (avg_activation / 300) * 100)
        
        # Calculate coordination score based on variability
        if 'mean_value' in df.columns and len(df) > 1:
            cv = stats.variation(df['mean_value'])  # Coefficient of variation
            # Lower variation = better coordination
            results['muscle_coordination_score'] = max(0, 100 - (cv * 50))
        
        # Detailed per-muscle analysis
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
    
    def analyze_clinical_tests(self, clinical_data: Dict) -> Dict:
        """
        Analyze clinical test results (6MWT, 10MWT, TUG)
        
        Args:
            clinical_data: Dictionary with clinical test values
        
        Returns:
            Dictionary with functional capacity scores
        """
        results = {
            'functional_capacity_score': 0.0,
            'endurance_score': 0.0,
            'mobility_score': 0.0
        }
        
        # 6MWT Analysis (6-Minute Walk Test)
        if 'distance_6mwt_meters' in clinical_data:
            distance = clinical_data['distance_6mwt_meters']
            # Normalize based on typical pediatric ranges (0-600m)
            results['endurance_score'] = min(100, (distance / 600) * 100)
        
        # 10MWT Analysis (10-Meter Walk Test)
        if 'time_10mwt_seconds' in clinical_data:
            time_10mwt = clinical_data['time_10mwt_seconds']
            # Lower time = better (assuming < 10s is excellent)
            if time_10mwt > 0:
                results['mobility_score'] = max(0, 100 - ((time_10mwt - 10) * 5))
        
        # TUG Analysis (Timed Up and Go)
        if 'tug_time_seconds' in clinical_data:
            tug_time = clinical_data['tug_time_seconds']
            # Lower time = better mobility and fall risk
            if tug_time > 0:
                tug_score = max(0, 100 - ((tug_time - 10) * 3))
                results['mobility_score'] = (results.get('mobility_score', 0) + tug_score) / 2
        
        # Overall functional capacity
        scores = [v for k, v in results.items() if k.endswith('_score') and v > 0]
        if scores:
            results['functional_capacity_score'] = sum(scores) / len(scores)
        
        return results


class BalanceAnalyzer:
    """Analyzes balance and stability data"""
    
    def analyze_balance_data(self, balance_metrics: Dict) -> Dict:
        """
        Analyze balance test metrics
        
        Args:
            balance_metrics: Dictionary with balance test values
        
        Returns:
            Dictionary with balance assessment scores
        """
        results = {
            'balance_score': 0.0,
            'stability_score': 0.0,
            'fall_risk_level': 'unknown',
            'postural_control_score': 0.0
        }
        
        # Stability analysis
        if 'total_stability_index' in balance_metrics:
            stability_index = balance_metrics['total_stability_index']
            # Lower index = better stability
            # Typical range: 0-10 (< 3 is good)
            results['stability_score'] = max(0, 100 - (stability_index / 10 * 100))
        
        # Time on balance
        if 'time_seconds' in balance_metrics:
            time_seconds = balance_metrics['time_seconds']
            # Longer time = better balance (30s is target)
            results['balance_score'] = min(100, (time_seconds / 30) * 100)
        
        # Fall risk assessment
        if 'total_stability_index' in balance_metrics:
            stability_index = balance_metrics['total_stability_index']
            if stability_index < 2:
                results['fall_risk_level'] = 'low'
            elif stability_index < 4:
                results['fall_risk_level'] = 'medium'
            else:
                results['fall_risk_level'] = 'high'
        
        # Postural control (trunk sway analysis)
        trunk_sway_keys = [k for k in balance_metrics.keys() if 'trunk_sway' in k]
        if trunk_sway_keys:
            trunk_sway_values = [abs(balance_metrics[k]) for k in trunk_sway_keys if balance_metrics[k] is not None]
            if trunk_sway_values:
                avg_sway = sum(trunk_sway_values) / len(trunk_sway_values)
                # Lower sway = better postural control
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
        Calculate comprehensive disability index
        
        Args:
            motor_analysis: Results from motor function analysis
            balance_analysis: Results from balance analysis
            clinical_analysis: Results from clinical tests analysis
            gmfcs_level: GMFCS classification level (1-5)
        
        Returns:
            Dictionary with disability quantification
        """
        # Weighted scoring
        weights = {
            'motor': 0.35,
            'balance': 0.30,
            'functional': 0.25,
            'clinical': 0.10
        }
        
        scores = []
        
        # Motor function component
        if motor_analysis.get('muscle_coordination_score'):
            scores.append(motor_analysis['muscle_coordination_score'] * weights['motor'])
        
        # Balance component
        if balance_analysis.get('balance_score'):
            scores.append(balance_analysis['balance_score'] * weights['balance'])
        
        # Functional capacity
        if clinical_analysis.get('functional_capacity_score'):
            scores.append(clinical_analysis['functional_capacity_score'] * weights['functional'])
        
        # GMFCS adjustment
        if gmfcs_level:
            # GMFCS Level 1 = mild, 5 = severe
            gmfcs_score = (6 - gmfcs_level) * 20  # Convert to 0-100 scale
            scores.append(gmfcs_score * weights['clinical'])
        
        # Calculate composite disability index (0-100, higher = less disabled)
        disability_index = sum(scores) if scores else 0
        
        # Invert to get disability severity (100 = most disabled)
        severity_index = 100 - disability_index
        
        # Classify severity
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
                'gmfcs_score': (6 - gmfcs_level) * 20 if gmfcs_level else None
            },
            'confidence_score': min(100, len(scores) / 4 * 100)  # Based on data completeness
        }


class CognitiveAssessor:
    """Assess cognitive function indicators from motor patterns"""
    
    def assess_cognitive_indicators(self, 
                                    emg_data: List[Dict],
                                    balance_data: Dict,
                                    clinical_data: Dict) -> Dict:
        """
        Assess cognitive function based on motor-cognitive correlations
        
        Args:
            emg_data: EMG measurements
            balance_data: Balance test results
            clinical_data: Clinical test data
        
        Returns:
            Dictionary with cognitive assessment scores
        """
        results = {
            'cognitive_function_score': 0.0,
            'attention_score': 0.0,
            'motor_planning_score': 0.0
        }
        
        # Attention can be inferred from balance consistency
        if 'total_stability_index' in balance_data:
            # Better balance control suggests better attention
            stability = balance_data['total_stability_index']
            results['attention_score'] = max(0, 100 - (stability / 5 * 100))
        
        # Motor planning from EMG coordination patterns
        if emg_data:
            df = pd.DataFrame(emg_data)
            if 'mean_value' in df.columns and len(df) > 1:
                # Consistent muscle activation patterns suggest good motor planning
                consistency = 100 - (df['mean_value'].std() / df['mean_value'].mean() * 100) \
                    if df['mean_value'].mean() > 0 else 0
                results['motor_planning_score'] = max(0, min(100, consistency))
        
        # Overall cognitive function score
        scores = [v for k, v in results.items() if k.endswith('_score') and v > 0]
        if scores:
            results['cognitive_function_score'] = sum(scores) / len(scores)
        
        return results
