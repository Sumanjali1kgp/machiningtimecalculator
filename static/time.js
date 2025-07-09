// time.js — Streamlined and Modular Time Calculation Logic

// Global setup time value (updated from input)
let manualSetupTime = 0;

/** Helper: Safely update a UI element by ID */
function updateIfExists(id, value, formatter = v => v.toFixed(2)) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = formatter(value);
        el.dataset.total = value.toString();
        return true;
    }
    return false;
}

/** Update manual setup time and recalculate */
function updateSetupTime() {
    const input = document.getElementById('manualSetupTime');
    manualSetupTime = input ? parseFloat(input.value) || 0 : 0;
    updateIfExists('setupTime', manualSetupTime);
    calculateAndDisplayTimes();
}

/** Update tool time and recalculate */
function updateToolTime() {
    const input = document.getElementById('manualToolTime');
    const value = input ? parseFloat(input.value) || 0 : 0;
    updateIfExists('toolTime', value);
    calculateAndDisplayTimes();
}

/** Update miscellaneous time and recalculate */
function updateMiscTime() {
    const input = document.getElementById('manualMiscTime');
    const value = input ? parseFloat(input.value) || 0 : 0;
    updateIfExists('miscTime', value);
    calculateAndDisplayTimes();
}

/** Show the time section */
function showTimeSection() {
    const timeSection = document.getElementById('timeSection');
    if (timeSection) {
        // Ensure the section is visible and has proper display
        timeSection.style.display = 'block';
        timeSection.style.visibility = 'visible';
        timeSection.style.opacity = '1';
        timeSection.classList.remove('hidden');
        
        // Force a reflow to ensure styles are applied
        void timeSection.offsetHeight;
        
        // Scroll to the section smoothly
        timeSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        console.log('Time section visibility:', {
            display: window.getComputedStyle(timeSection).display,
            visibility: window.getComputedStyle(timeSection).visibility,
            opacity: window.getComputedStyle(timeSection).opacity,
            classList: Array.from(timeSection.classList)
        });
    } else {
        console.error('Time section element not found');
    }
}

/** Main function: calculate time from all operation entries and update UI */
async function calculateAndDisplayTimes() {
    console.log('🔍 Starting calculateAndDisplayTimes');
    
    // Show the time section when calculations are performed
    showTimeSection();
    const entries = document.querySelectorAll('.operation-entry, .process-entry');
    console.log(`Found ${entries.length} operation entries`);

    // Get manual input values
    const setup = parseFloat(document.getElementById('manualSetupTime')?.value) || 0;
    const tool = parseFloat(document.getElementById('manualToolTime')?.value) || 0;
    const misc = parseFloat(document.getElementById('manualMiscTime')?.value) || 0;
    
    // Calculate machining and idle times
    let totalMachining = 0, totalIdle = 0;
    
    entries.forEach((entry) => {
        const timeInput = entry.querySelector('input[type="number"]');
        if (timeInput) {
            const time = parseFloat(timeInput.value) || 0;
            const isIdle = entry.dataset.operationType === 'idle' || entry.classList.contains('idle');
            isIdle ? totalIdle += time : totalMachining += time;
        }
    });
    
    // Update the UI with calculated values
    updateIfExists('machiningTime', totalMachining);
    updateIfExists('idleTime', totalIdle);
    updateIfExists('setupTime', setup);
    updateIfExists('toolTime', tool);
    updateIfExists('miscTime', misc);
    
    // Calculate and update total time
    const totalTime = totalMachining + totalIdle + setup + tool + misc;
    updateIfExists('totalTime', totalTime);
    
    console.log('📊 Time calculations:', {
        machining: totalMachining,
        idle: totalIdle,
        setup,
        tool,
        misc,
        total: totalTime
    });

    const total = totalMachining + totalIdle + setup + tool + misc;
    
    console.log('📈 Calculated totals:', {
        totalMachining,
        totalIdle,
        setup,
        tool,
        misc,
        total
    });

    // Update UI
    console.log('🔄 Updating UI elements...');
    const updates = [
        { id: 'machiningTime', value: totalMachining },
        { id: 'idleTime', value: totalIdle },
        { id: 'setupTime', value: setup },
        { id: 'toolTime', value: tool },
        { id: 'miscTime', value: misc },
        { id: 'totalTime', value: total }
    ];

    updates.forEach(({ id, value }) => {
        const element = document.getElementById(id);
        console.log(`  ${id}:`, { 
            elementExists: !!element,
            currentValue: element?.textContent,
            newValue: value
        });
        updateIfExists(id, value);
    });

    // Show time section & enable cost button
    const timeSection = document.getElementById('timeSection');
    if (timeSection) {
        timeSection.classList.remove('hidden');
        console.log('⏱️  Time section shown');
    }
    
    const costBtn = document.getElementById('calculateCostBtn');
    if (costBtn) {
        costBtn.disabled = false;
        console.log('💰 Cost button enabled');
    }

    console.log('✅ Finished calculateAndDisplayTimes');
    return { total, totalMachining, totalIdle, setup, tool, misc };
}

