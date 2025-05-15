from flask import Flask, render_template, request, send_file
import json
import os
import webbrowser
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
import io
from datetime import datetime
from add_qr_to_pdf import add_qr_to_pdf
import uuid
import sys
import subprocess
import logging

# Suppress all stdout and stderr
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Define the allowed hardware ID (e.g., MAC address)
ALLOWED_HARDWARE_ID = "f0-b6-1e-99-90-f8"  # Replace with your computer's full MAC address

def get_hardware_id():
    """Retrieve the MAC address of the current computer."""
    try:
        # Use the 'getmac' command to fetch the MAC address
        result = subprocess.check_output("getmac", shell=True, text=True)
        mac_addresses = [line.split()[0] for line in result.splitlines() if "-" in line]
        if mac_addresses:
            return mac_addresses[0].lower()  # Return the first valid MAC address
        else:
            raise ValueError("No valid MAC address found.")
    except Exception as e:
        print(f"Error retrieving hardware ID: {e}")
        return None

# Check if the application is running on the allowed computer
current_hardware_id = get_hardware_id()
if current_hardware_id != ALLOWED_HARDWARE_ID:
    print("This application is not authorized to run on this computer.")
    sys.exit(1)

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
    can.drawString( 460,  630, "Dealer Copy")  # Adjust position as needed
    
    # Reset font for other text
    can.setFont("Helvetica", 10)
    
    # Certificate Details - Move right by 10px and down by 5px
    can.drawString(180, 490, form_data['certificate_no'])
    can.drawString( 430, 115, form_data['test_report_no'])
    y -= 20
    can.drawString( 450, 92, form_data['tac_no'])
    
    # Dealer Information - Move right by 10px and up by 5px
    y -= 30
    can.drawString(180,  460, form_data['dealer_name'].split('&')[0] + '&')  # First part
    y -= 15  # Move down for the next line
    can.drawString(180,  450, form_data['dealer_name'].split('&')[1].strip())  # Second part
    can.drawString(180,  425, form_data['dealer_location'])
    y -= 20
    can.drawString(180,  400, form_data['dealer_invoice_no'])
    can.drawString(450,  400, form_data['dealer_invoice_date'])
    
    # Customer & Fitment Center Details
    y -= 100
    # Split address into multiple lines if needed
    customer_details = form_data['customer_details'].split('\n')
    z=350
    z1=350
    for line in customer_details:
        clean_line = line.strip()
        can.drawString( 100, z, clean_line)  # Moved left by 100px and up by 25px
        z-=10
    y -= 10
    fitment_details = form_data['fitment_center_details'].split('\n')
    for line in fitment_details:
        clean_line = line.strip()
        can.drawString( 280, z1, clean_line)
        z1-=15
    
    # Vehicle Details
    y -= 20
    can.drawString(180,  183, form_data['vehicle_make_model'])
    can.drawString( 180,115, form_data['chassis_no'])
    can.drawString( 177,136, form_data['engine_no'])  # Moved down by 30px and right by 10px
    y -= 20
    can.drawString(180, 155, form_data['vehicle_reg_no'])
    can.drawString(0, -20, form_data['vehicle_reg_date'])
    y -= 20
    can.drawString( 450,  420, form_data['rto_location'])
    
    # SLD Details
    y -= 30
    sld_model_lines = form_data['sld_model'].split(' / ')  # Split the SLD model into parts
    for line in sld_model_lines:
        can.drawString(400,  185, line)  # Draw each line
        y -= 15  # Move down for the next line
    
    can.drawString( 450,  155, form_data['sld_ecu_no'])
    y -= 20
    can.drawString( 450, 446, form_data['sld_motor_unit'])
    y -= 20
    can.drawString( 450,  139, form_data['speed_sensor_type'])  # Moved right by 3px
    can.drawString( 180,  92, form_data['roto_seal_no'])
    
    # Installation & Renewal Dates
    y -= 30
    can.drawString( 450,  490, form_data['installation_date'])
    can.drawString( 450,  470, form_data['sld_renewal_date'])
    
    # Add images to the PDF
    if form_data['image1_path']:
        can.drawImage(form_data['image1_path'],  470, 300, width=1 * inch, height=.9 * inch)  # Adjust size and position as needed
    else:
        print("Image1 path is empty or invalid.")  # Debug statement

    if form_data['image2_path']:
        can.drawImage(form_data['image2_path'],  470 ,  230, width=1 * inch, height=.9 * inch)  # Adjust size and position as needed
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

def append_pdf(original_pdf_path, pdf_to_append_path, output_pdf_path, installation_date):
    """Append one PDF to another and add installation_date to PRICOLPage2a."""
    writer = PdfWriter()

    # Read the original PDF
    original_pdf = PdfReader(original_pdf_path)
    for page in original_pdf.pages:
        writer.add_page(page)

    # Read the PDF to append
    pdf_to_append = PdfReader(pdf_to_append_path)
    for i, page in enumerate(pdf_to_append.pages):
        if i == 0:  # Add installation_date to the first page of PRICOLPage2a
            packet = io.BytesIO()

            # Define a custom page size (e.g., increase height to 1000 points)
            custom_page_size = (letter[0], 900)  # Width remains the same, height is increased
            can = canvas.Canvas(packet, pagesize=custom_page_size)
            can.setFont("Helvetica", 10)

            # Calculate y-coordinate for the top of the custom page
            page_width, page_height = custom_page_size
            top_margin = 20  # Adjust this value as needed
            y = page_height - top_margin

            can.drawString(225, y-33, installation_date)  # Adjust x as needed
            can.save()
            packet.seek(0)

            # Merge the new content with the existing page
            overlay_pdf = PdfReader(packet)
            page.merge_page(overlay_pdf.pages[0])

        writer.add_page(page)

    # Write the combined PDF to the output path
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
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
                if image1 and image1.filename:  # Check if a file was uploaded
                    image1_path = os.path.join(app.config['UPLOAD_FOLDER'], image1.filename)
                    image1.save(image1_path)
                    form_data['image1_path'] = image1_path
                else:
                    print("No file selected for Image1 or filename is empty.")  # Debug statement
            
            if 'image2' in request.files:
                image2 = request.files['image2']
                if image2 and image2.filename:  # Check if a file was uploaded
                    image2_path = os.path.join(app.config['UPLOAD_FOLDER'], image2.filename)
                    image2.save(image2_path)
                    form_data['image2_path'] = image2_path
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
            
            # Append additional PDF page with installation_date
            temp_combined_path = output_path + ".combined.pdf"
            append_pdf(output_path, "PRICOLPage2a.pdf", temp_combined_path, form_data['installation_date'])
            
            # Check if the original file exists and delete it before renaming
            if os.path.exists(output_path):
                os.remove(output_path)
            
            # Rename the combined file to the original output path
            os.rename(temp_combined_path, output_path)
            
            # Send the file to user
            return send_file(output_path, as_attachment=True)
            
        except Exception as e:
            return render_template('index.html', message=str(e), success=False)
    
    return render_template('index.html')

if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False)