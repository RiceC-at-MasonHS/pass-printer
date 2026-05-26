#!/bin/bash

# Get today's date in M/D/YYYY format
TODAY=$(date +%-m/%-d/%Y)

# Read the CSV and find the URL for today
# ------------------------------------------------------ change this to the actual path of your CSV file
URL=$(awk -F',' -v date="$TODAY" '$1 == date {print $3}' daily-qr-links.example.csv)

if [ -z "$URL" ]; then
    echo "Error: No URL found for today's date ($TODAY)"
    exit 1
fi

echo "Found URL for $TODAY: $URL"

# Generate QR code from the URL
echo "Generating QR code..."
python qr-gen.py --content "$URL" --output qr_code.png

if [ $? -ne 0 ]; then
    echo "Error: Failed to generate QR code"
    exit 1
fi

echo "QR code generated: qr_code.png"

# Generate medium sized output image from HTML
echo "Generating output medium size output image from HTML..."
python html-to-img.py code_md.html --width 480 --height 800 --output output_md.png

if [ $? -ne 0 ]; then
    echo "Error: Failed to generate output image"
    exit 1
fi

# Generate large sized output image from HTML
echo "Generating output large size output image from HTML..."
python html-to-img.py code.html --width 1404 --height 1872 --output output.png

if [ $? -ne 0 ]; then
    echo "Error: Failed to generate output image"
    exit 1
fi


echo "Output image generated: output.png"
echo "Nightly build completed successfully!"
