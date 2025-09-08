// JavaScript principal para el Sistema de Planes de Desarrollo Municipal

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-cerrar alertas después de 5 segundos
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (!alert.classList.contains('alert-permanent')) {
            setTimeout(function() {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });

    // Confirmación para acciones destructivas
    var confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            var message = this.getAttribute('data-confirm') || '¿Está seguro de realizar esta acción?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Loading states para botones
    var loadingButtons = document.querySelectorAll('[data-loading]');
    loadingButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var originalText = this.innerHTML;
            var loadingText = this.getAttribute('data-loading') || 'Cargando...';

            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' + loadingText;
            this.disabled = true;

            // Restaurar después de 10 segundos si no se ha restaurado manualmente
            setTimeout(function() {
                if (button.disabled) {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }
            }, 10000);
        });
    });

    // Función para restaurar botones de loading
    window.restoreButton = function(button) {
        var originalText = button.getAttribute('data-original-text') || button.innerHTML.replace(/<[^>]*>/g, '').trim();
        button.innerHTML = originalText;
        button.disabled = false;
    };

    // Validación de formularios en tiempo real
    var forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(function(form) {
        var inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateField(this);
            });

            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });

    // Función de validación de campo
    function validateField(field) {
        var isValid = true;
        var feedback = field.parentNode.querySelector('.invalid-feedback');

        // Validaciones básicas
        if (field.hasAttribute('required') && !field.value.trim()) {
            isValid = false;
        }

        if (field.type === 'email' && field.value) {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
                isValid = false;
            }
        }

        if (field.hasAttribute('minlength')) {
            var minLength = parseInt(field.getAttribute('minlength'));
            if (field.value.length < minLength) {
                isValid = false;
            }
        }

        // Actualizar clases de validación
        field.classList.remove('is-valid', 'is-invalid');
        if (feedback) {
            feedback.style.display = 'none';
        }

        if (field.value && isValid) {
            field.classList.add('is-valid');
        } else if (field.value && !isValid) {
            field.classList.add('is-invalid');
            if (feedback) {
                feedback.style.display = 'block';
            }
        }
    }

    // Función para mostrar notificaciones toast
    window.showToast = function(message, type = 'info', duration = 3000) {
        var toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        var toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-' + type + ' border-0';
        toast.setAttribute('role', 'alert');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        var bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Auto-remover después de la duración
        setTimeout(function() {
            toast.remove();
        }, duration);
    };

    // Función para copiar al portapapeles
    window.copyToClipboard = function(text, successMessage = 'Copiado al portapapeles') {
        navigator.clipboard.writeText(text).then(function() {
            showToast(successMessage, 'success');
        }).catch(function(err) {
            console.error('Error al copiar:', err);
            showToast('Error al copiar al portapapeles', 'error');
        });
    };

    // Inicializar componentes específicos de la página
    initializePageComponents();
});

function initializePageComponents() {
    // Dashboard específico
    if (document.querySelector('.dashboard-page')) {
        initializeDashboard();
    }

    // Formularios específicos
    if (document.querySelector('.auth-form')) {
        initializeAuthForm();
    }
}

function initializeDashboard() {
    // Animar cards del dashboard
    var cards = document.querySelectorAll('.stat-card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
        card.classList.add('fade-in');
    });

    // Auto-refresh de estadísticas (cada 5 minutos)
    setInterval(function() {
        updateDashboardStats();
    }, 300000);
}

function initializeAuthForm() {
    // Auto-focus en el primer campo
    var firstInput = document.querySelector('.auth-form input:not([type="hidden"])');
    if (firstInput) {
        firstInput.focus();
    }

    // Toggle password visibility
    var passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            var target = document.querySelector(this.getAttribute('data-target'));
            if (target) {
                if (target.type === 'password') {
                    target.type = 'text';
                    this.innerHTML = '<i class="fas fa-eye-slash"></i>';
                } else {
                    target.type = 'password';
                    this.innerHTML = '<i class="fas fa-eye"></i>';
                }
            }
        });
    });
}

function updateDashboardStats() {
    // Aquí iría la lógica para actualizar estadísticas
    // Por ahora solo mostramos que se está actualizando
    console.log('Actualizando estadísticas del dashboard...');
}

// Función para manejar errores de AJAX
window.handleAjaxError = function(xhr, status, error) {
    console.error('Error AJAX:', error);
    var message = 'Ha ocurrido un error inesperado. Por favor, inténtelo de nuevo.';

    if (xhr.status === 403) {
        message = 'No tiene permisos para realizar esta acción.';
    } else if (xhr.status === 404) {
        message = 'El recurso solicitado no fue encontrado.';
    } else if (xhr.status === 500) {
        message = 'Error interno del servidor. Contacte al administrador.';
    }

    showToast(message, 'error');
};

// Función para confirmar eliminación
window.confirmDelete = function(message = '¿Está seguro de que desea eliminar este elemento?') {
    return confirm(message);
};
