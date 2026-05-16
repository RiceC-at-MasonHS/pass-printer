var FLASK_SERVER_URL = "SECRET_PRINT_SERVER_URL"; // read CONFIG.md
var PRINT_PASSKEY    = "SECRET_PRINT_PASSKEY";    // read CONFIG.md

function onFormSubmit(e) {
  try {
    // Get Form responses from the event object
    var responses = e.values;
    Logger.log("Google Form responses: " + JSON.stringify(responses));

    // Map responses to variables (adjust indices based on your form structure)
    var firstName    = responses[1].trim();
    var lastName     = responses[2].trim();
    var studentName  = firstName + " " + lastName;
    var studentId    = responses[3].trim();
    var reason       = responses[5].trim();

    // Generate timestamps for the hall pass
    var now         = new Date();
    var arrivalTime = Utilities.formatDate(now, Session.getScriptTimeZone(), "h:mm a");
    var arrivalDate = Utilities.formatDate(now, Session.getScriptTimeZone(), "EEEE, MMMM d, yyyy");
    var isoTimestamp = now.toISOString();

    // Don't print a pass for Early Release
    if (responses[4].trim() == "Early dismissal"){
      Logger.log("Early Release: " + studentName + " | Skipping print");
      return
    }

    // Don't print a pass if the daily_key is invalid
    if (responses[6].trim() != getDailyKey()){
      Logger.log("invalid daily_key: " + studentName + " | Skipping print");
      return
    }
    
    //-------------------------------------------------------------------------
    printHallPass(firstName, lastName, isoTimestamp, studentId, reason);
    // TODO: email teacher OR create 'late arrival' Smartpass directly (if Smartpass supports it)

    Logger.log("Late arrival processed: " + studentName);

  } catch (err) {
    Logger.log("Error in onFormSubmit: " + err.toString());
  }
}

/*
 * Sends a request to the print server with the student's information and reason for lateness.
 * The print server will handle the actual printing of the hall pass, and getting more data.
 * ------
 * Ensures the print server receives all necessary information to generate a hall pass, including:
 * --> student name, student ID, reason for lateness, and timestamp.
 * Uses a secret passkey for authentication to prevent unauthorized printing requests.
 * Logs the response from the print server for debugging and monitoring purposes.
 */
function printHallPass(firstName, lastName, isoTimestamp, studentId, reason) {
  var payload = {
    first_name : firstName,
    last_name  : lastName,
    timestamp  : isoTimestamp,
    late_reason: reason,
    student_id : studentId
  };

  var options = {
    method      : "post",
    contentType : "application/json",
    payload     : JSON.stringify(payload),
    headers     : {
      "Authorization": "Bearer " + PRINT_PASSKEY
    },
    muteHttpExceptions: true
  };

  try {
    var response = UrlFetchApp.fetch(FLASK_SERVER_URL, options);
    Logger.log("Print server response: " + response.getContentText());
  } catch (err) {
    Logger.log("Print server unreachable: " + err.toString());
  }
}

/*
 * Retrieves the daily key from the "daily_key" sheet based on today's date.
 * The sheet should have dates in column A and corresponding daily keys in column B.
 * Returns the daily key if a match is found, or null if no match is found.
 * ------
 * Allows for unique daily attendance prefilled-URLs (daily_key as a query parameter).
 * Prevent use of old links, guarding against students using links from previous days.
 * Facilitates data aggregation into a single sheet for attendance tracking and reporting.
 */
function getDailyKey() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("daily_key"); // Ensure this matches the name of your sheet
  const data = sheet.getDataRange().getValues();
  
  // Create search date and strip time to 00:00:00
  // Create 'Today' search date and strip time to 00:00:00
  const searchTime = searchDate.getTime();

  const returnColumnIndex = 1; // Column B: holds the daily key value

  for (let i = 0; i < data.length; i++) {
    let rowValue = data[i][0]; // Column A: holds the date to match against

    // Verify the cell is a Date object
    if (rowValue instanceof Date) {
      // Normalize row date to midnight for comparison
      rowValue.setHours(0, 0, 0, 0);
      
      if (rowValue.getTime() === searchTime) {
        let dailyKey = data[i][returnColumnIndex];
        Logger.log("Date: " +searchDate+ "| key: "+ dailyKey);
        Logger.log("Date: " +searchDate+ "| key: "+ dailyKey);
      }
    }
  }
  
  Logger.log("No daily_key match found for " + searchDate.toDateString());
  return null;
}
