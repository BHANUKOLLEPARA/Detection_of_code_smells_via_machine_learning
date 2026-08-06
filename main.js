/*!
 * CodeSmell Detector - Main JavaScript
 * Version: 1.0
 * Author: CodeSmell Team
 */

'use strict';

// Global variables
let chartInstances = {};

// Document ready
$(document).ready(function() {
    // Initialize all components
    initTooltips();
    initPopovers();
    initSidebar();
    initFileUploads();
    initCodeEditor();
    initCharts();
    initFormValidation();
    initNotifications();
    initSearch();
    initDarkMode();
    initCopyButtons();
    initDatePickers();
    initModals();
    initProgressBars();
    initTabs();
    initDropdowns();
    initScrollSpy();
    initAjaxForms();
    initLivePreview();
    
    // Check for notifications
    checkNotifications();
    
    // Log page view
    logPageView();
});

/* ===== INITIALIZATION FUNCTIONS ===== */

function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            animation: true,
            delay: { show: 500, hide: 100 }
        });
    });
}

function initPopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            animation: true,
            trigger: 'hover'
        });
    });
}

function initSidebar() {
    // Sidebar toggle
    $('#sidebarCollapse').on('click', function() {
        $('#sidebar').toggleClass('active');
        $('#content').toggleClass('active');
        
        // Store sidebar state
        localStorage.setItem('sidebarActive', $('#sidebar').hasClass('active'));
        
        // Trigger resize for charts
        setTimeout(function() {
            $(window).trigger('resize');
        }, 300);
    });

    // Check sidebar state on load
    if (localStorage.getItem('sidebarActive') === 'true') {
        $('#sidebar').addClass('active');
        $('#content').addClass('active');
    } else {
        $('#sidebar').removeClass('active');
        $('#content').removeClass('active');
    }

    // Handle dropdowns in sidebar
    $('#sidebar .dropdown-toggle').on('click', function(e) {
        e.preventDefault();
        $(this).next('.collapse').toggleClass('show');
        $(this).find('i:last-child').toggleClass('fa-chevron-down fa-chevron-up');
    });

    // Highlight active menu
    var currentUrl = window.location.pathname;
    $('#sidebar a').each(function() {
        if ($(this).attr('href') === currentUrl) {
            $(this).parent().addClass('active');
        }
    });
}

function initFileUploads() {
    // Single file upload
    $('#fileUpload, #codeFile').on('change', function(e) {
        handleFileSelect(e, '#file-info');
    });

    // Multiple file upload
    $('#folderFiles').on('change', function(e) {
        handleMultipleFileSelect(e, '#folder-info');
    });

    // Drag and drop
    $('.upload-area').on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('dragover');
    });

    $('.upload-area').on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
    });

    $('.upload-area').on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
        
        var files = e.originalEvent.dataTransfer.files;
        var inputId = $(this).find('input[type="file"]').attr('id');
        
        if (inputId === 'folderFiles') {
            handleMultipleFileDrop(files, '#folder-info');
        } else {
            handleFileDrop(files, inputId, '#file-info');
        }
    });
}