/** Calculate time for individual operation and update the UI */
async function calculateOperationTime(entryId, operationType) {
    const entry = document.getElementById(entryId);
    if (!entry) throw new Error(`Entry '${entryId}' not found`);

    const operationId = entry.dataset.operationId || entryId.split('_')[1];
    const materialId = entry.dataset.materialId || document.getElementById('materialSelect')?.value;
    if (!materialId) throw new Error('Material not selected');

    if (operationId === '10' || operationType.toLowerCase() === 'idle') {
        const idleInput = entry.querySelector('input[name="idle_time"]');
        const idleTime = parseFloat(idleInput?.value) || 0;
        
        // Update the total time display
        const totalTimeInput = document.getElementById(`${entryId}_total_time`);
        if (totalTimeInput) {
            totalTimeInput.value = idleTime.toFixed(2);
        }
        
        // Update the entry data
        entry.dataset.calculationResult = JSON.stringify({ 
            operation_name: 'Idle', 
            time: idleTime 
        });
        
        updateOperationResultUI(entryId, { time: idleTime });
        return calculateAndDisplayTimes();
    }

    const dimensions = {};
    entry.querySelectorAll('input, select').forEach(input => {
        if (input.name && input.value !== '') {
            dimensions[input.name] = isNaN(input.value) ? input.value : parseFloat(input.value);
        }
    });

    const payload = {
        material_id: parseInt(materialId),
        operation_id: parseInt(operationId),
        operation_name: operationType,
        dimensions
    };

    const res = await fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    const time = parseFloat(data.time) || 0;

    document.getElementById(`${entryId}_time`).value = time.toFixed(2);
    entry.dataset.calculationResult = JSON.stringify(data.data || {});
    updateOperationResultUI(entryId, data);
    return calculateAndDisplayTimes();
}

/** Show result below each operation block */
function updateOperationResultUI(entryId, result) {
    const entry = document.getElementById(entryId);
    const container = entry?.querySelector('.operation-result');
    if (container) {
        container.innerHTML = `<div class="p-2 bg-gray-100 rounded mt-2">Time: ${parseFloat(result.time || 0).toFixed(2)} min</div>`;
    }
}

/** Exported public functions */
export {
    calculateOperationTime,
    calculateAndDisplayTimes,
    updateSetupTime,
    updateToolTime,
    updateMiscTime,
    updateIfExists,
    updateOperationResultUI
};

// Expose for inline HTML use
window.calculateOperationTime = calculateOperationTime;
window.calculateAndDisplayTimes = calculateAndDisplayTimes;
window.updateSetupTime = updateSetupTime;
window.updateToolTime = updateToolTime;
window.updateMiscTime = updateMiscTime;
window.updateIfExists = updateIfExists;
window.updateOperationResultUI = updateOperationResultUI;
