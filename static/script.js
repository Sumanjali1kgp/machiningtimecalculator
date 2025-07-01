// script.js - Main application script for the Machining Time Calculator

// Global variables
let operations = [];
let materials = [];
let currentOperationId = 0;
let currentOperationType = '';
let processCount = 0;
let formContainer, addProcessBtn;
let operationList; // Declare operationList as a global variable

// These will be set by the module loader in lathe.html
let calculateAndDisplayTimes, updateToolTime, updateMiscTime, updateSetupTime, calculateOperationTime, calculateAndDisplayCosts;

// Wait for the window to be fully loaded
window.addEventListener('load', () => {
    // These will be available after the modules are loaded
    calculateAndDisplayTimes = window.calculateAndDisplayTimes;
    updateToolTime = window.updateToolTime;
    updateMiscTime = window.updateMiscTime;
    updateSetupTime = window.updateSetupTime;
    calculateOperationTime = window.calculateOperationTime;
    calculateAndDisplayCosts = window.calculateAndDisplayCosts;
    
    console.log('Global functions initialized in script.js');
});

// Helper function to update UI elements if they exist
function updateIfExists(id, value, formatter = v => v) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = formatter(value);
    }
}


document.addEventListener('DOMContentLoaded', () => {
    initApp();
    
    // Toggle between time and cost sections
    const calculateTimeBtn = document.getElementById('calculateTimeBtn');
    const calculateCostBtn = document.getElementById('calculateCostBtn');
    const timeSection = document.getElementById('timeSection');
    const costSection = document.getElementById('costDetailsSection');
    
    if (calculateTimeBtn && timeSection) {
        // Remove any existing event listeners
        const newTimeBtn = calculateTimeBtn.cloneNode(true);
        calculateTimeBtn.parentNode.replaceChild(newTimeBtn, calculateTimeBtn);
        
        // Add new click handler
        newTimeBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Calculate Time button clicked');
            
            // Debug: Log current state
            console.log('Time section before show:', {
                display: timeSection.style.display,
                classList: timeSection.className,
                hidden: timeSection.hidden,
                offsetParent: timeSection.offsetParent,
                clientHeight: timeSection.clientHeight,
                scrollHeight: timeSection.scrollHeight
            });
            
            // Show the time section
            timeSection.classList.remove('hidden');
            timeSection.style.display = 'block';
            
            // Hide the cost section if it exists
            if (costSection) {
                costSection.classList.add('hidden');
                costSection.style.display = 'none';
            }
            
            // Force a reflow to ensure the UI updates
            void timeSection.offsetHeight;
            
            console.log('Time section after show:', {
                display: timeSection.style.display,
                classList: timeSection.className,
                hidden: timeSection.hidden,
                offsetParent: timeSection.offsetParent,
                clientHeight: timeSection.clientHeight,
                scrollHeight: timeSection.scrollHeight
            });
            
            try {
                console.log('Calling calculateAndDisplayTimes...');
                const result = await calculateAndDisplayTimes();
                console.log('calculateAndDisplayTimes completed with result:', result);
                
                // Force another reflow after calculation
                void timeSection.offsetHeight;
                
                console.log('Time section after calculation:', {
                    display: timeSection.style.display,
                    classList: timeSection.className,
                    hidden: timeSection.hidden,
                    offsetParent: timeSection.offsetParent,
                    clientHeight: timeSection.clientHeight,
                    scrollHeight: timeSection.scrollHeight
                });
                
                // Scroll to the time section
                timeSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } catch (error) {
                console.error('Error in calculateAndDisplayTimes:', error);
            }
        });
    }
    
    if (calculateCostBtn && costSection) {
        calculateCostBtn.addEventListener('click', () => {
            costSection.classList.remove('hidden');
            if (timeSection) timeSection.classList.add('hidden');
            calculateAndDisplayCosts();
        });
    }
    
    // Sidebar drawer universal toggle
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    function openSidebar() {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
    }
    function closeSidebar() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
    }
    if (hamburger) {
        hamburger.addEventListener('click', openSidebar);
    }
    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }
});

// ============================ INITIALIZATION ============================

/**
 * Initialize the application
 * - Sets up UI elements
 * - Initializes event listeners
 * - Loads initial data
 */
