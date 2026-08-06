"""
Advanced Model Training for Code Smell Detection
Trains and evaluates multiple ML models on the generated dataset
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Scikit-learn imports
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler, MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                           confusion_matrix, classification_report, roc_curve, auc,
                           precision_recall_curve, matthews_corrcoef, balanced_accuracy_score)
from sklearn.pipeline import Pipeline
import joblib


class CodeSmellModelTrainer:
    """
    Advanced model trainer for code smell detection
    Trains multiple models and selects the best one
    """
    
    def __init__(self, dataset_path, output_dir='trained_models', test_size=0.2, random_state=42):
        """
        Initialize the model trainer
        
        Args:
            dataset_path: Path to the dataset CSV or JSON file
            output_dir: Directory to save trained models and results
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
        """
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.test_size = test_size
        self.random_state = random_state
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'plots'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'models'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'reports'), exist_ok=True)
        
        # Load dataset
        print(f"📊 Loading dataset from {dataset_path}")
        self._load_dataset()
        
        # Prepare data
        self._prepare_data()
        
        # Define models and hyperparameters
        self._define_models()
        
    def _load_dataset(self):
        """Load dataset from file"""
        try:
            if self.dataset_path.endswith('.csv'):
                self.df = pd.read_csv(self.dataset_path)
            elif self.dataset_path.endswith('.json'):
                self.df = pd.read_json(self.dataset_path)
            else:
                raise ValueError(f"Unsupported file format: {self.dataset_path}")
            
            print(f"   Dataset shape: {self.df.shape}")
            print(f"   Columns: {list(self.df.columns)}")
            
            # Display basic statistics
            print(f"   Total samples: {len(self.df)}")
            print(f"   Features: {len(self.df.columns)}")
            
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            raise
    
    def _prepare_data(self):
        """Prepare data for training"""
        # Define columns to exclude (non-feature columns)
        self.exclude_cols = ['sample_id', 'language', 'language_name', 'smell_id', 
                             'smell_name', 'severity', 'code_file', 'code_preview', 
                             'generated_at', 'Unnamed: 0']
        
        # Get feature columns (numeric columns not in exclude list)
        self.feature_cols = []
        for col in self.df.columns:
            if col not in self.exclude_cols:
                if self.df[col].dtype in ['int64', 'float64']:
                    self.feature_cols.append(col)
        
        print(f"   Feature columns: {self.feature_cols}")
        
        # Check if we have the target column
        target_options = ['smell_id', 'smell_name', 'target', 'label', 'class']
        self.target_col = None
        
        for col in target_options:
            if col in self.df.columns:
                self.target_col = col
                break
        
        if self.target_col is None:
            # If no target column found, use the last column as target
            self.target_col = self.df.columns[-1]
            print(f"⚠️ No target column found. Using last column: {self.target_col}")
        else:
            print(f"   Target column: {self.target_col}")
        
        # Extract features and target
        self.X = self.df[self.feature_cols].copy()
        self.y = self.df[self.target_col].copy()
        
        # Handle missing values
        self.X = self.X.fillna(self.X.mean())
        
        # Encode target if it's categorical
        if self.y.dtype == 'object':
            self.label_encoder = LabelEncoder()
            self.y = self.label_encoder.fit_transform(self.y)
            self.class_names = self.label_encoder.classes_
        else:
            self.label_encoder = None
            self.class_names = np.unique(self.y)
        
        print(f"   Number of classes: {len(self.class_names)}")
        print(f"   Classes: {self.class_names}")
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=self.test_size, random_state=self.random_state, 
            stratify=self.y if len(self.class_names) > 1 else None
        )
        
        print(f"   Training samples: {len(self.X_train)}")
        print(f"   Testing samples: {len(self.X_test)}")
        
        # Scale features
        self.scaler = StandardScaler()
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)
    
    def _define_models(self):
        """Define machine learning models and hyperparameters"""
        self.models = {
            'Random Forest': {
                'model': RandomForestClassifier(random_state=self.random_state, n_jobs=-1),
                'params': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [10, 20, 30, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'max_features': ['sqrt', 'log2', None]
                },
                'description': 'Ensemble of decision trees with bagging'
            },
            'Gradient Boosting': {
                'model': GradientBoostingClassifier(random_state=self.random_state),
                'params': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [3, 5, 7],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'min_samples_split': [2, 5],
                    'min_samples_leaf': [1, 2],
                    'subsample': [0.8, 1.0]
                },
                'description': 'Sequential ensemble of weak learners'
            },
            'AdaBoost': {
                'model': AdaBoostClassifier(random_state=self.random_state),
                'params': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.5, 1.0, 1.5],
                    'algorithm': ['SAMME', 'SAMME.R']
                },
                'description': 'Adaptive boosting algorithm'
            },
            'Decision Tree': {
                'model': DecisionTreeClassifier(random_state=self.random_state),
                'params': {
                    'max_depth': [5, 10, 20, 30, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'criterion': ['gini', 'entropy'],
                    'splitter': ['best', 'random']
                },
                'description': 'Single decision tree classifier'
            },
            'Support Vector Machine': {
                'model': SVC(probability=True, random_state=self.random_state),
                'params': {
                    'C': [0.1, 1, 10, 100],
                    'gamma': ['scale', 'auto', 0.1, 0.01],
                    'kernel': ['rbf', 'linear', 'poly'],
                    'degree': [2, 3, 4]  # for poly kernel
                },
                'description': 'Support Vector Machine with RBF kernel'
            },
            'Neural Network': {
                'model': MLPClassifier(random_state=self.random_state, max_iter=1000),
                'params': {
                    'hidden_layer_sizes': [(50,), (100,), (50, 25), (100, 50)],
                    'activation': ['relu', 'tanh'],
                    'alpha': [0.0001, 0.001, 0.01],
                    'learning_rate': ['constant', 'adaptive'],
                    'solver': ['adam', 'sgd']
                },
                'description': 'Multi-layer Perceptron neural network'
            },
            'Logistic Regression': {
                'model': LogisticRegression(random_state=self.random_state, max_iter=1000),
                'params': {
                    'C': [0.1, 1, 10, 100],
                    'penalty': ['l2', 'none'],
                    'solver': ['lbfgs', 'newton-cg', 'sag'],
                    'multi_class': ['ovr', 'multinomial']
                },
                'description': 'Linear model for classification'
            },
            'K-Nearest Neighbors': {
                'model': KNeighborsClassifier(),
                'params': {
                    'n_neighbors': [3, 5, 7, 9, 11],
                    'weights': ['uniform', 'distance'],
                    'algorithm': ['auto', 'ball_tree', 'kd_tree'],
                    'p': [1, 2]  # 1: Manhattan, 2: Euclidean
                },
                'description': 'Instance-based learning'
            },
            'Naive Bayes': {
                'model': GaussianNB(),
                'params': {
                    'var_smoothing': [1e-9, 1e-8, 1e-7, 1e-6]
                },
                'description': 'Probabilistic classifier based on Bayes theorem'
            }
        }
    
    def train_all_models(self, perform_grid_search=True, cv_folds=5, save_plots=True):
        """
        Train all models and evaluate their performance
        
        Args:
            perform_grid_search: Whether to perform hyperparameter tuning
            cv_folds: Number of cross-validation folds
            save_plots: Whether to save evaluation plots
            
        Returns:
            Dictionary containing results for all models
        """
        print("\n" + "="*60)
        print("🚀 Starting Model Training")
        print("="*60)
        
        results = {}
        best_score = 0
        best_model_name = None
        best_model = None
        best_params = None
        
        for name, config in self.models.items():
            print(f"\n📈 Training {name}...")
            print(f"   {config['description']}")
            
            try:
                if perform_grid_search:
                    # Perform grid search for hyperparameter tuning
                    print(f"   Performing grid search with {cv_folds}-fold CV...")
                    
                    # Create grid search object
                    grid_search = GridSearchCV(
                        config['model'],
                        config['params'],
                        cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=self.random_state),
                        scoring='accuracy',
                        n_jobs=-1,
                        verbose=0
                    )
                    
                    # Fit grid search
                    grid_search.fit(self.X_train_scaled, self.y_train)
                    
                    # Get best model and parameters
                    model = grid_search.best_estimator_
                    best_params = grid_search.best_params_
                    cv_score = grid_search.best_score_
                    
                    print(f"   Best CV Score: {cv_score:.4f}")
                    print(f"   Best Params: {best_params}")
                    
                else:
                    # Train with default parameters
                    model = config['model']
                    model.fit(self.X_train_scaled, self.y_train)
                    best_params = None
                
                # Make predictions
                y_pred = model.predict(self.X_test_scaled)
                y_pred_proba = model.predict_proba(self.X_test_scaled) if hasattr(model, 'predict_proba') else None
                
                # Calculate metrics
                accuracy = accuracy_score(self.y_test, y_pred)
                balanced_acc = balanced_accuracy_score(self.y_test, y_pred)
                precision = precision_score(self.y_test, y_pred, average='weighted', zero_division=0)
                recall = recall_score(self.y_test, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(self.y_test, y_pred, average='weighted', zero_division=0)
                mcc = matthews_corrcoef(self.y_test, y_pred)
                
                # Cross-validation scores
                cv_scores = cross_val_score(
                    model, self.X_train_scaled, self.y_train, 
                    cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=self.random_state),
                    scoring='accuracy'
                )
                
                # Confusion matrix
                cm = confusion_matrix(self.y_test, y_pred)
                
                # Classification report
                report = classification_report(
                    self.y_test, y_pred, 
                    target_names=self.class_names if self.label_encoder else None,
                    output_dict=True,
                    zero_division=0
                )
                
                # Store results
                results[name] = {
                    'model': model,
                    'best_params': best_params,
                    'accuracy': accuracy * 100,
                    'balanced_accuracy': balanced_acc * 100,
                    'precision': precision * 100,
                    'recall': recall * 100,
                    'f1_score': f1 * 100,
                    'mcc': mcc,
                    'cv_scores': cv_scores.tolist(),
                    'cv_mean': cv_scores.mean() * 100,
                    'cv_std': cv_scores.std() * 100,
                    'confusion_matrix': cm.tolist(),
                    'classification_report': report,
                    'feature_importance': self._get_feature_importance(model)
                }
                
                print(f"   ✅ Test Accuracy: {accuracy*100:.2f}%")
                print(f"   ✅ F1 Score: {f1*100:.2f}%")
                print(f"   ✅ CV Mean: {cv_scores.mean()*100:.2f}% (±{cv_scores.std()*100:.2f})")
                
                # Track best model
                if accuracy > best_score:
                    best_score = accuracy
                    best_model_name = name
                    best_model = model
                    best_params = results[name]['best_params']
                
                # Save plots if requested
                if save_plots:
                    self._save_model_plots(name, model, y_pred, y_pred_proba, cm)
                
            except Exception as e:
                print(f"   ❌ Error training {name}: {e}")
                results[name] = {
                    'model': None,
                    'error': str(e),
                    'accuracy': 0,
                    'balanced_accuracy': 0,
                    'precision': 0,
                    'recall': 0,
                    'f1_score': 0,
                    'mcc': 0,
                    'cv_scores': [],
                    'cv_mean': 0,
                    'cv_std': 0
                }
        
        # Save best model
        if best_model is not None:
            self._save_best_model(best_model, best_model_name, best_params, results)
        
        # Save all results
        self._save_results(results, best_model_name)
        
        # Create comparison plots
        if save_plots:
            self._create_comparison_plots(results)
        
        print("\n" + "="*60)
        print(f"🏆 Best Model: {best_model_name} with Accuracy: {best_score*100:.2f}%")
        print("="*60)
        
        return {
            'best_model': best_model_name,
            'best_score': best_score * 100,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_feature_importance(self, model):
        """Extract feature importance from model if available"""
        importance = {}
        
        if hasattr(model, 'feature_importances_'):
            # For tree-based models
            for i, col in enumerate(self.feature_cols):
                importance[col] = float(model.feature_importances_[i])
        elif hasattr(model, 'coef_'):
            # For linear models
            if len(model.coef_.shape) > 1:
                # Multi-class: take mean absolute importance
                coef = np.mean(np.abs(model.coef_), axis=0)
            else:
                coef = np.abs(model.coef_)
            
            for i, col in enumerate(self.feature_cols):
                importance[col] = float(coef[i])
        
        return importance
    
    def _save_model_plots(self, name, model, y_pred, y_pred_proba, cm):
        """Save evaluation plots for a model"""
        try:
            # Confusion Matrix
            plt.figure(figsize=(10, 8))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                       xticklabels=self.class_names,
                       yticklabels=self.class_names)
            plt.title(f'Confusion Matrix - {name}')
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'plots', f'confusion_matrix_{name.lower().replace(" ", "_")}.png'), dpi=100)
            plt.close()
            
            # Feature Importance
            importance = self._get_feature_importance(model)
            if importance:
                plt.figure(figsize=(10, 6))
                features = list(importance.keys())
                values = list(importance.values())
                
                # Sort by importance
                sorted_idx = np.argsort(values)
                features = [features[i] for i in sorted_idx]
                values = [values[i] for i in sorted_idx]
                
                plt.barh(features, values, color='#4361ee')
                plt.title(f'Feature Importance - {name}')
                plt.xlabel('Importance')
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'plots', f'feature_importance_{name.lower().replace(" ", "_")}.png'), dpi=100)
                plt.close()
            
            # ROC Curves (for binary classification)
            if len(self.class_names) == 2 and y_pred_proba is not None:
                plt.figure(figsize=(8, 6))
                fpr, tpr, _ = roc_curve(self.y_test, y_pred_proba[:, 1])
                roc_auc = auc(fpr, tpr)
                
                plt.plot(fpr, tpr, color='#4361ee', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
                plt.plot([0, 1], [0, 1], color='gray', lw=2, linestyle='--', label='Random')
                plt.xlim([0.0, 1.0])
                plt.ylim([0.0, 1.05])
                plt.xlabel('False Positive Rate')
                plt.ylabel('True Positive Rate')
                plt.title(f'ROC Curve - {name}')
                plt.legend(loc="lower right")
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'plots', f'roc_curve_{name.lower().replace(" ", "_")}.png'), dpi=100)
                plt.close()
                
        except Exception as e:
            print(f"   ⚠️ Could not save plots for {name}: {e}")
    
    def _create_comparison_plots(self, results):
        """Create comparison plots for all models"""
        try:
            # Extract metrics
            model_names = []
            accuracies = []
            f1_scores = []
            cv_means = []
            
            for name, metrics in results.items():
                if metrics['model'] is not None:
                    model_names.append(name)
                    accuracies.append(metrics['accuracy'])
                    f1_scores.append(metrics['f1_score'])
                    cv_means.append(metrics['cv_mean'])
            
            # Accuracy Comparison
            plt.figure(figsize=(12, 6))
            x = np.arange(len(model_names))
            width = 0.25
            
            plt.bar(x - width, accuracies, width, label='Test Accuracy', color='#4361ee')
            plt.bar(x, f1_scores, width, label='F1 Score', color='#10b981')
            plt.bar(x + width, cv_means, width, label='CV Mean', color='#f59e0b')
            
            plt.xlabel('Models')
            plt.ylabel('Score (%)')
            plt.title('Model Performance Comparison')
            plt.xticks(x, model_names, rotation=45, ha='right')
            plt.legend()
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'plots', 'model_comparison.png'), dpi=100)
            plt.close()
            
            # Create results DataFrame
            results_df = pd.DataFrame({
                'Model': model_names,
                'Accuracy': accuracies,
                'F1 Score': f1_scores,
                'CV Mean': cv_means
            })
            results_df.to_csv(os.path.join(self.output_dir, 'reports', 'model_comparison.csv'), index=False)
            
        except Exception as e:
            print(f"⚠️ Could not create comparison plots: {e}")
    
    def _save_best_model(self, model, model_name, best_params, results):
        """Save the best model to disk"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save model
            model_filename = f'best_model_{model_name.lower().replace(" ", "_")}_{timestamp}.pkl'
            model_path = os.path.join(self.output_dir, 'models', model_filename)
            joblib.dump(model, model_path)
            
            # Save scaler
            scaler_filename = f'scaler_{timestamp}.pkl'
            scaler_path = os.path.join(self.output_dir, 'models', scaler_filename)
            joblib.dump(self.scaler, scaler_path)
            
            # Save label encoder if exists
            if self.label_encoder:
                encoder_filename = f'encoder_{timestamp}.pkl'
                encoder_path = os.path.join(self.output_dir, 'models', encoder_filename)
                joblib.dump(self.label_encoder, encoder_path)
            
            # Save model metadata
            metadata = {
                'model_name': model_name,
                'timestamp': timestamp,
                'accuracy': results[model_name]['accuracy'],
                'f1_score': results[model_name]['f1_score'],
                'precision': results[model_name]['precision'],
                'recall': results[model_name]['recall'],
                'mcc': results[model_name]['mcc'],
                'best_params': best_params,
                'features_used': self.feature_cols,
                'num_classes': len(self.class_names),
                'classes': self.class_names.tolist() if hasattr(self.class_names, 'tolist') else list(self.class_names),
                'model_file': model_filename,
                'scaler_file': scaler_filename,
                'encoder_file': 'encoder_{}.pkl'.format(timestamp) if self.label_encoder else None,
                'test_size': self.test_size,
                'random_state': self.random_state
            }
            
            metadata_path = os.path.join(self.output_dir, 'models', f'model_metadata_{timestamp}.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"\n💾 Best model saved to: {model_path}")
            print(f"📊 Metadata saved to: {metadata_path}")
            
        except Exception as e:
            print(f"❌ Error saving best model: {e}")
    
    def _save_results(self, results, best_model_name):
        """Save all results to a JSON file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Prepare results for JSON serialization
            serializable_results = {}
            for name, metrics in results.items():
                serializable_results[name] = {
                    'accuracy': metrics.get('accuracy', 0),
                    'balanced_accuracy': metrics.get('balanced_accuracy', 0),
                    'precision': metrics.get('precision', 0),
                    'recall': metrics.get('recall', 0),
                    'f1_score': metrics.get('f1_score', 0),
                    'mcc': metrics.get('mcc', 0),
                    'cv_mean': metrics.get('cv_mean', 0),
                    'cv_std': metrics.get('cv_std', 0),
                    'best_params': metrics.get('best_params', {}),
                    'feature_importance': metrics.get('feature_importance', {}),
                    'error': metrics.get('error', None)
                }
            
            summary = {
                'timestamp': timestamp,
                'best_model': best_model_name,
                'best_accuracy': results[best_model_name]['accuracy'] if best_model_name else 0,
                'dataset_info': {
                    'path': self.dataset_path,
                    'total_samples': len(self.df),
                    'features': self.feature_cols,
                    'num_classes': len(self.class_names),
                    'classes': self.class_names.tolist() if hasattr(self.class_names, 'tolist') else list(self.class_names),
                    'train_samples': len(self.X_train),
                    'test_samples': len(self.X_test)
                },
                'results': serializable_results
            }
            
            results_path = os.path.join(self.output_dir, 'reports', f'training_results_{timestamp}.json')
            with open(results_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"📊 Results saved to: {results_path}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def train_with_selected_features(self, feature_subset):
        """
        Train models using only a subset of features
        
        Args:
            feature_subset: List of feature names to use
        """
        print(f"\n🔍 Training with selected features: {feature_subset}")
        
        # Filter features
        valid_features = [f for f in feature_subset if f in self.feature_cols]
        
        if not valid_features:
            print("❌ No valid features selected")
            return None
        
        # Prepare data with selected features
        X_selected = self.X[valid_features].copy()
        X_selected = X_selected.fillna(X_selected.mean())
        
        # Split and scale
        X_train, X_test, y_train, y_test = train_test_split(
            X_selected, self.y, test_size=self.test_size, 
            random_state=self.random_state, stratify=self.y if len(self.class_names) > 1 else None
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train models
        results = {}
        for name, config in self.models.items():
            print(f"\n📈 Training {name} with selected features...")
            
            try:
                model = config['model']
                model.fit(X_train_scaled, y_train)
                
                y_pred = model.predict(X_test_scaled)
                
                accuracy = accuracy_score(y_test, y_pred)
                f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                
                print(f"   ✅ Accuracy: {accuracy*100:.2f}%")
                print(f"   ✅ F1 Score: {f1*100:.2f}%")
                
                results[name] = {
                    'model': model,
                    'accuracy': accuracy * 100,
                    'f1_score': f1 * 100,
                    'features_used': valid_features
                }
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return results
    
    def cross_validate_model(self, model_name, cv_folds=10):
        """
        Perform detailed cross-validation for a specific model
        
        Args:
            model_name: Name of the model to validate
            cv_folds: Number of cross-validation folds
        """
        if model_name not in self.models:
            print(f"❌ Model {model_name} not found")
            return None
        
        print(f"\n🔍 Performing {cv_folds}-fold cross-validation for {model_name}")
        
        config = self.models[model_name]
        model = config['model']
        
        # Perform cross-validation
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=self.random_state)
        
        # Multiple scoring metrics
        scoring = ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']
        
        cv_results = {}
        for score in scoring:
            scores = cross_val_score(model, self.X_train_scaled, self.y_train, cv=cv, scoring=score)
            cv_results[score] = {
                'scores': scores.tolist(),
                'mean': scores.mean() * 100,
                'std': scores.std() * 100
            }
        
        print(f"\n📊 Cross-validation Results:")
        for score, values in cv_results.items():
            print(f"   {score}: {values['mean']:.2f}% (±{values['std']:.2f})")
        
        return cv_results


# Command-line interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Train code smell detection models')
    parser.add_argument('dataset', help='Path to dataset file (CSV or JSON)')
    parser.add_argument('--output', '-o', default='trained_models', help='Output directory')
    parser.add_argument('--test-size', '-t', type=float, default=0.2, help='Test set size')
    parser.add_argument('--no-grid-search', action='store_true', help='Skip grid search')
    parser.add_argument('--cv-folds', type=int, default=5, help='Cross-validation folds')
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = CodeSmellModelTrainer(
        dataset_path=args.dataset,
        output_dir=args.output,
        test_size=args.test_size
    )
    
    # Train models
    results = trainer.train_all_models(
        perform_grid_search=not args.no_grid_search,
        cv_folds=args.cv_folds
    )
    
    print("\n✨ Training complete!")