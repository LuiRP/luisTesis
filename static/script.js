window.addEventListener('load', function () {
    /** 1. LOGIC FOR CREATED_AT (unchanged) **/
    const dateInput = document.querySelector('input[name="created_at"]');
    if (dateInput) {
        dateInput.type = 'datetime-local';
        const now = new Date();
        const formattedNow = now.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
        dateInput.max = formattedNow;
        if (dateInput.value) {
            const currentVal = new Date(dateInput.value);
            if (!isNaN(currentVal)) {
                dateInput.value = currentVal.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
            }
        }
    }

    /** 2. LOGIC FOR EXCHANGE RATES & CURRENCY **/
    const currencySelect = document.querySelector('select[name="currency"]');
    const isCustomCheckbox = document.querySelector('input[name="is_custom"]');
    const standardRateInput = document.querySelector('select[name="exchange_rate"]');
    const customRateInput = document.querySelector('input[name="exchange_custom_rate"]');

    if (currencySelect && isCustomCheckbox) {
        const updateVisibility = () => {
            const standardWrapper = standardRateInput?.closest('div');
            const customWrapper = customRateInput?.closest('div');
            const checkboxWrapper = isCustomCheckbox?.closest('div');

            // If currency is VEs, hide everything related to exchange rates
            if (currencySelect.value === 'VES') {
                if (standardWrapper) standardWrapper.style.display = 'none';
                if (customWrapper) customWrapper.style.display = 'none';
                if (checkboxWrapper) checkboxWrapper.style.display = 'none';

                // Reset values so they don't interfere with the form submission
                if (standardRateInput) standardRateInput.value = "";
                if (customRateInput) customRateInput.value = "";
                isCustomCheckbox.checked = false;
            }
            // If currency is NOT VEs, show the checkbox and handle standard/custom toggle
            else {
                if (checkboxWrapper) checkboxWrapper.style.display = 'block';

                if (isCustomCheckbox.checked) {
                    if (customWrapper) customWrapper.style.display = 'block';
                    if (standardWrapper) standardWrapper.style.display = 'none';
                } else {
                    if (customWrapper) customWrapper.style.display = 'none';
                    if (standardWrapper) standardWrapper.style.display = 'block';
                }
            }
        };

        // Run on page load and whenever currency or checkbox changes
        updateVisibility();
        currencySelect.addEventListener('change', updateVisibility);
        isCustomCheckbox.addEventListener('change', updateVisibility);
    }
});