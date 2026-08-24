import os
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from PIL import Image as PILImage

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header rule & title
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 750, 558, 750)
        self.drawString(54, 755, "VIEW • Document OCR Suite")
        
        # Footer rule & page
        self.line(54, 45, 558, 45)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_text)
        self.drawString(54, 32, "Generated with VIEW CLI Tool")
        self.restoreState()

class PDFDocumentBuilder:
    def __init__(self, title: str = "Structured OCR Document", author: str = "VIEW CLI"):
        self.title = title
        self.author = author
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        # Palette: Clean modern tech theme (Slate / Cyan / Indigo)
        self.styles.add(ParagraphStyle(
            'DocTitle',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            'DocSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15
        ))

        self.styles.add(ParagraphStyle(
            'SectionHeading',
            parent=self.styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0284c7"),
            spaceBefore=12,
            spaceAfter=8,
            keepWithNext=True
        ))

        self.styles.add(ParagraphStyle(
            'SubSectionHeading',
            parent=self.styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        ))

        self.styles.add(ParagraphStyle(
            'BodyTextCustom',
            parent=self.styles['BodyText'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=6
        ))

        self.styles.add(ParagraphStyle(
            'BulletCustom',
            parent=self.styles['BodyText'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=4
        ))

        self.styles.add(ParagraphStyle(
            'CodeBlock',
            parent=self.styles['Code'],
            fontName='Courier',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
            backColor=colors.HexColor("#f1f5f9"),
            borderPadding=6,
            spaceBefore=6,
            spaceAfter=6
        ))

    def _format_text_to_flowables(self, text: str) -> List[Any]:
        flowables = []
        lines = text.split('\n')
        
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                flowables.append(Spacer(1, 4))
                continue
            
            # Detect Markdown / Formatting heuristics
            # 1. Heading 1 / Title (# or all uppercase short line)
            if line.startswith('# '):
                flowables.append(Paragraph(line[2:].strip(), self.styles['DocTitle']))
            elif line.startswith('## '):
                flowables.append(Paragraph(line[3:].strip(), self.styles['SectionHeading']))
            elif line.startswith('### '):
                flowables.append(Paragraph(line[4:].strip(), self.styles['SubSectionHeading']))
            elif line.isupper() and len(line) < 50 and not line.startswith(('HTTP', 'WWW')):
                flowables.append(Paragraph(line, self.styles['SectionHeading']))
            elif line.startswith(('-', '*', '•', '–')):
                bullet_content = line.lstrip('-*•– ').strip()
                flowables.append(Paragraph(f"• {bullet_content}", self.styles['BulletCustom']))
            elif re_match_numbered := re_numbered(line):
                flowables.append(Paragraph(line, self.styles['BulletCustom']))
            else:
                flowables.append(Paragraph(line, self.styles['BodyTextCustom']))
                
        return flowables

    def build_pdf(
        self,
        extracted_data: List[Dict[str, Any]],
        output_path: str,
        include_thumbnails: bool = True,
        theme_title: Optional[str] = None
    ) -> str:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=60,
            bottomMargin=54
        )
        
        story = []
        
        # Cover / Header Banner
        doc_title = theme_title or self.title
        story.append(Paragraph(doc_title, self.styles['DocTitle']))
        story.append(Paragraph(f"Structured OCR Extraction • {len(extracted_data)} Image Source(s)", self.styles['DocSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=15))
        
        for idx, item in enumerate(extracted_data):
            img_path = item.get("image_path", "")
            img_name = os.path.basename(img_path)
            full_text = item.get("full_text", "")
            engine = item.get("engine", "OCR")
            
            # Source Header Table / Banner
            source_info = f"<b>Source Image {idx + 1}:</b> {img_name} <i>(Engine: {engine})</i>"
            header_para = Paragraph(source_info, self.styles['SubSectionHeading'])
            
            table_data = [[header_para]]
            t = Table(table_data, colWidths=[504])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))
            
            # Thumbnail optional
            if include_thumbnails and os.path.exists(img_path):
                try:
                    with PILImage.open(img_path) as pimg:
                        w, h = pimg.size
                        max_w = 480
                        max_h = 160
                        scale = min(max_w / w, max_h / h, 1.0)
                        target_w, target_h = int(w * scale), int(h * scale)
                    
                    story.append(RLImage(img_path, width=target_w, height=target_h))
                    story.append(Spacer(1, 8))
                except Exception:
                    pass
            
            # Extracted Text Section
            story.append(Paragraph("<b>Extracted Structured Text:</b>", self.styles['SubSectionHeading']))
            text_flowables = self._format_text_to_flowables(full_text)
            story.extend(text_flowables)
            
            # Separator or Page break between documents
            if idx < len(extracted_data) - 1:
                story.append(Spacer(1, 15))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=15))
                
        doc.build(story, canvasmaker=NumberedCanvas)
        return output_path

def re_numbered(text: str) -> bool:
    import re
    return bool(re.match(r'^\d+[\.\)]\s+', text))
