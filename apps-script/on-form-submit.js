var FLASK_SERVER_URL   = "https://pass-printer-test.comet-tech.org/print";  // replace with your Pi's IP
var SCHOOL_NAME        = "Mason High School";
var PRINT_PASSKEY      = "your-super-secret-passkey-here";  // Must match the passkey set in the Flask server

function onFormSubmit(e) {
  try {
    var responses = e.values;
    Logger.log("Google Form responses: " + JSON.stringify(responses));

    var firstName    = responses[1].trim();
    var lastName     = responses[2].trim();
    var studentName  = firstName + " " + lastName;
    var studentId    = responses[3].trim();
    var reason       = responses[5].trim();

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
    
    printHallPass(firstName, lastName, isoTimestamp, reason, "prototype", "prototype", "unknown", "unknown","unknown");

    Logger.log("Late arrival processed: " + studentName);

  } catch (err) {
    Logger.log("Error in onFormSubmit: " + err.toString());
  }
}

function printHallPass(firstName, lastName, isoTimestamp, reason, teacher, room, period, lateThisBell, lateOverall) {
  var payload = {
    first_name : firstName,
    last_name  : lastName,
    timestamp  : isoTimestamp,
    late_reason: reason,
    heading_to : {
      teacher  : teacher,
      room     : room,
      class    : "Bell " + period
    }, 
    late_count : {
      this_bell: lateThisBell,
      overall  : lateOverall
    }
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
