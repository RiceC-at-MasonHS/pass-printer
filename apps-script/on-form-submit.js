var FLASK_SERVER_URL   = "https://pass-printer-test.comet-tech.org/print";  // replace with your Pi's IP
var SCHOOL_NAME        = "Mason High School";

function onFormSubmit(e) {
  try {
    Logger.log("e object: " + JSON.stringify(e));
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
    // print-server will use the ISO timestamp to get the current class-period
    // `studentId` and `studentName` could be used to lookup location and teacher, if not a FERPA violation

    // ------------------------------------------------------

    // GUARD_CLAUSE: Don't print a pass for Early Release
    if (responses[4].trim() == "Early dismissal"){
      Logger.log("Early Release: " + studentName + " | Skipping print");
      return
    }

    printHallPass(firstName, lastName, isoTimestamp, reason);

    Logger.log("Late arrival processed: " + studentName);

  } catch (err) {
    Logger.log("Error in onFormSubmit: " + err.toString());
  }
}

function printHallPass(firstName, lastName, isoTimestamp, reason) {
  var payload = {
    first_name : firstName,
    last_name  : lastName,
    timestamp  : isoTimestamp,
    late_reason: reason
  };

  var options = {
    method      : "post",
    contentType : "application/json",
    payload     : JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    var response = UrlFetchApp.fetch(FLASK_SERVER_URL, options);
    Logger.log("Print server response: " + response.getContentText());
  } catch (err) {
    Logger.log("Print server unreachable: " + err.toString());
  }
}