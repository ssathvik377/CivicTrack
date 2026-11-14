// CIVICTRACK - SMART COMPLAINT SYSTEM

let complaints = [];

const form = document.getElementById("complaintForm");
let currentStep = 1;


// STEP NAVIGATION

function nextStep(stepNumber) {

    if (stepNumber > currentStep) {

        const currentSection = document.getElementById(
            "step" + currentStep
        );

        const inputs = currentSection.querySelectorAll(
            "input, select, textarea"
        );

        for (let input of inputs) {
            if (!input.checkValidity()) {
                input.reportValidity();
                return;
            }
        }
    }

    document.querySelectorAll(".form-step").forEach(step => {
        step.hidden = true;
    });

    document.getElementById("step" + stepNumber).hidden = false;

    for (let i = 1; i <= 3; i++) {

        const indicator = document.getElementById(
            "step" + i + "Indicator"
        );

        indicator.classList.remove("active", "completed");

        if (i < stepNumber) {
            indicator.classList.add("completed");
        }

        if (i === stepNumber) {
            indicator.classList.add("active");
        }
    }

    currentStep = stepNumber;
}


// PRIORITY CALCULATION

function calculatePriority(category, description) {

    const text = description.toLowerCase();

    if (
        text.includes("accident") ||
        text.includes("open manhole") ||
        text.includes("danger") ||
        text.includes("hospital")
    ) {
        return "Critical";
    }

    if (
        category === "Road Damage" ||
        category === "Water Leakage" ||
        category === "Drainage"
    ) {
        return "High";
    }

    if (category === "Garbage") {
        return "Medium";
    }

    return "Low";
}


// LOAD COMPLAINTS FROM DATABASE

async function loadComplaints() {

    try {

        const response = await fetch("/api/complaints");

        if (!response.ok) {
            throw new Error("Unable to load complaints");
        }

        complaints = await response.json();

        updateDashboard();

    } catch (error) {

        console.error(error);

    }
}


// SUBMIT COMPLAINT

form.addEventListener("submit", async function(e) {

    e.preventDefault();

    const complaint = {

        name: document.getElementById("name").value.trim(),

        category: document.getElementById("category").value,

        description: document.getElementById("description").value.trim(),

        location: document.getElementById("location").value.trim()

    };

    complaint.priority = calculatePriority(
        complaint.category,
        complaint.description
    );

    try {

        const response = await fetch("/api/complaints", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                ...complaint,
                severity: complaint.priority.toLowerCase()
            })

        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Submission failed");
        }

        complaint.id = data.id;
        complaint.priority = data.priority;
        complaint.status = data.status;

        complaints.unshift(complaint);

        const message = document.getElementById("message");

        message.innerHTML = "";

        const successBox = document.createElement("div");
        successBox.className = "success-box";

        const heading = document.createElement("h3");
        heading.textContent = "✓ Complaint Submitted Successfully!";

        successBox.appendChild(heading);

        [
            ["Complaint ID:", complaint.id],
            ["Category:", complaint.category],
            ["Priority:", complaint.priority],
            ["Status:", complaint.status]
        ].forEach(([label, value]) => {

            const p = document.createElement("p");
            const b = document.createElement("b");

            b.textContent = label + " ";

            p.appendChild(b);
            p.appendChild(document.createTextNode(value));

            successBox.appendChild(p);

        });

        message.appendChild(successBox);

        form.reset();

        nextStep(1);

        updateDashboard();

        document.getElementById("searchId").value =
            complaint.id;

        trackComplaint();

        document.getElementById("track").scrollIntoView({
            behavior: "smooth"
        });

    } catch (error) {

        alert("Error: " + error.message);

        console.error(error);

    }

});


// UPDATE DASHBOARD

function updateDashboard() {

    document.getElementById("total").textContent =
        complaints.length;

    document.getElementById("pending").textContent =
        complaints.filter(c => c.status !== "Resolved").length;

    document.getElementById("resolved").textContent =
        complaints.filter(c => c.status === "Resolved").length;

    const list = document.getElementById("complaintList");

    list.innerHTML = "";

    complaints.forEach(c => {

        const row = document.createElement("tr");

        [
            c.id,
            c.category,
            c.location,
            c.priority,
            c.status
        ].forEach(value => {

            const cell = document.createElement("td");

            cell.textContent = value || "";

            row.appendChild(cell);

        });

        // ADMIN ACTION DROPDOWN

        const actionCell = document.createElement("td");

        const select = document.createElement("select");

        ["Pending", "In Progress", "Resolved"].forEach(status => {

            const option = document.createElement("option");

            option.value = status;
            option.textContent = status;

            if (c.status === status) {
                option.selected = true;
            }

            select.appendChild(option);

        });

        select.addEventListener("change", function() {

            updateComplaintStatus(c.id, select.value);

        });

        actionCell.appendChild(select);

        row.appendChild(actionCell);

        list.appendChild(row);

    });

}


// UPDATE COMPLAINT STATUS IN DATABASE

async function updateComplaintStatus(id, status) {

    try {

        const response = await fetch(
            "/api/complaints/" + encodeURIComponent(id),
            {
                method: "PATCH",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    status: status
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Status update failed");
        }

        const complaint = complaints.find(c => c.id === id);

        if (complaint) {
            complaint.status = data.status;
        }

        updateDashboard();

        alert("Complaint status updated successfully!");

    } catch (error) {

        alert("Error: " + error.message);

        console.error(error);

        await loadComplaints();

    }

}


// TRACK COMPLAINT

function trackComplaint() {

    const id = document.getElementById("searchId")
        .value.trim();

    const complaint = complaints.find(
        c => c.id.toLowerCase() === id.toLowerCase()
    );

    const result = document.getElementById("trackResult");

    if (!id) {
        result.textContent = "Please enter a Complaint ID.";
        return;
    }

    if (!complaint) {
        result.textContent = "Complaint not found!";
        return;
    }

    result.innerHTML = "";

    const details = document.createElement("div");
    details.className = "success-box";

    const heading = document.createElement("h3");
    heading.textContent = "Complaint Tracking Details";

    details.appendChild(heading);

    [
        ["Complaint ID:", complaint.id],
        ["Name:", complaint.name],
        ["Category:", complaint.category],
        ["Location:", complaint.location],
        ["Priority:", complaint.priority],
        ["Status:", complaint.status]
    ].forEach(([label, value]) => {

        const p = document.createElement("p");
        const b = document.createElement("b");

        b.textContent = label + " ";

        p.appendChild(b);
        p.appendChild(document.createTextNode(value || ""));

        details.appendChild(p);

    });

    result.appendChild(details);

}


// INITIALIZE WEBSITE

loadComplaints();