function handleFileSelect(e, infoSelector) {
    var file = e.target.files[0];
    if (file) {
        var fileSize = (file.size / 1024).toFixed(2);
        var fileType = file.type || 'unknown';
        var fileExt = file.name.split('.').pop();
        
        var info = `
            <div class="file-info-item">
                <i class="fas fa-check-circle text-success me-2"></i>
                <strong>${file.name}</strong>
                <span class="text-muted ms-2">(${fileSize} KB)</span>
                <span class="badge bg-light text-dark ms-2">${fileExt}</span>
                <button type="button" class="btn btn-sm btn-link text-danger ms-2" onclick="clearFile('${infoSelector}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        $(infoSelector).html(info);
        
        // Validate file type
        validateFileType(file, infoSelector);
    }
}

function handleMultipleFileSelect(e, infoSelector) {
    var files = e.target.files;
    if (files.length > 0) {
        var info = '<div class="file-info-list">';
        info += `<p><i class="fas fa-check-circle text-success me-2"></i>Selected ${files.length} file(s):</p>`;
        info += '<ul class="list-unstyled ms-3">';
        
        var totalSize = 0;
        var supportedCount = 0;
        var unsupportedFiles = [];
        
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            var fileSize = (file.size / 1024).toFixed(2);
            totalSize += parseFloat(fileSize);
            
            var ext = file.name.split('.').pop();
            var isSupported = isFileSupported(ext);
            
            if (isSupported) {
                supportedCount++;
            } else {
                unsupportedFiles.push(file.name);
            }
            
            var icon = isSupported ? 'fa-file-code text-primary' : 'fa-exclamation-triangle text-warning';
            
            info += `<li class="mb-1">
                <i class="fas ${icon} me-2"></i>
                ${file.name} <small class="text-muted">(${fileSize} KB)</small>
            </li>`;
        }
        
        info += '</ul>';
        
        if (unsupportedFiles.length > 0) {
            info += `<div class="alert alert-warning mt-2 mb-0 small">
                <i class="fas fa-info-circle me-2"></i>
                ${unsupportedFiles.length} unsupported file(s) will be skipped
            </div>`;
        }
        
        info += `<div class="mt-2 small text-muted">
            Total: ${files.length} files (${totalSize.toFixed(2)} KB) | 
            Supported: ${supportedCount} files
        </div>`;
        info += '</div>';
        
        $(infoSelector).html(info);
    }
}

function handleFileDrop(files, inputId, infoSelector) {
    var dataTransfer = new DataTransfer();
    dataTransfer.items.add(files[0]);
    document.getElementById(inputId).files = dataTransfer.files;
    
    handleFileSelect({ target: { files: files } }, infoSelector);
}

function handleMultipleFileDrop(files, infoSelector) {
    var dataTransfer = new DataTransfer();
    for (var i = 0; i < files.length; i++) {
        dataTransfer.items.add(files[i]);
    }
    document.getElementById('folderFiles').files = dataTransfer.files;
    
    handleMultipleFileSelect({ target: { files: files } }, infoSelector);
}

function clearFile(infoSelector) {
    $(infoSelector).empty();
    $('#fileUpload, #codeFile, #folderFiles').val('');
}

function isFileSupported(extension) {
    var supported = ['py', 'java', 'js', 'php', 'c', 'cpp', 'cs', 'rb', 'go', 'rs', 'swift', 'kt', 'scala', 'txt'];
    return supported.includes(extension.toLowerCase());
}

function validateFileType(file, infoSelector) {
    var ext = file.name.split('.').pop().toLowerCase();
    var supported = ['py', 'java', 'js', 'php', 'c', 'cpp', 'cs', 'rb', 'go'];
    
    if (!supported.includes(ext)) {
        var warning = `
            <div class="alert alert-warning mt-2 small">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Warning: .${ext} files may not be fully supported
            </div>
        `;
        $(infoSelector).append(warning);
    }
}

function initCodeEditor() {
    // Line numbers
    function updateLineNumbers() {
        var lines = $('#codeSnippet').val().split('\n').length;
        var lineNumbers = '';
        for (var i = 1; i <= lines; i++) {
            lineNumbers += i + '<br>';
        }
        $('#lineNumbers').html(lineNumbers);
    }

    if ($('#codeSnippet').length) {
        $('#codeSnippet').on('keyup', function() {
            updateLineNumbers();
        });

        // Initialize line numbers
        updateLineNumbers();

        // Tab key handling
        $('#codeSnippet').on('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                var start = this.selectionStart;
                var end = this.selectionEnd;
                
                this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
                this.selectionStart = this.selectionEnd = start + 4;
            }
        });

        // Auto-indent on enter
        $('#codeSnippet').on('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                var start = this.selectionStart;
                var value = this.value;
                var lineStart = value.lastIndexOf('\n', start - 1) + 1;
                var currentLine = value.substring(lineStart, start);
                
                // Find indentation of current line
                var indent = currentLine.match(/^\s*/)[0];
                
                this.value = value.substring(0, start) + '\n' + indent + value.substring(start);
                this.selectionStart = this.selectionEnd = start + indent.length + 1;
            }
        });
    }
}

function initCharts() {
    // Destroy existing chart instances
    for (var key in chartInstances) {
        if (chartInstances.hasOwnProperty(key)) {
            chartInstances[key].destroy();
        }
    }
    
    // Activity Chart
    if (document.getElementById('activityChart')) {
        var ctx = document.getElementById('activityChart').getContext('2d');
        chartInstances.activityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Analyses',
                    data: [12, 19, 15, 17, 14, 8, 5],
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#4361ee',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: getChartOptions('line', 'Analyses Over Time')
        });
    }

    // Smell Distribution Chart
    if (document.getElementById('smellDistributionChart')) {
        var ctx = document.getElementById('smellDistributionChart').getContext('2d');
        chartInstances.smellChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Long Method', 'Large Class', 'Feature Envy', 'God Class', 'Data Class'],
                datasets: [{
                    data: [45, 25, 15, 10, 5],
                    backgroundColor: [
                        '#4361ee',
                        '#f72585',
                        '#4cc9f0',
                        '#f8961e',
                        '#4895ef'
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: getChartOptions('doughnut', 'Code Smell Distribution')
        });
    }

    // Metrics Chart
    if (document.getElementById('metricsChart')) {
        var ctx = document.getElementById('metricsChart').getContext('2d');
        chartInstances.metricsChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['LOC', 'WMC', 'CBO', 'TCC', 'LCOM', 'RFC', 'Complexity'],
                datasets: [{
                    label: 'Current Metrics',
                    data: [150, 25, 12, 0.7, 8, 45, 18],
                    backgroundColor: 'rgba(67, 97, 238, 0.2)',
                    borderColor: '#4361ee',
                    borderWidth: 2,
                    pointBackgroundColor: '#4361ee',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: getChartOptions('radar', 'Code Metrics')
        });
    }

    // Confusion Matrix
    if (document.getElementById('confusionMatrix')) {
        var ctx = document.getElementById('confusionMatrix').getContext('2d');
        
        // Generate sample confusion matrix data
        var matrixData = [
            [45, 2, 1, 0, 0],
            [3, 38, 2, 1, 0],
            [1, 2, 42, 1, 1],
            [0, 1, 2, 40, 2],
            [0, 0, 1, 3, 44]
        ];
        
        chartInstances.matrixChart = new Chart(ctx, {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Confusion Matrix',
                    data: matrixData.flatMap((row, i) => 
                        row.map((value, j) => ({ x: j, y: i, v: value }))
                    ),
                    backgroundColor: function(context) {
                        var value = context.dataset.data[context.dataIndex].v;
                        var alpha = Math.min(1, value / 50);
                        return 'rgba(67, 97, 238, ' + alpha + ')';
                    },
                    borderColor: '#fff',
                    borderWidth: 1,
                    width: function(ctx) {
                        var a = ctx.chart.chartArea || {};
                        return (a.right - a.left) / 6 - 5;
                    },
                    height: function(ctx) {
                        var a = ctx.chart.chartArea || {};
                        return (a.bottom - a.top) / 6 - 5;
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: false,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                var v = context.dataset.data[context.dataIndex];
                                return ['True: ' + (v.y + 1), 'Predicted: ' + (v.x + 1), 'Count: ' + v.v];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        labels: ['LM', 'LC', 'FE', 'GC', 'DC'],
                        offset: true,
                        grid: { display: false },
                        title: {
                            display: true,
                            text: 'Predicted'
                        }
                    },
                    y: {
                        type: 'category',
                        labels: ['LM', 'LC', 'FE', 'GC', 'DC'],
                        offset: true,
                        grid: { display: false },
                        title: {
                            display: true,
                            text: 'Actual'
                        }
                    }
                }
            }
        });
    }

    // Feature Importance Chart
    if (document.getElementById('featureImportance')) {
        var ctx = document.getElementById('featureImportance').getContext('2d');
        chartInstances.featureChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['LOC', 'WMC', 'CBO', 'TCC', 'LCOM', 'RFC', 'Complexity'],
                datasets: [{
                    label: 'Feature Importance',
                    data: [0.25, 0.18, 0.15, 0.12, 0.10, 0.12, 0.08],
                    backgroundColor: '#4361ee',
                    borderRadius: 5
                }]
            },
            options: getChartOptions('bar', 'Feature Importance', true)
        });
    }
}

function getChartOptions(type, title, horizontal = false) {
    var options = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 1000,
            easing: 'easeInOutQuart'
        },
        plugins: {
            legend: {
                display: type !== 'bar',
                position: 'bottom',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        family: "'Inter', sans-serif",
                        size: 12
                    }
                }
            },
            title: {
                display: !!title,
                text: title,
                font: {
                    family: "'Inter', sans-serif",
                    size: 16,
                    weight: 'bold'
                },
                padding: { bottom: 20 }
            },
            tooltip: {
                backgroundColor: 'rgba(30, 30, 47, 0.9)',
                titleFont: { family: "'Inter', sans-serif", size: 13 },
                bodyFont: { family: "'Inter', sans-serif", size: 12 },
                padding: 12,
                cornerRadius: 8,
                displayColors: true
            }
        }
    };

    if (type === 'bar' && horizontal) {
        options.indexAxis = 'y';
    }

    if (type === 'line') {
        options.elements = {
            line: { borderWidth: 3 },
            point: { radius: 5, hoverRadius: 7 }
        };
    }

    return options;
}

function initFormValidation() {
    $('form').on('submit', function(e) {
        var $form = $(this);
        var isValid = true;

        // Check required fields
        $form.find('[required]').each(function() {
            if (!$(this).val() || $(this).val().trim() === '') {
                $(this).addClass('is-invalid');
                isValid = false;
                
                // Add error message
                var errorMsg = $(this).data('error') || 'This field is required';
                if (!$(this).next('.invalid-feedback').length) {
                    $(this).after('<div class="invalid-feedback">' + errorMsg + '</div>');
                }
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        // Email validation
        $form.find('input[type="email"]').each(function() {
            var email = $(this).val();
            if (email && !isValidEmail(email)) {
                $(this).addClass('is-invalid');
                if (!$(this).next('.invalid-feedback').length) {
                    $(this).after('<div class="invalid-feedback">Please enter a valid email address</div>');
                }
                isValid = false;
            }
        });

        // Password confirmation
        var password = $form.find('#password1, #password').val();
        var confirmPassword = $form.find('#password2, #confirm_password').val();
        
        if (confirmPassword && password !== confirmPassword) {
            $form.find('#password2, #confirm_password').addClass('is-invalid');
            if (!$form.find('#password2, #confirm_password').next('.invalid-feedback').length) {
                $form.find('#password2, #confirm_password').after('<div class="invalid-feedback">Passwords do not match</div>');
            }
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
            showNotification('Please fix the errors in the form', 'error');
            
            // Scroll to first error
            $('html, body').animate({
                scrollTop: $('.is-invalid:first').offset().top - 100
            }, 500);
        }
    });

    // Clear validation on input
    $('.form-control, .form-select').on('input change', function() {
        $(this).removeClass('is-invalid');
        $(this).next('.invalid-feedback').remove();
    });
}

function isValidEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function initNotifications() {
    window.showNotification = function(message, type = 'info') {
        var icon = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        }[type] || 'info-circle';
        
        var notification = `
            <div class="alert alert-premium ${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${icon} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        $('#notification-area').html(notification);
        
        // Auto dismiss after 5 seconds
        setTimeout(function() {
            $('.alert').fadeOut(300, function() {
                $(this).remove();
            });
        }, 5000);
    };
}

