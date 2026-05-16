# CONFIG for Apps Script

Google Apps Scripts are best when they are simple. 
So you should only need to get and change the few items below.

## **SECRETS:** for security

There are a few secrets that you will hard-code into the 'real' Apps Script, 
as a string, after copy-pasting the full Apps Script into your Google Sheet. 

This manual process avoids more complex solutions that could break if Apps Scripts every change.

### Print Server Location

`SECRET_PRINT_SERVER_URL` = "https://pass-printer-test.comet-tech.org/print"

The pass printer needs to live in a 'fixed' location for this web-based Apps Script to reach it. 
A local IP address can't work, because the Apps Script run in the cloud (on Google's servers).

So, we recommend setting up a DNS record and a cloudflare tunnel. The temporary example shown above,
demonstrates the basic idea (but our own 'live' printer has since changed locations).

### Print Server Passkey

`SECRET_PRINT_PASSKEY`    = "your-super-secret-passkey-here"

This passkey is checked before the printer will print a pass. It avoids student printing passes by
any other means (since a public DNS record is accessible by anyone). Its just another layer of 
defense, to keep the system working with less potential for tampering from outside players. 

This value needs to match the environment variables for the `print-server` and it is recommended:
- rotate this value every semester, week, daily (as needed, based on attack-history)
- use something strong, like a v4 UUID [https://www.uuidgenerator.net/](https://www.uuidgenerator.net/)


## **CONFIGURATION:** for customization

Customizations have been depricated inside the Apps Scritps, to keep this as simple as possible. 

Customizations for your school's passes have been migrated to the 'print-server' itself, so they do not live in the cloud.