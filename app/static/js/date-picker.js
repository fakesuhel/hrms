/**
 * Simple Date Picker JS 
 * A lightweight date picker for the HR payroll system
 */

class SimpleDatePicker {
    constructor(options = {}) {
        this.selectedDate = options.selectedDate || new Date();
        this.onSelect = options.onSelect || function() {};
        this.minDate = options.minDate;
        this.maxDate = options.maxDate;
        this.element = null;
        this.isVisible = false;
    }

    // Generate the date picker HTML
    generate() {
        const wrapper = document.createElement('div');
        wrapper.classList.add('date-picker');
        
        // Header with month/year selection
        const header = document.createElement('div');
        header.classList.add('header');
        
        // Month selector
        const monthSelect = document.createElement('select');
        monthSelect.classList.add('month-select');
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December'];
        months.forEach((month, idx) => {
            const option = document.createElement('option');
            option.value = idx;
            option.textContent = month;
            monthSelect.appendChild(option);
        });
        monthSelect.value = this.selectedDate.getMonth();
        monthSelect.addEventListener('change', () => this.updateCalendar(parseInt(monthSelect.value), parseInt(yearSelect.value)));
        
        // Year selector
        const yearSelect = document.createElement('select');
        yearSelect.classList.add('year-select');
        const currentYear = new Date().getFullYear();
        for (let year = currentYear - 5; year <= currentYear + 5; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearSelect.appendChild(option);
        }
        yearSelect.value = this.selectedDate.getFullYear();
        yearSelect.addEventListener('change', () => this.updateCalendar(parseInt(monthSelect.value), parseInt(yearSelect.value)));
        
        header.appendChild(monthSelect);
        header.appendChild(yearSelect);
        wrapper.appendChild(header);
        
        // Calendar grid
        const calendar = document.createElement('div');
        calendar.classList.add('calendar');
        
        // Weekday headers
        ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(day => {
            const dayElement = document.createElement('div');
            dayElement.classList.add('weekday');
            dayElement.textContent = day;
            calendar.appendChild(dayElement);
        });
        
        // Days of month (placeholders, will be filled by updateCalendar)
        for (let i = 0; i < 42; i++) {
            const dayElement = document.createElement('div');
            dayElement.classList.add('day');
            calendar.appendChild(dayElement);
        }
        
        wrapper.appendChild(calendar);
        
        // Footer with buttons
        const footer = document.createElement('div');
        footer.classList.add('footer');
        
        const todayButton = document.createElement('button');
        todayButton.classList.add('btn', 'btn-sm', 'btn-outline');
        todayButton.textContent = 'Today';
        todayButton.addEventListener('click', () => {
            const today = new Date();
            this.selectedDate = today;
            this.updateCalendar(today.getMonth(), today.getFullYear());
            monthSelect.value = today.getMonth();
            yearSelect.value = today.getFullYear();
        });
        
        const closeButton = document.createElement('button');
        closeButton.classList.add('btn', 'btn-sm', 'btn-primary');
        closeButton.textContent = 'Done';
        closeButton.addEventListener('click', () => {
            this.hide();
        });
        
        footer.appendChild(todayButton);
        footer.appendChild(closeButton);
        wrapper.appendChild(footer);
        
        this.element = wrapper;
        this.monthSelect = monthSelect;
        this.yearSelect = yearSelect;
        this.calendar = calendar;
        
        // Initial calendar update
        this.updateCalendar(this.selectedDate.getMonth(), this.selectedDate.getFullYear());
        
        return wrapper;
    }
    
    // Update the calendar for the given month and year
    updateCalendar(month, year) {
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const today = new Date();
        
        // Get all day elements
        const dayElements = this.calendar.querySelectorAll('.day');
        
        // Clear all days
        dayElements.forEach(day => {
            day.textContent = '';
            day.className = 'day';
            day.removeAttribute('data-date');
        });
        
        // Fill in the days from previous month
        const firstDayOfWeek = firstDay.getDay();
        const prevMonthLastDay = new Date(year, month, 0).getDate();
        
        for (let i = 0; i < firstDayOfWeek; i++) {
            const dayNum = prevMonthLastDay - firstDayOfWeek + i + 1;
            dayElements[i].textContent = dayNum;
            dayElements[i].classList.add('other-month');
        }
        
        // Fill in days of current month
        for (let i = 1; i <= lastDay.getDate(); i++) {
            const dayElement = dayElements[firstDayOfWeek + i - 1];
            dayElement.textContent = i;
            
            const currentDate = new Date(year, month, i);
            dayElement.setAttribute('data-date', currentDate.toISOString().split('T')[0]);
            
            // Check if it's today
            if (i === today.getDate() && month === today.getMonth() && year === today.getFullYear()) {
                dayElement.classList.add('today');
            }
            
            // Check if it's the selected date
            if (i === this.selectedDate.getDate() && month === this.selectedDate.getMonth() && year === this.selectedDate.getFullYear()) {
                dayElement.classList.add('selected');
            }
            
            // Add click handler
            dayElement.addEventListener('click', () => {
                // Remove selected class from all days
                dayElements.forEach(day => day.classList.remove('selected'));
                
                // Add selected class to clicked day
                dayElement.classList.add('selected');
                
                // Update selected date
                this.selectedDate = new Date(year, month, i);
                
                // Call onSelect callback
                this.onSelect(this.selectedDate);
                
                // Hide date picker
                this.hide();
            });
        }
        
        // Fill in days from next month
        const totalDays = firstDayOfWeek + lastDay.getDate();
        let nextMonthDay = 1;
        
        for (let i = totalDays; i < 42; i++) {
            dayElements[i].textContent = nextMonthDay++;
            dayElements[i].classList.add('other-month');
        }
    }
    
    // Attach to an input element
    attachTo(input) {
        // Add date picker after the input
        input.parentNode.insertBefore(this.element, input.nextSibling);
        
        // Show date picker on input focus
        input.addEventListener('click', () => {
            this.show();
            
            // Position the date picker
            const inputRect = input.getBoundingClientRect();
            this.element.style.top = `${inputRect.bottom + window.scrollY}px`;
            this.element.style.left = `${inputRect.left + window.scrollX}px`;
        });
        
        // Update input value when date is selected
        this.onSelect = (date) => {
            const formattedDate = date.toISOString().split('T')[0]; // YYYY-MM-DD
            input.value = formattedDate;
            input.dispatchEvent(new Event('change'));
        };
        
        // Hide date picker when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isVisible && e.target !== input && !this.element.contains(e.target)) {
                this.hide();
            }
        });
    }
    
    // Show the date picker
    show() {
        this.element.style.display = 'block';
        this.isVisible = true;
    }
    
    // Hide the date picker
    hide() {
        this.element.style.display = 'none';
        this.isVisible = false;
    }
}

// Helper function to create and attach a date picker
function createDatePicker(inputId, options = {}) {
    const input = document.getElementById(inputId);
    if (!input) return null;
    
    const datePicker = new SimpleDatePicker(options);
    const element = datePicker.generate();
    datePicker.attachTo(input);
    
    return datePicker;
}
