window.addEventListener('load', function () {
    /** 1. LOGIC FOR CREATED_AT **/
    const dateInput = document.querySelector('input[name="created_at"]');

    if (dateInput) {
        // Change type so the browser shows the calendar/clock picker
        dateInput.type = 'datetime-local';

        // Set 'max' to right now so they can't pick future dates
        const now = new Date();
        const formattedNow = now.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
        dateInput.max = formattedNow;

        // If the field has a value (Editing existing record), 
        // format it so the browser widget can actually display it.
        if (dateInput.value) {
            const currentVal = new Date(dateInput.value);
            if (!isNaN(currentVal)) {
                // Formatting to YYYY-MM-DDTHH:mm
                dateInput.value = currentVal.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
            }
        }
    }

    /** 2. LOGIC FOR EXCHANGE RATES SWAP **/
    const isCustomCheckbox = document.querySelector('input[name="is_custom"]');
    const standardRateInput = document.querySelector('select[name="exchange_rate"]');
    const customRateInput = document.querySelector('input[name="exchange_custom_rate"]');

    if (isCustomCheckbox) {
        const toggleRates = () => {
            const standardWrapper = standardRateInput?.closest('div');
            const customWrapper = customRateInput?.closest('div');

            if (isCustomCheckbox.checked) {
                if (customWrapper) customWrapper.style.display = 'block';
                if (standardWrapper) standardWrapper.style.display = 'none';
                // Optional: Clear standard rate when custom is active
                if (standardRateInput) standardRateInput.value = "";
            } else {
                if (customWrapper) customWrapper.style.display = 'none';
                if (standardWrapper) standardWrapper.style.display = 'block';
                // Optional: Clear custom rate when standard is active
                if (customRateInput) customRateInput.value = "";
            }
        };

        toggleRates();
        isCustomCheckbox.addEventListener('change', toggleRates);
    }
});