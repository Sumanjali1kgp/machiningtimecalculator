let processCount = 0;
let materials = [];
let operations = [];

// Load materials and operations on page load
document.addEventListener('DOMContentLoaded', function() {
    const materialSelect = document.getElementById('materialSelect');
    const operationSelect = document.getElementById('operationSelect');
    
    // Load materials
    fetch('/api/materials')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(materialsData => {
            materials = materialsData;
            materialSelect.innerHTML = '<option value="">Select Material</option>';
            materials.forEach(material => {
                const option = document.createElement('option');
                option.value = material.id;
                option.textContent = `${material.name} (${(material.rating * 100).toFixed(0)}% machinable)`;
                materialSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading materials:', error);
            alert('Failed to load materials. Please check console for details.');
        });

    // Load operations
    fetch('/api/operations')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(operationsData => {
            operations = operationsData;
            operationSelect.innerHTML = '<option value="">Select Operation</option>';
            operations.forEach(operation => {
                const option = document.createElement('option');
                option.value = operation.id;
                option.textContent = operation.name;
                operationSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading operations:', error);
            alert('Failed to load operations. Please check console for details.');
        });

    function calculateTotalTime() {
        const materialId = document.getElementById('materialSelect')?.value;
        const operationId = document.getElementById('operationSelect')?.value;
        
        if (!materialId || !operationId) {
            alert('Please select both material and operation');
            return;
        }

        const formData = {
            material_id: parseInt(materialId),
            operation_id: parseInt(operationId),
            diameter: parseFloat(document.getElementById('f_dia')?.value || 
                            document.getElementById('ti_dia')?.value || 
                            document.getElementById('bi_dia')?.value || 0),
            length: parseFloat(document.getElementById('t_len')?.value || 
                              document.getElementById('d_len')?.value || 
                              document.getElementById('b_len')?.value || 
                              document.getElementById('h_len')?.value || 
                              document.getElementById('k_len')?.value || 0),
            final_diameter: parseFloat(document.getElementById('tf_dia')?.value || 
                                      document.getElementById('bf_dia')?.value || 0),
            hole_diameter: parseFloat(document.getElementById('di_dia')?.value || 0),
            drill_angle: parseFloat(document.getElementById('b_drill_angle')?.value || 0),
            pitch: parseFloat(document.getElementById('h_pitch')?.value || 0)
        };
    const selectedMaterial = materials.find(m => m.id === parseInt(materialId));
    
    if (!selectedMaterial) {
        alert("Please select a valid material");
        return;
    }

    const materialDiv = document.createElement('div');
    materialDiv.className = 'material-entry';
    materialDiv.innerHTML = `
        <p>Material: ${selectedMaterial.name}</p>
        <input type="hidden" value="${selectedMaterial.id}" class="material-id">
        <button onclick="removeEntry(this)">Remove</button>
    `;
    
    const formContainer = document.getElementById('formContainer');
    formContainer.insertBefore(materialDiv, formContainer.firstChild);

    addProcess();
}

function addProcess() {
    const operationSelect = document.getElementById('operationSelect');
    const selectedOperationId = operationSelect.value;
    const selectedOperation = operations.find(o => o.id === parseInt(selectedOperationId));
    
    if (!selectedOperation) {
        alert("Please select a valid operation");
        return;
    }

    const operationDiv = document.createElement('div');
    operationDiv.className = 'operation-entry';
    operationDiv.innerHTML = `
        <p>Operation: ${selectedOperation.name}</p>
        <input type="hidden" value="${selectedOperation.id}" class="operation-id">
        <button onclick="removeEntry(this)">Remove</button>
    `;
    
    const formContainer = document.getElementById('formContainer');
    formContainer.insertBefore(operationDiv, formContainer.firstChild);

    // Add specific input fields based on operation
    const inputContainer = document.createElement('div');
    inputContainer.className = 'input-container';
    
    switch(selectedOperation.name.toLowerCase()) {
        case 'facing':
            inputContainer.innerHTML = `
                <label>Initial Diameter (mm): <input type="number" id="f_dia"></label>
            `;
            break;
        case 'turning':
            inputContainer.innerHTML = `
                <label>Initial Diameter (mm): <input type="number" id="ti_dia"></label>
                <label>Final Diameter (mm): <input type="number" id="tf_dia"></label>
                <label>Length (mm): <input type="number" id="t_len"></label>
            `;
            break;
        case 'drilling':
            inputContainer.innerHTML = `
                <label>Hole Length (mm): <input type="number" id="d_len"></label>
                <label>Hole Diameter (mm): <input type="number" id="di_dia"></label>
            `;
            break;
        case 'boring':
            inputContainer.innerHTML = `
                <label>Initial Diameter (mm): <input type="number" id="bi_dia"></label>
                <label>Final Diameter (mm): <input type="number" id="bf_dia"></label>
                <label>Length (mm): <input type="number" id="b_len"></label>
                <label>Drill Angle (degrees): <input type="number" id="b_drill_angle"></label>
            `;
            break;
        case 'threading':
            inputContainer.innerHTML = `
                <label>Pitch (mm): <input type="number" id="h_pitch"></label>
                <label>Length (mm): <input type="number" id="h_len"></label>
            `;
            break;
        case 'knurling':
            inputContainer.innerHTML = `
                <label>Length (mm): <input type="number" id="k_len"></label>
            `;
            break;
        case 'slabmilling':
            inputContainer.innerHTML = `
                <label>Width (mm): <input type="number" id="sm_width"></label>
                <label>Depth of Cut (mm): <input type="number" id="sm_depth"></label>
                <label>Feed (mm/rev): <input type="number" id="sm_feed"></label>
            `;
            break;
        case 'facemilling':
            inputContainer.innerHTML = `
                <label>Width (mm): <input type="number" id="fm_width"></label>
                <label>Depth of Cut (mm): <input type="number" id="fm_depth"></label>
                <label>Feed (mm/rev): <input type="number" id="fm_feed"></label>
            `;
            break;
        case 'endmilling':
            inputContainer.innerHTML = `
                <label>Length (mm): <input type="number" id="em_length"></label>
                <label>Depth of Cut (mm): <input type="number" id="em_depth"></label>
                <label>Feed (mm/rev): <input type="number" id="em_feed"></label>
            `;
            break;
        default:
            inputContainer.innerHTML = '<p>Operation not supported</p>';
    }
    
    formContainer.insertBefore(inputContainer, formContainer.firstChild);
}

function calculateTotalTime() {
    const entries = document.querySelectorAll('.process-entry');
    let total = 0;
    const extraTimes = {
        'facing': 5,
        'turning': 10,
        'drilling': 8,
        'boring': 12,
        'threading': 15,
        'knurling': 7,
        'slabmilling': 10,
        'facemilling': 8,
        'endmilling': 12
    };

    entries.forEach(entry => {
        const process = entry.querySelector('select').value;
        const timeField = entry.querySelector('.time-field');
        let time = 0;
        const formData = {};

        // Get form data based on process
        switch(process) {
            case 'facing':
                formData.diameter = parseFloat(entry.querySelector('#f_dia')?.value || 0);
                formData.length = parseFloat(entry.querySelector('#t_len')?.value || 0);
                break;
            case 'turning':
                formData.diameter = parseFloat(entry.querySelector('#ti_dia')?.value || 0);
                formData.final_diameter = parseFloat(entry.querySelector('#tf_dia')?.value || 0);
                formData.length = parseFloat(entry.querySelector('#t_len')?.value || 0);
                break;
            case 'drilling':
                formData.hole_diameter = parseFloat(entry.querySelector('#di_dia')?.value || 0);
                formData.length = parseFloat(entry.querySelector('#d_len')?.value || 0);
                break;
            case 'boring':
                formData.diameter = parseFloat(entry.querySelector('#bi_dia')?.value || 0);
                formData.final_diameter = parseFloat(entry.querySelector('#bf_dia')?.value || 0);
                formData.length = parseFloat(entry.querySelector('#b_len')?.value || 0);
                formData.drill_angle = parseFloat(entry.querySelector('#b_drill_angle')?.value || 0);
                break;
            case 'threading':
                formData.pitch = parseFloat(entry.querySelector('#h_pitch')?.value || 0);
                formData.length = parseFloat(entry.querySelector('#h_len')?.value || 0);
                break;
            case 'knurling':
                formData.length = parseFloat(entry.querySelector('#k_len')?.value || 0);
                break;
        }

        // Get machining parameters from database
        const materialId = parseInt(entry.querySelector('.material-id').value);
        const operationId = parseInt(entry.querySelector('.operation-id').value);

        fetch(`/api/parameters?material_id=${materialId}&operation_id=${operationId}`)
            .then(response => response.json())
            .then(params => {
                if (params && params.feed_rate_min && params.feed_rate_max) {
                    const feedRate = (params.feed_rate_min + params.feed_rate_max) / 2;
                    
                    // Calculate time based on process
                    switch(process) {
                        case 'facing':
                            if (!isNaN(formData.diameter) && !isNaN(formData.length) && formData.length > 0) {
                                time = (formData.diameter * formData.length) / (feedRate * 100);
                            }
                            break;
                        case 'turning':
                            if (!isNaN(formData.diameter) && !isNaN(formData.length) && formData.length > 0) {
                                time = (formData.diameter * formData.length) / (feedRate * 100);
                            }
                            break;
                        case 'drilling':
                            if (!isNaN(formData.hole_diameter) && !isNaN(formData.length) && formData.length > 0) {
                                time = (formData.hole_diameter * formData.length) / (feedRate * 100);
                            }
                            break;
                        case 'boring':
                            if (!isNaN(formData.diameter) && !isNaN(formData.length) && formData.length > 0) {
                                time = (formData.diameter * formData.length) / (feedRate * 100);
                            }
                            break;
                        case 'threading':
                            if (!isNaN(formData.pitch) && !isNaN(formData.length) && formData.length > 0) {
                                time = (formData.pitch * formData.length) / (feedRate * 100);
                            }
                            break;
                        case 'knurling':
                            if (!isNaN(formData.length) && formData.length > 0) {
                                time = formData.length / (feedRate * 100);
                            }
                            break;
                    }

                    const extra = extraTimes[process] || 0;
                    if (!isNaN(time) && time > 0) {
                        const timeWithExtra = time + extra;
                        timeField.value = timeWithExtra.toFixed(2);
                        total += timeWithExtra;
                    } else {
                        timeField.value = 'Invalid';
                    }
                } else {
                    timeField.value = 'Invalid';
                }

                // Update total time
                const restTime = 50;
                const finalTotal = total + restTime;
                document.getElementById('totalTime').innerText = finalTotal.toFixed(2);
            })
            .catch(error => {
                console.error('Error:', error);
                timeField.value = 'Error';
            });
    });
}

// ... (rest of the code remains the same)
    document.getElementById('formContainer').innerHTML = '';
    document.getElementById('formContainer').classList.remove('form-container-active');
    document.getElementById('totalTime').innerText = '0';
    processCount = 0;
    document.getElementById('optionSelect').value = '';
},

async function exportToPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    let y = 10;
    doc.text('Machining Time Report', 10, y);
    y += 10;

    const entries = document.querySelectorAll('.process-entry');
    entries.forEach(entry => {
        const title = entry.querySelector('h3').innerText;
        const inputs = entry.querySelectorAll('input');
        const values = Array.from(inputs).map(input => input.value);
        doc.text(`${title}`, 10, y);
        y += 8;
        doc.text(`Inputs: ${values.join(', ')}`, 10, y);
        y += 10;
    });

    doc.text(`Total Time: ${document.getElementById('totalTime').innerText} min`, 10, y);
    doc.save('machining_time_report.pdf');
})
