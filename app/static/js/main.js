// JavaScript principal para Proyecto INNOVA

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

// =============================================
// SISTEMA DE MONITOREO DE ACTIVIDAD DEL USUARIO
// =============================================

(function() {
    'use strict';

    let activityTimeout;
    let lastActivityTime = Date.now();
    const ACTIVITY_TIMEOUT = 5 * 60 * 1000; // 5 minutos de inactividad antes de enviar actualización
    const HEARTBEAT_INTERVAL = 30 * 1000; // Enviar heartbeat cada 30 segundos

    // Eventos que indican actividad del usuario
    const activityEvents = [
        'mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click',
        'keydown', 'keyup', 'focus', 'blur', 'wheel', 'contextmenu'
    ];

    // Función para actualizar actividad
    function updateActivity(eventType = 'user_action') {
        const now = Date.now();
        lastActivityTime = now;

        // Limpiar timeout anterior
        clearTimeout(activityTimeout);

        // Enviar actualización de actividad al servidor
        sendActivityUpdate(eventType);

        // Mostrar indicador visual de actividad
        showActivityIndicator();

        // Configurar próximo timeout
        activityTimeout = setTimeout(function() {
            sendActivityUpdate('timeout');
        }, ACTIVITY_TIMEOUT);
    }

    // Función para enviar actualización al servidor
    function sendActivityUpdate(eventType) {
        const data = {
            timestamp: new Date().toISOString(),
            event_type: eventType,
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            url: window.location.href,
            referrer: document.referrer
        };

        const csrfToken = getCsrfToken();

        fetch('/api/activity/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        }).then(response => {
            if (!response.ok) {
                console.warn('Error updating activity:', response.status, eventType);
            }
        }).catch(error => {
            // Solo log errores de red importantes, no todos
            if (error.name !== 'TypeError' || !error.message.includes('Failed to fetch')) {
                console.error('Activity update network error:', error);
            }
        });
    }

    // Función para enviar heartbeat periódico
    function sendHeartbeat() {
        const timeSinceLastActivity = Date.now() - lastActivityTime;
        const isActive = timeSinceLastActivity < (10 * 60 * 1000); // Considerar activo si actividad en los últimos 10 minutos

        const csrfToken = getCsrfToken();

        fetch('/api/activity/heartbeat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                timestamp: new Date().toISOString(),
                time_since_activity: Math.floor(timeSinceLastActivity / 1000),
                is_active: isActive
            })
        }).then(response => {
            if (!response.ok) {
                console.warn('Heartbeat failed:', response.status);
            }
        }).catch(error => {
            // Solo log errores críticos de heartbeat
            if (!navigator.onLine) {
                console.warn('Heartbeat failed - offline');
            }
        });
    }

    // Función para mostrar indicador de actividad
    function showActivityIndicator() {
        // Remover indicador anterior si existe
        const existingIndicator = document.getElementById('activity-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        // Solo mostrar indicador si el usuario está autenticado (tiene el navbar)
        if (!document.querySelector('.navbar')) {
            return;
        }

        // Crear nuevo indicador
        const indicator = document.createElement('div');
        indicator.id = 'activity-indicator';
        indicator.innerHTML = '●';
        indicator.title = 'Actividad detectada - Sistema monitoreando';
        indicator.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            color: #10b981;
            font-size: 12px;
            z-index: 9999;
            opacity: 0.8;
            pointer-events: none;
            transition: opacity 0.3s ease;
            text-shadow: 0 0 3px rgba(16, 185, 129, 0.5);
        `;

        document.body.appendChild(indicator);

        // Ocultar después de 3 segundos con animación
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.style.opacity = '0';
                setTimeout(() => indicator.remove(), 300);
            }
        }, 3000);
    }

    // Función para obtener CSRF token
    function getCsrfToken() {
        // Buscar token en diferentes lugares
        let token = null;

        // En formularios (input oculto)
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput && csrfInput.value) {
            token = csrfInput.value;
        }

        // En meta tags
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (!token && csrfMeta) {
            token = csrfMeta.getAttribute('content');
        }

        // En headers de la respuesta (almacenado por JavaScript)
        if (!token && window.csrfToken) {
            token = window.csrfToken;
        }

        // Solo mostrar warning si realmente no hay token (primera vez)
        if (!token && !window.csrfWarned) {
            console.warn('No se encontró token CSRF');
            window.csrfWarned = true;
        }

        return token || '';
    }

    // Función para manejar visibilidad de página
    function handleVisibilityChange() {
        if (document.hidden) {
            sendActivityUpdate('page_hidden');
        } else {
            sendActivityUpdate('page_visible');
            updateActivity('page_focus');
        }
    }

    // Función para manejar antes de cerrar la página
    function handleBeforeUnload() {
        // Enviar una actualización final antes de que el usuario se vaya
        navigator.sendBeacon('/api/activity/beforeunload', JSON.stringify({
            timestamp: new Date().toISOString(),
            event_type: 'page_unload',
            url: window.location.href
        }));
    }

    // Función de inicialización
    function initializeActivityMonitoring() {
        // Solo inicializar si hay un usuario autenticado
        if (!document.querySelector('.navbar')) {
            console.log('Activity monitoring: No authenticated user detected');
            return;
        }

        console.log('🔔 Sistema de monitoreo de actividad activado');
        console.log('📊 Tu actividad será monitoreada para mejorar la experiencia del sistema');
        console.log('🔄 Actualizaciones automáticas cada 5 minutos de actividad detectada');

        // Agregar event listeners para detectar actividad
        activityEvents.forEach(eventType => {
            document.addEventListener(eventType, function(e) {
                updateActivity(eventType);
            }, { passive: true });
        });

        // Event listeners para cambios de visibilidad
        document.addEventListener('visibilitychange', handleVisibilityChange);

        // Event listener para antes de cerrar la página
        window.addEventListener('beforeunload', handleBeforeUnload);

        // Configurar heartbeat periódico
        setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);

        // Actualización inicial
        updateActivity('page_load');

        // Mostrar notificación inicial (solo una vez por sesión)
        if (!sessionStorage.getItem('activityMonitoringNotified')) {
            setTimeout(() => {
                showToast('🔔 Sistema de monitoreo activo - Tu actividad es rastreada para seguridad', 'info', 4000);
                sessionStorage.setItem('activityMonitoringNotified', 'true');
            }, 2000);
        }
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeActivityMonitoring);
    } else {
        initializeActivityMonitoring();
    }

    // Exponer algunas funciones globalmente para debugging
    window.activityMonitor = {
        updateActivity: updateActivity,
        sendHeartbeat: sendHeartbeat,
        showActivityIndicator: showActivityIndicator,
        getLastActivityTime: () => lastActivityTime,
        getTimeSinceActivity: () => Date.now() - lastActivityTime
    };

})();