function initSearch() {
    $('#searchInput').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('.searchable-table tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
        
        // Show no results message
        var visibleRows = $('.searchable-table tbody tr:visible').length;
        if (visibleRows === 0) {
            if (!$('.no-results').length) {
                $('.searchable-table tbody').append(`
                    <tr class="no-results">
                        <td colspan="10" class="text-center py-4">
                            <i class="fas fa-search fa-2x text-muted mb-2"></i>
                            <p class="text-muted">No results found for "${value}"</p>
                        </td>
                    </tr>
                `);
            }
        } else {
            $('.no-results').remove();
        }
    });
}

function initDarkMode() {
    // Dark mode toggle
    $('#darkModeToggle').on('click', function() {
        $('body').toggleClass('dark-mode');
        
        if ($('body').hasClass('dark-mode')) {
            localStorage.setItem('darkMode', 'true');
            $(this).html('<i class="fas fa-sun me-2"></i>Light Mode');
        } else {
            localStorage.setItem('darkMode', 'false');
            $(this).html('<i class="fas fa-moon me-2"></i>Dark Mode');
        }
        
        // Update charts for dark mode
        updateChartsForTheme();
    });

    // Check dark mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        $('body').addClass('dark-mode');
        $('#darkModeToggle').html('<i class="fas fa-sun me-2"></i>Light Mode');
    } else if (localStorage.getItem('darkMode') === null && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        $('body').addClass('dark-mode');
        $('#darkModeToggle').html('<i class="fas fa-sun me-2"></i>Light Mode');
        localStorage.setItem('darkMode', 'true');
    }
}

