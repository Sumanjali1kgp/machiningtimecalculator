// jsPDF and autoTable are loaded globally in lathe.html

const PDF_TERMS = `Terms & Conditions:
1. This is a computer-generated estimate and valid for 30 days.
2. Prices may vary based on raw material availability and market conditions.
3. Delivery timeline is estimated and subject to workshop schedule.
4. Final dimensions and specifications must be confirmed before production.`;

// Format date as DD/MM/YY
function formatDate(date = new Date()) {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = String(d.getFullYear()).slice(-2);
    return `${day}/${month}/${year}`;
}

/**
 * Prompt customer details before generating PDF
 */
function getCustomerDetails() {
    const name = prompt("Enter Customer Name:");
    const project = prompt("Enter Project Name / Description:");
    const orderId = `ORD-${Date.now()}`;
    return { name: name || 'N/A', project: project || 'N/A', orderId };
}

export async function exportToPDF(type = 'customer') {
    const { jsPDF } = window.jspdf.jsPDF ? window.jspdf : { jsPDF: window.jspdf };
    if (!jsPDF) {
        alert("PDF library not loaded.");
        return;
    }

    const doc = new jsPDF();
    const date = formatDate();
    const title = type === 'shop' 
        ? 'CWISS - Workshop Operation Sheet' 
        : 'CWISS - Quotation for Machining Services';

    // Get customer details for customer PDF
    const customerDetails = type === 'customer' ? getCustomerDetails() : null;
    
    // Get all cost values from the page
    const getNumericValue = (id) => {
        const el = document.getElementById(id);
        return el ? parseFloat(el.textContent.replace(/[^0-9.-]+/g, '')) || 0 : 0;
    };

    // Get time values
    const machiningTime = document.getElementById('machiningTime')?.textContent || '0.00';
    const setupTime = document.getElementById('setupTime')?.textContent || '0.00';
    const idleTime = document.getElementById('idleTime')?.textContent || '0.00';
    const totalTime = document.getElementById('totalTime')?.textContent || '0.00';

    // Get cost values
    const materialCost = getNumericValue('materialCost');
    const laborCost = getNumericValue('laborCost');
    const machineCost = getNumericValue('machineCost');
    const toolingCost = getNumericValue('toolingCost');
    const setupIdleCost = getNumericValue('setupIdleCost');
    const overheadCost = getNumericValue('overheadCost');
    const finalCost = document.getElementById('finalCost')?.textContent || '₹0.00';
    
    // Calculate non-productive cost (material + setup & idle)
    const nonProductiveCost = materialCost + setupIdleCost;

    // Header with logo and title
    doc.setFontSize(20);
    doc.setTextColor(0, 0, 0);
    doc.setFont('helvetica', 'bold');
    doc.text('CWISS', 20, 20);
    
    doc.setFontSize(14);
    doc.setTextColor(100);
    doc.setFont('helvetica', 'normal');
    doc.text('Central Workshop & Instrument Service Section', 20, 28);
    doc.text('Indian Institute of Technology Kharagpur', 20, 34);
    
    // Document title and date
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text(title, 105, 20, { align: 'center' });
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Date: ${date}`, 190, 20, { align: 'right' });
    doc.text(`Quotation #: ${customerDetails?.orderId || 'N/A'}`, 190, 25, { align: 'right' });

    // Customer details for customer PDF
    if (type === 'customer' && customerDetails) {
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.text('Customer Details', 20, 55);
        doc.setFont('helvetica', 'normal');
        doc.text(`Name: ${customerDetails.name}`, 20, 62);
        doc.text(`Project: ${customerDetails.project}`, 20, 69);
    }

    // Add content based on PDF type
    if (type === 'customer') {
        // Cost summary for customer - simplified
        const startY = customerDetails ? 85 : 60;
        
        doc.autoTable({
            startY: startY,
            head: [
                [
                    { content: 'DESCRIPTION', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102] }},
                    { content: 'QUANTITY', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102], halign: 'right' }},
                    { content: 'AMOUNT (₹)', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102], halign: 'right' }}
                ]
            ],
            body: [
                [
                    { content: 'Non-Productive Cost', styles: { fontStyle: 'bold' }},
                    { content: '1', styles: { halign: 'right' }},
                    { content: `₹${nonProductiveCost.toFixed(2)}`, styles: { halign: 'right' }}
                ],
                [
                    { content: 'Machining Cost', styles: { fontStyle: 'bold' }},
                    { content: '1', styles: { halign: 'right' }},
                    { content: `₹${machineCost.toFixed(2)}`, styles: { halign: 'right' }}
                ],
                [
                    { content: 'Tooling Cost', styles: { fontStyle: 'bold' }},
                    { content: '1', styles: { halign: 'right' }},
                    { content: `₹${toolingCost.toFixed(2)}`, styles: { halign: 'right' }}
                ],
                [
                    { content: 'Overhead Charges (40%)', styles: { fontStyle: 'bold' }},
                    { content: '1', styles: { halign: 'right' }},
                    { content: `₹${overheadCost.toFixed(2)}`, styles: { halign: 'right' }}
                ],
                [
                    { content: 'TOTAL ESTIMATED COST', styles: { fontStyle: 'bold' }},
                    { content: '', styles: { halign: 'right' }},
                    { content: finalCost, styles: { fontStyle: 'bold', halign: 'right' }}
                ]
            ],
            theme: 'grid',
            headStyles: { 
                fillColor: [0, 51, 102],
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                halign: 'left'
            },
            columnStyles: {
                0: { cellWidth: 'auto' },
                1: { cellWidth: 30, halign: 'right' },
                2: { cellWidth: 40, halign: 'right' }
            },
            styles: { 
                fontSize: 10,
                cellPadding: 3,
                lineWidth: 0.5
            },
            margin: { top: 10 }
        });

        // Add terms and conditions
        doc.setFontSize(9);
        doc.setFont('helvetica', 'bold');
        doc.text('Terms & Conditions:', 14, doc.lastAutoTable.finalY + 15);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        const splitTerms = doc.splitTextToSize(PDF_TERMS, 180);
        doc.text(splitTerms, 20, doc.lastAutoTable.finalY + 20);
        
        // Add footer
        doc.setFontSize(8);
        doc.setTextColor(100);
        doc.text('Thank you for choosing CWISS - IIT Kharagpur', 105, 280, { align: 'center' });

    } else if (type === 'shop') {
        // Time summary for shop
        doc.autoTable({
            startY: 50,
            head: [['Operation', 'Time (min)']],
            body: [
                ['Machining Time', machiningTime],
                ['Setup Time', setupTime],
                ['Idle Time', idleTime],
                [{ content: 'Total Time', styles: { fontStyle: 'bold' }}, 
                 { content: totalTime, styles: { fontStyle: 'bold' }}]
            ],
            theme: 'grid',
            headStyles: { fillColor: [41, 128, 185] },
            styles: { fontSize: 10 }
        });

        // Cost details for shop
        doc.autoTable({
            startY: doc.lastAutoTable.finalY + 10,
            head: [['Cost Component', 'Amount (₹)']],
            body: [
                ['Material Cost', materialCost],
                ['Labor Cost', laborCost],
                ['Machine Cost', machineCost],
                ['Overhead', overheadCost],
                [{ content: 'Total Cost', styles: { fontStyle: 'bold' }}, 
                 { content: finalCost, styles: { fontStyle: 'bold' }}]
            ],
            theme: 'grid',
            headStyles: { fillColor: [41, 128, 185] },
            styles: { fontSize: 10 }
        });
    }

    // Save the PDF with a professional filename
    const formattedDate = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const fileName = type === 'customer' 
        ? `CWISS_Quote_${customerDetails?.orderId || formattedDate}.pdf`
        : `CWISS_Worksheet_${formattedDate}.pdf`;
    
    doc.save(fileName);
}
