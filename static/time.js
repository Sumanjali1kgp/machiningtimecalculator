// time.js — Handles all time calculations and UI updates for machining operations

// Setup time value (in minutes)
let manualSetupTime = 0;

// Calculate the time for a single operation entry
async function calculateOperationTime(entryId, operationType) {
    try {
        console.log('Calculating time for entry:', entryId);
        const entry = document.getElementById(entryId);
        if (!entry) {
            console.error('Entry not found with ID:', entryId);
            throw new Error(`Could not find entry with ID: ${entryId}`);
        }

        // Get operation ID from data attribute or parse from ID
        let operationId = entry.dataset.operationId;
        if (!operationId) {
            const idParts = entry.id.split('_');
            if (idParts.length >= 2) {
                operationId = idParts[1];
            } else {
                console.error('Could not parse operation ID from entry ID:', entry.id);
                throw new Error('Could not determine operation type.');
            }
        }

        // Handle idle operations (operation_id 10) differently - just use the input value directly
        if (operationId === '10' || operationType.toLowerCase() === 'idle') {
            const idleTimeInput = entry.querySelector('input[name="idle_time"]');
            if (!idleTimeInput) {
                throw new Error('Idle time input not found');
            }
            
            const idleTime = parseFloat(idleTimeInput.value) || 0;
            const result = {
                time: idleTime,
                data: {
                    operation_name: 'Idle',
                    time: idleTime,
                    description: 'User-specified idle time'
                }
            };

            const timeInput = document.getElementById(`${entryId}_time`);
            if (timeInput) {
                timeInput.value = idleTime.toFixed(2);
            }

            entry.dataset.calculationResult = JSON.stringify(result.data);
            updateOperationResultUI(entryId, result);
            await calculateAndDisplayTimes();
            return result;
        }

        // For non-idle operations, proceed with normal calculation
        const materialId = entry.dataset.materialId || document.getElementById('materialSelect')?.value;
        if (!materialId) throw new Error('Please select a material before calculating.');

        // Gather all inputs for this entry
        const dimensions = {};
        entry.querySelectorAll('input, select').forEach(input => {
            if (input.name && input.value !== '') {
                dimensions[input.name] = isNaN(parseFloat(input.value)) 
                    ? input.value 
                    : parseFloat(input.value);
            }
        });

        console.log('Using operation ID:', operationId, 'for entry:', entryId);

        const payload = {
            material_id: parseInt(materialId, 10),
            operation_id: parseInt(operationId, 10),
            operation_name: operationType,
            dimensions
        };

        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to calculate operation time');
        }

        const result = await response.json();
        
        const timeInput = document.getElementById(`${entryId}_time`);
        if (timeInput) {
            timeInput.value = parseFloat(result.time || 0).toFixed(2);
        }

        entry.dataset.calculationResult = JSON.stringify(result.data || {});
        updateOperationResultUI(entryId, result);
        await calculateAndDisplayTimes();
        
        return result;
    } catch (error) {
        console.error('Error in calculateOperationTime:', error);
        const timeInput = document.getElementById(`${entryId}_time`);
        if (timeInput) {
            timeInput.value = 'Error';
            timeInput.title = error.message || 'Calculation failed';
        }
        alert(`Error: ${error.message || 'Failed to calculate operation time'}`);
        throw error;
    }
}
// Validate and invoke the time calculation
export async function calculateOperation(entryId, operationType) {
    const resultDiv = document.getElementById(`result-${entryId}`);
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="alert alert-info">Calculating...</div>';
    }

    try {
        // Validate the form before calculating
        validateOperationForm(entryId, operationType); // Make sure this is defined!

        // Perform the time calculation
        await calculateOperationTime(entryId, operationType);

        if (resultDiv) {
            resultDiv.innerHTML = '<div class="alert alert-success">Time calculated successfully</div>';
        }
    } catch (error) {
        if (resultDiv) {
            resultDiv.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
        }
        console.error('Error in calculateOperation:', error);
    }
}