function updateChartsForTheme() {
    var isDark = $('body').hasClass('dark-mode');
    var textColor = isDark ? '#fff' : '#333';
    var gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
    
    for (var key in chartInstances) {
        if (chartInstances.hasOwnProperty(key)) {
            var chart = chartInstances[key];
            if (chart.options) {
                if (chart.options.scales) {
                    Object.values(chart.options.scales).forEach(scale => {
                        if (scale.ticks) {
                            scale.ticks.color = textColor;
                        }
                        if (scale.grid) {
                            scale.grid.color = gridColor;
                        }
                    });
                }
                if (chart.options.plugins?.legend?.labels) {
                    chart.options.plugins.legend.labels.color = textColor;
                }
                chart.update();
            }
        }
    }
}

function initCopyButtons() {
    $('.copy-btn, [onclick*="copyApiKey"]').on('click', function() {
        var text = $(this).data('copy') || $('#apiKey').val();
        
        if (text) {
            navigator.clipboard.writeText(text).then(function() {
                showNotification('Copied to clipboard!', 'success');
                
                // Visual feedback
                $(this).find('i').removeClass('fa-copy').addClass('fa-check');
                setTimeout(() => {
                    $(this).find('i').removeClass('fa-check').addClass('fa-copy');
                }, 2000);
            }.bind(this)).catch(function() {
                showNotification('Failed to copy!', 'error');
            });
        }
    });
}

