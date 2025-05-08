from flask import Flask, render_template, request, send_file
import json
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io
from datetime import datetime
from add_qr_to_pdf import add_qr_to_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'generated_pdfs'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def create_qr_data(form_data):
    """Create formatted QR code data string"""
    return (f"Mfg by: Pricol Ltd., "
            f"Cert No: {form_data['certificate_no']}, "
            f"Dt: {form_data['dealer_invoice_date']}, "
            f"Veh Reg. No:{form_data['vehicle_reg_no']} "
            f"Chas. No: {form_data['chassis_no']}, "
            f"Eng. No:{form_data['engine_no']}, "
            f"SLD ECU No: {form_data['sld_ecu_no']}, "
            f"Speed: 80")

def fill_pdf_form(input_pdf_path, output_pdf_path, form_data):
    # Create a new PDF with form data
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Set consistent font and size for all text
    can.setFont("Helvetica", 10)
    
    # Start position - Base positions
    x1 = 1 * inch + 100  # Base left position
    x2 = 4.5 * inch + 100  # Base right position
    y = 500  # Base starting y position
    
    # Add "Customer Copy" text
    can.setFont("Helvetica", 10)  # Set font for the label
    can.drawString(x1 + 300, y + 128, "Department Copy")  # Adjust position as needed
    
    # Reset font for other text
    can.setFont("Helvetica", 10)
    
    # Certificate Details - Move right by 10px and down by 5px
    can.drawString(x1 + 10, y - 9, form_data['certificate_no'])
    can.drawString(x2 + 30, y - 385, form_data['test_report_no'])
    y -= 20
    can.drawString(x1 + 280, y - 390, form_data['tac_no'])
    
    # Dealer Information - Move right by 10px and up by 5px
    y -= 30
    can.drawString(x1 + 10, y + 10, form_data['dealer_name'].split('&')[0] + '&')  # First part
    y -= 15  # Move down for the next line
    can.drawString(x1 + 10, y + 10, form_data['dealer_name'].split('&')[1].strip())  # Second part
    can.drawString(x2 - 240, y - 11, form_data['dealer_location'])
    y -= 20
    can.drawString(x1 + 10, y - 12, form_data['dealer_invoice_no'])
    can.drawString(x2 + 25, y - 12, form_data['dealer_invoice_date'])
    
    # Customer & Fitment Center Details
    y -= 100
    # Split address into multiple lines if needed
    customer_details = form_data['customer_details'].split('\n')
    for line in customer_details:
        can.drawString(x1 - 100, y + 25, line)  # Moved left by 100px and up by 25px
        y -= 10
    
    y -= 10
    fitment_details = form_data['fitment_center_details'].split('\n')
    for line in fitment_details:
        can.drawString(x1 + 100, y + 100, line)
        y -= 15
    
    # Vehicle Details
    y -= 20
    can.drawString(x1 + 8, y + 50, form_data['vehicle_make_model'])
    can.drawString(x1 + 8, y-20, form_data['chassis_no'])
    can.drawString(x1 + 10, y + 4, form_data['engine_no'])  # Moved down by 30px and right by 10px
    y -= 20
    can.drawString(x1 + 10, y + 40, form_data['vehicle_reg_no'])
    can.drawString(x2, y - 20, form_data['vehicle_reg_date'])
    y -= 20
    can.drawString(x1 + 280, y + 350, form_data['rto_location'])
    
    # SLD Details
    y -= 30
    sld_model_lines = form_data['sld_model'].split(' / ')  # Split the SLD model into parts
    for line in sld_model_lines:
        can.drawString(x1 + 255, y + 120, line)  # Draw each line
        y -= 15  # Move down for the next line
    
    can.drawString(x2 + 30, y + 105, form_data['sld_ecu_no'])
    y -= 20
    can.drawString(x1 + 280, y + 430, form_data['sld_motor_unit'])
    y -= 20
    can.drawString(x1 + 278, y + 130, form_data['speed_sensor_type'])  # Moved right by 3px
    can.drawString(x2 - 24, y - 20, form_data['roto_seal_no'])
    
    # Installation & Renewal Dates
    y -= 30
    can.drawString(x1 + 280, y + 515, form_data['installation_date'])
    can.drawString(x2 + 30, y + 495, form_data['sld_renewal_date'])
    
    # Add images to the PDF
    if form_data['image1_path']:
        print(f"Adding image1: {form_data['image1_path']}")  # Debug statement
        can.drawImage(form_data['image1_path'], x1 + 312, y + 340, width=1 * inch, height=.7 * inch)  # Adjust size and position as needed
    else:
        print("Image1 path is empty or invalid.")  # Debug statement

    if form_data['image2_path']:
        print(f"Adding image2: {form_data['image2_path']}")  # Debug statement
        can.drawImage(form_data['image2_path'], x1 + 1.5 * inch + 208, y + 280, width=1 * inch, height=.7 * inch)  # Adjust size and position as needed
    else:
        print("Image2 path is empty or invalid.")  # Debug statement
    
    can.save()
    
    # Move to the beginning of the buffer
    packet.seek(0)
    
    # Create a new PDF with the text
    new_pdf = PdfReader(packet)
    
    # Read the existing PDF
    existing_pdf = PdfReader(input_pdf_path)
    output = PdfWriter()
    
    # Add the text to the existing page
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)
    
    # Write the output PDF
    with open(output_pdf_path, 'wb') as output_file:
        output.write(output_file)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("Form submitted.")  # Debug statement
        print(f"Request files: {request.files}")  # Debug statement
        try:
            # Use the actual form data from the user
            form_data = {
                'certificate_no': request.form['certificate_no'],
                'test_report_no': request.form['test_report_no'],
                'tac_no': request.form['tac_no'],
                'dealer_name': request.form['dealer_name'],
                'dealer_location': request.form['dealer_location'],
                'dealer_invoice_no': request.form['dealer_invoice_no'],
                'dealer_invoice_date': request.form['dealer_invoice_date'],
                'customer_details': request.form['customer_details'],
                'fitment_center_details': request.form['fitment_center_details'],
                'vehicle_make_model': request.form['vehicle_make_model'],
                'chassis_no': request.form['chassis_no'],
                'engine_no': request.form['engine_no'],
                'vehicle_reg_no': request.form['vehicle_reg_no'],
                'vehicle_reg_date': '',
                'rto_location': request.form['rto_location'],
                'sld_model': request.form['sld_model'],
                'sld_ecu_no': request.form['sld_ecu_no'],
                'sld_motor_unit': request.form['sld_motor_unit'],
                'speed_sensor_type': request.form['speed_sensor_type'],
                'roto_seal_no': request.form['roto_seal_no'],
                'installation_date': request.form['installation_date'],
                'sld_renewal_date': request.form['sld_renewal_date'],
                'image1_path': '',  # Handle image paths separately
                'image2_path': '',  # Handle image paths separately
            }
            
            # Handle image uploads
            if 'image1' in request.files:
                image1 = request.files['image1']
                print(f"Image1 filename: {image1.filename}")  # Debug statement
                if image1 and image1.filename:  # Check if a file was uploaded
                    image1_path = os.path.join(app.config['UPLOAD_FOLDER'], image1.filename)
                    image1.save(image1_path)
                    form_data['image1_path'] = image1_path
                    print(f"Image1 saved at: {image1_path}")  # Debug statement
                else:
                    print("No file selected for Image1 or filename is empty.")  # Debug statement
            
            if 'image2' in request.files:
                image2 = request.files['image2']
                print(f"Image2 filename: {image2.filename}")  # Debug statement
                if image2 and image2.filename:  # Check if a file was uploaded
                    image2_path = os.path.join(app.config['UPLOAD_FOLDER'], image2.filename)
                    image2.save(image2_path)
                    form_data['image2_path'] = image2_path
                    print(f"Image2 saved at: {image2_path}")  # Debug statement
                else:
                    print("No file selected for Image2 or filename is empty.")  # Debug statement
            
            # Generate output filename
            output_filename = f"certificate_{form_data['certificate_no']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            # First fill the PDF form
            fill_pdf_form("PRICOL _empty.pdf", output_path, form_data)
            
            # Then add QR code to the filled PDF
            temp_path = output_path + ".temp.pdf"
            os.rename(output_path, temp_path)
            
            # Create formatted QR code data
            qr_data = create_qr_data(form_data)
            
            # Add QR code to the filled PDF
            add_qr_to_pdf(temp_path, output_path, qr_data)
            
            # Clean up temporary file
            os.remove(temp_path)
            
            # Send the file to user
            return send_file(output_path, as_attachment=True)
            
        except Exception as e:
            return render_template('index.html', message=str(e), success=False)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 