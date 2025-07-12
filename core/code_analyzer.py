#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Code Analyzer
محلل الأكواد المتقدم
"""

import ast
import re
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class IssueType(Enum):
    """أنواع المشاكل في الكود"""
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    STYLE_ISSUE = "style_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_ISSUE = "security_issue"
    BEST_PRACTICE = "best_practice"
    UNUSED_CODE = "unused_code"
    COMPLEXITY_ISSUE = "complexity_issue"

class Severity(Enum):
    """مستويات الخطورة"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class CodeIssue:
    """مشكلة في الكود"""
    type: IssueType
    severity: Severity
    line_number: int
    column: int
    message: str
    description: str
    suggestion: str
    code_snippet: str
    fix_suggestion: Optional[str] = None

@dataclass
class CodeMetrics:
    """مقاييس الكود"""
    lines_of_code: int
    lines_of_comments: int
    blank_lines: int
    cyclomatic_complexity: int
    functions_count: int
    classes_count: int
    imports_count: int
    code_duplication: float
    maintainability_index: float

class PythonAnalyzer:
    """محلل أكواد Python"""
    
    def __init__(self):
        self.issues = []
        self.metrics = None
        
    def analyze(self, code: str, file_path: str = None) -> Tuple[List[CodeIssue], CodeMetrics]:
        """تحليل كود Python"""
        self.issues = []
        
        try:
            # تحليل نحوي
            tree = ast.parse(code)
            
            # تحليل المشاكل
            self._analyze_syntax(code)
            self._analyze_style(code, tree)
            self._analyze_complexity(tree)
            self._analyze_best_practices(code, tree)
            self._analyze_security(code, tree)
            self._analyze_performance(code, tree)
            
            # حساب المقاييس
            self.metrics = self._calculate_metrics(code, tree)
            
        except SyntaxError as e:
            self.issues.append(CodeIssue(
                type=IssueType.SYNTAX_ERROR,
                severity=Severity.CRITICAL,
                line_number=e.lineno or 1,
                column=e.offset or 0,
                message="خطأ نحوي",
                description=str(e),
                suggestion="تحقق من صحة النحو",
                code_snippet=self._get_line(code, e.lineno or 1),
                fix_suggestion=self._suggest_syntax_fix(e)
            ))
            
            # مقاييس أساسية للكود مع أخطاء نحوية
            self.metrics = self._calculate_basic_metrics(code)
        
        return self.issues, self.metrics
    
    def _analyze_syntax(self, code: str):
        """تحليل الأخطاء النحوية"""
        lines = code.split('\\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # فحص الأقواس غير المتوازنة
            if self._check_unbalanced_brackets(line):
                self.issues.append(CodeIssue(
                    type=IssueType.SYNTAX_ERROR,
                    severity=Severity.HIGH,
                    line_number=i,
                    column=0,
                    message="أقواس غير متوازنة",
                    description="الأقواس غير متطابقة في هذا السطر",
                    suggestion="تأكد من إغلاق جميع الأقواس",
                    code_snippet=line
                ))
            
            # فحص المسافات البادئة
            if line and not line.startswith(' ') and not line.startswith('\\t'):
                if i > 1 and lines[i-2].rstrip().endswith(':'):
                    self.issues.append(CodeIssue(
                        type=IssueType.SYNTAX_ERROR,
                        severity=Severity.HIGH,
                        line_number=i,
                        column=0,
                        message="مسافة بادئة مفقودة",
                        description="يجب إضافة مسافة بادئة بعد ':'",
                        suggestion="أضف 4 مسافات في بداية السطر",
                        code_snippet=line
                    ))
    
    def _analyze_style(self, code: str, tree: ast.AST):
        """تحليل أسلوب الكود (PEP 8)"""
        lines = code.split('\\n')
        
        for i, line in enumerate(lines, 1):
            # فحص طول السطر
            if len(line) > 79:
                self.issues.append(CodeIssue(
                    type=IssueType.STYLE_ISSUE,
                    severity=Severity.LOW,
                    line_number=i,
                    column=79,
                    message="السطر طويل جداً",
                    description=f"السطر يحتوي على {len(line)} حرف (الحد الأقصى 79)",
                    suggestion="قسم السطر إلى عدة أسطر",
                    code_snippet=line
                ))
            
            # فحص المسافات الزائدة
            if line.endswith(' ') or line.endswith('\\t'):
                self.issues.append(CodeIssue(
                    type=IssueType.STYLE_ISSUE,
                    severity=Severity.LOW,
                    line_number=i,
                    column=len(line.rstrip()),
                    message="مسافات زائدة في نهاية السطر",
                    description="يوجد مسافات غير ضرورية في نهاية السطر",
                    suggestion="احذف المسافات الزائدة",
                    code_snippet=line
                ))
            
            # فحص استخدام التبويب والمسافات
            if '\\t' in line and ' ' in line[:len(line) - len(line.lstrip())]:
                self.issues.append(CodeIssue(
                    type=IssueType.STYLE_ISSUE,
                    severity=Severity.MEDIUM,
                    line_number=i,
                    column=0,
                    message="خلط بين التبويب والمسافات",
                    description="لا تخلط بين التبويب والمسافات للمسافة البادئة",
                    suggestion="استخدم 4 مسافات فقط للمسافة البادئة",
                    code_snippet=line
                ))
        
        # فحص أسماء المتغيرات والدوال
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not self._is_snake_case(node.name):
                    self.issues.append(CodeIssue(
                        type=IssueType.STYLE_ISSUE,
                        severity=Severity.LOW,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="اسم دالة غير متوافق مع PEP 8",
                        description=f"اسم الدالة '{node.name}' يجب أن يكون بصيغة snake_case",
                        suggestion=f"غير الاسم إلى '{self._to_snake_case(node.name)}'",
                        code_snippet=f"def {node.name}("
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if not self._is_pascal_case(node.name):
                    self.issues.append(CodeIssue(
                        type=IssueType.STYLE_ISSUE,
                        severity=Severity.LOW,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="اسم كلاس غير متوافق مع PEP 8",
                        description=f"اسم الكلاس '{node.name}' يجب أن يكون بصيغة PascalCase",
                        suggestion=f"غير الاسم إلى '{self._to_pascal_case(node.name)}'",
                        code_snippet=f"class {node.name}:"
                    ))
    
    def _analyze_complexity(self, tree: ast.AST):
        """تحليل تعقيد الكود"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                
                if complexity > 10:
                    severity = Severity.HIGH if complexity > 15 else Severity.MEDIUM
                    self.issues.append(CodeIssue(
                        type=IssueType.COMPLEXITY_ISSUE,
                        severity=severity,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="تعقيد دوري عالي",
                        description=f"الدالة '{node.name}' لها تعقيد دوري = {complexity}",
                        suggestion="قسم الدالة إلى دوال أصغر",
                        code_snippet=f"def {node.name}("
                    ))
                
                # فحص عدد المعاملات
                args_count = len(node.args.args)
                if args_count > 5:
                    self.issues.append(CodeIssue(
                        type=IssueType.COMPLEXITY_ISSUE,
                        severity=Severity.MEDIUM,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="عدد كبير من المعاملات",
                        description=f"الدالة '{node.name}' لها {args_count} معاملات",
                        suggestion="استخدم كائن أو قاموس لتجميع المعاملات",
                        code_snippet=f"def {node.name}("
                    ))
    
    def _analyze_best_practices(self, code: str, tree: ast.AST):
        """تحليل أفضل الممارسات"""
        # فحص استخدام global
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                self.issues.append(CodeIssue(
                    type=IssueType.BEST_PRACTICE,
                    severity=Severity.MEDIUM,
                    line_number=node.lineno,
                    column=node.col_offset,
                    message="استخدام global",
                    description="تجنب استخدام المتغيرات العامة",
                    suggestion="مرر المتغيرات كمعاملات أو استخدم كلاس",
                    code_snippet=f"global {', '.join(node.names)}"
                ))
            
            # فحص استخدام except عام
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues.append(CodeIssue(
                        type=IssueType.BEST_PRACTICE,
                        severity=Severity.MEDIUM,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="except عام",
                        description="تجنب استخدام except بدون تحديد نوع الاستثناء",
                        suggestion="حدد نوع الاستثناء المتوقع",
                        code_snippet="except:"
                    ))
            
            # فحص استخدام print في الكود
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    self.issues.append(CodeIssue(
                        type=IssueType.BEST_PRACTICE,
                        severity=Severity.LOW,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="استخدام print",
                        description="استخدم logging بدلاً من print",
                        suggestion="استبدل print بـ logging",
                        code_snippet="print("
                    ))
    
    def _analyze_security(self, code: str, tree: ast.AST):
        """تحليل الأمان"""
        # فحص استخدام eval
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                    self.issues.append(CodeIssue(
                        type=IssueType.SECURITY_ISSUE,
                        severity=Severity.CRITICAL,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message=f"استخدام {node.func.id} خطير",
                        description=f"استخدام {node.func.id} يمكن أن يؤدي إلى تنفيذ كود ضار",
                        suggestion="استخدم بدائل آمنة أو تحقق من المدخلات",
                        code_snippet=f"{node.func.id}("
                    ))
        
        # فحص كلمات المرور في الكود
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', code, re.IGNORECASE):
            lines = code.split('\\n')
            for i, line in enumerate(lines, 1):
                if re.search(r'password\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                    self.issues.append(CodeIssue(
                        type=IssueType.SECURITY_ISSUE,
                        severity=Severity.HIGH,
                        line_number=i,
                        column=0,
                        message="كلمة مرور مكشوفة",
                        description="لا تضع كلمات المرور في الكود",
                        suggestion="استخدم متغيرات البيئة أو ملفات التكوين",
                        code_snippet=line.strip()
                    ))
    
    def _analyze_performance(self, code: str, tree: ast.AST):
        """تحليل الأداء"""
        for node in ast.walk(tree):
            # فحص الحلقات المتداخلة
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = self._count_nested_loops(node)
                if nested_loops > 2:
                    self.issues.append(CodeIssue(
                        type=IssueType.PERFORMANCE_ISSUE,
                        severity=Severity.MEDIUM,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="حلقات متداخلة كثيرة",
                        description=f"عمق التداخل: {nested_loops}",
                        suggestion="فكر في خوارزمية أكثر كفاءة",
                        code_snippet="for/while loop"
                    ))
            
            # فحص استخدام + لربط النصوص في الحلقات
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.op, ast.Add) and self._is_in_loop(node, tree):
                    self.issues.append(CodeIssue(
                        type=IssueType.PERFORMANCE_ISSUE,
                        severity=Severity.LOW,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="ربط النصوص في حلقة",
                        description="استخدام += للنصوص في الحلقات بطيء",
                        suggestion="استخدم join() أو قائمة",
                        code_snippet="+="
                    ))
    
    def _calculate_metrics(self, code: str, tree: ast.AST) -> CodeMetrics:
        """حساب مقاييس الكود"""
        lines = code.split('\\n')
        
        # عد الأسطر
        lines_of_code = 0
        lines_of_comments = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                lines_of_comments += 1
            else:
                lines_of_code += 1
                # فحص التعليقات في نفس السطر
                if '#' in line:
                    lines_of_comments += 1
        
        # عد العناصر
        functions_count = 0
        classes_count = 0
        imports_count = 0
        total_complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions_count += 1
                total_complexity += self._calculate_cyclomatic_complexity(node)
            elif isinstance(node, ast.ClassDef):
                classes_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports_count += 1
        
        # حساب التعقيد الدوري المتوسط
        avg_complexity = total_complexity / max(functions_count, 1)
        
        # حساب مؤشر القابلية للصيانة (مبسط)
        maintainability_index = max(0, 171 - 5.2 * avg_complexity - 0.23 * avg_complexity - 16.2 * (lines_of_code / max(functions_count, 1)))
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            blank_lines=blank_lines,
            cyclomatic_complexity=int(avg_complexity),
            functions_count=functions_count,
            classes_count=classes_count,
            imports_count=imports_count,
            code_duplication=0.0,  # يحتاج تحليل أكثر تعقيداً
            maintainability_index=maintainability_index
        )
    
    def _calculate_basic_metrics(self, code: str) -> CodeMetrics:
        """حساب مقاييس أساسية للكود مع أخطاء"""
        lines = code.split('\\n')
        
        lines_of_code = 0
        lines_of_comments = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                lines_of_comments += 1
            else:
                lines_of_code += 1
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            blank_lines=blank_lines,
            cyclomatic_complexity=0,
            functions_count=0,
            classes_count=0,
            imports_count=0,
            code_duplication=0.0,
            maintainability_index=0.0
        )
    
    # دوال مساعدة
    def _check_unbalanced_brackets(self, line: str) -> bool:
        """فحص الأقواس غير المتوازنة"""
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in line:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    return True
                if brackets[stack.pop()] != char:
                    return True
        
        return len(stack) > 0
    
    def _is_snake_case(self, name: str) -> bool:
        """فحص إذا كان الاسم بصيغة snake_case"""
        return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None
    
    def _is_pascal_case(self, name: str) -> bool:
        """فحص إذا كان الاسم بصيغة PascalCase"""
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
    
    def _to_snake_case(self, name: str) -> str:
        """تحويل إلى snake_case"""
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """تحويل إلى PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """حساب التعقيد الدوري"""
        complexity = 1  # البداية
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _count_nested_loops(self, node: ast.AST) -> int:
        """عد الحلقات المتداخلة"""
        max_depth = 0
        current_depth = 0
        
        def visit(n):
            nonlocal max_depth, current_depth
            if isinstance(n, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
                for child in ast.iter_child_nodes(n):
                    visit(child)
                current_depth -= 1
            else:
                for child in ast.iter_child_nodes(n):
                    visit(child)
        
        visit(node)
        return max_depth
    
    def _is_in_loop(self, node: ast.AST, tree: ast.AST) -> bool:
        """فحص إذا كان العقدة داخل حلقة"""
        # تنفيذ مبسط - يحتاج تحسين
        return False
    
    def _get_line(self, code: str, line_number: int) -> str:
        """الحصول على سطر معين"""
        lines = code.split('\\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""
    
    def _suggest_syntax_fix(self, error: SyntaxError) -> Optional[str]:
        """اقتراح إصلاح للخطأ النحوي"""
        error_msg = str(error).lower()
        
        if "invalid syntax" in error_msg:
            return "تحقق من الأقواس والفواصل"
        elif "unexpected eof" in error_msg:
            return "تحقق من إغلاق الأقواس والكتل"
        elif "indentation" in error_msg:
            return "تحقق من المسافات البادئة"
        
        return None

class JavaScriptAnalyzer:
    """محلل أكواد JavaScript"""
    
    def __init__(self):
        self.issues = []
    
    def analyze(self, code: str, file_path: str = None) -> Tuple[List[CodeIssue], CodeMetrics]:
        """تحليل كود JavaScript"""
        self.issues = []
        
        # تحليل أساسي للـ JavaScript
        self._analyze_basic_issues(code)
        self._analyze_style_issues(code)
        
        # حساب مقاييس أساسية
        metrics = self._calculate_basic_metrics(code)
        
        return self.issues, metrics
    
    def _analyze_basic_issues(self, code: str):
        """تحليل المشاكل الأساسية"""
        lines = code.split('\\n')
        
        for i, line in enumerate(lines, 1):
            # فحص استخدام var
            if re.search(r'\\bvar\\b', line):
                self.issues.append(CodeIssue(
                    type=IssueType.BEST_PRACTICE,
                    severity=Severity.LOW,
                    line_number=i,
                    column=line.find('var'),
                    message="استخدام var",
                    description="استخدم let أو const بدلاً من var",
                    suggestion="استبدل var بـ let أو const",
                    code_snippet=line.strip()
                ))
            
            # فحص == بدلاً من ===
            if '==' in line and '===' not in line and '!=' in line and '!==' not in line:
                self.issues.append(CodeIssue(
                    type=IssueType.BEST_PRACTICE,
                    severity=Severity.MEDIUM,
                    line_number=i,
                    column=line.find('=='),
                    message="مقارنة غير صارمة",
                    description="استخدم === بدلاً من ==",
                    suggestion="استبدل == بـ ===",
                    code_snippet=line.strip()
                ))
    
    def _analyze_style_issues(self, code: str):
        """تحليل مشاكل الأسلوب"""
        lines = code.split('\\n')
        
        for i, line in enumerate(lines, 1):
            # فحص الفاصلة المنقوطة المفقودة
            stripped = line.strip()
            if stripped and not stripped.endswith((';', '{', '}', ':', ',')):
                if not stripped.startswith(('if', 'for', 'while', 'function', 'class')):
                    self.issues.append(CodeIssue(
                        type=IssueType.STYLE_ISSUE,
                        severity=Severity.LOW,
                        line_number=i,
                        column=len(line),
                        message="فاصلة منقوطة مفقودة",
                        description="أضف فاصلة منقوطة في نهاية السطر",
                        suggestion="أضف ; في نهاية السطر",
                        code_snippet=line.strip()
                    ))
    
    def _calculate_basic_metrics(self, code: str) -> CodeMetrics:
        """حساب مقاييس أساسية"""
        lines = code.split('\\n')
        
        lines_of_code = 0
        lines_of_comments = 0
        blank_lines = 0
        functions_count = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('//') or stripped.startswith('/*'):
                lines_of_comments += 1
            else:
                lines_of_code += 1
                if 'function' in line:
                    functions_count += 1
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            blank_lines=blank_lines,
            cyclomatic_complexity=1,
            functions_count=functions_count,
            classes_count=0,
            imports_count=0,
            code_duplication=0.0,
            maintainability_index=50.0
        )

class CodeAnalyzer:
    """محلل الأكواد الرئيسي"""
    
    def __init__(self):
        self.analyzers = {
            'python': PythonAnalyzer(),
            'javascript': JavaScriptAnalyzer(),
            'js': JavaScriptAnalyzer(),
            'py': PythonAnalyzer()
        }
    
    def analyze_code(self, code: str, language: str, file_path: str = None) -> Dict[str, Any]:
        """تحليل الكود"""
        language = language.lower()
        
        if language not in self.analyzers:
            return {
                'issues': [],
                'metrics': None,
                'summary': {
                    'total_issues': 0,
                    'critical_issues': 0,
                    'high_issues': 0,
                    'medium_issues': 0,
                    'low_issues': 0
                },
                'recommendations': ["نوع الملف غير مدعوم للتحليل المتقدم"]
            }
        
        analyzer = self.analyzers[language]
        issues, metrics = analyzer.analyze(code, file_path)
        
        # تلخيص النتائج
        summary = self._create_summary(issues)
        recommendations = self._generate_recommendations(issues, metrics)
        
        return {
            'issues': [self._issue_to_dict(issue) for issue in issues],
            'metrics': self._metrics_to_dict(metrics) if metrics else None,
            'summary': summary,
            'recommendations': recommendations
        }
    
    def _create_summary(self, issues: List[CodeIssue]) -> Dict[str, int]:
        """إنشاء ملخص المشاكل"""
        summary = {
            'total_issues': len(issues),
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'info_issues': 0
        }
        
        for issue in issues:
            if issue.severity == Severity.CRITICAL:
                summary['critical_issues'] += 1
            elif issue.severity == Severity.HIGH:
                summary['high_issues'] += 1
            elif issue.severity == Severity.MEDIUM:
                summary['medium_issues'] += 1
            elif issue.severity == Severity.LOW:
                summary['low_issues'] += 1
            else:
                summary['info_issues'] += 1
        
        return summary
    
    def _generate_recommendations(self, issues: List[CodeIssue], metrics: CodeMetrics) -> List[str]:
        """توليد التوصيات"""
        recommendations = []
        
        # توصيات بناءً على المشاكل
        critical_count = sum(1 for issue in issues if issue.severity == Severity.CRITICAL)
        if critical_count > 0:
            recommendations.append(f"🚨 يوجد {critical_count} مشكلة حرجة تحتاج إصلاح فوري")
        
        high_count = sum(1 for issue in issues if issue.severity == Severity.HIGH)
        if high_count > 0:
            recommendations.append(f"⚠️ يوجد {high_count} مشكلة عالية الأولوية")
        
        # توصيات بناءً على المقاييس
        if metrics:
            if metrics.cyclomatic_complexity > 10:
                recommendations.append("🔄 التعقيد الدوري عالي - فكر في تقسيم الدوال")
            
            if metrics.lines_of_code > 500:
                recommendations.append("📏 الملف كبير - فكر في تقسيمه إلى ملفات أصغر")
            
            if metrics.lines_of_comments / max(metrics.lines_of_code, 1) < 0.1:
                recommendations.append("📝 أضف المزيد من التعليقات لتوضيح الكود")
            
            if metrics.maintainability_index < 50:
                recommendations.append("🔧 مؤشر القابلية للصيانة منخفض - يحتاج تحسين")
        
        if not recommendations:
            recommendations.append("✅ الكود يبدو جيداً! استمر في العمل الرائع")
        
        return recommendations
    
    def _issue_to_dict(self, issue: CodeIssue) -> Dict[str, Any]:
        """تحويل المشكلة إلى قاموس"""
        return {
            'type': issue.type.value,
            'severity': issue.severity.value,
            'line_number': issue.line_number,
            'column': issue.column,
            'message': issue.message,
            'description': issue.description,
            'suggestion': issue.suggestion,
            'code_snippet': issue.code_snippet,
            'fix_suggestion': issue.fix_suggestion
        }
    
    def _metrics_to_dict(self, metrics: CodeMetrics) -> Dict[str, Any]:
        """تحويل المقاييس إلى قاموس"""
        return {
            'lines_of_code': metrics.lines_of_code,
            'lines_of_comments': metrics.lines_of_comments,
            'blank_lines': metrics.blank_lines,
            'cyclomatic_complexity': metrics.cyclomatic_complexity,
            'functions_count': metrics.functions_count,
            'classes_count': metrics.classes_count,
            'imports_count': metrics.imports_count,
            'code_duplication': metrics.code_duplication,
            'maintainability_index': metrics.maintainability_index
        }
    
    def get_fix_suggestions(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """الحصول على اقتراحات الإصلاح"""
        fixes = []
        
        for issue in issues:
            if issue.get('fix_suggestion'):
                fixes.append({
                    'line_number': issue['line_number'],
                    'original_code': issue['code_snippet'],
                    'fixed_code': issue['fix_suggestion'],
                    'description': issue['description']
                })
        
        return fixes