function initDatePickers() {
    $('#dateFilter').on('change', function() {
        var date = $(this).val();
        if (date) {
            window.location.href = updateQueryStringParameter(window.location.href, 'date', date);
        }
    });
}

function initModals() {
    // Delete confirmation
    window.confirmDelete = function(itemId, itemName) {
        if (confirm('Are you sure you want to delete "' + itemName + '"? This action cannot be undone.')) {
            document.getElementById('deleteForm' + itemId).submit();
        }
    };
}

function initProgressBars() {
    $('.progress-bar').each(function() {
        var width = $(this).data('width') || $(this).attr('style')?.match(/width: (\d+)%/)?.pop() || 0;
        $(this).css('width', width + '%').attr('aria-valuenow', width);
    });
}

function initTabs() {
    // Store active tab in URL hash
    var hash = window.location.hash;
    if (hash) {
        $('.nav-tabs a[href="' + hash + '"]').tab('show');
    }

    $('.nav-tabs a').on('shown.bs.tab', function(e) {
        window.location.hash = e.target.hash;
        
        // Trigger resize for charts
        setTimeout(function() {
            $(window).trigger('resize');
        }, 100);
    });
}

function initDropdowns() {
    $('.dropdown-toggle').dropdown();
}

function initScrollSpy() {
    var spy = new bootstrap.ScrollSpy(document.body, {
        target: '#sidebar'
    });
}

