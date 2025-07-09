// cost.js — Handles all cost calculations and UI updates

// Constants
const OVERHEAD_RATE = 0.4; // 40% overhead

/**
 * Main function to calculate and display costs
 */
function calculateAndDisplayCosts() {
    const materialCost = parseFloat(document.getElementById('materialCostInput')?.value) || 0;
    const laborRatePerHour = parseFloat(document.getElementById('laborRateInput')?.value) || 0;
    const laborRatePerMin = laborRatePerHour / 60;
    const toolCostPerUse = parseFloat(document.getElementById('toolCostInput')?.value) || 0;
    const miscCost = parseFloat(document.getElementById('miscCostInput')?.value) || 0;

    // Time inputs (from time section IDs)
    const setupTime = parseFloat(document.getElementById('setupTime')?.textContent) || 0;
    const idleTime = parseFloat(document.getElementById('idleTime')?.textContent) || 0;
    const machiningTime = parseFloat(document.getElementById('machiningTime')?.textContent) || 0;
    const toolTime = parseFloat(document.getElementById('toolTime')?.textContent) || 0;

    // Cost calculations
    const setupIdleTime = setupTime + idleTime;
    const setupIdleCost = setupIdleTime * laborRatePerMin;
    const nonProductiveCost = materialCost + setupIdleCost;
    const machiningCost = machiningTime * laborRatePerMin;
    const toolingCost = toolCostPerUse + (toolTime * laborRatePerMin);

    const totalRawCost = nonProductiveCost + machiningCost + toolingCost + miscCost;
    const overheadCost = totalRawCost * OVERHEAD_RATE;
    const finalCost = totalRawCost + overheadCost;

    // Helper function to safely set text content
    const setTextContent = (id, text, prefix = '') => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = `${prefix}${text}`;
        } else {
            console.warn(`Element with ID '${id}' not found`);
        }
    };

    // Update UI elements safely
    setTextContent('setupIdleTimeValue', setupIdleTime.toFixed(2));
    setTextContent('setupIdleCost', `₹${setupIdleCost.toFixed(2)}`);
    setTextContent('materialCost', `₹${materialCost.toFixed(2)}`);
    setTextContent('machiningTimeValue', machiningTime.toFixed(2));
    setTextContent('machiningCost', `₹${machiningCost.toFixed(2)}`);
    setTextContent('toolingTimeValue', toolTime.toFixed(2));
    setTextContent('toolingCost', `₹${toolingCost.toFixed(2)}`);
    setTextContent('miscCostDisplay', `₹${miscCost.toFixed(2)}`);
    setTextContent('totalRawCost', `₹${totalRawCost.toFixed(2)}`);
    setTextContent('overheadCost', `+ ₹${overheadCost.toFixed(2)}`);
    setTextContent('finalCost', `₹${finalCost.toFixed(2)}`);

    // Update summary elements if they exist (optional)
    const summaryIds = ['totalRawCostSummary', 'overheadCostSummary', 'finalCostSummary'];
    const summaryExists = summaryIds.every(id => document.getElementById(id));
    
    if (summaryExists) {
        setTextContent('totalRawCostSummary', totalRawCost.toFixed(2));
        setTextContent('overheadCostSummary', overheadCost.toFixed(2));
        setTextContent('finalCostSummary', finalCost.toFixed(2));
    }

    // Show cost section
    document.getElementById('costDetailsSection').classList.remove('hidden');
}

// Helper function to get labor rate per minute
function getLaborRatePerMin() {
    const laborRatePerHour = parseFloat(document.getElementById('laborRateInput')?.value) || 0;
    return laborRatePerHour / 60;
}

/**
 * Calculate material cost based on input field
 * @returns {number} Material cost in rupees
 */
function calculateMaterialCost() {
    return parseFloat(document.getElementById('materialCostInput')?.value) || 0;
}

/**
 * Calculate labor cost for given minutes
 * @param {number} minutes - Time in minutes
 * @returns {number} Labor cost in rupees
 */
function calculateLaborCost(minutes) {
    return minutes * getLaborRatePerMin();
}

/**
 * Calculate machine cost based on machining time
 * @returns {number} Machine cost in rupees
 */
function calculateMachineCost() {
    const machiningTime = parseFloat(document.getElementById('machiningTime')?.textContent) || 0;
    return calculateLaborCost(machiningTime);
}

/**
 * Calculate tooling cost including tool cost per use and labor for tool time
 * @returns {number} Tooling cost in rupees
 */
function calculateToolingCost() {
    const toolCostPerUse = parseFloat(document.getElementById('toolCostInput')?.value) || 0;
    const toolTime = parseFloat(document.getElementById('toolTime')?.textContent) || 0;
    return toolCostPerUse + calculateLaborCost(toolTime);
}

/**
 * Calculate setup and idle time cost
 * @returns {number} Setup and idle cost in rupees
 */
function calculateSetupIdleCost() {
    const setupTime = parseFloat(document.getElementById('setupTime')?.textContent) || 0;
    const idleTime = parseFloat(document.getElementById('idleTime')?.textContent) || 0;
    return calculateLaborCost(setupTime + idleTime);
}

/**
 * Calculate total cost including all components
 * @returns {number} Total cost in rupees
 */
function calculateTotalCost() {
    const materialCost = calculateMaterialCost();
    const setupIdleCost = calculateSetupIdleCost();
    const machiningCost = calculateMachineCost();
    const toolingCost = calculateToolingCost();
    const miscCost = parseFloat(document.getElementById('miscCostInput')?.value) || 0;
    
    const subtotal = materialCost + setupIdleCost + machiningCost + toolingCost + miscCost;
    return subtotal + (subtotal * OVERHEAD_RATE);
}

/**
 * Update cost UI elements
 */
function updateCostUI() {
    // This will be called by the main calculateAndDisplayCosts function
    calculateAndDisplayCosts();
}

/**
 * Update cost summary table
 */
function updateCostSummaryTable() {
    // This function can be expanded if there's a separate summary table to update
    // Currently, the summary is updated in calculateAndDisplayCosts
}

// Export all functions
export {
    calculateAndDisplayCosts,
    calculateMaterialCost,
    calculateLaborCost,
    calculateMachineCost,
    calculateToolingCost,
    calculateSetupIdleCost,
    calculateTotalCost,
    updateCostUI,
    updateCostSummaryTable
};
