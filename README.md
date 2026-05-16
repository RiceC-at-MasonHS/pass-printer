# **PASS-PRINTER:** late arrival automated POS printer

## **The Mission**

The goal of this project is to streamline the high school attendance office workflow by automating the creation of physical "attendance receipts". Using a tech stack that will never undermine records-integrity and an off-the-shelf Point Of Sale (POS) printer.

By bridging modern cloud tools with local hardware, we are replacing manual note-writing with an instant, automated printing system. This project serves as a real-world application of full-stack engineering, networking, and hardware integration within a school environment.

## **Key Features**

- **🔄 Automatic Schedule Integration:** Student passes automatically display current class, room, teacher, and period information pulled from the local database
- **🛡️ Multi-Layer Security:** Bearer token authentication, school hours enforcement, and rate limiting prevent unauthorized use
- **📍 Resilient Operation:** If the schedule database is unavailable, passes still print with graceful defaults—the system never fails
- **🔧 Automatic Retry Logic:** Failed print jobs are automatically re-queued up to a configurable maximum (default: 5 attempts)
- **📊 Job Tracking:** Query the status of any print job by ID to monitor successful prints and diagnose failures
- **⏱️ School Hours Only:** Printing is restricted to configured school hours (Mon-Fri only) for compliance and security

## **The Story**

After a student recieved one-too-many tardy passes, the kernel of the idea was born.

A collaboration between Cybersecurity/ Applied Technology students and staff to solve a specific logistical problem: the manual process of writing falsifiable late-arrival passes. We moved from concept to a working prototype using industry-standard tools like Python and Flask, eventually securing the connection through Cloudflare tunnels to ensure a professional and secured deployment on the school network.

## **How It Works**

The system follows a linear data path from student input to physical output:

1. **Input:** A student completes a Google Form designated for tracking late arrivals and early releases.  
2. **Trigger:** The form submission is recorded in a Google Spreadsheet. An Apps Script trigger detects the new entry.  
3. **Transmission:** The Apps Script sends a secure HTTP request to the print server with student details (name, timestamp, reason, student ID).  
4. **Schedule Lookup:** The print server queries the local SQLite database to fetch the student's current class schedule (period, room, teacher, end time).  
5. **Pass Generation:** The server formats a hall pass with student info, late reason, and current class details.  
6. **Output:** The pass is sent to a USB-connected POS thermal printer to generate a physical receipt for the student to carry to class.

**Resilience:** If the schedule database is unavailable, the pass will still print with "unknown" fields rather than failing completely, ensuring the system remains operational.


## **Local Cache / Schedule Scraper**

The `local-cache` component is a critical sidecar utility that automatically extracts and maintains an up-to-date cache of student schedules from Smartpass. This data enables the print server to include current class information on each printed pass.

**Key Features:**
- **Automated Daily Sync:** Runs daily at 3:00 AM (via systemd timer) to pull the latest student schedules from Smartpass using headless browser automation
- **Local SQLite Database:** Caches schedule data at `/opt/pass-printer/data.db` for fast lookups with zero external dependencies
- **On-Demand Syncing:** Provides a local web API on port 48273 for manual schedule refreshes when needed
- **Secure Authentication:** Uses the `auth_clever.py` module for automated, headless login via Playwright
- **Graceful Degradation:** If the database is unavailable, the print server continues to function and generates passes with default values

**Data Integration:** When a pass is printed, the server automatically queries the local cache to fetch the student's current period, class name, room number, teacher name, and period end time—all populated from the Smartpass extract.

See [local-cache/README.md](local-cache/README.md) and [local-cache/SCHEMA.md](local-cache/SCHEMA.md) for technical details.

## **Technical Stack**

| Component | Technology Used | Purpose |
| :---- | :---- | :---- |
| **Front End** | Google Forms | User input and data collection |
| **Middle Tier** | Google Apps Script | Event listener and API relay |
| **Server** | Python / Flask | Application logic and printer management |
| **Local Cache** | Python / Playwright | Automated student schedule extraction from Smartpass |
| **Hardware** | Raspberry Pi | Local host for the server and printer connection |
| **Networking** | Cloudflare Tunnel | Securely exposing the local server to the internet |
| **Output** | POS Thermal Printer | Creating the physical attendance artifact |

## **Networking & Security**

To ensure the system is reachable by Google Services while remaining secure behind the school firewall, we use a **Zero-Trust Cloudflare Tunnel**. The server is hosted at a dedicated domain to maintain a stable endpoint on the internet. Multiple layers of security protect the system:

- **Host Address:** Cloudflare Tunnel provides a secure, non-moving location on the internet while keeping the local server behind the school firewall.
- **Bearer Token Authentication:** All print requests require a strong API passkey sent in the HTTP Authorization header. This prevents unauthorized printing even if the tunnel URL is discovered.
- **Access Control:** The server runs under a secure, non-root user account with restricted permissions.
- **School Hours Enforcement:** The server will only process print requests during configured school hours (Monday-Friday, 7:30 AM - 2:30 PM by default), adding an additional layer of protection.

For detailed security configuration, see [print-server/README.md](print-server/README.md).

## **Installation Procedure**

For a complete walkthrough, start with the component-specific guides linked below.

### Quick Start
1. Obtain a POS thermal printer and Raspberry Pi with Debian/Ubuntu.
2. Configure the Raspberry Pi for network access and attach the printer via USB.
3. Run the automated installation:
```shell
curl -fsSL https://raw.githubusercontent.com/RiceC-at-MasonHS/pass-printer/main/install.sh | sudo bash
```

### Component Setup

**Print Server** (receives print requests, manages printer)
- See [print-server/README.md](print-server/README.md) for detailed setup, configuration, and API documentation
- Configure your API passkey, school hours, and printer USB IDs via `.env`

**Local Cache / Schedule Scraper** (maintains student schedule database)
- See [local-cache/README.md](local-cache/README.md) for installation and configuration
- Set up Cleverly credentials for automated Smartpass extraction
- Configure the daily sync timer (defaults to 3:00 AM)

**Google Apps Script** (form submission handler)
- See [apps-script/README.md](apps-script/README.md) and [apps-script/CONFIG.md](apps-script/CONFIG.md)
- Copy the Apps Script code to your Google Sheet
- Configure the print server URL and API passkey as secrets in the script
- Set up the form submission trigger

### After Installation
1. Test the full pipeline: submit a form entry and verify a pass prints
2. Check print server logs for any errors: `systemctl status pass-printer`
3. Verify database sync: `systemctl start schedule-scraper && systemctl status schedule-scraper`
4. Monitor the printer queue: `curl http://localhost:5000/queue` (requires port forwarding or local access)


## **Implementation Team**

* **Project Lead:** RiceC-at-MasonHS  
* **Technical Collaborators:**   Cybersecurity Students
* **Stakeholder:** Mason High School (Attendance Office)


## **Future Directions**

Once the prototype is fully validated, the next step is to present a formal demo to the administration and evaluate the long-term impact on office efficiency. 
This work stands as a model for student-led innovation and high-level project development in Mason High School's Applied Technology department.
