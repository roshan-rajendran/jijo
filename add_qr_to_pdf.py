import qrcode
from PyPDF2 import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
from PIL import Image

def generate_qr_code(data, size=200):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to RGB mode if necessary
    if qr_image.mode != 'RGB':
        qr_image = qr_image.convert('RGB')
    
    # Resize QR code
    qr_image = qr_image.resize((size, size))
    return qr_image

def add_qr_to_pdf(input_pdf_path, output_pdf_path, qr_data):
    # Generate QR code
    qr_image = generate_qr_code(qr_data, size=100)
    
    # Save QR code to a temporary file
    temp_qr_path = 'temp_qr.png'
    qr_image.save(temp_qr_path)
    
    # Read the existing PDF
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    
    # Get the first page
    page = reader.pages[0]
    
    # Create a new PDF with the QR code
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Add QR code to the right side after "INSTALLATION CERTIFICATE"
    # Coordinates are from bottom-left corner
    can.drawImage(temp_qr_path, 405, 610, width=100, height=100)
    can.save()
    
    # Move to the beginning of the buffer
    packet.seek(0)
    
    # Create a new PDF with the QR code
    new_pdf = PdfReader(packet)
    
    # Merge the QR code onto the existing page
    page.merge_page(new_pdf.pages[0])
    
    # Add the modified page
    writer.add_page(page)
    
    # Add remaining pages
    for page_num in range(1, len(reader.pages)):
        writer.add_page(reader.pages[page_num])
    
    # Write the modified PDF to a new file
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)
    
    # Clean up temporary file
    import os
    os.remove(temp_qr_path)

if __name__ == "__main__":
    input_pdf = "PRICOL _empty.pdf"
    output_pdf = "PRICOL_with_QR.pdf"
    qr_data = "https://example.com/verify"  # Replace with your actual verification URL or data
    
    try:
        add_qr_to_pdf(input_pdf, output_pdf, qr_data)
        print(f"Successfully created {output_pdf} with QR code")
    except Exception as e:
        print(f"An error occurred: {str(e)}") 