// Update UI with the results of a single operation
function updateOperationResultUI(entryId, result) {
    const entry = document.getElementById(entryId);
    if (!entry || !result) return;

    const resultContainer = entry.querySelector('.operation-result');
    if (!resultContainer) return;

    resultContainer.innerHTML = `
        <div class="p-2 bg-gray-50 rounded mt-2">
            <div class="text-sm text-gray-600">Time: ${parseFloat(result.time || 0).toFixed(2)} min</div>
        </div>
    `;
}

// Update tool time
function updateToolTime() {
    const toolTimeInput = document.getElementById('toolTimeInput');
    const toolTimeDisplay = document.getElementById('toolTime');

    if (toolTimeInput && toolTimeDisplay) {
        const toolTime = parseFloat(toolTimeInput.value) || 0;
        toolTimeDisplay.textContent = toolTime.toFixed(2) + ' min';
        calculateAndDisplayTimes();
    }
}

// Update miscellaneous time
function updateMiscTime() {
    const miscInput = document.getElementById('miscInput');
    const miscTimeElement = document.getElementById('miscTime');
    
    if (!miscInput || !miscTimeElement) return;

    // Get the manually entered time
    const miscTime = parseFloat(miscInput.value) || 0;
    
    if (isNaN(miscTime) || miscTime < 0) {
        alert('Please enter a valid positive number for miscellaneous time');
        return;
    }
    
    // Update the display and store the value directly
    miscTimeElement.textContent = miscTime.toFixed(2) + ' min';
    miscTimeElement.dataset.total = miscTime.toString();
    
    // Update the total time calculation
    calculateAndDisplayTimes();
}

// Calculate and display all time metrics
async function calculateAndDisplayTimes() {
    console.log('Starting calculateAndDisplayTimes');
    try {
        // Ensure time section is visible
        const timeSectionElement = document.getElementById('timeSection');
        if (timeSectionElement) {
            timeSectionElement.style.display = 'block';
            timeSectionElement.classList.remove('hidden');
            // Force a reflow to ensure the UI updates
            void timeSectionElement.offsetHeight;
        }

        const entries = Array.from(document.querySelectorAll('.process-entry'));
        console.log(`Found ${entries.length} process entries`);
        
        let totalMachiningTime = 0;
        let totalIdleTime = 0;
        
        // Get input values with fallback to 0
        const setupTimeInput = document.getElementById('setupTimeInput');
        const toolTimeInput = document.getElementById('toolTimeInput');
        const miscInput = document.getElementById('miscInput');
        
        let totalSetupTime = setupTimeInput ? parseFloat(setupTimeInput.value) || 0 : 0;
        let totalToolTime = toolTimeInput ? parseFloat(toolTimeInput.value) || 0 : 0;
        let totalMiscTime = miscInput ? parseFloat(miscInput.value) || 0 : 0;

        // Process each operation entry
        for (const entry of entries) {
            const entryId = entry.id || '';
            const timeInput = document.getElementById(`${entryId}_time`);
            
            if (timeInput && timeInput.value.trim() !== '' && !isNaN(parseFloat(timeInput.value))) {
                const time = parseFloat(timeInput.value);
                console.log(`Processing entry ${entryId} with time: ${time} minutes`);
                
                // Check if this is an idle operation
                const isIdle = entryId.includes('idle') || entryId.includes('Idle');
                
                if (isIdle) {
                    totalIdleTime += time;
                    console.log(`Added ${time} minutes to idle time`);
                } else {
                    totalMachiningTime += time;
                    console.log(`Added ${time} minutes to machining time`);
                }
            } else {
                console.log(`Skipping entry ${entryId} - no valid time input found`);
                console.log('Time input element:', timeInput);
            }
        }

        console.log('Updating UI with calculated times:', {
            machining: totalMachiningTime,
            idle: totalIdleTime,
            setup: totalSetupTime,
            tool: totalToolTime,
            misc: totalMiscTime
        });

        // Update the UI with the calculated times
        const updates = [
            { id: 'machiningTime', value: totalMachiningTime },
            { id: 'idleTime', value: totalIdleTime },
            { id: 'setupTime', value: totalSetupTime },
            { id: 'toolTime', value: totalToolTime },
            { id: 'miscTime', value: totalMiscTime }
        ];

        updates.forEach(({id, value}) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value.toFixed(2) + ' min';
                element.dataset.total = value.toString();
                console.log(`Updated ${id}: ${element.textContent}`);
            } else {
                console.warn(`Element with id '${id}' not found`);
            }
        });
        
        // Calculate and update total time
        const totalTime = totalMachiningTime + totalIdleTime + totalSetupTime + totalToolTime + totalMiscTime;
        const totalTimeElement = document.getElementById('totalTime');
        if (totalTimeElement) {
            totalTimeElement.textContent = totalTime.toFixed(2) + ' min';
            totalTimeElement.dataset.total = totalTime.toString();
            console.log(`Updated totalTime: ${totalTimeElement.textContent}`);
        }
        
        // Make sure the time section is visible
        const timeSection = document.getElementById('timeSection');
        if (timeSection) {
            timeSection.style.display = 'block';
            timeSection.classList.remove('hidden');
            console.log('Time section is now visible');
        } else {
            console.warn('timeSection element not found');
        }

        // Enable cost calculation button
        const calculateCostBtn = document.getElementById('calculateCostBtn');
        if (calculateCostBtn) {
            calculateCostBtn.disabled = false;
            calculateCostBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            console.log('Enabled calculateCostBtn');
        } else {
            console.warn('calculateCostBtn not found');
        }

        const results = {
            totalTime,
            totalMachiningTime,
            totalIdleTime,
            totalSetupTime,
            totalToolTime,
            totalMiscTime
        };
        
        console.log('Calculation completed successfully', results);
        return results;
    } catch (error) {
        console.error('Error in calculateAndDisplayTimes:', error);
        throw error;
    }
}

