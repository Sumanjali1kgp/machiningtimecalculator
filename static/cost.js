// cost.js — Enhanced for detailed cost estimation workflow

// Configuration for rates and constants
const COST_RATES = {
    // Material rate (₹ per kg)
    MATERIAL_RATE_PER_KG: 200,
    
    // Labor and machine rates (₹ per minute)
    LABOR_RATE_PER_MIN: 5,        // Operator cost per minute
    MACHINE_RATE_PER_MIN: 10,      // Machine cost per minute (depreciation + power + maintenance)
    
    // Tooling costs
    TOOL_LIFE_MIN: 100,           // Tool life in minutes
    TOOL_COST: 5000,              // Cost of a new tool (₹)
    
    // Overhead and profit
    OVERHEAD_RATE: 0.4,           // 40% overhead on direct costs (updated to match UI)
    PROFIT_MARGIN: 0.15           // 15% profit margin
};

// Material density in g/cm³
const MATERIAL_DENSITY = {
    'aluminum': 2.7,
    'brass': 8.4,
    'copper': 8.96,
    'stainless steel': 8.0,
    'mild steel': 7.85,
    'titanium': 4.5,
    'plastic': 1.0,
    'default': 7.85
};

/**
 * Calculate material weight based on dimensions
 * @param {Object} dimensions - Object containing part dimensions
 * @param {string} materialType - Type of material (e.g., 'steel', 'aluminum')
 * @returns {number} Weight in kg
 */
function calculateMaterialWeight(dimensions = {}, materialType = 'steel') {
    const { length = 0, diameter = 0 } = dimensions;
    const density = MATERIAL_DENSITY[materialType.toLowerCase()] || MATERIAL_DENSITY.default;
    
    // Calculate volume in cm³ (convert mm to cm)
    const radiusCm = (diameter / 2) / 10;  // Convert mm to cm
    const lengthCm = length / 10;
    const volumeCm3 = Math.PI * Math.pow(radiusCm, 2) * lengthCm;
    
    // Weight in kg = volume (cm³) * density (g/cm³) / 1000
    return (volumeCm3 * density) / 1000;
}

/**
 * Calculate material cost based on weight and material type
 * @param {number} weightKg - Weight in kg
 * @param {string} materialType - Type of material
 * @returns {number} Material cost in ₹
 */
function calculateMaterialCost(weightKg, materialType = 'steel') {
    // Material-specific adjustments can be added here
    return weightKg * COST_RATES.MATERIAL_RATE_PER_KG;
}

/**
 * Calculate labor cost based on operation time
 * @param {number} operationTime - Total operation time in minutes
 * @returns {number} Labor cost in ₹
 */
function calculateLaborCost(operationTime) {
    return operationTime * COST_RATES.LABOR_RATE_PER_MIN;
}

/**
 * Calculate machine cost based on operation time
 * @param {number} operationTime - Total operation time in minutes
 * @returns {number} Machine cost in ₹
 */
function calculateMachineCost(operationTime) {
    return operationTime * COST_RATES.MACHINE_RATE_PER_MIN;
}

/**
 * Calculate tooling cost based on tool usage time
 * @param {number} toolTime - Tool usage time in minutes
 * @returns {number} Tooling cost in ₹
 */
function calculateToolingCost(toolTime) {
    if (!toolTime) return 0;
    const toolUsage = toolTime / COST_RATES.TOOL_LIFE_MIN;
    return toolUsage * COST_RATES.TOOL_COST;
}

/**
 * Calculate combined setup and idle time cost
 * @param {number} setupTime - Total setup time in minutes
 * @param {number} idleTime - Total idle time in minutes
 * @returns {number} Combined setup and idle cost in ₹
 */
function calculateSetupIdleCost(setupTime = 0, idleTime = 0) {
    const totalTime = setupTime + idleTime;
    return totalTime * COST_RATES.LABOR_RATE_PER_MIN;
}

