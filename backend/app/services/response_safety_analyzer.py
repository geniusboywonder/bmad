"""Response Safety Analyzer for advanced HITL safety controls."""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import re
import structlog
from decimal import Decimal
from datetime import datetime

from app.database.models import ResponseApprovalDB
from app.database.connection import get_session
from app.config import settings

logger = structlog.get_logger(__name__)


class SafetyAnalysisResult:
    """Result of safety analysis for agent responses."""

    def __init__(
        self,
        content_safety_score: float,
        code_validation_score: float,
        quality_metrics: Dict[str, Any],
        safety_flags: List[str],
        recommendations: List[str],
        auto_approvable: bool = False
    ):
        self.content_safety_score = content_safety_score
        self.code_validation_score = code_validation_score
        self.quality_metrics = quality_metrics
        self.safety_flags = safety_flags
        self.recommendations = recommendations
        self.auto_approvable = auto_approvable

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content_safety_score": self.content_safety_score,
            "code_validation_score": self.code_validation_score,
            "quality_metrics": self.quality_metrics,
            "safety_flags": self.safety_flags,
            "recommendations": self.recommendations,
            "auto_approvable": self.auto_approvable
        }


class ResponseSafetyAnalyzer:
    """Advanced analyzer for agent response safety and quality."""

    def __init__(self):
        self.safety_patterns = {
            'dangerous_commands': re.compile(
                r'\b(rm\s+-rf\s+/|sudo\s+rm\s+|format\s+|del\s+/|shutdown\s+|reboot\s+)',
                re.IGNORECASE
            ),
            'sensitive_data': re.compile(
                r'\b(password|secret|key|token|api_key|credential)\s*[:=]\s*[\w\d]+',
                re.IGNORECASE
            ),
            'malicious_urls': re.compile(
                r'https?://[^\s]*\.(exe|bat|cmd|scr|com|pif|jar|msi|deb|rpm)[^\s]*',
                re.IGNORECASE
            ),
            'sql_injection': re.compile(
                r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+.*?(FROM|INTO|TABLE)\s+.*?(WHERE|VALUES|SET)',
                re.IGNORECASE | re.DOTALL
            )
        }

        self.code_patterns = {
            'python_syntax': re.compile(r'^\s*(def|class|import|from)\s+\w+'),
            'javascript_syntax': re.compile(r'^\s*(function|const|let|var)\s+\w+'),
            'sql_syntax': re.compile(r'^\s*(SELECT|INSERT|UPDATE|DELETE)\s+', re.IGNORECASE),
            'shell_syntax': re.compile(r'^\s*[\w/]+\s+.*[|&;>]')
        }

    async def analyze_response(
        self,
        response_content: Dict[str, Any],
        agent_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> SafetyAnalysisResult:
        """Analyze agent response for safety and quality."""

        content_text = self._extract_text_content(response_content)
        content_safety_score = await self._analyze_content_safety(content_text)
        code_validation_score = await self._analyze_code_validation(content_text, agent_type)
        quality_metrics = await self._calculate_quality_metrics(content_text, response_content)

        safety_flags = self._identify_safety_flags(content_text)
        recommendations = self._generate_recommendations(safety_flags, quality_metrics)

        # Determine if response can be auto-approved
        auto_approvable = self._is_auto_approvable(
            content_safety_score,
            code_validation_score,
            safety_flags,
            quality_metrics
        )

        return SafetyAnalysisResult(
            content_safety_score=content_safety_score,
            code_validation_score=code_validation_score,
            quality_metrics=quality_metrics,
            safety_flags=safety_flags,
            recommendations=recommendations,
            auto_approvable=auto_approvable
        )

    def _extract_text_content(self, response_content: Dict[str, Any]) -> str:
        """Extract text content from response for analysis."""
        if isinstance(response_content, str):
            return response_content

        # Handle structured responses
        text_parts = []

        if 'output' in response_content:
            text_parts.append(str(response_content['output']))

        if 'artifacts' in response_content:
            for artifact in response_content['artifacts']:
                if isinstance(artifact, dict) and 'content' in artifact:
                    text_parts.append(str(artifact['content']))

        if 'message' in response_content:
            text_parts.append(str(response_content['message']))

        return ' '.join(text_parts)

    async def _analyze_content_safety(self, content: str) -> float:
        """Analyze content for safety concerns. Returns score 0.0-1.0 (1.0 = safe)."""
        if not content:
            return 1.0

        safety_score = 1.0
        penalties = []

        # Check for dangerous patterns
        for pattern_name, pattern in self.safety_patterns.items():
            matches = pattern.findall(content)
            if matches:
                penalty = min(len(matches) * 0.2, 0.5)  # Max penalty of 0.5 per pattern type
                safety_score -= penalty
                penalties.append(f"{pattern_name}: {len(matches)} matches")

        # Length-based safety (very short responses might be suspicious)
        if len(content.strip()) < 10:
            safety_score -= 0.1

        # Check for excessive special characters (might indicate obfuscation)
        special_chars = len(re.findall(r'[^\w\s]', content))
        if special_chars / len(content) > 0.3:
            safety_score -= 0.1

        logger.info("Content safety analysis completed",
                   safety_score=max(0.0, safety_score),
                   penalties=penalties)

        return max(0.0, safety_score)

    async def _analyze_code_validation(self, content: str, agent_type: str) -> float:
        """Analyze code quality and syntax validation. Returns score 0.0-1.0 (1.0 = valid)."""
        if not content:
            return 1.0

        validation_score = 1.0

        # Detect code language and validate syntax
        detected_languages = self._detect_code_languages(content)

        if detected_languages:
            for language in detected_languages:
                syntax_score = self._validate_syntax(content, language)
                validation_score = min(validation_score, syntax_score)

            # Bonus for multiple languages (shows versatility)
            if len(detected_languages) > 1:
                validation_score += 0.1
        else:
            # No code detected - neutral score
            validation_score = 0.8

        # Check for code quality indicators
        quality_indicators = self._assess_code_quality(content)
        validation_score *= quality_indicators

        logger.info("Code validation analysis completed",
                   validation_score=min(1.0, max(0.0, validation_score)),
                   detected_languages=detected_languages)

        return min(1.0, max(0.0, validation_score))

    def _detect_code_languages(self, content: str) -> List[str]:
        """Detect programming languages in content."""
        detected = []

        for lang, pattern in self.code_patterns.items():
            if pattern.search(content):
                detected.append(lang)

        return detected

    def _validate_syntax(self, content: str, language: str) -> float:
        """Validate syntax for a specific language. Returns score 0.0-1.0."""
        # Basic syntax validation - in production, this would use actual parsers
        if language == 'python_syntax':
            return self._validate_python_syntax(content)
        elif language == 'javascript_syntax':
            return self._validate_javascript_syntax(content)
        elif language == 'sql_syntax':
            return self._validate_sql_syntax(content)
        elif language == 'shell_syntax':
            return self._validate_shell_syntax(content)

        return 0.7  # Neutral score for unknown languages

    def _validate_python_syntax(self, content: str) -> float:
        """Basic Python syntax validation."""
        try:
            # Check for common Python patterns
            if 'import' in content and not re.search(r'import\s+\w+', content):
                return 0.3
            if 'def' in content and not re.search(r'def\s+\w+\s*\(', content):
                return 0.4
            if 'class' in content and not re.search(r'class\s+\w+', content):
                return 0.4
            return 0.9
        except:
            return 0.2

    def _validate_javascript_syntax(self, content: str) -> float:
        """Basic JavaScript syntax validation."""
        try:
            # Check for common JS patterns
            if 'function' in content and not re.search(r'function\s+\w+\s*\(', content):
                return 0.4
            if ('const' in content or 'let' in content) and not re.search(r'(const|let)\s+\w+', content):
                return 0.4
            return 0.9
        except:
            return 0.2

    def _validate_sql_syntax(self, content: str) -> float:
        """Basic SQL syntax validation."""
        try:
            # Check for basic SQL structure
            if not re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', content, re.IGNORECASE):
                return 0.3
            if 'SELECT' in content.upper() and 'FROM' not in content.upper():
                return 0.5
            return 0.8
        except:
            return 0.2

    def _validate_shell_syntax(self, content: str) -> float:
        """Basic shell syntax validation."""
        try:
            # Check for dangerous shell patterns
            if 'rm -rf' in content or 'sudo' in content:
                return 0.3
            return 0.8
        except:
            return 0.2

    def _assess_code_quality(self, content: str) -> float:
        """Assess overall code quality indicators."""
        quality_score = 1.0

        # Check for comments (good practice)
        comment_lines = len(re.findall(r'^\s*#|^\s*//|^\s*/\*', content, re.MULTILINE))
        total_lines = len(content.split('\n'))
        if total_lines > 0 and comment_lines / total_lines < 0.1:
            quality_score -= 0.1

        # Check for error handling
        if 'try:' not in content and 'except' not in content:
            quality_score -= 0.1

        # Check for reasonable length (not too long)
        if len(content) > 10000:
            quality_score -= 0.1

        return max(0.3, quality_score)

    async def _calculate_quality_metrics(self, content: str, response_content: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics."""
        metrics = {
            'length': len(content),
            'word_count': len(content.split()),
            'line_count': len(content.split('\n')),
            'has_code': bool(self._detect_code_languages(content)),
            'readability_score': self._calculate_readability(content),
            'structure_score': self._assess_structure(response_content),
            'completeness_score': self._assess_completeness(response_content)
        }

        return metrics

    def _calculate_readability(self, content: str) -> float:
        """Calculate basic readability score."""
        if not content:
            return 0.0

        # Simple readability based on sentence structure and length
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0

        # Optimal readability: 10-20 words per sentence
        if 10 <= avg_words_per_sentence <= 20:
            return 1.0
        elif 5 <= avg_words_per_sentence <= 25:
            return 0.8
        else:
            return 0.5

    def _assess_structure(self, response_content: Dict[str, Any]) -> float:
        """Assess response structure quality."""
        structure_score = 0.5

        # Check for expected fields
        expected_fields = ['status', 'output', 'artifacts', 'confidence']
        present_fields = [field for field in expected_fields if field in response_content]
        structure_score += (len(present_fields) / len(expected_fields)) * 0.5

        return min(1.0, structure_score)

    def _assess_completeness(self, response_content: Dict[str, Any]) -> float:
        """Assess response completeness."""
        completeness_score = 0.5

        # Check for required completion indicators
        if response_content.get('status') == 'completed':
            completeness_score += 0.3

        if 'output' in response_content and response_content['output']:
            completeness_score += 0.2

        if 'artifacts' in response_content and response_content['artifacts']:
            completeness_score += 0.2

        return min(1.0, completeness_score)

    def _identify_safety_flags(self, content: str) -> List[str]:
        """Identify specific safety concerns."""
        flags = []

        for pattern_name, pattern in self.safety_patterns.items():
            if pattern.search(content):
                flags.append(f"Pattern detected: {pattern_name}")

        if len(content.strip()) < 5:
            flags.append("Response too short")

        if len(content) > 50000:
            flags.append("Response too long")

        return flags

    def _generate_recommendations(self, safety_flags: List[str], quality_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if safety_flags:
            recommendations.append("Review response for safety concerns before approval")

        if quality_metrics.get('readability_score', 1.0) < 0.7:
            recommendations.append("Consider improving response readability")

        if not quality_metrics.get('has_code', False) and quality_metrics.get('length', 0) < 100:
            recommendations.append("Response may be too brief for the task")

        if quality_metrics.get('completeness_score', 1.0) < 0.7:
            recommendations.append("Response appears incomplete")

        return recommendations

    def _is_auto_approvable(self, safety_score: float, code_score: float,
                           safety_flags: List[str], quality_metrics: Dict[str, Any]) -> bool:
        """Determine if response can be auto-approved."""
        # Auto-approval criteria
        min_safety_score = 0.8
        min_code_score = 0.7
        max_safety_flags = 0

        return (
            safety_score >= min_safety_score and
            code_score >= min_code_score and
            len(safety_flags) <= max_safety_flags and
            quality_metrics.get('completeness_score', 0) >= 0.7
        )

    async def create_response_approval_record(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        approval_request_id: UUID,
        response_content: Dict[str, Any],
        analysis_result: SafetyAnalysisResult
    ) -> UUID:
        """Create a response approval record in the database."""

        approval_record = ResponseApprovalDB(
            project_id=project_id,
            task_id=task_id,
            agent_type=agent_type,
            approval_request_id=approval_request_id,
            response_content=response_content,
            response_metadata=analysis_result.quality_metrics,
            content_safety_score=Decimal(str(analysis_result.content_safety_score)),
            code_validation_score=Decimal(str(analysis_result.code_validation_score)),
            quality_metrics=analysis_result.quality_metrics,
            status="AUTO_APPROVED" if analysis_result.auto_approvable else "PENDING",
            auto_approved=analysis_result.auto_approvable,
            approval_reason="Auto-approved based on safety analysis" if analysis_result.auto_approvable else None
        )

        db = next(get_session())
        try:
            db.add(approval_record)
            db.commit()
            db.refresh(approval_record)

            logger.info("Response approval record created",
                       record_id=str(approval_record.id),
                       auto_approved=analysis_result.auto_approvable,
                       safety_score=analysis_result.content_safety_score)

            return approval_record.id

        finally:
            db.close()

    async def get_response_approval_analysis(self, approval_id: UUID) -> Optional[Dict[str, Any]]:
        """Get analysis results for a response approval."""

        db = next(get_session())
        try:
            approval = db.query(ResponseApprovalDB).filter(
                ResponseApprovalDB.id == approval_id
            ).first()

            if not approval:
                return None

            return {
                "approval_id": str(approval.id),
                "content_safety_score": float(approval.content_safety_score) if approval.content_safety_score else None,
                "code_validation_score": float(approval.code_validation_score) if approval.code_validation_score else None,
                "quality_metrics": approval.quality_metrics,
                "status": approval.status,
                "auto_approved": approval.auto_approved,
                "approved_by": approval.approved_by,
                "approval_reason": approval.approval_reason,
                "created_at": approval.created_at.isoformat(),
                "approved_at": approval.approved_at.isoformat() if approval.approved_at else None
            }

        finally:
            db.close()