// Update setup time from manual input
function updateSetupTime() {
    const setupTimeInput = document.getElementById('setupTimeInput');
    if (setupTimeInput) {
        manualSetupTime = parseFloat(setupTimeInput.value) || 0;
        // Recalculate times when setup time changes
        calculateAndDisplayTimes();
    }
    // Return 0 as a fallback to indicate no setup time
    return 0;
}

// Helper function to update UI elements if they exist
function updateIfExists(id, value, formatter = v => v) {
    const element = document.getElementById(id);
    if (element) {
        const formattedValue = formatter(value);
        console.log(`Updating ${id}:`, { value, formatted: formattedValue });
        element.textContent = formattedValue;
        element.dataset.total = value.toString();
        return true;
    }
    console.warn(`Element with id '${id}' not found`);
    return false;
}

// Calculate total time including all components
function calculateTotalTime() {
    const machiningTime = parseFloat(document.getElementById('machiningTime')?.textContent || 0);
    const idleTime = parseFloat(document.getElementById('idleTime')?.textContent || 0);
    const setupTime = parseFloat(document.getElementById('setupTime')?.textContent || 0);
    const toolTime = parseFloat(document.getElementById('toolTime')?.textContent || 0);
    const miscTime = parseFloat(document.getElementById('miscTime')?.textContent || 0);

    const totalTime = machiningTime + idleTime + setupTime + toolTime + miscTime;
    
    const totalTimeElement = document.getElementById('totalTime');
    if (totalTimeElement) {
        totalTimeElement.textContent = totalTime.toFixed(2) + ' min';
    }
    
    return totalTime;
}

// Export public functions
export {
    calculateOperationTime,
    updateToolTime,
    updateMiscTime,
    updateSetupTime,
    updateOperationResultUI,
    updateIfExists,
    calculateAndDisplayTimes,
    calculateTotalTime
};

// Make functions available globally for inline HTML event handlers
window.calculateOperationTime = calculateOperationTime;
window.updateToolTime = updateToolTime;
window.updateMiscTime = updateMiscTime;
window.updateSetupTime = updateSetupTime;
window.updateOperationResultUI = updateOperationResultUI;
window.updateIfExists = updateIfExists;
window.calculateAndDisplayTimes = calculateAndDisplayTimes;
window.calculateTotalTime = calculateTotalTime;
