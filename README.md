# **PASS-PRINTER:** late arrival automated POS printer

## **The Mission**

The goal of this project is to streamline the high school attendance office workflow by automating the creation of physical "attendance receipts". Using a tech stack that will never undermine records-integrity and an off-the-shelf Point Of Sale (POS) printer.

By bridging modern cloud tools with local hardware, we are replacing manual note-writing with an instant, automated printing system. This project serves as a real-world application of full-stack engineering, networking, and hardware integration within a school environment.

## **The Story**

After a student recieved one-too-many tardy passes, the kernel of the idea was born.

A collaboration between Cybersecurity/ Applied Technology students and staff to solve a specific logistical problem: the manual process of writing falsifiable late-arrival passes. We moved from concept to a working prototype using industry-standard tools like Python and Flask, eventually securing the connection through Cloudflare tunnels to ensure a professional and secured deployment on the school network.

## **How It Works**

The system follows a linear data path from student input to physical output:

1. **Input:** A student completes a Google Form designated for attendance tracking late arrivals and early releases from school.  
2. **Trigger:** The form submission is recorded in a Google Spreadsheet. An Apps Script trigger detects the new entry.  
3. **Transmission:** The Apps Script sends an HTTP request to our dedicated server.  
4. **Processing:** A Python/Flask server running on a Raspberry Pi receives the data.  
5. **Output:** The server communicates with a POS (Point of Sale) printer to generate a physical receipt/artifact for the student to carry to class.

## **Technical Stack**

| Component | Technology Used | Purpose |
| :---- | :---- | :---- |
| **Front End** | Google Forms | User input and data collection |
| **Middle Tier** | Google Apps Script | Event listener and API relay |
| **Server** | Python / Flask | Application logic and printer management |
| **Hardware** | Raspberry Pi | Local host for the server and printer connection |
| **Networking** | Cloudflare Tunnel | Securely exposing the local server to the internet |
| **Output** | POS Thermal Printer | Creating the physical attendance artifact |

## **Networking & Security**

To ensure the system is reachable by Google Services while remaining secure behind the school firewall, we placed the server at a permanent **Zero-Trust Cloudflare Tunnel**. The server is hosted at a dedicated domain to maintain a "non-moving place on the internet". Authorization is required to transmit data to the print-server.

* **Host Address:** `REDACTED-URL` with access guarded by authorization.   
* **Access Control:** Secure non-root user accounts and private keys are utilized for server management.

## **Installation Procedure**

1. Obtain a POS printer and Raspberry Pi with Headless Raspbian or Debian. 
2. Configure the Raspberry Pi for the network, and attach the printer via USB.
3. On the Raspberry Pi (either terminal/SSH *or* local monitor, keyboard, mouse) run the following command:
```shell
curl -fsSL https://raw.githubusercontent.com/RiceC-at-MasonHS/pass-printer/main/install.sh | sudo bash
```
4. Set a kryptonite-level API key for the Flask server, following [these instructions](print-server/README.md). Update as needed.
5. Create a Google Form for attendance that meets [an exacting set of requirements](/apps-script/README.md).
6. Copy the [contents of the Apps Script](apps-script/on-form-submit.js) to the Sheet's Apps Script.
7. Adjust any and all secrets in Apps Script to match requirements: 
    - `FLASK_SERVER_URL` The URL location for the cloudflare tunnel
    - API Key for Flask server (to match value in step 4 above)
8. Set the 'trigger' in the Apps Script to execute 'on Form Submit' and test that it works!


## **Implementation Team**

* **Project Lead:** RiceC-at-MasonHS  
* **Technical Collaborators:**   Cybersecurity Students
* **Stakeholder:** Mason High School (Attendance Office)


## **Future Directions**

Once the prototype is fully validated, the next step is to present a formal demo to the administration and evaluate the long-term impact on office efficiency. 
This work stands as a model for student-led innovation and high-level project development in Mason High School's Applied Technology department.
