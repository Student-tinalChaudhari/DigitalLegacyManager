// ======================================================
// DIGITAL LEGACY MANAGER - COMMON JAVASCRIPT
// ======================================================


// ======================================================
// PAGE LOAD
// ======================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("Digital Legacy Manager loaded successfully.");

});


// ======================================================
// CONFIRM DELETE
// ======================================================

function confirmDelete(message) {

    if (!message) {
        message = "Are you sure you want to delete this item?";
    }

    return confirm(message);
}


// ======================================================
// FORM VALIDATION
// ======================================================

function validateForm(form) {

    const requiredFields = form.querySelectorAll("[required]");

    for (let field of requiredFields) {

        if (field.value.trim() === "") {

            alert("Please fill all required fields.");

            field.focus();

            return false;
        }
    }

    return true;
}


// ======================================================
// EMAIL VALIDATION
// ======================================================

function validateEmail(email) {

    const emailPattern =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    return emailPattern.test(email);
}


// ======================================================
// PHONE VALIDATION
// ======================================================

function validatePhone(phone) {

    const phonePattern =
        /^[0-9]{10}$/;

    return phonePattern.test(phone);
}


// ======================================================
// SUCCESS MESSAGE
// ======================================================

function showSuccessMessage(message) {

    if (!message) {
        message = "Operation completed successfully!";
    }

    alert("✅ " + message);
}


// ======================================================
// SEARCH VALIDATION
// ======================================================

function validateSearch(form) {

    const searchInput =
        form.querySelector('input[name="search"]');

    if (!searchInput) {
        return true;
    }

    if (searchInput.value.trim() === "") {

        alert("Please enter something to search.");

        searchInput.focus();

        return false;
    }

    return true;
}