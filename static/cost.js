// Cost calculation module for Machining Time Calculator

// Cost calculation constants
const COST_RATES = {
    // Labor and machine rate (k1) - cost per minute for all time-based activities
    LABOR_RATE: 0.5,  // $ per minute
    MACHINE_RATE: 1.0, // $ per minute
    
    // Material cost rates ($ per cubic mm)
    MATERIAL_RATES: {
        'aluminum': 0.002,
        'steel': 0.005,
        'stainless': 0.008,
        'titanium': 0.02,
        'brass': 0.01,
        'copper': 0.015,
        'plastic': 0.001
    },
    
    // Overhead rate (percentage of direct costs)
    OVERHEAD_RATE: 0.3, // 30%
    
    // Profit margin (percentage of total cost)
    PROFIT_MARGIN: 0.2 // 20%
};

/**
 * Calculate material cost based on volume and material type
 * @param {number} volume - Volume in cubic mm
 * @param {string} materialType - Type of material (e.g., 'aluminum', 'steel')
 * @returns {number} Material cost in USD
 */
export function calculateMaterialCost(volume, materialType) {
    const rate = COST_RATES.MATERIAL_RATES[materialType.toLowerCase()] || 0.01; // Default rate
    return volume * rate;
}

/**
 * Calculate labor cost based on time in minutes
 * @param {number} timeInMinutes - Time in minutes
 * @returns {number} Labor cost in USD
 */
export function calculateLaborCost(timeInMinutes) {
    return timeInMinutes * COST_RATES.LABOR_RATE;
}

/**
 * Calculate machine cost based on time in minutes
 * @param {number} timeInMinutes - Time in minutes
 * @returns {number} Machine cost in USD
 */
export function calculateMachineCost(timeInMinutes) {
    return timeInMinutes * COST_RATES.MACHINE_RATE;
}

/**
 * Calculate total cost including overhead and profit
 * @param {Object} costs - Object containing direct costs
 * @param {number} costs.material - Material cost
 * @param {number} costs.labor - Labor cost
 * @param {number} costs.machine - Machine cost
 * @returns {Object} Object containing all cost components
 */
export function calculateTotalCost({ material = 0, labor = 0, machine = 0 }) {
    const directCosts = material + labor + machine;
    const overhead = directCosts * COST_RATES.OVERHEAD_RATE;
    const subtotal = directCosts + overhead;
    const profit = subtotal * COST_RATES.PROFIT_MARGIN;
    const total = subtotal + profit;
    
    return {
        material,
        labor,
        machine,
        overhead,
        subtotal,
        profit,
        total
    };
}

/**
 * Format currency value
 * @param {number} value - Numeric value to format
 * @returns {string} Formatted currency string
 */
export function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

/**
 * Update the cost section in the UI
 * @param {Object} costs - Object containing cost components
 */
export function updateCostUI(costs) {
    const costSection = document.getElementById('costEstimationSection');
    if (!costSection) return;
    
    // Show the cost section if it was hidden
    costSection.style.display = 'block';
    
    // Update cost values in the UI
    const updateElement = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = formatCurrency(value);
        }
    };
    
    updateElement('materialCost', costs.material);
    updateElement('laborCost', costs.labor);
    updateElement('machineCost', costs.machine);
    updateElement('overheadCost', costs.overhead);
    updateElement('profitCost', costs.profit);
    updateElement('totalCost', costs.total);
}

// Initialize cost section to be hidden by default
function initCostSection() {
    const costSection = document.getElementById('costEstimationSection');
    if (costSection) {
        costSection.style.display = 'none';
    }
}

// Export public functions
const CostCalculator = {
    calculateMaterialCost,
    calculateLaborCost,
    calculateMachineCost,
    calculateTotalCost,
    updateCostUI,
    init: initCostSection
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCostSection);
} else {
    initCostSection();
}

// Make CostCalculator available globally
window.CostCalculator = CostCalculator;
