class AttendanceForm {
  constructor(node) {
    this.eventCard = node;
    this.attendanceForm = this.eventCard.querySelector(
      "form[data-attendance-form]",
    );
    if (this.attendanceForm) {
      this.getDomData();
      this.handleClick = this.handleClick.bind(this);
      this.attendanceButton.addEventListener("click", this.handleClick);
    }
  }

  getDomData() {
    this.attendanceDescription = this.eventCard.querySelector(
      "p[data-attendance-description]",
    );
    this.attendanceDescriptionType = this.attendanceDescription.getAttribute(
      "data-attendance-description-type",
    );
    this.attendanceButton = this.attendanceForm.querySelector(
      "button[data-attendance-button]",
    );
    this.loadingSpinner =
      this.attendanceForm.querySelector("div[data-loading]");
    this.errorMessage = this.eventCard.querySelector("p[data-error]");
    this.unattendUrl = this.attendanceForm.getAttribute("data-unattend-url");
    this.attendUrl = this.attendanceForm.getAttribute("data-attend-url");
    this.formAction = this.attendanceForm.getAttribute("data-form-action");
    this.buttonTextAttend = this.attendanceForm.getAttribute(
      "data-button-text-attend",
    );
    this.buttonTextUnattend = this.attendanceForm.getAttribute(
      "data-button-text-unattend",
    );
    this.attendeeCount =
      this.attendanceForm.getAttribute("data-attendee-count") * 1;
    this.maximumAttendees =
      this.attendanceForm.getAttribute("data-maximum-attendees") * 1;
  }

  async handleClick(event) {
    event.preventDefault();
    this.startLoading();
    this.errorMessage.classList.add("hidden");
    try {
      const result = await this.sendAjaxRequest();
      if (result.success) {
        this.updateAttendanceDescription();
        this.swapButtonType();
      } else {
        throw new Error(result.error_message);
      }
    } catch (err) {
      this.errorMessage.innerText = err;
      this.errorMessage.classList.remove("hidden");
    } finally {
      this.endLoading();
    }
  }

  async sendAjaxRequest() {
    const data = new FormData(this.attendanceForm);
    const csrfToken = this.attendanceForm.querySelector(
      '[name="csrfmiddlewaretoken"]',
    ).value;
    const request = {
      method: "POST",
      body: data,
      headers: {
        "X-CSRFToken": csrfToken,
        Accept: "application/json",
      },
    };

    let url = null;
    if (this.formAction === "unattend") {
      url = this.unattendUrl;
    } else if (this.formAction === "attend") {
      url = this.attendUrl;
    }

    const res = await fetch(url, request);
    const result = await res.json();
    return result;
  }

  updateAttendanceDescription() {
    if (this.attendanceDescriptionType === "list") {
      if (this.formAction === "unattend") {
        this.attendeeCount--;
        this.attendanceDescription.innerText = `${
          this.maximumAttendees - this.attendeeCount
        } spaces left`;
      } else if (this.formAction === "attend") {
        this.attendeeCount++;
        this.attendanceDescription.innerText = `${
          this.maximumAttendees - this.attendeeCount
        } spaces left - you are attending`;
      }
    } else if (this.attendanceDescriptionType === "detail") {
      if (this.formAction === "unattend") {
        this.attendeeCount--;
        const remainingSpaces = this.maximumAttendees - this.attendeeCount;
        this.attendanceDescription.innerText = `${this.attendeeCount} ${
          this.attendeeCount === 1 ? "attendee" : "attendees"
        } out of ${
          this.maximumAttendees
        } spaces filled - ${remainingSpaces} spaces left.`;
      } else if (this.formAction === "attend") {
        this.attendeeCount++;
        const remainingSpaces = this.maximumAttendees - this.attendeeCount;
        this.attendanceDescription.innerText = `${this.attendeeCount} ${
          this.attendeeCount === 1 ? "attendee" : "attendees"
        } out of ${
          this.maximumAttendees
        } spaces filled - ${remainingSpaces} spaces left - you are attending.`;
      }
    }
  }

  swapButtonType() {
    if (this.formAction === "unattend") {
      this.formAction = "attend";
      this.attendanceButton.classList.remove("unattend_button");
      this.attendanceButton.classList.add("attend_button");
      this.attendanceButton.innerText = this.buttonTextAttend;
    } else if (this.formAction === "attend") {
      this.formAction = "unattend";
      this.attendanceButton.classList.remove("attend_button");
      this.attendanceButton.classList.add("unattend_button");
      this.attendanceButton.innerText = this.buttonTextUnattend;
    }
  }

  startLoading() {
    this.attendanceButton.disabled = true;
    this.attendanceButton.classList.add("hidden");
    this.loadingSpinner.classList.remove("hidden");
  }

  endLoading() {
    this.attendanceButton.disabled = false;
    this.attendanceButton.classList.remove("hidden");
    this.loadingSpinner.classList.add("hidden");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  eventCardNodeList = document.querySelectorAll("article[data-event-card]");
  eventCardNodeList.forEach((eventCard) => {
    new AttendanceForm(eventCard);
  });
});
