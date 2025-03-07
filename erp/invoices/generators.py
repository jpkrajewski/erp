from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from jinja2 import Template
from xhtml2pdf import pisa

from erp.models import Invoice

INVOICE_TEMPLATE_PATH = Path(__file__).parent / "invoice.html"

def generate_invoice(instance: Invoice):
    with open(INVOICE_TEMPLATE_PATH, "r") as f:
        template_html = f.read()

    # Create a Jinja2 Template object
    template = Template(template_html)

    # Render the template with the Invoice instance
    rendered_html = template.render(invoice=instance)

    # Convert the rendered HTML to PDF
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(rendered_html.encode('utf-8')), dest=pdf_file)

    if pisa_status.err:
        raise Exception("Error converting HTML to PDF")

    # Save the PDF and attach it to the Invoice model
    file_name = f"invoice_{instance.invoice_number}.pdf"
    instance.generated_pdf.save(file_name, ContentFile(pdf_file.getvalue()))
    instance.save()

    return rendered_html
