"""
PDF reporter module.
Generates PDF format reports using reportlab.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class PDFReporter:
    """Generates PDF format reports using reportlab."""
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize the reporter.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        markdown_content: str = None,
        markdown_file: str = None,
        filename: str = None
    ) -> str:
        """
        Generate PDF report from Markdown content or file.
        
        Args:
            markdown_content: Markdown content as string
            markdown_file: Path to existing Markdown file
            filename: Optional custom filename
            
        Returns:
            Path to generated PDF file
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor, black, white
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
            from reportlab.pdfgen import canvas
        except ImportError as e:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install it with: pip install reportlab"
            ) from e
        
        # Get content
        if markdown_file:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
        elif markdown_content:
            content = markdown_content
        else:
            raise ValueError("Either markdown_content or markdown_file must be provided")
        
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"summary_{timestamp}.pdf"
        
        output_path = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for elements
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#0078D4'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=HexColor('#0078D4'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#106EBE'),
            spaceAfter=10,
            spaceBefore=10
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            spaceAfter=12
        )
        
        # Parse markdown and convert to PDF elements
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Title (# )
            if line.startswith('# '):
                text = line[2:].strip()
                elements.append(Paragraph(text, title_style))
                elements.append(Spacer(1, 0.2 * inch))
            
            # Heading 1 (## )
            elif line.startswith('## '):
                text = line[3:].strip()
                elements.append(Spacer(1, 0.2 * inch))
                elements.append(Paragraph(text, heading1_style))
            
            # Heading 2 (### )
            elif line.startswith('### '):
                text = line[4:].strip()
                elements.append(Spacer(1, 0.15 * inch))
                elements.append(Paragraph(text, heading2_style))
            
            # Table
            elif line.startswith('|'):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                i -= 1  # Back up one since we'll increment at the end
                
                # Parse table
                table_data = []
                for tline in table_lines:
                    # Skip separator lines (|---|---|)
                    if re.match(r'\|[\s\-:]+\|', tline):
                        continue
                    
                    # Split by | and clean up
                    cells = [cell.strip() for cell in tline.split('|')[1:-1]]
                    table_data.append(cells)
                
                if table_data:
                    # Create table
                    t = Table(table_data)
                    
                    # Style the table
                    table_style = TableStyle([
                        # Header row
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#0078D4')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        
                        # Data rows
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#F0F0F0'), white]),
                        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ])
                    
                    t.setStyle(table_style)
                    elements.append(t)
                    elements.append(Spacer(1, 0.2 * inch))
            
            # List items
            elif line.startswith('- ') or line.startswith('* '):
                text = line[2:].strip()
                # Handle bold (**text**)
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                # Handle code (`text`)
                text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
                
                bullet_style = ParagraphStyle(
                    'Bullet',
                    parent=body_style,
                    leftIndent=20,
                    bulletIndent=10
                )
                elements.append(Paragraph(f'• {text}', bullet_style))
            
            # Regular paragraph
            else:
                text = line
                # Handle bold (**text**)
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                # Handle code (`text`)
                text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
                
                elements.append(Paragraph(text, body_style))
            
            i += 1
        
        # Build PDF
        doc.build(elements)
        
        logger.info(f"PDF report generated: {output_path}")
        return str(output_path)