/**
 * Calculate total cost including all components
 * @param {Object} params - Cost components
 * @param {number} params.materialCost - Material cost
 * @param {number} params.laborCost - Labor cost
 * @param {number} params.machineCost - Machine cost
 * @param {number} params.toolingCost - Tooling cost
 * @param {number} params.setupIdleCost - Setup and idle time cost
 * @returns {Object} Object containing all cost components
 */
function calculateTotalCost({ 
    materialCost = 0, 
    laborCost = 0, 
    machineCost = 0, 
    toolingCost = 0, 
    setupIdleCost = 0
} = {}) {
    const directCosts = materialCost + laborCost + machineCost + toolingCost + setupIdleCost;
    const results = {
        material: materialCost,
        labor: laborCost,
        machine: machineCost,
        tooling: toolingCost,
        setupIdle: setupIdleCost,
        // Overhead (40% of direct costs)
        overhead: directCosts * COST_RATES.OVERHEAD_RATE,
        // Profit (15% of total cost before profit)
        profit: (directCosts * (1 + COST_RATES.OVERHEAD_RATE)) * COST_RATES.PROFIT_MARGIN
    };
    
    // Calculate final cost (direct + overhead + profit)
    const finalCost = directCosts + results.overhead + results.profit;
    results.finalCost = finalCost;
    results.subtotal = directCosts;
    results.total = finalCost;
    
    return results;
}

/**
 * Main function to calculate and display all costs
 * @param {Object} times - Object containing time components
 * @param {Object} dimensions - Object containing part dimensions
 * @param {string} materialType - Type of material
 * @param {number} operationCount - Number of operations
 * @returns {Object} Object containing all cost components
 */
function calculateAndDisplayCosts({ 
    totalTime = 0, 
    totalToolTime = 0, 
    totalSetupTime = 0,
    totalIdleTime = 0
} = {}, dimensions = {}, materialType = 'mild steel') {
    // 1. Calculate material cost
    const weight = calculateMaterialWeight(dimensions, materialType);
    const materialCost = calculateMaterialCost(weight, materialType);
    
    // 2. Calculate setup and idle time cost
    const setupIdleCost = calculateSetupIdleCost(totalSetupTime, totalIdleTime);
    
    // 3. Calculate machining cost
    const machiningCost = calculateLaborCost(totalTime);
    
    // 4. Calculate tooling cost
    const toolingCost = calculateToolingCost(totalToolTime);
    
    // Calculate total raw cost (before overhead and profit)
    const totalRawCost = materialCost + setupIdleCost + machiningCost + toolingCost;
    
    // Calculate final cost with overhead and profit
    const overhead = totalRawCost * COST_RATES.OVERHEAD_RATE;
    const finalCost = totalRawCost + overhead;
    
    // Prepare detailed cost breakdown
    const costs = {
        material: materialCost,
        setupIdle: setupIdleCost,
        machining: machiningCost,
        tooling: toolingCost,
        totalRaw: totalRawCost,
        overhead,
        finalCost,
        weight,
        totalTime: totalTime,
        setupTime: totalSetupTime,
        idleTime: totalIdleTime,
        toolTime: totalToolTime
    };
    
    // Update the UI with detailed cost breakdown
    updateCostUI(costs);
    
    return costs;
}

/**
 * Format currency value
 * @param {number} value - Numeric value to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

/**
 * Update the cost section in the UI with detailed breakdown
 * @param {Object} costs - Object containing cost components
 */
function updateCostUI(costs) {
    const costSection = document.getElementById('costEstimationSection');
    if (!costSection) return;
    
    // Show the cost section if it was hidden
    costSection.style.display = 'block';
    
    // Helper function to update an element's text content
    const updateElement = (id, value, isTime = false) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = isTime ? value : formatCurrency(value);
        }
    };
    
    // Update material information
    updateElement('materialWeight', costs.weight ? `${costs.weight.toFixed(3)} kg` : 'N/A', true);
    
    // Update cost summary table
    updateElement('materialCost', costs.material);
    updateElement('setupIdleCost', costs.setupIdle);
    updateElement('machiningCost', costs.machining);
    updateElement('toolingCost', costs.tooling);
    updateElement('overheadCost', costs.overhead);
    updateElement('totalRawCost', costs.totalRaw);
    updateElement('finalCost', costs.finalCost);
    
    // Update time information
    updateElement('totalTime', `${costs.totalTime.toFixed(2)} min`, true);
    updateElement('setupTime', `${costs.setupTime.toFixed(2)} min`, true);
    updateElement('idleTime', `${costs.idleTime.toFixed(2)} min`, true);
    updateElement('toolTime', `${costs.toolTime.toFixed(2)} min`, true);
    
    // Generate and update the cost summary table
    updateCostSummaryTable(costs);
}

