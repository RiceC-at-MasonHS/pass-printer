import argparse
import qrcode

URL="https://docs.google.com/forms/d/e/1FAIpQLSdwQnv7zdama9aYRP4ZeeuwjG07w2LuhN2Ujf5Gs6vWE4hkSQ/viewform?usp=pp_url&entry.835224228=1bc83bc9-20f6-4f2d-b7a7-97a9296a2b67"

def main():
    parser = argparse.ArgumentParser(description="Generate a QR code image from text or a URL.")
    parser.add_argument(
        "--content",
        "-c",
        default=URL,
        help="Text or URL to encode in the QR code (default: a sample Google Form URL)",
    )
    parser.add_argument(
        "--width",
        "-w",
        type=int,
        default=50,
        help="Width of each QR box in pixels (default: 50)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="qr_code.png",
        help="Output filename for the generated QR code image (default: qr_code.png)",
    )

    args = parser.parse_args()
    qr_image = generate_qr_code(args.content, width=args.width)
    qr_image.save(args.output)

def generate_qr_code(url, width=50):
    """
    Generate a QR code image from a URL.
    
    Args:
        url (str): The URL to encode
        width (int): Width of each box in pixels (default: 50)
    
    Returns:
        PIL.Image: The generated QR code image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=width,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img

if __name__ == "__main__":
    main()

# example usage from command line:
#   python qr-gen.py
#   python qr-gen.py --content "https://www.example.com" --width 30
