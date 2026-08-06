import re
import os
import ast
import tokenize
from io import BytesIO, StringIO
import javalang
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import tempfile
import subprocess

def extract_metrics_from_code(file_path=None, code_content=None, is_snippet=False, language='python'):
    """
    Extract software metrics from source code using regex and basic parsing
    """
    metrics = {
        'loc': 0,
        'wmc': 0,
        'cbo': 0,
        'tcc': 0.0,
        'lcom': 0,
        'rfc': 0,
        'complexity': 0
    }
    
    # Get code content
    if file_path and not is_snippet:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
    else:
        code = code_content or ''
    
    if not code:
        return metrics
    
    # Lines of Code (LOC)
    lines = code.split('\n')
    metrics['loc'] = len([l for l in lines if l.strip() and not l.strip().startswith('//') and not l.strip().startswith('#')])
    
    # Determine language
    if file_path:
        ext = Path(file_path).suffix.lower()
        if ext in ['.py']:
            language = 'python'
        elif ext in ['.java']:
            language = 'java'
        elif ext in ['.js']:
            language = 'javascript'
        elif ext in ['.php']:
            language = 'php'
        elif ext in ['.c', '.cpp', '.h']:
            language = 'c_cpp'
    
    # Language-specific analysis
    if language == 'python':
        metrics = analyze_python_code(code, metrics)
    elif language == 'java':
        metrics = analyze_java_code(code, metrics)
    elif language == 'javascript':
        metrics = analyze_javascript_code(code, metrics)
    elif language == 'php':
        metrics = analyze_php_code(code, metrics)
    elif language == 'c_cpp':
        metrics = analyze_c_cpp_code(code, metrics)
    else:
        # Generic analysis for other languages
        metrics = analyze_generic_code(code, metrics)
    
    return metrics

def analyze_python_code(code, metrics):
    """Analyze Python code specifically"""
    try:
        tree = ast.parse(code)
        
        # Weighted Method Count (WMC) - count functions and methods
        metrics['wmc'] = len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))])
        
        # Coupling Between Objects (CBO) - rough estimate
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        metrics['cbo'] = len(imports)
        
        # Lack of Cohesion of Methods (LCOM) - rough estimate
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        if classes:
            total_methods = 0
            for cls in classes:
                methods = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                total_methods += len(methods)
            metrics['lcom'] = total_methods // len(classes)
        
        # Response for Class (RFC)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        metrics['rfc'] = len(calls)
        
        # Cyclomatic Complexity
        metrics['complexity'] = calculate_cyclomatic_complexity_python(tree)
        
        # Tight Class Cohesion (TCC) - estimate
        if metrics['wmc'] > 0:
            metrics['tcc'] = min(1.0, metrics['lcom'] / metrics['wmc'])
        
    except:
        # Fallback to generic analysis
        metrics = analyze_generic_code(code, metrics)
    
    return metrics

def calculate_cyclomatic_complexity_python(tree):
    """Calculate cyclomatic complexity for Python AST"""
    complexity = 1  # Base complexity
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.Try):
            complexity += len(node.handlers)
    
    return complexity

def analyze_java_code(code, metrics):
    """Analyze Java code"""
    try:
        # Count methods (WMC)
        method_pattern = r'(public|private|protected)?\s+[\w<>[\]]+\s+(\w+)\s*\([^)]*\)\s*\{?'
        methods = re.findall(method_pattern, code)
        metrics['wmc'] = len(methods)
        
        # Count imports (CBO)
        imports = re.findall(r'import\s+[\w.]+;', code)
        metrics['cbo'] = len(imports)
        
        # Cyclomatic complexity
        decisions = re.findall(r'\b(if|while|for|switch|case|catch)\b', code)
        metrics['complexity'] = len(decisions) + 1
        
        # LOC already counted
        metrics['rfc'] = len(re.findall(r'\w+\(', code))  # Rough RFC
        
    except Exception as e:
        print(f"Error analyzing Java: {e}")
    
    return metrics

def analyze_javascript_code(code, metrics):
    """Analyze JavaScript code"""
    try:
        # Count functions (WMC)
        functions = re.findall(r'function\s+\w+\s*\(|const\s+\w+\s*=\s*\(|let\s+\w+\s*=\s*\(|=>', code)
        metrics['wmc'] = len(functions)
        
        # Count requires/imports (CBO)
        imports = re.findall(r'(require\(|import\s+.*from)', code)
        metrics['cbo'] = len(imports)
        
        # Complexity
        decisions = re.findall(r'\b(if|else|for|while|switch|case|catch)\b', code)
        metrics['complexity'] = len(decisions) + 1
        
    except Exception as e:
        print(f"Error analyzing JavaScript: {e}")
    
    return metrics

def analyze_php_code(code, metrics):
    """Analyze PHP code"""
    try:
        # Count functions (WMC)
        functions = re.findall(r'function\s+(\w+)\s*\(', code)
        metrics['wmc'] = len(functions)
        
        # Count includes/requires (CBO)
        includes = re.findall(r'(include|require|include_once|require_once)', code)
        metrics['cbo'] = len(includes)
        
        # Complexity
        decisions = re.findall(r'\b(if|else|for|foreach|while|switch|case|catch)\b', code)
        metrics['complexity'] = len(decisions) + 1
        
    except Exception as e:
        print(f"Error analyzing PHP: {e}")
    
    return metrics

