"""
PDF Report Generator for Code Smell Detection Results
"""

import os
import sys
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib
matplotlib.use('Agg')  # Force non-interactive backend BEFORE importing pyplot
import matplotlib.pyplot as plt
import numpy as np
import io
import tempfile
import time
from django.conf import settings
import base64
import threading

# Ensure matplotlib uses non-interactive backend
plt.switch_backend('Agg')

class CodeSmellReportGenerator:
    """Generate PDF reports for code smell analysis"""
    
    def __init__(self, analysis_job):
        self.job = analysis_job
        self.results = analysis_job.results_json
        self.elements = []
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        self.temp_files = []  # Track temporary files for cleanup
        self._lock = threading.Lock()  # Add lock for thread safety
        
    def _create_custom_styles(self):
        """Create custom styles for the report"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4361ee'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#334155'),
            spaceBefore=15,
            spaceAfter=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#475569'),
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=colors.HexColor('#4361ee'),
            alignment=TA_CENTER,
            spaceAfter=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER,
            spaceBefore=0
        ))
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    # Wait a moment and retry if file is locked
                    for _ in range(3):
                        try:
                            os.unlink(temp_file)
                            break
                        except PermissionError:
                            time.sleep(0.1)
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file}: {e}")
    
    def generate_report(self, output_path=None):
        """Generate the complete PDF report"""
        try:
            if not output_path:
                # Create reports directory if not exists
                reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
                os.makedirs(reports_dir, exist_ok=True)
                
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(reports_dir, f'code_smell_report_{self.job.id}_{timestamp}.pdf')
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
                title=f'Code Smell Analysis Report - {self.job.name}'
            )
            
            # Build report content
            self._add_header()
            self._add_executive_summary()
            self._add_metrics_summary()
            self._add_smell_details()
            
            # Generate visualizations in a thread-safe manner
            with self._lock:
                self._add_visualizations()
            
            self._add_recommendations()
            
            # Build PDF
            doc.build(self.elements)
            
            # Clean up temporary files
            self._cleanup_temp_files()
            
            return output_path
            
        except Exception as e:
            # Clean up even if there's an error
            self._cleanup_temp_files()
            raise e
    
    def _add_header(self):
        """Add report header"""
        # Title
        self.elements.append(Paragraph(
            f"Code Smell Analysis Report",
            self.styles['CustomTitle']
        ))
        
        # Subtitle
        self.elements.append(Paragraph(
            f"<i>{self.job.name}</i>",
            self.styles['CustomHeading3']
        ))
        
        self.elements.append(Spacer(1, 20))
        
        # Report metadata
        metadata = [
            ["Report Generated:", datetime.now().strftime('%B %d, %Y at %H:%M')],
            ["Analysis Date:", self.job.created_at.strftime('%B %d, %Y at %H:%M')],
            ["Analysis Type:", self.job.get_analysis_type_display()],
            ["Files Analyzed:", str(self.job.file_count)],
            ["Language:", self.job.language.upper() if self.job.language else "Multiple"],
            ["Model Used:", self.job.model_used.name if self.job.model_used else "N/A"]
        ]
        
        t = Table(metadata, colWidths=[120, 300])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4361ee')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        self.elements.append(t)
        self.elements.append(Spacer(1, 30))
        
        # Horizontal line
        self.elements.append(self._draw_line())
        self.elements.append(Spacer(1, 20))
    
    def _add_executive_summary(self):
        """Add executive summary section"""
        self.elements.append(Paragraph(
            "Executive Summary",
            self.styles['CustomHeading2']
        ))
        
        total_smells = self.job.total_smells_found
        quality_score = self.results.get('overall_quality', 0)
        
        if quality_score >= 80:
            quality_text = "Excellent"
            quality_color = "#10b981"
        elif quality_score >= 60:
            quality_text = "Good"
            quality_color = "#f59e0b"
        else:
            quality_text = "Needs Improvement"
            quality_color = "#ef4444"
        
        summary_text = f"""
        This report presents the results of an automated code smell analysis performed on 
        <b>{self.job.file_count} file(s)</b>. The analysis identified <b>{total_smells} potential code smell(s)</b> 
        that may affect code maintainability and quality.
        
        The overall code quality score is <b><font color='{quality_color}'>{quality_score:.1f}% ({quality_text})</font></b>.
        """
        
        self.elements.append(Paragraph(summary_text, self.styles['CustomNormal']))
        self.elements.append(Spacer(1, 20))
    
    def _add_metrics_summary(self):
        """Add metrics summary section"""
        self.elements.append(Paragraph(
            "Code Metrics Overview",
            self.styles['CustomHeading2']
        ))
        
        # Create metrics table
        metrics_data = [['Metric', 'Value', 'Description']]
        
        metrics = self.results.get('metrics', {})
        metric_descriptions = {
            'loc': 'Lines of Code',
            'wmc': 'Weighted Methods per Class',
            'cbo': 'Coupling Between Objects',
            'tcc': 'Tight Class Cohesion',
            'lcom': 'Lack of Cohesion of Methods',
            'rfc': 'Response for Class',
            'complexity': 'Cyclomatic Complexity'
        }
        
        for metric, description in metric_descriptions.items():
            if metric in metrics:
                value = metrics[metric]
                if metric == 'tcc':
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                metrics_data.append([description, formatted_value, ''])
        
        t = Table(metrics_data, colWidths=[200, 100, 200])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        self.elements.append(t)
        self.elements.append(Spacer(1, 20))
    
    def _add_smell_details(self):
        """Add detailed smell analysis section"""
        self.elements.append(Paragraph(
            "Detected Code Smells",
            self.styles['CustomHeading2']
        ))
        
        # Get smells from results
        smells = self.results.get('smells', [])
        
        if not smells:
            self.elements.append(Paragraph(
                "No code smells detected in the analyzed code.",
                self.styles['CustomNormal']
            ))
        else:
            for i, smell in enumerate(smells, 1):
                self.elements.append(Paragraph(
                    f"{i}. {smell.get('smell_name', 'Unknown Smell')}",
                    self.styles['CustomHeading3']
                ))
                
                # Smell details table
                smell_data = [
                    ['Confidence:', f"{smell.get('confidence', 0):.1f}%"],
                    ['Severity:', smell.get('severity', 'MEDIUM')],
                    ['Location:', f"Lines {smell.get('line_start', '?')} - {smell.get('line_end', '?')}"],
                ]
                
                t = Table(smell_data, colWidths=[100, 400])
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4361ee')),
                    ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1e293b')),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                self.elements.append(t)
                self.elements.append(Spacer(1, 10))
                
                # Code snippet if available
                if smell.get('code_snippet'):
                    self.elements.append(Paragraph(
                        "<b>Code Snippet:</b>",
                        self.styles['CustomNormal']
                    ))
                    
                    # Format code snippet
                    code_text = smell['code_snippet'].replace('\n', '<br/>')
                    code_style = ParagraphStyle(
                        'CodeStyle',
                        parent=self.styles['Code'],
                        fontSize=9,
                        backColor=colors.HexColor('#f8fafc'),
                        borderPadding=10,
                        borderColor=colors.HexColor('#e2e8f0'),
                        borderWidth=1,
                        borderRadius=5
                    )
                    
                    self.elements.append(Paragraph(code_text, code_style))
                    self.elements.append(Spacer(1, 15))
    
    def _add_visualizations(self):
        """Add charts and visualizations"""
        self.elements.append(PageBreak())
        self.elements.append(Paragraph(
            "Visual Analysis",
            self.styles['CustomHeading2']
        ))
        
        # Create visualizations using matplotlib
        self._add_metrics_chart()
        self._add_smell_distribution_chart()
        self._add_quality_gauge()
    
    def _create_temp_image(self, plt_figure):
        """Create a temporary image file and return the path"""
        # Save figure to a bytes buffer first
        buf = io.BytesIO()
        plt_figure.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(buf.getvalue())
            tmp.flush()
            self.temp_files.append(tmp.name)
            return tmp.name
    
    def _add_metrics_chart(self):
        """Add metrics bar chart"""
        self.elements.append(Paragraph(
            "Metrics Comparison",
            self.styles['CustomHeading3']
        ))
        
        # Prepare data
        metrics = self.results.get('metrics', {})
        labels = []
        values = []
        
        metric_names = {
            'loc': 'Lines of Code',
            'wmc': 'Methods',
            'cbo': 'Coupling',
            'tcc': 'Cohesion',
            'complexity': 'Complexity'
        }
        
        for key, label in metric_names.items():
            if key in metrics:
                labels.append(label)
                value = metrics[key]
                if key == 'tcc':
                    values.append(value * 100)  # Convert to percentage
                else:
                    values.append(min(value, 100))  # Cap at 100 for visualization
        
        if values:
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(8, 4))
            bars = ax.bar(labels, values, color='#4361ee', alpha=0.8)
            ax.set_ylabel('Value')
            ax.set_title('Code Metrics Analysis')
            ax.set_xticklabels(labels, rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{value:.1f}', ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            
            # Save to temporary file
            img_path = self._create_temp_image(fig)
            plt.close(fig)
            
            # Add to PDF
            img = Image(img_path, width=400, height=200)
            self.elements.append(img)
            self.elements.append(Spacer(1, 20))
    
    def _add_smell_distribution_chart(self):
        """Add pie chart for smell distribution"""
        self.elements.append(Paragraph(
            "Smell Distribution",
            self.styles['CustomHeading3']
        ))
        
        # Count smells by type
        smells = self.results.get('smells', [])
        smell_counts = {}
        for smell in smells:
            name = smell.get('smell_name', 'Unknown')
            smell_counts[name] = smell_counts.get(name, 0) + 1
        
        if smell_counts:
            labels = list(smell_counts.keys())
            values = list(smell_counts.values())
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(6, 6))
            colors_list = ['#4361ee', '#f72585', '#4cc9f0', '#f8961e', '#4895ef', '#10b981', '#8b5cf6']
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=colors_list[:len(labels)])
            ax.set_title('Code Smell Distribution')
            ax.axis('equal')
            
            plt.tight_layout()
            
            # Save to temporary file
            img_path = self._create_temp_image(fig)
            plt.close(fig)
            
            # Add to PDF
            img = Image(img_path, width=300, height=300)
            self.elements.append(img)
            self.elements.append(Spacer(1, 20))
    
    def _add_quality_gauge(self):
        """Add quality gauge chart"""
        self.elements.append(Paragraph(
            "Quality Score",
            self.styles['CustomHeading3']
        ))
        
        quality_score = self.results.get('overall_quality', 0)
        
        # Create gauge chart
        fig, ax = plt.subplots(figsize=(6, 3))
        
        # Create a gauge-like bar
        colors = ['#ef4444', '#f59e0b', '#10b981']
        ax.barh([0], [100], color='#e2e8f0', height=0.5)
        ax.barh([0], [quality_score], 
                color=colors[2] if quality_score > 60 else colors[1] if quality_score > 30 else colors[0], 
                height=0.5)
        
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.5, 0.5)
        ax.set_yticks([])
        ax.set_xlabel('Quality Score (%)')
        ax.set_title(f'Overall Quality Score: {quality_score:.1f}%')
        
        # Add markers at 33% and 66%
        ax.axvline(x=33, color='#94a3b8', linestyle='--', alpha=0.5)
        ax.axvline(x=66, color='#94a3b8', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        # Save to temporary file
        img_path = self._create_temp_image(fig)
        plt.close(fig)
        
        # Add to PDF
        img = Image(img_path, width=400, height=150)
        self.elements.append(img)
        self.elements.append(Spacer(1, 20))
    
    def _add_recommendations(self):
        """Add refactoring recommendations"""
        self.elements.append(PageBreak())
        self.elements.append(Paragraph(
            "Refactoring Recommendations",
            self.styles['CustomHeading2']
        ))
        
        recommendations = {
            'Long Method': """
            • Extract smaller methods from the long method
            • Each method should have a single responsibility
            • Look for repeated code blocks that can be extracted
            • Use meaningful method names that describe the functionality
            """,
            'Large Class': """
            • Split the class into smaller, focused classes
            • Identify groups of related methods and fields
            • Use composition instead of inheritance where appropriate
            • Consider using design patterns like Strategy or State
            """,
            'Feature Envy': """
            • Move the method to the class it envies
            • Consider if the data and behavior belong together
            • Use the "Tell, Don't Ask" principle
            • Look for methods that use more features of other classes
            """,
            'God Class': """
            • Break down the class into multiple cohesive classes
            • Identify distinct responsibilities and separate them
            • Use facade pattern to simplify complex interfaces
            • Consider dependency injection for better separation
            """,
            'Data Class': """
            • Add behavior to the data class
            • Move methods that operate on the data into the class
            • Encapsulate fields and provide meaningful methods
            • Consider if the class should be a value object
            """,
            'Complex Method': """
            • Reduce cyclomatic complexity by extracting conditions
            • Use polymorphism instead of switch statements
            • Break nested conditions into guard clauses
            • Consider using the Strategy pattern
            """
        }
        
        smells = self.results.get('smells', [])
        added_recommendations = set()
        
        for smell in smells:
            smell_name = smell.get('smell_name', '')
            for key in recommendations:
                if key.lower() in smell_name.lower() and key not in added_recommendations:
                    self.elements.append(Paragraph(
                        f"<b>For {smell_name}:</b>",
                        self.styles['CustomHeading3']
                    ))
                    
                    self.elements.append(Paragraph(
                        recommendations[key],
                        self.styles['CustomNormal']
                    ))
                    
                    self.elements.append(Spacer(1, 15))
                    added_recommendations.add(key)
        
        if not added_recommendations:
            self.elements.append(Paragraph(
                "No specific recommendations - the code appears to be well-structured.",
                self.styles['CustomNormal']
            ))
    
    def _draw_line(self):
        """Draw a horizontal line"""
        from reportlab.platypus.flowables import HRFlowable
        return HRFlowable(
            width="100%",
            thickness=1,
            lineCap='round',
            color=colors.HexColor('#e2e8f0'),
            spaceBefore=0,
            spaceAfter=0
        )


def generate_report(analysis_job):
    """Convenience function to generate report"""
    generator = CodeSmellReportGenerator(analysis_job)
    return generator.generate_report()