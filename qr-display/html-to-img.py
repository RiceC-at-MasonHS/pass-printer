#!/usr/bin/env python3
# Usage examples:
#   python html-to-img.py input.html
#   python html-to-img.py code.html --width 1404 --height 1872 --output output.png
#   python html-to-img.py code_md.html --width 480 --height 800 --output output_md.png

import sys
import os
import argparse
from datetime import datetime
from jinja2 import Template
from html2image import Html2Image

def main():
    parser = argparse.ArgumentParser(
        description="Convert an HTML file to an image with local assets automatically resolved."
    )
    parser.add_argument(
        "html_file",
        help="Path to the HTML file to convert"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Width of the output image in pixels (default: 1920)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Height of the output image in pixels (default: 1080)"
    )
    parser.add_argument(
        "--output",
        help="Output image file path (default: same as input with .png extension)"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.html_file):
        print(f"Error: HTML file '{args.html_file}' not found.", file=sys.stderr)
        sys.exit(1)

    # Normalize absolute paths so everything maps cleanly
    html_path = os.path.abspath(args.html_file)
    html_dir = os.path.dirname(html_path)
    output_file = args.output or os.path.splitext(html_path)[0] + '.png'
    output_path = os.path.abspath(output_file)

    try:
        # 1. Read the raw HTML file content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 2. Force an explicit white background by appending to the END of the string.
        # In CSS, if two rules use !important, the LAST one declared wins. 
        # Appending here guarantees it overrides all nested styles above it.
        white_bg_style = "\n<style>html, body { background-color: #ffffff !important; }</style>\n"
        html_content += white_bg_style

        # 3. Initialize Html2Image pointing to the original HTML directory.
        hti = Html2Image(
            temp_path=html_dir,
            custom_flags=[
                '--allow-file-access-from-files',      # Allows Chrome to load local assets
                '--hide-scrollbars',                   # Strips scrollbars from the snapshot
                '--default-background-color=ffffffff', # Exact Hex RGBA match for solid white canvas
                '--disable-gpu'                        # Mutes/Resolves Windows Headless GPU exceptions
            ]
        )
        hti.size = (args.width, args.height)
        
        # 4. Render Jinja2 variables before rendering the HTML to an image
        rendered_html = Template(html_content).render(
            date=datetime.now().strftime("%m-%d-%Y")
        )
        hti.screenshot(html_str=rendered_html, save_as=output_file)
        print(f"Image successfully saved to: {output_path}")

    except Exception as e:
        print(f"Error converting HTML to image: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()