/**
 * Generate and update the cost summary table in the UI
 * @param {Object} costs - Object containing cost components
 */
function updateCostSummaryTable(costs) {
    const summaryTable = document.getElementById('costSummaryTable');
    if (!summaryTable) return;
    
    const operationCount = costs.operationCount || 1;
    const perUnitCost = costs.total / operationCount;
    
    const rows = [
        { item: 'Material Cost', time: '—', cost: costs.material },
        { item: 'Labor Cost', time: '—', cost: costs.labor },
        { item: 'Machine Cost', time: '—', cost: costs.machine },
        { item: 'Tooling Cost', time: '—', cost: costs.tooling },
        { item: 'Setup & Idle Cost', time: '—', cost: costs.setupIdle },
        { 
            item: `Overhead (${(COST_RATES.OVERHEAD_RATE * 100).toFixed(0)}%)`,
            time: '—',
            cost: costs.overhead,
            className: 'border-t-2 border-gray-200'
        },
        { 
            item: `Profit Margin (${(COST_RATES.PROFIT_MARGIN * 100).toFixed(0)}%)`,
            time: '—',
            cost: costs.profit,
            className: 'border-b-2 border-gray-200'
        },
        { 
            item: `Total Cost${operationCount > 1 ? ` (${operationCount} pcs)` : ''}`,
            time: '—',
            cost: costs.total,
            className: 'font-bold bg-gray-50',
            isTotal: true
        }
    ];
    
    // Add per-unit cost if multiple operations
    if (operationCount > 1) {
        rows.push({
            item: 'Cost per Unit',
            time: '—',
            cost: perUnitCost,
            className: 'text-sm text-gray-600',
            isSubtotal: true
        });
    }
    
    // Generate table rows
    const tbody = summaryTable.querySelector('tbody') || document.createElement('tbody');
    tbody.innerHTML = '';
    
    rows.forEach(row => {
        const tr = document.createElement('tr');
        if (row.className) tr.className = row.className;
        
        const costClass = row.isTotal ? 'text-green-600 font-bold' : 
                           row.isSubtotal ? 'text-blue-600' : 'text-gray-700';
        
        tr.innerHTML = `
            <td class="px-4 py-2 text-sm ${costClass}">${row.item}</td>
            <td class="px-4 py-2 text-sm text-gray-500 text-right">${row.time}</td>
            <td class="px-4 py-2 text-sm font-medium text-right ${costClass}">₹${formatCurrency(row.cost)}</td>
        `;
        
        tbody.appendChild(tr);
    });
    
    summaryTable.appendChild(tbody);
    
    // Update the total cost display
    updateIfExists('finalCost', costs.total, v => `₹${formatCurrency(v)}`);
    updateIfExists('totalRawCost', costs.material + costs.labor + costs.machine + costs.tooling + costs.setupIdle, 
                  v => `₹${formatCurrency(v)}`);
}

// Export public functions
export {
    calculateMaterialCost,
    calculateLaborCost,
    calculateMachineCost,
    calculateToolingCost,
    calculateSetupIdleCost,
    calculateTotalCost,
    calculateAndDisplayCosts,
    formatCurrency,
    updateCostUI,
    updateCostSummaryTable,
    COST_RATES
};

// Make functions available globally for inline HTML event handlers
window.calculateAndDisplayCosts = calculateAndDisplayCosts;
window.updateCostUI = updateCostUI;
window.updateCostSummaryTable = updateCostSummaryTable;
