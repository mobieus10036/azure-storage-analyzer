"""
PDF reporter module.
Generates visually appealing PDF format reports using reportlab.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re
from reportlab.lib.colors import HexColor, white, black, Color

logger = logging.getLogger(__name__)


class PDFReporter:
    """Generates professional, visually appealing PDF format reports using reportlab."""
    
    # Color scheme - Modern Azure-inspired palette
    COLORS = {
        'primary': '#0078D4',      # Azure blue
        'primary_dark': '#106EBE',  # Darker blue
        'success': '#107C10',       # Green
        'warning': '#FFB900',       # Yellow/Orange
        'danger': '#D83B01',        # Red
        'info': '#00BCF2',          # Light blue
        'gray_light': '#F3F2F1',    # Light gray
        'gray_medium': '#EDEBE9',   # Medium gray
        'gray_dark': '#605E5C',     # Dark gray
        'text': '#323130',          # Almost black
        'white': '#FFFFFF',
    }
    
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
        Generate professional PDF report from Markdown content or file.
        
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
            from reportlab.lib.units import inch, cm
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, 
                                           TableStyle, PageBreak, KeepTogether, Frame, 
                                           PageTemplate)
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
            from reportlab.pdfgen import canvas as pdfcanvas
            from reportlab.graphics.shapes import Drawing, Rect, Circle
            from reportlab.graphics import renderPDF
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
        
        # Create PDF document with custom page template
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch,
            title="Azure Storage Assessment Report",
            author="Azure Storage Assessment Toolkit"
        )
        
        # Container for elements
        elements = []
        
        # Define custom styles
        styles = self._create_custom_styles()
        
        # Add cover page
        elements.extend(self._create_cover_page(content, styles))
        elements.append(PageBreak())
        
        # Parse and add content
        elements.extend(self._parse_markdown_to_elements(content, styles))
        
        # Build PDF with custom page template
        def header_footer(canvas, doc):
            """Add header and footer to each page."""
            canvas.saveState()
            
            # Header - only on non-cover pages
            if canvas.getPageNumber() > 1:
                canvas.setStrokeColor(HexColor(self.COLORS['primary']))
                canvas.setLineWidth(2)
                canvas.line(0.75*inch, letter[1] - 0.6*inch, 
                           letter[0] - 0.75*inch, letter[1] - 0.6*inch)
            
            # Footer
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(HexColor(self.COLORS['gray_dark']))
            
            # Page number
            page_num = canvas.getPageNumber()
            if page_num > 1:  # Skip page number on cover
                text = f"Page {page_num - 1}"
                canvas.drawRightString(letter[0] - 0.75*inch, 0.5*inch, text)
            
            # Timestamp
            timestamp = datetime.now().strftime("%B %d, %Y %I:%M %p")
            canvas.drawString(0.75*inch, 0.5*inch, f"Generated: {timestamp}")
            
            # Tool name
            canvas.drawCentredString(letter[0]/2, 0.5*inch, 
                                    "Azure Storage Assessment Toolkit v1.0.0")
            
            canvas.restoreState()
        
        # Build PDF
        doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
        
        logger.info(f"PDF report generated: {output_path}")
        return str(output_path)
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the PDF."""
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
        from reportlab.lib.units import inch
        
        styles = getSampleStyleSheet()
        
        # Cover page title
        styles.add(ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontSize=32,
            textColor=HexColor(self.COLORS['primary']),
            spaceAfter=20,
            spaceBefore=40,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Cover subtitle
        styles.add(ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=HexColor(self.COLORS['gray_dark']),
            spaceAfter=40,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section title with colored background
        styles.add(ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=white,
            spaceAfter=15,
            spaceBefore=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            backColor=HexColor(self.COLORS['primary']),
            leftIndent=10,
            rightIndent=10,
            borderPadding=(8, 8, 8, 8)
        ))
        
        # Subsection heading
        styles.add(ParagraphStyle(
            'SubsectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor(self.COLORS['primary_dark']),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=HexColor(self.COLORS['primary']),
            borderPadding=0,
            leftIndent=5,
            borderLeftWidth=3,
            borderLeftColor=HexColor(self.COLORS['primary'])
        ))
        
        # Metric heading (for ### )
        styles.add(ParagraphStyle(
            'MetricHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=HexColor(self.COLORS['primary_dark']),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=HexColor(self.COLORS['text']),
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Bullet list
        styles.add(ParagraphStyle(
            'BulletList',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=HexColor(self.COLORS['text']),
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        # Key-value pairs (for summary data)
        styles.add(ParagraphStyle(
            'KeyValue',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor(self.COLORS['text']),
            spaceAfter=8,
            fontName='Helvetica'
        ))
        
        return styles
        
    def _create_cover_page(self, content: str, styles: dict) -> List:
        """Create an attractive cover page."""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import inch
        from reportlab.graphics.shapes import Drawing, Rect
        
        elements = []
        
        # Extract title from content (first # line)
        title = "Azure Storage Assessment Report"
        for line in content.split('\n'):
            if line.strip().startswith('# '):
                title = line.strip()[2:]
                break
        
        # Add top spacer
        elements.append(Spacer(1, 1.5*inch))
        
        # Create decorative header bar
        d = Drawing(6.5*inch, 0.3*inch)
        d.add(Rect(0, 0, 6.5*inch, 0.3*inch, 
                  fillColor=HexColor(self.COLORS['primary']), 
                  strokeColor=None))
        elements.append(d)
        elements.append(Spacer(1, 0.3*inch))
        
        # Title
        elements.append(Paragraph(title, styles['CoverTitle']))
        
        # Subtitle
        timestamp = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"Assessment Date: {timestamp}", styles['CoverSubtitle']))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Create summary box with key metrics
        summary_data = self._extract_summary_metrics(content)
        if summary_data:
            summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor(self.COLORS['gray_light'])),
                ('TEXTCOLOR', (0, 0), (0, -1), HexColor(self.COLORS['primary_dark'])),
                ('TEXTCOLOR', (1, 0), (1, -1), HexColor(self.COLORS['text'])),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('BOX', (0, 0), (-1, -1), 2, HexColor(self.COLORS['primary'])),
            ]))
            elements.append(summary_table)
        
        elements.append(Spacer(1, 1*inch))
        
        # Tool info
        tool_info = Paragraph(
            "<b>Generated by:</b> Azure Storage Assessment Toolkit v1.0.0<br/>"
            "<b>Purpose:</b> Cost optimization, security, and governance assessment",
            styles['CoverSubtitle']
        )
        elements.append(tool_info)
        
        return elements
    
    def _extract_summary_metrics(self, content: str) -> List[List[str]]:
        """Extract key metrics for cover page summary."""
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.colors import HexColor
        
        metrics = []
        
        # Look for common metrics in the content
        patterns = {
            'Storage Accounts': r'(\d+)\s+storage accounts?',
            'Total Capacity': r'Total capacity:\s*([\d.,]+\s*[GT]B)',
            'Estimated Cost': r'Estimated monthly cost:\s*\$?([\d.,]+)',
            'Subscriptions': r'(\d+)\s+subscriptions?',
        }
        
        for label, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1)
                metrics.append([label, value])
        
        return metrics if metrics else None
    
    def _parse_markdown_to_elements(self, content: str, styles: dict) -> List:
        """Parse markdown content and convert to PDF elements with enhanced styling."""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether
        from reportlab.lib.units import inch
        
        elements = []
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Title (# ) - skip on content pages as it's on cover
            if line.startswith('# '):
                i += 1
                continue
            
            # Section (## )
            elif line.startswith('## '):
                text = line[3:].strip()
                # Add visual section divider
                elements.append(Spacer(1, 0.3*inch))
                elements.append(Paragraph(text, styles['SectionTitle']))
                elements.append(Spacer(1, 0.1*inch))
            
            # Subsection (### )
            elif line.startswith('### '):
                text = line[4:].strip()
                elements.append(Spacer(1, 0.15*inch))
                elements.append(Paragraph(text, styles['SubsectionHeading']))
                elements.append(Spacer(1, 0.05*inch))
            
            # Table
            elif line.startswith('|'):
                table_elements = self._create_styled_table(lines, i)
                if table_elements:
                    elements.extend(table_elements)
                    # Skip past table lines
                    while i < len(lines) and lines[i].strip().startswith('|'):
                        i += 1
                    continue
            
            # List items
            elif line.startswith('- ') or line.startswith('* '):
                text = line[2:].strip()
                text = self._format_inline_markdown(text)
                
                # Color-code based on keywords
                bullet_color = self.COLORS['primary']
                if any(word in text.lower() for word in ['high', 'critical', 'error']):
                    bullet_color = self.COLORS['danger']
                elif any(word in text.lower() for word in ['warning', 'medium']):
                    bullet_color = self.COLORS['warning']
                elif any(word in text.lower() for word in ['success', 'compliant', 'good']):
                    bullet_color = self.COLORS['success']
                
                bullet = f'<font color="{bullet_color}">●</font> {text}'
                elements.append(Paragraph(bullet, styles['BulletList']))
            
            # Regular paragraph
            else:
                text = self._format_inline_markdown(line)
                elements.append(Paragraph(text, styles['CustomBody']))
            
            i += 1
        
        return elements
    
    def _create_styled_table(self, lines: List[str], start_idx: int) -> List:
        """Create a beautifully styled table from markdown table lines."""
        from reportlab.platypus import Table, TableStyle, Spacer
        from reportlab.lib.units import inch
        
        table_lines = []
        i = start_idx
        
        # Collect all table lines
        while i < len(lines) and lines[i].strip().startswith('|'):
            table_lines.append(lines[i].strip())
            i += 1
        
        # Parse table
        table_data = []
        is_header = True
        
        for tline in table_lines:
            # Skip separator lines (|---|---|)
            if re.match(r'\|[\s\-:]+\|', tline):
                is_header = False
                continue
            
            # Split by | and clean up
            cells = [cell.strip() for cell in tline.split('|')[1:-1]]
            table_data.append(cells)
        
        if not table_data:
            return None
        
        # Create table with auto-width
        table = Table(table_data, repeatRows=1)
        
        # Enhanced table styling
        style_commands = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(self.COLORS['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor(self.COLORS['gray_light'])]),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            
            # Borders
            ('BOX', (0, 0), (-1, -1), 1.5, HexColor(self.COLORS['primary'])),
            ('LINEBELOW', (0, 0), (-1, 0), 2, HexColor(self.COLORS['primary_dark'])),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, HexColor(self.COLORS['gray_medium'])),
        ]
        
        table.setStyle(TableStyle(style_commands))
        
        return [table, Spacer(1, 0.2 * inch)]
    
    def _format_inline_markdown(self, text: str) -> str:
        """Format inline markdown (bold, code, etc.) to HTML for reportlab."""
        # Bold (**text**)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Code (`text`)
        text = re.sub(r'`(.*?)`', r'<font name="Courier" color="#D83B01">\1</font>', text)
        
        # Links [text](url) - just show text
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'<i>\1</i>', text)
        
        return text