def analyze_c_cpp_code(code, metrics):
    """Analyze C/C++ code"""
    try:
        # Count functions (WMC)
        functions = re.findall(r'\w+\s+(\w+)\s*\([^)]*\)\s*\{', code)
        metrics['wmc'] = len(functions)
        
        # Count includes (CBO)
        includes = re.findall(r'#include\s*[<"][^>"]+[>"]', code)
        metrics['cbo'] = len(includes)
        
        # Complexity
        decisions = re.findall(r'\b(if|else|for|while|switch|case|catch)\b', code)
        metrics['complexity'] = len(decisions) + 1
        
    except Exception as e:
        print(f"Error analyzing C/C++: {e}")
    
    return metrics

def analyze_generic_code(code, metrics):
    """Generic code analysis for unsupported languages"""
    try:
        # Rough WMC - count function-like patterns
        functions = re.findall(r'\w+\s*\([^)]*\)\s*\{', code)
        metrics['wmc'] = len(functions)
        
        # Rough CBO - count imports/includes
        imports = re.findall(r'(import|include|require|from|using)', code, re.IGNORECASE)
        metrics['cbo'] = len(imports)
        
        # Rough complexity
        decisions = re.findall(r'\b(if|else|for|while|switch|case|catch|foreach)\b', code, re.IGNORECASE)
        metrics['complexity'] = len(decisions) + 1
        
        # Rough RFC - count function calls
        calls = re.findall(r'\w+\s*\(', code)
        metrics['rfc'] = len(calls)
        
        # Rough LCOM
        if metrics['wmc'] > 0:
            metrics['lcom'] = metrics['wmc'] // 2  # Rough estimate
        
    except Exception as e:
        print(f"Error in generic analysis: {e}")
    
    return metrics

def analyze_folder(folder_path):
    """Analyze entire folder for code smells"""
    results = {
        'files': [],
        'total_files': 0,
        'total_smells': 0,
        'languages': {}
    }
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in ['.py', '.java', '.js', '.php', '.c', '.cpp', '.h', '.cs', '.rb', '.go']:
                file_path = os.path.join(root, file)
                
                # Extract metrics
                metrics = extract_metrics_from_code(file_path)
                
                # Predict smells (simplified for demo)
                smells = predict_smells_from_metrics(metrics)
                
                results['files'].append({
                    'path': file_path,
                    'metrics': metrics,
                    'smells': smells
                })
                
                results['total_files'] += 1
                results['total_smells'] += len(smells)
                
                # Track languages
                lang = ext[1:] if ext else 'unknown'
                results['languages'][lang] = results['languages'].get(lang, 0) + 1
    
    return results

def predict_smells_from_metrics(metrics):
    """Simple rule-based smell detection (for demo)"""
    smells = []
    
    # Long Method detection
    if metrics['loc'] > 50 and metrics['complexity'] > 10:
        smells.append({
            'smell_name': 'Long Method',
            'confidence': 0.85,
            'severity': 'HIGH',
            'line_start': 1,
            'line_end': metrics['loc']
        })
    
    # Large Class detection
    if metrics['wmc'] > 20 and metrics['loc'] > 200:
        smells.append({
            'smell_name': 'Large Class',
            'confidence': 0.90,
            'severity': 'HIGH',
            'line_start': 1,
            'line_end': metrics['loc']
        })
    
    # Feature Envy detection
    if metrics['cbo'] > 10 and metrics['tcc'] < 0.3:
        smells.append({
            'smell_name': 'Feature Envy',
            'confidence': 0.75,
            'severity': 'MEDIUM',
            'line_start': 1,
            'line_end': metrics['loc']
        })
    
    # God Class detection
    if metrics['wmc'] > 30 and metrics['rfc'] > 50:
        smells.append({
            'smell_name': 'God Class',
            'confidence': 0.80,
            'severity': 'CRITICAL',
            'line_start': 1,
            'line_end': metrics['loc']
        })
    
    # Data Class detection
    if metrics['wmc'] < 5 and metrics['loc'] > 100:
        smells.append({
            'smell_name': 'Data Class',
            'confidence': 0.70,
            'severity': 'LOW',
            'line_start': 1,
            'line_end': metrics['loc']
        })
    
    return smells

def generate_report(analysis_job):
    """Generate PDF report for analysis"""
    try:
        # Create reports directory if not exists
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate report filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"report_{analysis_job.id}_{timestamp}.pdf"
        report_path = os.path.join(reports_dir, report_filename)
        
        # Create a simple text report (can be enhanced with reportlab for PDF)
        with open(report_path.replace('.pdf', '.txt'), 'w') as f:
            f.write(f"Code Smell Detection Report\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"Analysis ID: {analysis_job.id}\n")
            f.write(f"Analysis Name: {analysis_job.name}\n")
            f.write(f"Date: {analysis_job.created_at}\n")
            f.write(f"User: {analysis_job.user.username}\n")
            f.write(f"Analysis Type: {analysis_job.analysis_type}\n\n")
            
            f.write(f"Files Analyzed: {analysis_job.file_count}\n")
            f.write(f"Total Smells Found: {analysis_job.total_smells_found}\n")
            f.write(f"Processing Time: {analysis_job.processing_time:.2f} seconds\n\n")
            
            f.write("Detailed Results:\n")
            f.write("-" * 30 + "\n\n")
            
            results = SmellDetectionResult.objects.filter(analysis_job=analysis_job)
            for result in results:
                f.write(f"File: {result.file_name}\n")
                f.write(f"Smell: {result.smell_type.name}\n")
                f.write(f"Confidence: {result.confidence:.2%}\n")
                f.write(f"Severity: {result.smell_type.severity}\n")
                f.write(f"Lines: {result.line_start}-{result.line_end}\n")
                f.write("-" * 20 + "\n")
        
        # If we want actual PDF, we can use reportlab
        # For now, return the text file path
        return report_path.replace('.pdf', '.txt')
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return None