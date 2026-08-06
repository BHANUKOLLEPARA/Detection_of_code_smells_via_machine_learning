"""
Code Smell Dataset Generator
Generates synthetic code samples with labeled code smells for multiple programming languages
"""

import os
import json
import random
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import hashlib
from typing import List, Dict, Any, Tuple
import uuid

class CodeSmellDatasetGenerator:
    """
    Generate synthetic dataset for code smell detection
    Creates code samples with various smells and extracts metrics
    """
    
    def __init__(self, output_dir='datasets'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Define code smell types with their characteristics
        self.smell_types = [
            {
                'name': 'Long Method',
                'id': 'LONG_METHOD',
                'description': 'Method with too many lines of code',
                'severity': 'HIGH',
                'metrics_threshold': {
                    'loc': (50, 200),
                    'complexity': (10, 30),
                    'wmc': (5, 15)
                }
            },
            {
                'name': 'Large Class',
                'id': 'LARGE_CLASS',
                'description': 'Class with too many responsibilities',
                'severity': 'HIGH',
                'metrics_threshold': {
                    'loc': (200, 500),
                    'wmc': (20, 50),
                    'nof': (15, 40),
                    'lcom': (10, 30)
                }
            },
            {
                'name': 'Feature Envy',
                'id': 'FEATURE_ENVY',
                'description': 'Method that uses another class excessively',
                'severity': 'MEDIUM',
                'metrics_threshold': {
                    'cbo': (8, 20),
                    'tcc': (0.1, 0.3),
                    'rfc': (15, 30)
                }
            },
            {
                'name': 'God Class',
                'id': 'GOD_CLASS',
                'description': 'Class that does everything',
                'severity': 'CRITICAL',
                'metrics_threshold': {
                    'loc': (300, 1000),
                    'wmc': (30, 100),
                    'cbo': (15, 40),
                    'rfc': (40, 100),
                    'complexity': (50, 200)
                }
            },
            {
                'name': 'Data Class',
                'id': 'DATA_CLASS',
                'description': 'Class with only data and no behavior',
                'severity': 'LOW',
                'metrics_threshold': {
                    'wmc': (1, 5),
                    'nof': (5, 20),
                    'tcc': (0.8, 1.0),
                    'lcom': (1, 5)
                }
            },
            {
                'name': 'Complex Method',
                'id': 'COMPLEX_METHOD',
                'description': 'Method with high cyclomatic complexity',
                'severity': 'HIGH',
                'metrics_threshold': {
                    'complexity': (15, 50),
                    'loc': (30, 100)
                }
            },
            {
                'name': 'Shotgun Surgery',
                'id': 'SHOTGUN_SURGERY',
                'description': 'Change requires many small changes in many classes',
                'severity': 'HIGH',
                'metrics_threshold': {
                    'cbo': (10, 30),
                    'fan_out': (8, 25)
                }
            },
            {
                'name': 'Divergent Change',
                'id': 'DIVERGENT_CHANGE',
                'description': 'Class changed for different reasons',
                'severity': 'MEDIUM',
                'metrics_threshold': {
                    'wmc': (15, 40),
                    'lcom': (15, 40),
                    'tcc': (0.2, 0.5)
                }
            },
            {
                'name': 'Parallel Inheritance',
                'id': 'PARALLEL_INHERITANCE',
                'description': 'Creating subclass requires creating another subclass',
                'severity': 'MEDIUM',
                'metrics_threshold': {
                    'dit': (3, 6),
                    'nocc': (3, 10)
                }
            },
            {
                'name': 'Lazy Class',
                'id': 'LAZY_CLASS',
                'description': 'Class that doesn\'t do enough',
                'severity': 'LOW',
                'metrics_threshold': {
                    'wmc': (1, 3),
                    'loc': (10, 50),
                    'nof': (0, 2)
                }
            }
        ]
        
        # Language configurations
        self.languages = [
            {
                'name': 'Python',
                'id': 'python',
                'ext': '.py',
                'templates': self._get_python_templates(),
                'metrics_range': {
                    'loc': (5, 500),
                    'wmc': (1, 50),
                    'cbo': (0, 30),
                    'tcc': (0.0, 1.0),
                    'lcom': (0, 40),
                    'rfc': (0, 60),
                    'complexity': (1, 50),
                    'nof': (0, 30),
                    'nom': (1, 40),
                    'dit': (0, 5),
                    'nocc': (0, 8),
                    'fan_in': (0, 15),
                    'fan_out': (0, 20)
                }
            },
            {
                'name': 'Java',
                'id': 'java',
                'ext': '.java',
                'templates': self._get_java_templates(),
                'metrics_range': {
                    'loc': (5, 600),
                    'wmc': (1, 60),
                    'cbo': (0, 35),
                    'tcc': (0.0, 1.0),
                    'lcom': (0, 45),
                    'rfc': (0, 70),
                    'complexity': (1, 60),
                    'nof': (0, 35),
                    'nom': (1, 45),
                    'dit': (0, 6),
                    'nocc': (0, 10),
                    'fan_in': (0, 18),
                    'fan_out': (0, 25)
                }
            },
            {
                'name': 'JavaScript',
                'id': 'javascript',
                'ext': '.js',
                'templates': self._get_javascript_templates(),
                'metrics_range': {
                    'loc': (5, 400),
                    'wmc': (1, 40),
                    'cbo': (0, 25),
                    'tcc': (0.0, 1.0),
                    'lcom': (0, 30),
                    'rfc': (0, 50),
                    'complexity': (1, 45),
                    'nof': (0, 25),
                    'nom': (1, 35),
                    'dit': (0, 4),
                    'nocc': (0, 7),
                    'fan_in': (0, 12),
                    'fan_out': (0, 18)
                }
            },
            {
                'name': 'C++',
                'id': 'cpp',
                'ext': '.cpp',
                'templates': self._get_cpp_templates(),
                'metrics_range': {
                    'loc': (5, 550),
                    'wmc': (1, 55),
                    'cbo': (0, 30),
                    'tcc': (0.0, 1.0),
                    'lcom': (0, 40),
                    'rfc': (0, 65),
                    'complexity': (1, 55),
                    'nof': (0, 30),
                    'nom': (1, 40),
                    'dit': (0, 5),
                    'nocc': (0, 9),
                    'fan_in': (0, 16),
                    'fan_out': (0, 22)
                }
            },
            {
                'name': 'PHP',
                'id': 'php',
                'ext': '.php',
                'templates': self._get_php_templates(),
                'metrics_range': {
                    'loc': (5, 450),
                    'wmc': (1, 45),
                    'cbo': (0, 28),
                    'tcc': (0.0, 1.0),
                    'lcom': (0, 35),
                    'rfc': (0, 55),
                    'complexity': (1, 48),
                    'nof': (0, 28),
                    'nom': (1, 38),
                    'dit': (0, 5),
                    'nocc': (0, 8),
                    'fan_in': (0, 14),
                    'fan_out': (0, 20)
                }
            },
            {
                'name': 'Ruby',
                'id': 'ruby',
                'ext': '.rb',
                'templates': self._get_ruby_templates(),
                'metrics_range': {
                    'loc': (5, 400),
                    'wmc': (1, 40),
                    'cbo': (0, 25),
                    'tcc': (0.0, 1.0),
                    'lcom': (0, 30),
                    'rfc': (0, 50),
                    'complexity': (1, 42),
                    'nof': (0, 25),
                    'nom': (1, 35),
                    'dit': (0, 4),
                    'nocc': (0, 7),
                    'fan_in': (0, 12),
                    'fan_out': (0, 18)
                }
            },
            {
                'name': 'Go',
                'id': 'go',
                'ext': '.go',
                'templates': self._get_go_templates(),
                'metrics_range': {
                    'loc': (5, 450),
                    'wmc': (1, 45),
                    'cbo': (0, 25),
                    'tcc': (0.0, 1.0),
                    'lcom': (0, 35),
                    'rfc': (0, 55),
                    'complexity': (1, 45),
                    'nof': (0, 25),
                    'nom': (1, 40),
                    'dit': (0, 3),
                    'nocc': (0, 6),
                    'fan_in': (0, 15),
                    'fan_out': (0, 20)
                }
            },
            {
                'name': 'C#',
                'id': 'csharp',
                'ext': '.cs',
                'templates': self._get_csharp_templates(),
                'metrics_range': {
                    'loc': (5, 500),
                    'wmc': (1, 50),
                    'cbo': (0, 30),
                    'tcc': (0.0, 1.0),
                    'lcom': (0, 40),
                    'rfc': (0, 60),
                    'complexity': (1, 50),
                    'nof': (0, 30),
                    'nom': (1, 40),
                    'dit': (0, 5),
                    'nocc': (0, 8),
                    'fan_in': (0, 15),
                    'fan_out': (0, 20)
                }
            }
        ]
    
    def _get_python_templates(self):
        """Get Python code templates"""
        return {
            'simple_class': '''
class {class_name}:
    """Simple class template"""
    
    def __init__(self, {params}):
        {init_body}
    
    def simple_method(self, {method_params}):
        {method_body}
        return {return_value}
''',
            'complex_method': '''
def {method_name}({params}):
    """Complex method with many conditions"""
    result = None
    
    if {cond1}:
        for i in range({loop_count}):
            if {cond2}:
                while {cond3}:
                    if {cond4}:
                        result = {value1}
                    elif {cond5}:
                        result = {value2}
                    else:
                        result = {value3}
            else:
                try:
                    result = {operation}
                except Exception as e:
                    result = None
    else:
        result = {default_value}
    
    return result
''',
            'data_class': '''
class {class_name}:
    """Data class with only attributes"""
    
    def __init__(self, {params}):
        {init_assignments}
    
    def get_{attr1}(self):
        return self._{attr1}
    
    def set_{attr1}(self, value):
        self._{attr1} = value
''',
            'god_class': '''
class {class_name}:
    """God class doing everything"""
    
    def __init__(self):
        {init_complex}
    
    def database_operation(self):
        {db_code}
    
    def business_logic_1(self):
        {logic_code_1}
    
    def business_logic_2(self):
        {logic_code_2}
    
    def ui_rendering(self):
        {ui_code}
    
    def file_io(self):
        {file_code}
    
    def network_request(self):
        {network_code}
    
    def validation(self):
        {validation_code}
    
    def calculation(self):
        {calc_code}
''',
            'feature_envy': '''
def process_{class_name_lower}(self, obj):
    """Method that uses another class excessively"""
    # Using obj's data more than self's data
    result = obj.get_data()
    
    if obj.has_property():
        result = obj.transform(result)
    
    for item in obj.get_items():
        if obj.validate(item):
            result = obj.process(item)
    
    return result
'''
        }
    
    def _get_java_templates(self):
        """Get Java code templates"""
        return {
            'simple_class': '''
public class {class_name} {
    private {type1} {field1};
    private {type2} {field2};
    
    public {class_name}({type1} {field1}, {type2} {field2}) {
        this.{field1} = {field1};
        this.{field2} = {field2};
    }
    
    public {return_type} {method_name}({params}) {
        {method_body}
        return {return_value};
    }
}
''',
            'complex_method': '''
public {return_type} {method_name}({params}) {
    {return_type} result = null;
    
    if ({cond1}) {
        for (int i = 0; i < {loop_count}; i++) {
            if ({cond2}) {
                while ({cond3}) {
                    switch ({switch_var}) {
                        case 1:
                            result = {value1};
                            break;
                        case 2:
                            result = {value2};
                            break;
                        default:
                            result = {default_value};
                    }
                }
            } else {
                try {
                    result = {operation};
                } catch (Exception e) {
                    result = null;
                }
            }
        }
    }
    
    return result;
}
'''
        }
    
    def _get_javascript_templates(self):
        """Get JavaScript code templates"""
        return {
            'simple_class': '''
class {class_name} {
    constructor({params}) {
        {constructor_body}
    }
    
    {method_name}({method_params}) {
        {method_body}
        return {return_value};
    }
}
''',
            'complex_function': '''
function {function_name}({params}) {
    let result = null;
    
    if ({cond1}) {
        for (let i = 0; i < {loop_count}; i++) {
            if ({cond2}) {
                while ({cond3}) {
                    if ({cond4}) {
                        result = {value1};
                    } else if ({cond5}) {
                        result = {value2};
                    }
                }
            } else {
                result = {default_value};
            }
        }
    }
    
    return result;
}
'''
        }
    
    def _get_cpp_templates(self):
        """Get C++ code templates"""
        return {
            'simple_class': '''
class {class_name} {
private:
    {type1} {field1};
    {type2} {field2};

public:
    {class_name}({type1} {field1}, {type2} {field2}) {
        this->{field1} = {field1};
        this->{field2} = {field2};
    }
    
    {return_type} {method_name}({params}) {
        {method_body}
        return {return_value};
    }
};
'''
        }
    
    def _get_php_templates(self):
        """Get PHP code templates"""
        return {
            'simple_class': '''
<?php
class {class_name} {
    private ${field1};
    private ${field2};
    
    public function __construct({params}) {
        {constructor_body}
    }
    
    public function {method_name}({params}) {
        {method_body}
        return {return_value};
    }
}
?>
'''
        }
    
    def _get_ruby_templates(self):
        """Get Ruby code templates"""
        return {
            'simple_class': '''
class {class_name}
    def initialize({params})
        {constructor_body}
    end
    
    def {method_name}({params})
        {method_body}
        {return_value}
    end
end
'''
        }
    
    def _get_go_templates(self):
        """Get Go code templates"""
        return {
            'simple_struct': '''
type {struct_name} struct {
    {field1} {type1}
    {field2} {type2}
}

func (s *{struct_name}) {method_name}({params}) {return_type} {
    {method_body}
    return {return_value}
}
'''
        }
    
    def _get_csharp_templates(self):
        """Get C# code templates"""
        return {
            'simple_class': '''
public class {class_name} {
    private {type1} {field1};
    private {type2} {field2};
    
    public {class_name}({type1} {field1}, {type2} {field2}) {
        this.{field1} = {field1};
        this.{field2} = {field2};
    }
    
    public {return_type} {method_name}({params}) {
        {method_body}
        return {return_value};
    }
}
'''
        }
    
    def generate_random_metrics(self, language, smell_type=None):
        """Generate random metrics within ranges"""
        metrics = {}
        lang_config = next((l for l in self.languages if l['id'] == language), self.languages[0])
        
        # Generate base metrics
        for metric, (min_val, max_val) in lang_config['metrics_range'].items():
            if metric in ['tcc']:  # Float metrics
                metrics[metric] = round(random.uniform(min_val, max_val), 2)
            else:  # Integer metrics
                metrics[metric] = random.randint(min_val, max_val)
        
        # Adjust metrics based on smell type if provided
        if smell_type:
            smell_config = next((s for s in self.smell_types if s['id'] == smell_type), None)
            if smell_config and 'metrics_threshold' in smell_config:
                for metric, (min_val, max_val) in smell_config['metrics_threshold'].items():
                    if metric in metrics:
                        if metric in ['tcc']:
                            metrics[metric] = round(random.uniform(min_val, max_val), 2)
                        else:
                            metrics[metric] = random.randint(min_val, max_val)
        
        return metrics
    
    def generate_code_sample(self, language, smell_type, template_name, metrics):
        """Generate code sample from template"""
        templates = next((l['templates'] for l in self.languages if l['id'] == language), None)
        if not templates or template_name not in templates:
            return None
        
        template = templates[template_name]
        
        # Generate random values for template placeholders
        placeholders = {
            'class_name': f"Class_{uuid.uuid4().hex[:8]}",
            'struct_name': f"Struct_{uuid.uuid4().hex[:8]}",
            'method_name': f"method_{uuid.uuid4().hex[:8]}",
            'function_name': f"func_{uuid.uuid4().hex[:8]}",
            'field1': f"field_{uuid.uuid4().hex[:4]}",
            'field2': f"field_{uuid.uuid4().hex[:4]}",
            'attr1': f"attr_{uuid.uuid4().hex[:4]}",
            'type1': random.choice(['int', 'string', 'float', 'bool']),
            'type2': random.choice(['int', 'string', 'float', 'bool']),
            'return_type': random.choice(['int', 'string', 'float', 'bool', 'void']),
            'params': ', '.join([f"{random.choice(['int', 'string'])} p{i}" for i in range(random.randint(0, 3))]),
            'method_params': ', '.join([f"{random.choice(['int', 'string'])} p{i}" for i in range(random.randint(0, 3))]),
            'init_body': '\n        '.join([f"self._{random.choice(['x', 'y', 'z', 'value'])} = {random.randint(1, 100)}" for _ in range(random.randint(1, 3))]),
            'init_assignments': '\n        '.join([f"self._{random.choice(['x', 'y', 'z', 'value'])} = {random.choice(['x', 'y', 'z', 'value'])}" for _ in range(random.randint(2, 5))]),
            'init_complex': '\n        '.join([f"self.{random.choice(['db', 'ui', 'file', 'net'])} = {random.choice(['None', 'null', 'undefined'])}" for _ in range(random.randint(3, 7))]),
            'method_body': '\n        '.join([f"temp_{i} = {random.randint(1, 100)}" for i in range(random.randint(1, 5))]),
            'return_value': random.choice(['True', 'False', '0', 'null', 'None', 'result']),
            'cond1': random.choice(['x > 0', 'y < 10', 'value == True', 'items.length > 0']),
            'cond2': random.choice(['x > 5', 'y < 20', 'value != None', 'items.includes(item)']),
            'cond3': random.choice(['x < 100', 'y > 0', 'running', 'count < max']),
            'cond4': random.choice(['x == 10', 'y == 20', 'value == "test"', 'item.valid']),
            'cond5': random.choice(['x == 15', 'y == 25', 'value == "prod"', 'item.active']),
            'loop_count': random.randint(5, 50),
            'value1': random.choice(['result', 'temp', 'data', 'item']),
            'value2': random.choice(['result', 'temp', 'data', 'item']),
            'value3': random.choice(['result', 'temp', 'data', 'item']),
            'default_value': random.choice(['null', 'None', 'undefined', '0']),
            'switch_var': random.choice(['type', 'code', 'status']),
            'operation': random.choice(['x + y', 'data.process()', 'items.map(i => i.value)', 'calculate()']),
            'db_code': '\n        '.join([f"db.{random.choice(['query', 'insert', 'update', 'delete'])}()" for _ in range(random.randint(2, 5))]),
            'logic_code_1': '\n        '.join([f"process_{random.choice(['data', 'item', 'value'])}()" for _ in range(random.randint(2, 4))]),
            'logic_code_2': '\n        '.join([f"handle_{random.choice(['event', 'request', 'response'])}()" for _ in range(random.randint(2, 4))]),
            'ui_code': '\n        '.join([f"render_{random.choice(['component', 'view', 'page'])}()" for _ in range(random.randint(2, 4))]),
            'file_code': '\n        '.join([f"file.{random.choice(['read', 'write', 'delete'])}()" for _ in range(random.randint(2, 4))]),
            'network_code': '\n        '.join([f"http.{random.choice(['get', 'post', 'put'])}()" for _ in range(random.randint(2, 4))]),
            'validation_code': '\n        '.join([f"validate_{random.choice(['input', 'data', 'user'])}()" for _ in range(random.randint(2, 4))]),
            'calc_code': '\n        '.join([f"calculate_{random.choice(['total', 'average', 'sum'])}()" for _ in range(random.randint(2, 4))]),
            'class_name_lower': 'obj'
        }
        
        # Fill template
        code = template
        for key, value in placeholders.items():
            code = code.replace(f'{{{key}}}', str(value))
        
        return code
    
    def generate_dataset(self, samples_per_language=1000, output_format='csv'):
        """
        Generate complete dataset with code samples and metrics
        
        Args:
            samples_per_language: Number of samples per language
            output_format: 'csv' or 'json'
        
        Returns:
            Path to generated dataset file
        """
        print(f"🚀 Generating dataset with {samples_per_language} samples per language...")
        
        all_data = []
        code_samples_dir = os.path.join(self.output_dir, 'code_samples')
        os.makedirs(code_samples_dir, exist_ok=True)
        
        sample_id = 0
        
        for language_config in self.languages:
            language = language_config['id']
            print(f"\n📝 Generating {language} samples...")
            
            for i in range(samples_per_language):
                # Select random smell type
                smell = random.choice(self.smell_types)
                smell_id = smell['id']
                smell_name = smell['name']
                
                # Select random template
                template_name = random.choice(list(language_config['templates'].keys()))
                
                # Generate metrics influenced by the smell
                metrics = self.generate_random_metrics(language, smell_id)
                
                # Generate code sample
                code = self.generate_code_sample(language, smell_id, template_name, metrics)
                
                if code:
                    # Save code to file
                    code_filename = f"sample_{sample_id:06d}_{language}_{smell_id}{language_config['ext']}"
                    code_path = os.path.join(code_samples_dir, code_filename)
                    
                    with open(code_path, 'w', encoding='utf-8') as f:
                        f.write(code)
                    
                    # Create dataset entry with correct column names for training
                    entry = {
                        'sample_id': sample_id,
                        'language': language,
                        'language_name': language_config['name'],
                        'smell_id': smell_id,
                        'smell_type': smell_name,  # This is what the system expects
                        'severity': smell['severity'],
                        'code_file': code_filename,
                        'code_preview': code[:200] + '...' if len(code) > 200 else code,
                        # Include all the required metrics for training
                        'loc': metrics.get('loc', 0),
                        'wmc': metrics.get('wmc', 0),
                        'cbo': metrics.get('cbo', 0),
                        'tcc': metrics.get('tcc', 0.0),
                        'lcom': metrics.get('lcom', 0),
                        'rfc': metrics.get('rfc', 0),
                        'complexity': metrics.get('complexity', 0),
                        # Additional metrics (optional but useful)
                        'nof': metrics.get('nof', 0),
                        'nom': metrics.get('nom', 0),
                        'dit': metrics.get('dit', 0),
                        'nocc': metrics.get('nocc', 0),
                        'fan_in': metrics.get('fan_in', 0),
                        'fan_out': metrics.get('fan_out', 0),
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    all_data.append(entry)
                    sample_id += 1
                
                if (i + 1) % 100 == 0:
                    print(f"  Generated {i + 1}/{samples_per_language} samples")
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Ensure we have the required columns in the right order for training
        required_columns = ['loc', 'wmc', 'cbo', 'tcc', 'lcom', 'rfc', 'complexity', 'smell_type']
        optional_columns = ['sample_id', 'language', 'language_name', 'smell_id', 'severity', 
                           'code_file', 'code_preview', 'nof', 'nom', 'dit', 'nocc', 
                           'fan_in', 'fan_out', 'generated_at']
        
        # Reorder columns to put required ones first
        all_columns = required_columns + [col for col in optional_columns if col in df.columns]
        df = df[all_columns]
        
        # Save dataset
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'csv':
            output_file = os.path.join(self.output_dir, f'code_smell_dataset_{timestamp}.csv')
            df.to_csv(output_file, index=False)
        else:
            output_file = os.path.join(self.output_dir, f'code_smell_dataset_{timestamp}.json')
            df.to_json(output_file, orient='records', indent=2)
        
        # Save metadata
        metadata = {
            'dataset_name': f'Code Smell Dataset {timestamp}',
            'generated_at': datetime.now().isoformat(),
            'total_samples': len(all_data),
            'languages': list(set(df['language'])) if 'language' in df.columns else [],
            'smell_types': list(set(df['smell_type'])),
            'features': required_columns,
            'optional_features': [col for col in optional_columns if col in df.columns],
            'samples_per_language': samples_per_language,
            'file_format': output_format
        }
        
        metadata_file = os.path.join(self.output_dir, f'dataset_metadata_{timestamp}.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✅ Dataset generation complete!")
        print(f"   Total samples: {len(all_data)}")
        print(f"   Languages: {len(set(df['language'])) if 'language' in df.columns else 0}")
        print(f"   Smell types: {len(set(df['smell_type']))}")
        print(f"   Required columns: {required_columns}")
        print(f"   Dataset file: {output_file}")
        print(f"   Metadata file: {metadata_file}")
        print(f"   Code samples: {code_samples_dir}")
        
        # Show sample of the dataset
        print(f"\n📊 Dataset preview (first 3 rows):")
        print(df[required_columns].head(3).to_string())
        
        return output_file, metadata_file
    
    def generate_large_dataset(self, total_samples=10000):
        """
        Generate a large dataset with specified total samples
        Distributes samples across languages
        """
        samples_per_language = total_samples // len(self.languages)
        return self.generate_dataset(samples_per_language=samples_per_language)


class DatasetAugmenter:
    """
    Augment existing dataset with variations
    """
    
    def __init__(self, input_file):
        self.input_file = input_file
        self.df = pd.read_csv(input_file) if input_file.endswith('.csv') else pd.read_json(input_file)
    
    def add_noise(self, noise_level=0.1):
        """Add random noise to metrics"""
        augmented_df = self.df.copy()
        
        numeric_columns = self.df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col not in ['sample_id']:
                noise = np.random.normal(0, noise_level, len(augmented_df))
                augmented_df[col] = augmented_df[col] * (1 + noise)
                augmented_df[col] = augmented_df[col].clip(lower=0)
        
        return augmented_df
    
    def create_variations(self, num_variations=3):
        """Create multiple variations of each sample"""
        variations = []
        
        for _, row in self.df.iterrows():
            for i in range(num_variations):
                new_row = row.copy()
                # Add small variations to metrics
                for col in self.df.select_dtypes(include=[np.number]).columns:
                    if col not in ['sample_id']:
                        variation = np.random.uniform(0.9, 1.1)
                        new_row[col] = row[col] * variation
                
                new_row['sample_id'] = f"{row['sample_id']}_var_{i}"
                variations.append(new_row)
        
        return pd.DataFrame(variations)
    
    def balance_classes(self):
        """Balance the dataset by oversampling minority classes"""
        from sklearn.utils import resample
        
        balanced_dfs = []
        max_count = self.df['smell_type'].value_counts().max()
        
        for smell in self.df['smell_type'].unique():
            smell_df = self.df[self.df['smell_type'] == smell]
            if len(smell_df) < max_count:
                smell_df = resample(smell_df, 
                                   replace=True, 
                                   n_samples=max_count, 
                                   random_state=42)
            balanced_dfs.append(smell_df)
        
        return pd.concat(balanced_dfs)


# Command line interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Code Smell Dataset')
    parser.add_argument('--samples', type=int, default=200, help='Samples per language (default: 200)')
    parser.add_argument('--total', type=int, default=None, help='Total samples (overrides --samples)')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Output format')
    parser.add_argument('--output', default='datasets', help='Output directory')
    
    args = parser.parse_args()
    
    generator = CodeSmellDatasetGenerator(output_dir=args.output)
    
    print("\n" + "="*60)
    print("🔧 CodeSmell Dataset Generator")
    print("="*60)
    
    if args.total:
        generator.generate_large_dataset(total_samples=args.total)
    else:
        generator.generate_dataset(samples_per_language=args.samples, output_format=args.format)
    
    print("\n✨ Dataset generation complete! You can now use this dataset for training.")