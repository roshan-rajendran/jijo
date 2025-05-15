from flask import Flask, render_template, request, send_file
import json
import os
import webbrowser
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.colors import CMYKColor
import io
from datetime import datetime
from add_qr_to_pdf import add_qr_to_pdf
import uuid
import sys
import subprocess
import logging
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Suppress all stdout and stderr
# sys.stdout = open(os.devnull, 'w')
# sys.stderr = open(os.devnull, 'w')

# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

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
# current_hardware_id = get_hardware_id()
# if current_hardware_id != ALLOWED_HARDWARE_ID:
#     print("This application is not authorized to run on this computer.")
#     sys.exit(1)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'generated_pdfs'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register the regular and bold fonts
pdfmetrics.registerFont(TTFont('BookmanOldStyle', 'fonts/BOOKOS.ttf'))  # Regular
pdfmetrics.registerFont(TTFont('BookmanOldStyleBold', 'fonts/BOOKOSB.ttf'))  # Bold

def create_qr_data(form_data):
    """Create formatted QR code data string"""
    return (f"Mfg by: Pricol Ltd., "
            f"Cert No: {form_data['certificate_no']}, "
            f"Dt: {form_data['dealer_invoice_date']}, "
            f"Veh Reg. No: {form_data['vehicle_reg_no']} "
            f"Chas. No: {form_data['chassis_no']}, "
            f"Eng. No: {form_data['engine_no']}, "
            f"SLD ECU No: {form_data['sld_ecu_no']}, "
            f"Speed: 80")

def fill_pdf_form(input_pdf_path, output_pdf_path, form_data):
    # Create a new PDF with form data
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(letter[0], 900))
    
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name
   # Set the font to Bookman Old Style
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name
    
    # Start position - Base positions
    x1 = 1 * inch + 100  # Base left position
    x2 = 4.5 * inch + 100  # Base right position
    y = 500  # Base starting y position
    
    # Add "Customer Copy" text
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    can.setFillColor(colors.black)  # Use a predefined color instead
    can.drawString( 500,  718, "Customer Copy")  # Adjust position as needed
    
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name
# Reset font for other text
    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    # Certificate Details - Move right by 10px and down by 5px
    can.drawString(172, 595, form_data['certificate_no'])
    can.setFillColor(colors.blue)  # Use a predefined color instead

    can.drawString( 410, 335, form_data['test_report_no'])
    y -= 20
    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    can.drawString( 410, 320, form_data['tac_no'])
    
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name
# Dealer Information - Move right by 10px and up by 5px
    y -= 30
    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name
   
    can.drawString(172,  577, form_data['dealer_name'].split(' ')[0] + '')  # First part
    y -= 15  # Move down for the next line
    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    can.drawString(172,  561, form_data['dealer_location'])
    y -= 20
    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name
 
    can.drawString(172,  548, form_data['dealer_invoice_no'])
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name
    can.drawString(475,  547, form_data['dealer_invoice_date'])
    
    # Customer & Fitment Center Details
    y -= 100
    # Split address into multiple lines if needed
    customer_details = form_data['customer_details'].split('\n')
    z=350
    z1=350
    for line in customer_details:
        can.setFillColor(colors.blue)  # Use a predefined color instead

 
        can.setFont("BookmanOldStyle", 9)  # Use the registered font name
        clean_line = line.strip()  # Remove leading/trailing whitespace and special characters
        can.drawString(x1 -130, y + 200, clean_line)  # Moved left by 100px and up by 25px
        y -= 10
    
        clean_line = line.strip()
        # can.drawString( 50, z, clean_line)  # Moved left by 100px and up by 25px
        z-=10
    y -= 10
    can.setFont("BookmanOldStyle",8)  # Use the registered font name

    can.setFillColor(colors.black)  # Use a predefined color instead
    can.setFont("BookmanOldStyleBold", 8)  # Use the registered bold font name

    can.drawString(40, 450, f"Phone:")  # Adjust position as needed
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    can.drawString(68, 450, form_data['customer_phone'])  # Adjust position as needed


    fitment_details = form_data['fitment_center_details'].split('\n')
    can.setFont("BookmanOldStyle", 9)  # Use the registered font name
 
    can.setFillColor(colors.blue)  # Use a predefined color instead

    for line in fitment_details:
        clean_line = line.strip()  # Remove leading/trailing whitespace and special characters
        can.setFillColor(colors.blue)  # Use a predefined color instead
        can.setFont("BookmanOldStyle", 9)  # Use the registered font name

        can.drawString(x1 + 90, y + 240, clean_line)
        y -= 10
        clean_line = line.strip()
        # can.drawString( 280, z1, clean_line)
        z1-=10
    can.setFillColor(colors.black)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    # Get the current date and time
    current_time = datetime.now().strftime("%H:%M:%S")  # Format: 17:15:00

    # Draw the date and time
    can.drawString(34, 810, f"Date:")  # Adjust position as needed
    can.drawString(55, 810, form_data['installation_date']+" " + str(current_time)) # This line can be removed if you only want to show the current time
    can.setFont("BookmanOldStyleBold", 8)  # Use the registered bold font name

    can.drawString(256, 450, f" Phone:")  # Adjust position as needed