function initAjaxForms() {
    $('.ajax-form').on('submit', function(e) {
        e.preventDefault();
        
        var $form = $(this);
        var $submitBtn = $form.find('[type="submit"]');
        var originalText = $submitBtn.html();
        var url = $form.attr('action');
        var method = $form.attr('method') || 'POST';
        
        // Show loading state
        $submitBtn.html('<span class="spinner-border spinner-border-sm me-2"></span>Processing...').prop('disabled', true);
        
        $.ajax({
            url: url,
            method: method,
            data: new FormData(this),
            processData: false,
            contentType: false,
            success: function(response) {
                showNotification(response.message || 'Operation completed successfully!', 'success');
                
                if (response.redirect) {
                    setTimeout(function() {
                        window.location.href = response.redirect;
                    }, 1000);
                } else if (response.reload) {
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                }
            },
            error: function(xhr) {
                var message = 'An error occurred';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                } else if (xhr.responseText) {
                    try {
                        var response = JSON.parse(xhr.responseText);
                        message = response.message || message;
                    } catch(e) {}
                }
                showNotification(message, 'error');
            },
            complete: function() {
                $submitBtn.html(originalText).prop('disabled', false);
            }
        });
    });
}

function initLivePreview() {
    let analysisTimeout;
    
    $('#codeSnippet').on('keyup', function() {
        clearTimeout(analysisTimeout);
        var code = $(this).val();
        
        if (code.length > 50) {
            $('#analysis-preview').html(`
                <div class="text-center py-3">
                    <div class="spinner-premium small mx-auto mb-2"></div>
                    <p class="small text-muted">Analyzing code...</p>
                </div>
            `);
            
            analysisTimeout = setTimeout(function() {
                // Simulate analysis (replace with actual API call)
                var smellCount = Math.floor(Math.random() * 5);
                var qualityScore = Math.floor(Math.random() * 30) + 70;
                
                $('#analysis-preview').html(`
                    <div class="alert alert-info">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-chart-line fa-2x me-3"></i>
                            <div>
                                <strong>Live Preview:</strong> Detected ${smellCount} potential code smells<br>
                                <small>Quality Score: ${qualityScore}%</small>
                            </div>
                        </div>
                    </div>
                `);
            }, 1500);
        } else {
            $('#analysis-preview').empty();
        }
    });
}

function checkNotifications() {
    // Check for URL parameters that might contain messages
    var urlParams = new URLSearchParams(window.location.search);
    var message = urlParams.get('message');
    var messageType = urlParams.get('type') || 'info';
    
    if (message) {
        showNotification(decodeURIComponent(message), messageType);
        
        // Clean URL
        var url = window.location.pathname;
        window.history.replaceState({}, document.title, url);
    }
}

function logPageView() {
    console.log('Page viewed:', document.title);
}

/* ===== HELPER FUNCTIONS ===== */

function updateQueryStringParameter(uri, key, value) {
    var re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
    var separator = uri.indexOf('?') !== -1 ? "&" : "?";
    
    if (uri.match(re)) {
        return uri.replace(re, '$1' + key + "=" + value + '$2');
    } else {
        return uri + separator + key + "=" + value;
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    var k = 1024;
    var sizes = ['Bytes', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/* ===== EXPORT FUNCTIONS ===== */

window.exportData = function(type) {
    showNotification('Exporting ' + type + '...', 'info');
    
    // Simulate export (replace with actual export logic)
    setTimeout(function() {
        showNotification(type + ' exported successfully!', 'success');
    }, 2000);
};

window.printReport = function() {
    window.print();
};

window.refreshCharts = function() {
    initCharts();
    showNotification('Charts refreshed!', 'info');
};

window.filterByDate = function() {
    var date = $('#dateFilter').val();
    if (date) {
        window.location.href = updateQueryStringParameter(window.location.href, 'date', date);
    } else {
        window.location.href = window.location.pathname;
    }
};

/* ===== CHART.JS REGISTRATION ===== */

// Register matrix chart type
if (typeof Chart !== 'undefined' && !Chart.registry?.controllers?.matrix) {
    Chart.register({
        id: 'matrix',
        beforeInit: function(chart) {
            // Matrix chart implementation
        }
    });
}

/* ===== INITIALIZE ON PAGE LOAD ===== */

$(window).on('load', function() {
    // Hide page loader
    $('#pageLoader').fadeOut();
    
    // Update charts for theme
    updateChartsForTheme();
});

$(window).on('resize', function() {
    // Debounce chart resizing
    clearTimeout(window.resizeTimeout);
    window.resizeTimeout = setTimeout(function() {
        for (var key in chartInstances) {
            if (chartInstances.hasOwnProperty(key)) {
                chartInstances[key].resize();
            }
        }
    }, 250);
});