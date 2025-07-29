/**
 * Payment Tracking Module for Sales Dashboard
 * Handles payment milestones and payment recording
 */

class PaymentTracker {
    constructor() {
        this.initializeModals();
        this.setupEventListeners();
    }

    initializeModals() {
        // Add payment tracking modals to the page if they don't exist
        if (!document.getElementById('paymentSummaryModal')) {
            this.createPaymentSummaryModal();
        }
        if (!document.getElementById('addPaymentModal')) {
            this.createAddPaymentModal();
        }
        if (!document.getElementById('addMilestoneModal')) {
            this.createAddMilestoneModal();
        }
    }

    createPaymentSummaryModal() {
        const modalHTML = `
            <div id="paymentSummaryModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Payment Summary</h3>
                        <button class="modal-close" onclick="PaymentTracker.closeModal('paymentSummaryModal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="payment-overview">
                            <div class="payment-stats">
                                <div class="stat-card">
                                    <h4>Total Amount</h4>
                                    <p id="totalAmount">$0</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Paid Amount</h4>
                                    <p id="paidAmount">$0</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Remaining</h4>
                                    <p id="remainingAmount">$0</p>
                                </div>
                                <div class="stat-card">
                                    <h4>Progress</h4>
                                    <p id="paymentProgress">0%</p>
                                </div>
                            </div>
                            <div class="progress-bar">
                                <div id="progressBarFill" class="progress-fill"></div>
                            </div>
                        </div>
                        
                        <div class="payment-sections">
                            <div class="milestones-section">
                                <div class="section-header">
                                    <h4>Payment Milestones</h4>
                                    <button class="btn btn-sm btn-primary" onclick="PaymentTracker.openAddMilestone()">Add Milestone</button>
                                </div>
                                <div id="milestonesList" class="milestones-list">
                                    <!-- Milestones will be loaded here -->
                                </div>
                            </div>
                            
                            <div class="payments-section">
                                <div class="section-header">
                                    <h4>Payment History</h4>
                                    <button class="btn btn-sm btn-success" onclick="PaymentTracker.openAddPayment()">Record Payment</button>
                                </div>
                                <div id="paymentsList" class="payments-list">
                                    <!-- Payment history will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="PaymentTracker.closeModal('paymentSummaryModal')">Close</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    createAddPaymentModal() {
        const modalHTML = `
            <div id="addPaymentModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Record Payment</h3>
                        <button class="modal-close" onclick="PaymentTracker.closeModal('addPaymentModal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="addPaymentForm">
                            <div class="form-group">
                                <label for="paymentAmount">Amount *</label>
                                <input type="number" id="paymentAmount" class="form-control" step="0.01" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="paymentMethod">Payment Method *</label>
                                <select id="paymentMethod" class="form-control" required>
                                    <option value="">Select payment method</option>
                                    <option value="Bank Transfer">Bank Transfer</option>
                                    <option value="Check">Check</option>
                                    <option value="Credit Card">Credit Card</option>
                                    <option value="Cash">Cash</option>
                                    <option value="Online Payment">Online Payment</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="paymentDate">Payment Date *</label>
                                <input type="date" id="paymentDate" class="form-control" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="transactionId">Transaction ID</label>
                                <input type="text" id="transactionId" class="form-control" placeholder="Optional">
                            </div>
                            
                            <div class="form-group">
                                <label for="milestoneSelect">Related Milestone</label>
                                <select id="milestoneSelect" class="form-control">
                                    <option value="">No specific milestone</option>
                                    <!-- Milestones will be loaded here -->
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="paymentNotes">Notes</label>
                                <textarea id="paymentNotes" class="form-control" rows="3" placeholder="Optional notes about this payment"></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="PaymentTracker.closeModal('addPaymentModal')">Cancel</button>
                        <button class="btn btn-success" onclick="PaymentTracker.recordPayment()">Record Payment</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    createAddMilestoneModal() {
        const modalHTML = `
            <div id="addMilestoneModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Add Payment Milestone</h3>
                        <button class="modal-close" onclick="PaymentTracker.closeModal('addMilestoneModal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="addMilestoneForm">
                            <div class="form-group">
                                <label for="milestoneDescription">Description *</label>
                                <input type="text" id="milestoneDescription" class="form-control" 
                                       placeholder="e.g., Initial Payment (50%)" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="milestoneAmount">Amount *</label>
                                <input type="number" id="milestoneAmount" class="form-control" step="0.01" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="milestoneDueDate">Due Date *</label>
                                <input type="date" id="milestoneDueDate" class="form-control" required>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="PaymentTracker.closeModal('addMilestoneModal')">Cancel</button>
                        <button class="btn btn-primary" onclick="PaymentTracker.addMilestone()">Add Milestone</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    setupEventListeners() {
        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });

        // Set default payment date to today
        const today = new Date().toISOString().split('T')[0];
        if (document.getElementById('paymentDate')) {
            document.getElementById('paymentDate').value = today;
        }
    }

    static async openPaymentSummary(leadId) {
        try {
            const token = localStorage.getItem('bhoomitechzone_token');
            const response = await fetch(`/api/sales/leads/${leadId}/payment-summary`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load payment summary');
            }

            const data = await response.json();
            PaymentTracker.displayPaymentSummary(data);
            PaymentTracker.currentLeadId = leadId;
            document.getElementById('paymentSummaryModal').style.display = 'flex';
        } catch (error) {
            console.error('Error loading payment summary:', error);
            PaymentTracker.showToast('Error loading payment summary');
        }
    }

    static displayPaymentSummary(data) {
        // Update overview stats
        document.getElementById('totalAmount').textContent = `$${data.total_amount.toLocaleString()}`;
        document.getElementById('paidAmount').textContent = `$${data.paid_amount.toLocaleString()}`;
        document.getElementById('remainingAmount').textContent = `$${data.remaining_amount.toLocaleString()}`;
        document.getElementById('paymentProgress').textContent = `${data.payment_percentage}%`;

        // Update progress bar
        const progressBar = document.getElementById('progressBarFill');
        progressBar.style.width = `${data.payment_percentage}%`;
        progressBar.className = `progress-fill ${data.payment_percentage >= 100 ? 'complete' : data.payment_percentage >= 50 ? 'partial' : 'low'}`;

        // Display milestones
        PaymentTracker.displayMilestones(data.milestones);
        
        // Display payments
        PaymentTracker.displayPayments(data.payments);
        
        // Load milestones for payment form
        PaymentTracker.loadMilestonesForPayment(data.milestones);
    }

    static displayMilestones(milestones) {
        const container = document.getElementById('milestonesList');
        if (!milestones || milestones.length === 0) {
            container.innerHTML = '<p class="no-data">No milestones set</p>';
            return;
        }

        const milestonesHTML = milestones.map(milestone => {
            const statusClass = milestone.status === 'paid' ? 'status-paid' : 
                               new Date(milestone.due_date) < new Date() ? 'status-overdue' : 'status-pending';
            
            return `
                <div class="milestone-item ${statusClass}">
                    <div class="milestone-info">
                        <h5>${milestone.description}</h5>
                        <p>Amount: $${milestone.amount.toLocaleString()}</p>
                        <p>Due: ${new Date(milestone.due_date).toLocaleDateString()}</p>
                        ${milestone.status === 'paid' ? `<p>Paid: ${new Date(milestone.paid_date).toLocaleDateString()}</p>` : ''}
                    </div>
                    <div class="milestone-status">
                        <span class="status-badge ${statusClass}">${milestone.status.replace('_', ' ')}</span>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = milestonesHTML;
    }

    static displayPayments(payments) {
        const container = document.getElementById('paymentsList');
        if (!payments || payments.length === 0) {
            container.innerHTML = '<p class="no-data">No payments recorded</p>';
            return;
        }

        const paymentsHTML = payments.map(payment => `
            <div class="payment-item">
                <div class="payment-info">
                    <h5>$${payment.amount.toLocaleString()}</h5>
                    <p>Method: ${payment.payment_method}</p>
                    <p>Date: ${new Date(payment.payment_date).toLocaleDateString()}</p>
                    ${payment.transaction_id ? `<p>Transaction: ${payment.transaction_id}</p>` : ''}
                    ${payment.notes ? `<p>Notes: ${payment.notes}</p>` : ''}
                </div>
                <div class="payment-meta">
                    <small>Recorded by ${payment.recorded_by}</small>
                </div>
            </div>
        `).join('');

        container.innerHTML = paymentsHTML;
    }

    static loadMilestonesForPayment(milestones) {
        const select = document.getElementById('milestoneSelect');
        if (!select) return;

        // Clear existing options except the first one
        select.innerHTML = '<option value="">No specific milestone</option>';

        // Add pending milestones
        const pendingMilestones = milestones.filter(m => m.status === 'pending');
        pendingMilestones.forEach(milestone => {
            const option = document.createElement('option');
            option.value = milestone.id;
            option.textContent = `${milestone.description} - $${milestone.amount.toLocaleString()}`;
            select.appendChild(option);
        });
    }

    static openAddPayment() {
        document.getElementById('addPaymentModal').style.display = 'flex';
    }

    static openAddMilestone() {
        document.getElementById('addMilestoneModal').style.display = 'flex';
    }

    static closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    static async recordPayment() {
        try {
            const form = document.getElementById('addPaymentForm');
            const formData = new FormData(form);
            
            const paymentData = {
                amount: parseFloat(document.getElementById('paymentAmount').value),
                payment_method: document.getElementById('paymentMethod').value,
                payment_date: document.getElementById('paymentDate').value,
                transaction_id: document.getElementById('transactionId').value,
                notes: document.getElementById('paymentNotes').value,
                milestone_id: document.getElementById('milestoneSelect').value || null
            };

            // Validation
            if (!paymentData.amount || paymentData.amount <= 0) {
                PaymentTracker.showToast('Please enter a valid amount', 'error');
                return;
            }

            if (!paymentData.payment_method) {
                PaymentTracker.showToast('Please select a payment method', 'error');
                return;
            }

            if (!paymentData.payment_date) {
                PaymentTracker.showToast('Please select a payment date', 'error');
                return;
            }

            const token = localStorage.getItem('bhoomitechzone_token');
            const response = await fetch(`/api/sales/leads/${PaymentTracker.currentLeadId}/payments`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(paymentData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to record payment');
            }

            const result = await response.json();
            PaymentTracker.showToast('Payment recorded successfully', 'success');
            
            // Close modal and refresh summary
            PaymentTracker.closeModal('addPaymentModal');
            form.reset();
            
            // Refresh payment summary
            PaymentTracker.openPaymentSummary(PaymentTracker.currentLeadId);
            
        } catch (error) {
            console.error('Error recording payment:', error);
            PaymentTracker.showToast(error.message || 'Error recording payment', 'error');
        }
    }

    static async addMilestone() {
        try {
            const milestoneData = {
                description: document.getElementById('milestoneDescription').value,
                amount: parseFloat(document.getElementById('milestoneAmount').value),
                due_date: document.getElementById('milestoneDueDate').value
            };

            // Validation
            if (!milestoneData.description) {
                PaymentTracker.showToast('Please enter a description', 'error');
                return;
            }

            if (!milestoneData.amount || milestoneData.amount <= 0) {
                PaymentTracker.showToast('Please enter a valid amount', 'error');
                return;
            }

            if (!milestoneData.due_date) {
                PaymentTracker.showToast('Please select a due date', 'error');
                return;
            }

            const token = localStorage.getItem('bhoomitechzone_token');
            const response = await fetch(`/api/sales/leads/${PaymentTracker.currentLeadId}/payment-milestones`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(milestoneData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to add milestone');
            }

            PaymentTracker.showToast('Milestone added successfully', 'success');
            
            // Close modal and refresh summary
            PaymentTracker.closeModal('addMilestoneModal');
            document.getElementById('addMilestoneForm').reset();
            
            // Refresh payment summary
            PaymentTracker.openPaymentSummary(PaymentTracker.currentLeadId);
            
        } catch (error) {
            console.error('Error adding milestone:', error);
            PaymentTracker.showToast(error.message || 'Error adding milestone', 'error');
        }
    }

    static showToast(message, type = 'info') {
        // Create toast if it doesn't exist
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            toast.className = 'toast';
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PaymentTracker();
});

// Static properties
PaymentTracker.currentLeadId = null;