async function initApp() {
    // Initialize UI elements
    const materialSelect = document.getElementById('materialSelect');
    const operationSelect = document.getElementById('operationSelect');
    formContainer = document.getElementById('formContainer');
    operationList = document.getElementById('operationList');
    
    if (!operationList) {
        console.error('Operation list container not found in the DOM');
    }
    
    // Set up event listeners for form elements
    if (materialSelect) materialSelect.addEventListener('change', onMaterialSelected);
    if (operationSelect) operationSelect.addEventListener('change', addProcess);
    
    // Initialize sections as hidden
    const timeSectionEl = document.getElementById('timeSection');
    const costSectionEl = document.getElementById('costSection');
    
    if (timeSectionEl) {
        timeSectionEl.style.display = 'none';
        timeSectionEl.classList.add('hidden');
    }
    
    if (costSectionEl) {
        costSectionEl.style.display = 'none';
        costSectionEl.classList.add('hidden');
    }
    
    // Load data asynchronously
    await Promise.all([
        fetchAndPopulateMaterials(),
        fetchAndPopulateOperations()
    ]);
    
    // Set up button event listeners
    const setupCalculateButtons = () => {
        console.log('Setting up calculate buttons...');
        
        // Ensure time section is hidden by default
        const timeSection = document.getElementById('timeSection');
        if (timeSection) {
            timeSection.classList.add('hidden');
            console.log('Time section hidden by default');
        }

        // Time calculation button
        const calculateTimeBtn = document.getElementById('calculateTimeBtn');
        if (calculateTimeBtn) {
            console.log('Setting up calculateTimeBtn event listener');
            
            // Remove any existing event listeners
            const newBtn = calculateTimeBtn.cloneNode(true);
            calculateTimeBtn.parentNode.replaceChild(newBtn, calculateTimeBtn);
            
            // Add new event listener
            newBtn.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Calculate Time button clicked');
                console.log('Calculate Time button clicked');
                try {
                    // Show the time section
                    const timeSection = document.getElementById('timeSection');
                    if (timeSection) {
                        // Make sure the section is visible
                        timeSection.style.display = 'block';
                        timeSection.classList.remove('hidden');
                        
                        console.log('Calculating and displaying times...');
                        // Calculate and display times
                        const results = await calculateAndDisplayTimes();
                        console.log('Calculation results:', results);
                        
                        // Force UI update
                        document.body.style.visibility = 'hidden';
                        document.body.offsetHeight; // Trigger reflow
                        document.body.style.visibility = 'visible';
                        
                        // Scroll to the time section
                        console.log('Scrolling to time section...');
                        timeSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                } catch (error) {
                    console.error('Error in calculate time button click:', error);
                }
            });
        } else {
            console.warn('calculateTimeBtn not found in the DOM');
        }
        
        // Cost calculation button
        const calculateCostBtn = document.getElementById('calculateCostBtn');
        if (calculateCostBtn) {
            console.log('Found calculateCostBtn, adding event listener');
            // Remove any existing event listeners to prevent duplicates
            calculateCostBtn.replaceWith(calculateCostBtn.cloneNode(true));
            document.getElementById('calculateCostBtn').addEventListener('click', async () => {
                console.log('Calculate Cost button clicked');
                try {
                    toggleSection('costSection', true);
                    console.log('Calculating and displaying costs...');
                    await calculateAndDisplayCosts();
                } catch (error) {
                    console.error('Error in calculate cost button click:', error);
                }
            });
        } else {
            console.warn('calculateCostBtn not found in the DOM');
        }
    };
    
    // Set up the clear all button
    const clearAllBtn = document.getElementById('clearAllBtn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', clearAll);
    }
    
    // Show the time section by default when the page loads
    const timeSection = document.getElementById('timeSection');
    if (timeSection) {
        timeSection.style.display = ''; // Reset any inline display style
        timeSection.classList.remove('hidden');
    }
    
    // Hide the cost section by default
    const costSection = document.getElementById('costDetailsSection');
    if (costSection) {
        costSection.style.display = 'none'; // Explicitly hide with inline style
        costSection.classList.add('hidden');
    }
    
    // Initialize the calculate buttons
    setupCalculateButtons();
    
    // Also set up a small delay to ensure DOM is fully loaded
    setTimeout(() => {
        setupCalculateButtons();
        // Re-ensure visibility after potential async operations
        if (timeSection) {
            timeSection.style.display = '';
            timeSection.classList.remove('hidden');
        }
    }, 500);
    
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', clearAll);
    }
}

