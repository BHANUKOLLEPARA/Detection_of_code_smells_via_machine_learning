"""
Metric Extractor Module for Code Smell Detection
Extracts software metrics from source code
"""

import re
import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class MetricExtractor:
    """
    Main class for extracting software metrics from source code
    """
    
    def __init__(self):
        self.supported_languages = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.php': 'php',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.go': 'go',
        }
    
    def extract_from_code(self, code: str, language: str = 'python', filename: str = 'snippet') -> Dict[str, Any]:
        """
        Extract metrics from code string - Paste code option కోసం
        """
        # Initialize metrics with defaults
        metrics = {
            'loc': 0,
            'wmc': 0,
            'cbo': 0,
            'tcc': 0.5,
            'lcom': 0,
            'rfc': 0,
            'complexity': 1,
            'noc': 0,
            'nom': 0,
            'nof': 0,
        }
        
        if not code or not code.strip():
            print("⚠️ Warning: Empty code provided")
            return metrics
        
        print(f"\n{'='*60}")
        print(f"🔍 Extracting metrics from {language} code (Paste option)")
        print(f"{'='*60}")
        print(f"Code length: {len(code)} characters")
        print(f"First 100 chars: {code[:100]}...")
        
        # Count lines of code (non-empty lines) - ఇది పనిచేస్తుంది
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        metrics['loc'] = len(non_empty_lines)
        print(f"📊 Lines of code (non-empty): {metrics['loc']}")
        
        if metrics['loc'] == 0:
            print("⚠️ No non-empty lines found! Check your code.")
            return metrics
        
        # Language-specific extraction
        if language == 'python':
            self._extract_python_metrics(code, metrics)
        else:
            self._extract_generic_metrics(code, metrics)
        
        # Calculate derived metrics
        self._calculate_derived_metrics(metrics)
        
        print(f"\n📈 Final Metrics:")
        print(f"  📏 LOC: {metrics['loc']}")
        print(f"  🔧 WMC: {metrics['wmc']}")
        print(f"  🔗 CBO: {metrics['cbo']}")
        print(f"  🎯 TCC: {metrics['tcc']:.2f}")
        print(f"  📦 LCOM: {metrics['lcom']}")
        print(f"  📞 RFC: {metrics['rfc']}")
        print(f"  🧮 Complexity: {metrics['complexity']}")
        print(f"  📚 Classes: {metrics['noc']}")
        print(f"  📝 Methods: {metrics['nom']}")
        print(f"{'='*60}\n")
        
        return metrics
    
    def _extract_python_metrics(self, code: str, metrics: Dict[str, Any]):
        """Extract metrics from Python code using AST"""
        try:
            print("🔄 Parsing Python code with AST...")
            tree = ast.parse(code)
            
            # Walk through all nodes
            for node in ast.walk(tree):
                # Count functions/methods
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    metrics['wmc'] += 1
                    metrics['nom'] += 1
                    
                    # Calculate complexity
                    metrics['complexity'] += self._calculate_complexity(node)
                    print(f"  Found function: {node.name}")
                
                # Count classes
                elif isinstance(node, ast.ClassDef):
                    metrics['noc'] += 1
                    print(f"  Found class: {node.name}")
                    
                    # Count methods in class
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            metrics['nom'] += 1
                
                # Count imports (CBO)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics['cbo'] += 1
                    metrics['rfc'] += 1  # Imports count as references
                
                # Count function calls (RFC)
                elif isinstance(node, ast.Call):
                    metrics['rfc'] += 1
            
            print(f"✅ AST parsing complete:")
            print(f"   Found {metrics['noc']} classes, {metrics['nom']} methods/functions")
            print(f"   Found {metrics['cbo']} imports, {metrics['rfc']} calls")
            
        except SyntaxError as e:
            print(f"⚠️ Syntax error in Python code: {e}")
            print("Falling back to generic parsing...")
            self._extract_generic_metrics(code, metrics)
        except Exception as e:
            print(f"⚠️ Error parsing Python: {e}")
            print("Falling back to generic parsing...")
            self._extract_generic_metrics(code, metrics)
    
    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity for a node"""
        complexity = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                if isinstance(child.op, (ast.And, ast.Or)):
                    complexity += len(child.values) - 1
        return complexity
    
    def _extract_generic_metrics(self, code: str, metrics: Dict[str, Any]):
        """Extract metrics using regex patterns (fallback method)"""
        print("🔄 Using generic regex parsing...")
        
        # Count function definitions
        function_patterns = [
            (r'def\s+(\w+)\s*\(', 'Python'),           # Python
            (r'function\s+(\w+)\s*\(', 'JavaScript'),   # JavaScript
            (r'(public|private|protected).*?(\w+)\s*\(', 'Java/C#'),  # Java/C#
            (r'func\s+(\w+)\s*\(', 'Go'),               # Go
        ]
        
        total_functions = 0
        for pattern, lang in function_patterns:
            functions = re.findall(pattern, code, re.MULTILINE)
            count = len(functions)
            total_functions += count
            if count > 0:
                print(f"  Found {count} functions ({lang} pattern)")
        
        metrics['wmc'] = total_functions
        metrics['nom'] = total_functions
        
        # Count import statements
        import_patterns = [
            (r'import\s+[\w.]+', 'import'),
            (r'from\s+[\w.]+\s+import', 'from import'),
            (r'#include\s*[<"][^>"]+[>"]', 'include'),
            (r'require\s*\(', 'require'),
        ]
        
        total_imports = 0
        for pattern, name in import_patterns:
            imports = re.findall(pattern, code)
            count = len(imports)
            total_imports += count
            if count > 0:
                print(f"  Found {count} {name} statements")
        
        metrics['cbo'] = total_imports
        
        # Count function calls
        call_pattern = r'(\w+)\s*\([^)]*\)'
        calls = re.findall(call_pattern, code)
        metrics['rfc'] = len(calls)
        print(f"  Found {metrics['rfc']} function calls")
        
        # Count control flow for complexity
        control_patterns = [
            (r'\bif\b', 'if'),
            (r'\belse\b', 'else'),
            (r'\bfor\b', 'for'),
            (r'\bwhile\b', 'while'),
            (r'\bswitch\b', 'switch'),
            (r'\bcase\b', 'case'),
            (r'\bcatch\b', 'catch'),
            (r'&&', '&&'),
            (r'\|\|', '||'),
        ]
        
        decisions = 0
        for pattern, name in control_patterns:
            count = len(re.findall(pattern, code))
            decisions += count
            if count > 0:
                print(f"  Found {count} '{name}' statements")
        
        metrics['complexity'] = decisions + 1
        print(f"  Total complexity: {metrics['complexity']}")
    
    def _calculate_derived_metrics(self, metrics: Dict[str, Any]):
        """Calculate derived metrics like LCOM and TCC"""
        
        # Calculate LCOM (Lack of Cohesion of Methods)
        if metrics['nom'] > 0:
            metrics['lcom'] = metrics['nom'] // 2
        else:
            metrics['lcom'] = 0
        
        # Calculate TCC (Tight Class Cohesion)
        if metrics['nom'] > 0 and metrics['noc'] > 0:
            metrics['tcc'] = min(1.0, metrics['noc'] / metrics['nom'])
        else:
            metrics['tcc'] = 0.5


# Convenience function for paste code option
def extract_metrics_from_code(code: str, language: str = 'python', is_snippet: bool = True, **kwargs) -> Dict[str, Any]:
    """
    Extract metrics from code string - Paste code option కోసం ప్రత్యేకంగా
    """
    print(f"\n📥 Processing pasted code (language: {language})")
    extractor = MetricExtractor()
    return extractor.extract_from_code(code, language)


# Quick test function
def test_with_sample():
    """Test the extractor with sample code"""
    sample_code = """
def add(a, b):
    return a + b

def multiply(x, y):
    result = 0
    for i in range(y):
        result = add(result, x)
    return result

class Calculator:
    def __init__(self):
        self.history = []
    
    def calculate(self, a, b, operation):
        if operation == 'add':
            result = add(a, b)
        elif operation == 'multiply':
            result = multiply(a, b)
        else:
            result = 0
        self.history.append(result)
        return result
"""
    
    print("\n🧪 Testing with sample code...")
    metrics = extract_metrics_from_code(sample_code)
    
    print("\n📊 Test Results:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    return metrics


# Run test if executed directly
if __name__ == '__main__':
    test_with_sample()