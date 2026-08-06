from django.apps import AppConfig

class DetectorConfig(AppConfig):
    """
    Configuration for the Detector application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'detector'
    verbose_name = 'Code Smell Detector'
    
    def ready(self):
        """
        Initialize app when Django starts.
        Import signals to ensure they are registered.
        """
        try:
            import detector.signals  # noqa: F401
        except ImportError:
            pass
        
        # Initialize default code smell types if they don't exist
        self.create_default_smell_types()
        
    def create_default_smell_types(self):
        """
        Create default code smell types in the database if they don't exist.
        This runs when the app is ready.
        """
        try:
            from django.db.utils import OperationalError, ProgrammingError
            from .models import CodeSmellType
            
            # Try to create default smell types
            default_smells = [
                {
                    'name': 'Long Method',
                    'description': 'A method that contains too many lines of code. Long methods are difficult to understand, maintain, and test.',
                    'severity': 'HIGH',
                    'refactoring_tip': 'Break the method into smaller, focused methods using the Extract Method refactoring technique.',
                    'example_code': '''
def process_data(data):
    # Too many responsibilities
    validate_data(data)
    clean_data(data)
    transform_data(data)
    analyze_data(data)
    generate_report(data)
    send_notification(data)
    return data
                    '''
                },
                {
                    'name': 'Large Class',
                    'description': 'A class that has grown too large, trying to do too many things. It often has too many instance variables and methods.',
                    'severity': 'HIGH',
                    'refactoring_tip': 'Split the class into smaller, more focused classes using Extract Class or Extract Subclass refactoring.',
                    'example_code': '''
class UserManager:
    def validate_user(self): pass
    def save_user(self): pass
    def send_email(self): pass
    def generate_report(self): pass
    def calculate_stats(self): pass
    def backup_data(self): pass
    # ... 20 more methods
                    '''
                },
                {
                    'name': 'Feature Envy',
                    'description': 'A method that seems more interested in another class than its own. It accesses another class\'s data more than its own.',
                    'severity': 'MEDIUM',
                    'refactoring_tip': 'Move the method to the class it envies using the Move Method refactoring.',
                    'example_code': '''
class Order:
    def calculate_discount(self, customer):
        # Uses customer data more than order data
        if customer.is_premium and customer.years > 5:
            return self.total * 0.2
        return self.total * 0.1
                    '''
                },
                {
                    'name': 'God Class',
                    'description': 'A class that knows too much or does too much. It has become a central point of control and is difficult to maintain.',
                    'severity': 'CRITICAL',
                    'refactoring_tip': 'Split responsibilities into multiple classes. Use design patterns like Facade or Mediator to manage complexity.',
                    'example_code': '''
class Application:
    def handle_database(self): pass
    def process_ui(self): pass
    def manage_network(self): pass
    def calculate_business_logic(self): pass
    def handle_file_io(self): pass
    def manage_threads(self): pass
    # God class doing everything
                    '''
                },
                {
                    'name': 'Data Class',
                    'description': 'A class that only contains data fields and simple getters/setters, but no meaningful behavior.',
                    'severity': 'LOW',
                    'refactoring_tip': 'Move behavior into the data class. Encapsulate fields and add methods that operate on the data.',
                    'example_code': '''
class Point:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
    # Only getters and setters, no behavior
                    '''
                },
                {
                    'name': 'Complex Method',
                    'description': 'A method with high cyclomatic complexity due to many conditional statements, loops, or nested structures.',
                    'severity': 'HIGH',
                    'refactoring_tip': 'Simplify complex conditions, extract nested logic into separate methods, use polymorphism or strategy pattern.',
                    'example_code': '''
def complex_function(a, b, c, d, e):
    if a:
        if b:
            for i in range(c):
                if d[i] > e:
                    while condition:
                        # Deeply nested logic
                        pass
                else:
                    # More nested logic
                    pass
        else:
            # Even more complexity
            pass
    return result
                    '''
                },
                {
                    'name': 'Shotgun Surgery',
                    'description': 'A change that requires many small changes in many different classes. Opposite of divergent change.',
                    'severity': 'HIGH',
                    'refactoring_tip': 'Move all changes into a single class. Use Move Method and Move Field refactorings.',
                    'example_code': '''
# To add a new field, you need to modify:
# - Database schema
# - Data access layer
# - Business logic layer
# - Presentation layer
# - API endpoints
# - Validation logic
                    '''
                },
                {
                    'name': 'Divergent Change',
                    'description': 'When one class is changed in different ways for different reasons. The class has multiple responsibilities.',
                    'severity': 'MEDIUM',
                    'refactoring_tip': 'Split the class into multiple classes, each with a single responsibility.',
                    'example_code': '''
class ReportGenerator:
    def fetch_data(self): pass  # Changes with database
    def format_report(self): pass  # Changes with presentation
    def calculate_stats(self): pass  # Changes with business rules
    def send_email(self): pass  # Changes with communication
                    '''
                },
                {
                    'name': 'Parallel Inheritance Hierarchies',
                    'description': 'When creating a subclass of one class requires creating a subclass of another.',
                    'severity': 'MEDIUM',
                    'refactoring_tip': 'Remove duplication by merging hierarchies or using delegation.',
                    'example_code': '''
class Animal:
    pass

class AnimalView:
    pass

# Adding Dog requires adding DogView
# Adding Cat requires adding CatView
                    '''
                },
                {
                    'name': 'Lazy Class',
                    'description': 'A class that doesn\'t do enough to justify its existence. It adds unnecessary complexity.',
                    'severity': 'LOW',
                    'refactoring_tip': 'Remove the class and move its behavior to related classes, or inline it.',
                    'example_code': '''
class EmptyWrapper:
    def __init__(self, data):
        self.data = data
    # No additional behavior, just wrapping
                    '''
                },
                {
                    'name': 'Speculative Generality',
                    'description': 'Code that is more general than needed, created for future functionality that never materializes.',
                    'severity': 'LOW',
                    'refactoring_tip': 'Remove unused hooks, parameters, and abstractions. Simplify the code.',
                    'example_code': '''
class AbstractBaseFactoryWithManyHooks:
    def process(self, data, options=None, callback=None, 
                async_mode=False, transactional=False):
        # Many parameters never used
        pass
                    '''
                },
                {
                    'name': 'Temporary Field',
                    'description': 'A field that only gets set in certain circumstances and is empty the rest of the time.',
                    'severity': 'MEDIUM',
                    'refactoring_tip': 'Move the field to a separate class or remove it if not needed.',
                    'example_code': '''
class Order:
    def __init__(self):
        self.items = []
        self.discount_code = None  # Only used for premium orders
        self.special_instructions = None  # Rarely used
                    '''
                },
                {
                    'name': 'Message Chains',
                    'description': 'A client asks one object for another, then asks that object for another, forming a chain of calls.',
                    'severity': 'MEDIUM',
                    'refactoring_tip': 'Hide the delegation by adding methods to the intermediate objects.',
                    'example_code': '''
# Long chain of calls
department = company.get_department("IT")
manager = department.get_manager()
office = manager.get_office()
phone = office.get_phone()
phone.call()
                    '''
                },
                {
                    'name': 'Middle Man',
                    'description': 'A class that delegates most of its work to another class, serving mainly as a pass-through.',
                    'severity': 'LOW',
                    'refactoring_tip': 'Remove the middle man and let clients call the delegate directly.',
                    'example_code': '''
class MiddleMan:
    def __init__(self):
        self.real_worker = RealWorker()
    
    def do_work(self):  # Just passes through
        return self.real_worker.do_work()
                    '''
                },
                {
                    'name': 'Inappropriate Intimacy',
                    'description': 'Two classes that are too coupled, accessing each other\'s private parts excessively.',
                    'severity': 'HIGH',
                    'refactoring_tip': 'Move the common parts to a third class, or use change bidirectional association to unidirectional.',
                    'example_code': '''
class A:
    def __init__(self):
        self.b = B()
        self.secret = "secret"
    
    def access_b_secrets(self):
        return self.b.hidden_data  # Accessing B's private data

class B:
    def __init__(self):
        self.hidden_data = "hidden"
                    '''
                },
                {
                    'name': 'Alternative Classes with Different Interfaces',
                    'description': 'Two classes that do similar things but have different method names.',
                    'severity': 'MEDIUM',
                    'refactoring_tip': 'Rename methods to make them consistent, or create a common interface.',
                    'example_code': '''
class XMLParser:
    def parse_file(self, filename): pass

class JSONParser:
    def load_data(self, filepath): pass
# Both parse files but with different method names
                    '''
                },
                {
                    'name': 'Primitive Obsession',
                    'description': 'Using primitive data types instead of small objects for simple tasks.',
                    'severity': 'LOW',
                    'refactoring_tip': 'Replace primitives with small objects to make code more expressive.',
                    'example_code': '''
def process_order(customer_name, customer_email, customer_phone, 
                  order_items, order_total, order_date):
    # Too many primitive parameters
    pass
                    '''
                },
                {
                    'name': 'Switch Statements',
                    'description': 'Complex switch or if-else chains that check for type.',
                    'severity': 'MEDIUM',
                    'refactoring_tip': 'Replace conditional with polymorphism.',
                    'example_code': '''
def calculate_pay(employee_type, hours):
    if employee_type == "fulltime":
        return hours * 50
    elif employee_type == "parttime":
        return hours * 30
    elif employee_type == "contractor":
        return hours * 40
    # Growing switch statement
                    '''
                }
            ]
            
            for smell_data in default_smells:
                CodeSmellType.objects.get_or_create(
                    name=smell_data['name'],
                    defaults={
                        'description': smell_data['description'],
                        'severity': smell_data['severity'],
                        'refactoring_tip': smell_data['refactoring_tip'],
                        'example_code': smell_data['example_code']
                    }
                )
                
        except (OperationalError, ProgrammingError, ImportError):
            # Database not ready yet or models not available
            pass
        except Exception as e:
            # Log other errors but don't crash
            print(f"Error creating default smell types: {e}")
            pass