// Operation display names
const operationDisplayNames = {
    'facing': 'Facing',
    'turning': 'Turning',
    'drilling': 'Drilling',
    'boring': 'Boring',
    'threading': 'Threading',
    'knurling': 'Knurling',
    'parting': 'Parting',
    'grooving': 'Grooving',
    'milling': 'Milling',
    'slabmilling': 'Slab Milling',
    'facemilling': 'Face Milling',
    'endmilling': 'End Milling',
    'idle': 'Idle Time',
    'reaming': 'Reaming',

};

// Helper function to format numbers with specified decimal places
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return 'N/A';
    return typeof num === 'number' ? num.toFixed(decimals) : num;
}

// Fetch and populate materials from API
async function fetchAndPopulateMaterials() {
    try {
        const response = await fetch('/api/materials');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const materialsData = await response.json();
        
        materialSelect.innerHTML = '<option value="">Select Material</option>';
        materialsData.forEach(material => {
            const option = document.createElement('option');
            option.value = material.material_id;
            option.textContent = material.material_name;  // Add this line to display the material name
            materialSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading materials:', error);
        alert('Failed to load materials. Please try again later.');
    }
}

// Fetch and populate operations from API
async function fetchAndPopulateOperations() {
    try {
        const response = await fetch('/api/operations');
        const data = await response.json();
        operationSelect.innerHTML = '<option value="">Select Operation</option>';

        data.forEach(op => {
            if (op && op.operation_id) {
                const option = new Option(op.operation_name, op.operation_id);
                // Store the operation type in a data attribute for easy access
                option.dataset.type = op.operation_name.toLowerCase().replace(/\s+/g, '');
                operationSelect.add(option);
                operations[op.operation_id] = op.operation_name.toLowerCase();
            }
        });
    } catch (error) {
        console.error('Error loading operations:', error);
        loadDefaultOperations();
    }
}

// Load default operations if API fails
function loadDefaultOperations() {
    const defaultOperations = [
        { operation_id: 1, operation_name: 'Facing' },
        { operation_id: 2, operation_name: 'Turning' },
        { operation_id: 3, operation_name: 'Drilling' },
        { operation_id: 4, operation_name: 'Boring' },
        { operation_id: 5, operation_name: 'Reaming' },
        { operation_id: 6, operation_name: 'Threading' },
        { operation_id: 7, operation_name: 'Knurling' },
        { operation_id: 8, operation_name: 'Parting' },
        { operation_id: 9, operation_name: 'Grooving' },
        { operation_id: 10, operation_name: 'Idle' }
    ];
    
    operationSelect.innerHTML = '<option value="">Select Operation</option>';
    defaultOperations.forEach(op => {
        const option = new Option(op.operation_name, op.operation_id);
        operationSelect.add(option);
        operations[op.operation_id] = op.operation_name.toLowerCase();
    });
}

// Validate that a material is selected
function onMaterialSelected() {
    const selectedMaterial = materialSelect?.value;
    const errorElement = document.getElementById('materialError');

    if (!selectedMaterial) {
        if (errorElement) {
            errorElement.textContent = 'Please select a material';
        } else {
            console.error('Material error element not found');
        }
        return false;
    }

    if (errorElement) {
        errorElement.textContent = '';
    }
    return true;
}

// Called whenever material changes; optionally triggers recalculation for this process
function updateMaterial(processId, materialId) {
    console.log(`Updating material for ${processId} to materialId: ${materialId}`);

    const entry = document.getElementById(processId);
    if (!entry) return;

    const operationType = entry.querySelector('input[name="operation"]')?.value;
    if (operationType) {
        // Trigger recalculation for this operation if material changed
        calculateOperation(processId, operationType);
    }
}

// Add a new process entry to the list
function addProcess() {
    // Get the current values directly from the DOM
    const materialSelect = document.getElementById('materialSelect');
    const operationSelect = document.getElementById('operationSelect');
    
    if (!materialSelect || !operationSelect) {
        console.error('Required elements not found in the DOM');
        return;
    }
    
    const materialId = materialSelect.value;
    const operationId = operationSelect.value;
    
    if (!materialId) {
        alert('Please select a material first');
        return;
    }
    
    if (!operationId) {
        alert('Please select an operation');
        return;
    }
    
    // Get the selected option and its data
    const selectedOption = operationSelect.options[operationSelect.selectedIndex];
    
    // Get the operation type from the data-type attribute or fallback to the text content
    let operationType = selectedOption.getAttribute('data-type');
    if (!operationType) {
        // If no data-type, use the text content and clean it up
        operationType = selectedOption.textContent.trim().toLowerCase().replace(/\s+/g, '');
        // Update the data-type for future reference
        selectedOption.setAttribute('data-type', operationType);
    }
    
    // Create a unique ID for this process entry
    const timestamp = Date.now();
    const processId = `process_${operationId}_${timestamp}`;
    
    // Get the selected material
    const selectedMaterial = materialSelect.options[materialSelect.selectedIndex];
    
    console.log('Adding operation:', { 
        operationid: operationId, 
        operationname: selectedOption.textContent,
        materialid: materialId,
        materialname: selectedMaterial ? selectedMaterial.textContent : 'Not selected'
    });
    
    // Get the display name for the operation
    const operationName = operationDisplayNames[operationType] || operationType;
    
    // Create the process entry HTML
    const processHTML = `
        <div class="process-entry" id="${processId}" 
             data-operation-type="${operationType}"
             data-operation-id="${operationId}"
             data-material-id="${materialId}">
            <div class="process-header">
                <h4>${operationName}</h4>
                <button class="btn-remove" onclick="removeEntry('${processId}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="process-form">
                ${generateOperationForm(processId, operationType)}
            </div>
        </div>`;

    // Create a container div for the process entry
    const processEntry = document.createElement('div');
    processEntry.className = 'process-entry';
    processEntry.id = processId;
    processEntry.dataset.operationId = operationId;
    processEntry.dataset.materialId = materialId;
    processEntry.innerHTML = processHTML;
    
    // Add the process to the operation list
    if (operationList) {
        operationList.appendChild(processEntry);
        
        // Initialize the time input
        const timeInput = document.getElementById(`${processId}_time`);
        if (timeInput) {
            timeInput.addEventListener('input', () => {
                console.log(`Time input ${processId} changed:`, timeInput.value);
                calculateAndDisplayTimes();
            });
        }
    } else {
        console.error('Operation list container not found');
        return;
    }
    
    // Reset the operation select
    if (operationSelect) {
        operationSelect.value = '';
    }
    
    // Show the time section when a process is added
    toggleSection('timeSection', true);
    
    // Recalculate times
    calculateAndDisplayTimes();
    
    // Show action buttons if this is the first process
    const actionButtons = document.querySelector('.action-buttons');    
    if (actionButtons && actionButtons.style.display === 'none') {
        actionButtons.style.display = 'block';
    }

    console.log('Process successfully added.');
}

/**
 * Generate form HTML based on operation type
 * @param {string} operationId - The ID of the operation
 * @param {string} operationType - The type of operation (e.g., 'facing', 'turning')
 * @returns {string} HTML string for the operation form
 */
function generateOperationForm(operationId, operationType) {
    if (!operationType) {
        console.error('No operation type provided');
        return '';
    }

    // Use the provided operationId which already has the format 'process_X'
    const entryId = operationId;
    const opType = operationType.toLowerCase();
    
    // Helper function to create form groups
    const formGroup = (label, name, opts = {}) => {
        const { 
            type = 'text',
            step = '',
            min = '',
            value = '',
            required = true,
            options = []
        } = opts;
        const inputId = `${entryId}_${name}`;

        let input = '';
        if (type === 'select') {
            const optionTags = options
                .map(opt => `<option value="${opt.value}">${opt.text || opt.label || opt.value}</option>`)
                .join('');
            input = `
              <select class="form-control" id="${inputId}" name="${name}" ${required ? 'required' : ''}>
                  <option value="">-- Select --</option>${optionTags}
              </select>`;
    } else {
        input = `
          <input type="${type}"
                 class="form-control"
                 id="${inputId}"
                 name="${name}"
                 placeholder="${label}"
                 value="${value}"
                 ${required ? 'required' : ''}
                 ${step ? `step="${step}"` : ''}
                 ${min ? `min="${min}"` : ''}
          >`;
    }

    return `
      <div class="form-group mb-3">
        <label for="${inputId}" class="form-label">${label}</label>
        ${input}
      </div>`;
};
    
    // Form templates for each operation type
    const formTemplates = {
        'facing': () => [
            formGroup('Diameter (mm)', 'diameter'),
            formGroup('Depth of Cut (mm)', 'depth_of_cut'),
            formGroup('Feed (mm/rev)', 'feed'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'facing')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'turning': () => [
            formGroup('Start Diameter (mm)', 'start_diameter'),
            formGroup('End Diameter (mm)', 'end_diameter'),
            formGroup('Length (mm)', 'length'),
            formGroup('Depth of Cut (mm)', 'depth_of_cut'),
            formGroup('Feed (mm/rev)', 'feed'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'turning')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'drilling': () => [
            formGroup('Hole Depth (mm)', 'hole_depth'),
            formGroup('Hole Diameter (mm)', 'hole_diameter'),
            formGroup('Feed (mm/rev)', 'feed'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'drilling')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'reaming': () => [
            formGroup('Hole Diameter (mm)', 'hole_diameter'),
            formGroup('Hole Depth (mm)', 'hole_depth'),
            formGroup('Feed (mm/rev)', 'feed'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'reaming')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'boring': () => [
            formGroup('Hole Diameter (mm)', 'hole_diameter'),
            formGroup('Hole Depth (mm)', 'hole_depth'),
            formGroup('Cutting Depth (mm)', 'cutting_depth'),
            formGroup('Feed (mm/rev)', 'feed'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'boring')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'threading': () => [
            formGroup('Thread Length (mm)', 'thread_length'),
            formGroup('Thread Pitch (mm/thread)', 'thread_pitch'),
            formGroup('Threads per Pass', 'threads_per_pass'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'threading')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'grooving': () => [
            formGroup('Groove Width (mm)', 'groove_width'),
            formGroup('Groove Depth (mm)', 'groove_depth'),
            formGroup('Feed (mm/rev)', 'feed'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'grooving')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'parting': () => [
            formGroup('Parting Diameter (mm)', 'parting_diameter'),
            formGroup('Parting Tool Width (mm)', 'tool_width'),
            formGroup('Feed (mm/rev)', 'feed'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'parting')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'knurling': () => [
            formGroup('Knurling Length (mm)', 'knurling_length'),
            formGroup('Workpiece Diameter (mm)', 'workpiece_diameter'),
            formGroup('Knurl Pitch (teeth per inch)', 'knurl_pitch'),
            formGroup('Spindle Speed (RPM)', 'spindle_speed'),
            `<div class="form-group mt-4">
                <button type="button" 
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'knurling')">
                    <i class="fas fa-calculator"></i> Calculate Time
                </button>
                <div class="form-group">
                    <label for="${entryId}_time" class="form-label">Operation Time (minutes)</label>
                    <input id="${entryId}_time" 
                           type="number" 
                           class="form-control" 
                           placeholder="Enter time in minutes" 
                           step="0.01"
                           min="0"
                           onchange="calculateAndDisplayTimes()">
                </div>
            </div>`
        ].join(''),
        'idle': () => [
            formGroup('Idle Operation Type', 'idle_type', {
                type: 'select',
                options: [
                    { value: 'tool_movement', label: 'Tool Movement' },
                    { value: 'tool_replacement', label: 'Tool Replacement' },
                    { value: 'reorient_workpiece', label: 'Reorient Workpiece' },
                    { value: 'inspection', label: 'Inspection' },
                    { value: 'load_part', label: 'Load/Unload Part' },
                    { value: 'other', label: 'Other' }
                ]
            }),
            formGroup('Idle Time (minutes)', 'idle_time', {
                type: 'number',
                step: '0.1',
                min: '0'
            }),
            `<div class="form-group mt-4">
                <button type="button"
                        class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onclick="calculateOperationTime('${entryId}', 'idle')">
                    <i class="fas fa-calculator"></i> Calculate Idle Time
                </button>
                <input id="${entryId}_total_time"
                       type="text"
                       class="mt-2 block w-full p-2 border border-gray-300 rounded-md bg-gray-50"
                       placeholder="Idle Time (minutes)"
                       readonly>
            </div>`
            
        ].join('')
    };
    
    // Get the form generator function for the requested operation type
    const formGenerator = formTemplates[opType];
    if (!formGenerator) {
        console.error(`No form template found for operation type: ${operationType}`);
        return '';
    }
    
    try {
        return formGenerator();
    } catch (error) {
        console.error(`Error generating form for operation ${operationType}:`, error);
        return '';
    }
}
    
// ============================ UTILITY FUNCTIONS ============================

// Remove an operation entry
function removeEntry(entryId) {
    const entry = document.getElementById(entryId);
    if (entry) {
        entry.remove();
        // Trigger recalculations
        calculateAndDisplayTimes();
        calculateAndDisplayCosts();
    }
}

function clearAll() {
    const operationList = document.getElementById('operationList');
    if (operationList) operationList.innerHTML = '';
    
    // Reset form fields
    const materialSelect = document.getElementById('materialSelect');
    if (materialSelect) materialSelect.value = '';
    
    // Reset displayed values
    const displayFields = [
        'machiningTime', 'idleTime', 'setupTime', 'toolTime', 'miscTime', 'totalTime',
        'materialCost', 'timeBasedCost', 'toolingCost', 'fixedCost', 'totalCost'
    ];
    
    displayFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '0.00';
    });
    
    // Hide sections
    document.getElementById('timeSection')?.classList.remove('visible');
    document.getElementById('costSection')?.classList.remove('visible');
}

// ============================ VALIDATION ============================

function validateOperationForm(processId, operationType) {
    const entry = document.getElementById(processId);
    if (!entry) throw new Error('Process entry not found');

    const materialSelect = entry.querySelector(`select#material_${processId}`);
    if (!materialSelect || !materialSelect.value) {
        throw new Error('Please select a material');
    }

    const opType = operationType.toLowerCase();
    const required = requiredFields[opType] || [];
    const missingFields = [];

    required.forEach(field => {
        const input = entry.querySelector(`#${processId}_${field}`);
        if (!input || (input.value === '' && input.value !== '0')) {
            const label = entry.querySelector(`label[for="${processId}_${field}"]`);
            missingFields.push(label ? label.textContent.replace(':', '') : field);
        }
    });

    if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
    }
    return true;
}

// ============================ DYNAMIC OPERATION FORM HANDLING ============================

// Toggle section visibility
function toggleSection(sectionId, show = true) {
    const section = document.getElementById(sectionId);
    if (section) {
        if (show) {
            section.classList.remove('hidden');
            section.style.display = 'block';
            // Ensure the section is visible and properly positioned
            section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            section.classList.add('hidden');
            section.style.display = 'none';
        }
    }
}

function initializeEventListeners() {
    const materialSelect = document.getElementById('materialSelect');
    const operationSelect = document.getElementById('operationSelect');
    if (materialSelect) materialSelect.addEventListener('change', updateParamFormVisibility); // Provided elsewhere
    if (operationSelect) operationSelect.addEventListener('change', updateParamFormVisibility); // Provided elsewhere
}

// ============================ FORM VISIBILITY ============================

/**
 * Update the visibility of parameter forms based on selected operation
 */
function updateParamFormVisibility() {
    const operationSelect = document.getElementById('operationSelect');
    const paramFormContainer = document.getElementById('paramFormContainer');
    
    if (!operationSelect || !paramFormContainer) return;
    
    const selectedOperation = operationSelect.value;
    
    // Hide all parameter forms
    const allParamForms = paramFormContainer.querySelectorAll('.param-form');
    allParamForms.forEach(form => {
        form.style.display = 'none';
    });
    
    // Show the selected operation's parameter form if it exists
    const selectedForm = document.getElementById(`${selectedOperation}Params`);
    if (selectedForm) {
        selectedForm.style.display = 'block';
    }
}

// ============================ GLOBAL EXPORTS ============================

window.toggleSection = toggleSection;
window.updateParamFormVisibility = updateParamFormVisibility;
window.updateToolTime = updateToolTime;
window.updateMiscTime = updateMiscTime;
window.clearAll = clearAll;
window.calculateOperationTime = calculateOperationTime;
window.removeEntry = removeEntry;

// Remove an element by ID or element reference
function removeElement(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
        return true;
    }
    return false;
}

export {
    clearAll,
    toggleSection,
    validateOperationForm,
    removeElement
};

