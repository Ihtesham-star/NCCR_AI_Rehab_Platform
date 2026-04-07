"""
Rehabilitation Recommendation Engine
Generates personalized therapy protocols based on assessment results
"""
from typing import Dict, List, Optional
import json


class RehabRecommendationEngine:
    """Generate personalized rehabilitation recommendations"""
    
    def __init__(self):
        self.exercise_database = self._load_exercise_database()
        self.therapy_protocols = self._load_therapy_protocols()
    
    def generate_recommendations(self,
                                assessment: Dict,
                                motor_analysis: Dict,
                                balance_analysis: Dict,
                                gmfcs_level: Optional[int] = None) -> Dict:
        """
        Generate comprehensive rehabilitation recommendations
        
        Args:
            assessment: Overall disability assessment
            motor_analysis: Motor function analysis results
            balance_analysis: Balance analysis results
            gmfcs_level: GMFCS classification level
        
        Returns:
            Dictionary with rehabilitation protocol
        """
        recommendations = {
            'primary_focus': [],
            'therapy_types': [],
            'recommended_exercises': [],
            'target_muscles': [],
            'protocol_details': {},
            'expected_improvements': {},
            'monitoring_parameters': []
        }
        
        # Determine primary focus areas
        if balance_analysis.get('fall_risk_level') in ['medium', 'high']:
            recommendations['primary_focus'].append('balance')
        
        if motor_analysis.get('muscle_asymmetry', 0) > 20:
            recommendations['primary_focus'].append('symmetry')
        
        if motor_analysis.get('muscle_coordination_score', 100) < 60:
            recommendations['primary_focus'].append('coordination')
        
        if assessment.get('disability_severity') in ['severe', 'profound']:
            recommendations['primary_focus'].append('functional_mobility')
        
        # Select appropriate therapy types
        recommendations['therapy_types'] = self._select_therapy_types(
            assessment, gmfcs_level
        )
        
        # Generate exercise recommendations
        recommendations['recommended_exercises'] = self._select_exercises(
            recommendations['primary_focus'],
            motor_analysis,
            balance_analysis,
            gmfcs_level
        )
        
        # Identify target muscles for strengthening
        if motor_analysis.get('detailed_analysis'):
            weak_muscles = self._identify_weak_muscles(motor_analysis['detailed_analysis'])
            recommendations['target_muscles'] = weak_muscles
        
        # Create protocol details
        recommendations['protocol_details'] = self._create_protocol(
            assessment, gmfcs_level
        )
        
        # Define expected improvements
        recommendations['expected_improvements'] = self._define_expected_outcomes(
            recommendations['primary_focus'],
            assessment.get('disability_severity')
        )
        
        # Set monitoring parameters
        recommendations['monitoring_parameters'] = self._set_monitoring_parameters(
            recommendations['primary_focus']
        )
        
        return recommendations
    
    def _select_therapy_types(self, assessment: Dict, gmfcs_level: Optional[int]) -> List[str]:
        """Select appropriate therapy types"""
        therapies = ['physical_therapy']  # Always recommend PT
        
        severity = assessment.get('disability_severity')
        
        if severity in ['moderate', 'severe', 'profound']:
            therapies.append('occupational_therapy')
        
        if gmfcs_level and gmfcs_level >= 3:
            therapies.append('assistive_device_training')
        
        therapies.append('therapeutic_exercise')
        therapies.append('gait_training')
        
        return therapies
    
    def _select_exercises(self,
                         focus_areas: List[str],
                         motor_analysis: Dict,
                         balance_analysis: Dict,
                         gmfcs_level: Optional[int]) -> List[Dict]:
        """Select specific exercises based on needs"""
        exercises = []
        
        # Balance exercises
        if 'balance' in focus_areas:
            exercises.extend([
                {
                    'name': 'Single Leg Stance',
                    'description': 'Stand on one leg for increasing durations',
                    'duration': '30 seconds per leg',
                    'repetitions': 3,
                    'sets': 2,
                    'frequency': 'daily',
                    'progression': 'Increase hold time, add unstable surface'
                },
                {
                    'name': 'Weight Shifting',
                    'description': 'Shift weight from side to side while standing',
                    'duration': '2 minutes',
                    'repetitions': 10,
                    'sets': 2,
                    'frequency': '5 times per week'
                }
            ])
        
        # Coordination exercises
        if 'coordination' in focus_areas:
            exercises.extend([
                {
                    'name': 'Reciprocal Movements',
                    'description': 'Alternating arm and leg movements in coordinated patterns',
                    'duration': '5 minutes',
                    'repetitions': 15,
                    'sets': 3,
                    'frequency': 'daily'
                },
                {
                    'name': 'Proprioceptive Training',
                    'description': 'Balance exercises with eyes closed or on unstable surfaces',
                    'duration': '3 minutes',
                    'repetitions': 5,
                    'sets': 2,
                    'frequency': '4 times per week'
                }
            ])
        
        # Symmetry/asymmetry correction
        if 'symmetry' in focus_areas:
            exercises.extend([
                {
                    'name': 'Bilateral Strengthening',
                    'description': 'Focused strengthening of weaker side muscles',
                    'duration': '10 minutes',
                    'repetitions': 12,
                    'sets': 3,
                    'frequency': '3 times per week',
                    'notes': 'Focus on achieving equal muscle activation bilaterally'
                }
            ])
        
        # Functional mobility
        if 'functional_mobility' in focus_areas:
            exercises.extend([
                {
                    'name': 'Sit-to-Stand Training',
                    'description': 'Practice transitioning from sitting to standing position',
                    'repetitions': 10,
                    'sets': 3,
                    'frequency': 'daily'
                },
                {
                    'name': 'Gait Training',
                    'description': 'Walking practice with focus on proper form and endurance',
                    'duration': '10-15 minutes',
                    'frequency': 'daily',
                    'progression': 'Increase distance and speed gradually'
                }
            ])
        
        return exercises
    
    def _identify_weak_muscles(self, muscle_analysis: Dict) -> List[str]:
        """Identify muscles that need strengthening"""
        weak_muscles = []
        
        for muscle, metrics in muscle_analysis.items():
            if metrics.get('mean_activation', 0) < 50:  # Below 50% of typical activation
                weak_muscles.append(muscle)
        
        return weak_muscles
    
    def _create_protocol(self, assessment: Dict, gmfcs_level: Optional[int]) -> Dict:
        """Create detailed protocol parameters"""
        severity = assessment.get('disability_severity', 'moderate')
        
        # Base protocol
        protocol = {
            'frequency_per_week': 3,
            'session_duration_minutes': 45,
            'program_duration_weeks': 12,
            'intensity_level': 'medium'
        }
        
        # Adjust based on severity
        if severity == 'mild':
            protocol['frequency_per_week'] = 3
            protocol['intensity_level'] = 'medium-high'
            protocol['session_duration_minutes'] = 60
        elif severity == 'moderate':
            protocol['frequency_per_week'] = 4
            protocol['intensity_level'] = 'medium'
        elif severity in ['severe', 'profound']:
            protocol['frequency_per_week'] = 5
            protocol['intensity_level'] = 'low-medium'
            protocol['session_duration_minutes'] = 30
            protocol['program_duration_weeks'] = 16
        
        # Adjust for GMFCS level
        if gmfcs_level:
            if gmfcs_level >= 4:
                protocol['session_duration_minutes'] = min(protocol['session_duration_minutes'], 30)
                protocol['intensity_level'] = 'low'
        
        return protocol
    
    def _define_expected_outcomes(self, focus_areas: List[str], severity: str) -> Dict:
        """Define expected improvements"""
        outcomes = {}
        
        if 'balance' in focus_areas:
            outcomes['balance_improvement'] = {
                'metric': 'Stability index reduction',
                'target': '20-30% improvement',
                'timeframe': '8-12 weeks'
            }
        
        if 'coordination' in focus_areas:
            outcomes['coordination_improvement'] = {
                'metric': 'Muscle coordination score',
                'target': '15-25 point increase',
                'timeframe': '6-10 weeks'
            }
        
        if 'functional_mobility' in focus_areas:
            outcomes['mobility_improvement'] = {
                'metric': '6MWT distance',
                'target': '10-20% increase',
                'timeframe': '12 weeks'
            }
        
        return outcomes
    
    def _set_monitoring_parameters(self, focus_areas: List[str]) -> List[str]:
        """Set parameters to monitor during therapy"""
        parameters = [
            'Patient adherence to protocol',
            'Pain levels during exercises',
            'Fatigue levels'
        ]
        
        if 'balance' in focus_areas:
            parameters.extend([
                'Single leg stance time',
                'Stability index',
                'Fall incidents'
            ])
        
        if 'coordination' in focus_areas:
            parameters.extend([
                'EMG muscle activation patterns',
                'Movement quality assessment'
            ])
        
        if 'functional_mobility' in focus_areas:
            parameters.extend([
                '6MWT distance',
                '10MWT time',
                'TUG time'
            ])
        
        return parameters
    
    def _load_exercise_database(self) -> Dict:
        """Load exercise database (placeholder)"""
        return {}
    
    def _load_therapy_protocols(self) -> Dict:
        """Load therapy protocols (placeholder)"""
        return {}