# Adjust position as needed

    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    can.drawString(287, 450, form_data['fitment_center_phone']) # Adjust position as needed

    # Vehicle Details
    y -= 20
    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    can.drawString(140,  391, form_data['vehicle_make_model'])
    can.drawString( 140,348, form_data['chassis_no'])
    can.drawString( 140,363, form_data['engine_no'])  # Moved down by 30px and right by 10px
    y -= 20
    can.drawString(140, 378, form_data['vehicle_reg_no'])
    can.drawString(0, 299, form_data['vehicle_reg_date'])
    y -= 20
    can.drawString( 475,  562, form_data['rto_location'])
    
    # SLD Details
    y -= 30
    sld_model_lines = form_data['sld_model'].split(' / ')  # Split the SLD model into parts
    for line in sld_model_lines:
        can.setFillColor(colors.blue)  # Use a predefined color instead

        can.drawString(410,  391, line)  # Draw each line
        y -= 15  # Move down for the next line
    can.setFillColor(colors.blue)  # Use a predefined color instead
    can.setFont("BookmanOldStyle", 8)  # Use the registered font name

    can.drawString( 410,  377, form_data['sld_ecu_no'])
    y -= 20
    can.setFillColor(colors.blue)  # Use a predefined color instead

    can.drawString( 410, 363, form_data['sld_motor_unit'])
    y -= 20
    can.setFillColor(colors.blue)  # Use a predefined color instead

    can.drawString( 410,  350, form_data['speed_sensor_type'])  # Moved right by 3px
    can.setFillColor(colors.blue)  # Use a predefined color instead
  
    can.drawString( 140,  332, form_data['roto_seal_no'])
    # Set the CMYK values (example values)
    cyan = 0.0
    magenta = 0.0
    yellow = 0.0
    black = 1.0  # This will create a black color

    can.setFillColor(colors.blue)  # Use a predefined color instead

    
    # Installation & Renewal Dates


    y -= 30
    can.setFillColor(colors.blue)  # Use a predefined color instead

    can.drawString( 475,  595, form_data['installation_date'])
    can.drawString( 263, 262, form_data['installation_date'])

    can.drawString( 475,  577, form_data['sld_renewal_date'])
    
    # Add images to the PDF
    if form_data['image1_path']:
        can.drawImage(form_data['image1_path'],  470, 472, width=1 * inch, height=.89 * inch)  # Adjust size and position as needed
    else:
        print("Image1 path is empty or invalid.")  # Debug statement

    if form_data['image2_path']:
        can.drawImage(form_data['image2_path'],  470 ,  412, width=1 * inch, height=.9 * inch)  # Adjust size and position as needed
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
        try:
            # Log the incoming form data
            print(request.form)  # This will show you what data is being sent
            
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
                'customer_phone':request.form['customer_phone'],
                'fitment_center_phone':request.form['fitment_center_phone']
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
            fill_pdf_form("adobe1.pdf", output_path, form_data)
            
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
            
        except KeyError as e:
            print(f"Missing field: {e}")
            print(f"Form data received: {request.form}")  # Log the entire form data
            return render_template('index.html', message=f"Missing field: {e}", success=False)
        except Exception as e:
            print(f"Error: {e}")
            return render_template('index.html', message=str(e), success=False)
    
    return render_template('index.html')

if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False)