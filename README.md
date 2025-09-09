# Proyecto INNOVA

Una aplicación web completa para la gestión integral de proyectos innovadores, diseñada específicamente para organizaciones modernas. Incluye sistema de autenticación, gestión jerárquica de proyectos, indicadores con seguimiento trimestral y sistema de documentos anexos.

## 🚀 Características Principales

- ✅ **Sistema de autenticación completo** con roles de usuario
- ✅ **Dashboard administrativo** con estadísticas en tiempo real
- ✅ **Gestión completa de proyectos innovadores**
- ✅ **Estructura jerárquica completa**: Plan → Líneas Estratégicas → Componentes → Programas PDM → Proyectos
- ✅ **Sistema de indicadores** con seguimiento trimestral y cálculo automático de progreso
- ✅ **Gestión de documentos anexos** en cualquier nivel de la jerarquía
- ✅ **Interfaz responsiva y moderna** optimizada para dispositivos móviles
- ✅ **Preparado para deployment** en Apache/Nginx con Gunicorn
- ✅ **Base de datos SQLite** relacional completa
- ✅ **Sistema de logging y monitoreo**

## 🏗️ Arquitectura del Sistema

### Base de Datos Relacional (SQLite)

```
PlanDesarrollo
├── LineaEstrategica (CÓD LINEA)
│   ├── Componente (CÓD COMPONENTE)
│   │   ├── Programa (CÓD PROGRAMA)
│   │   │   ├── Proyecto (NOMBRE PROYECTO)
│   │   │   │   ├── IndicadorProducto (INDICADORES)
│   │   │   │   │   ├── EjecucionTrimestral (SEGUIMIENTO)
│   │   │   │   │   └── Documento (ANEXOS)
│   │   │   │   └── Documento (ANEXOS)
│   │   │   └── Documento (ANEXOS)
│   │   └── Documento (ANEXOS)
│   └── Documento (ANEXOS)
└── Documento (ANEXOS)
```

### Tecnologías Utilizadas

- **Backend**: Flask 3.1.2
- **Base de Datos**: SQLAlchemy 2.0 con SQLite
- **Autenticación**: Flask-Login
- **Formularios**: Flask-WTF
- **Frontend**: Bootstrap 5, Font Awesome, JavaScript vanilla
- **Deployment**: Gunicorn, Apache/Nginx
- **Gestión de Archivos**: Werkzeug (subida segura)

## 📊 Funcionalidades Implementadas

### 1. Sistema de Autenticación
- ✅ Login/logout seguro
- ✅ Registro de nuevos usuarios
- ✅ Control de roles (Admin, Editor, Viewer)
- ✅ Usuarios asociados a municipios

### 2. Dashboard Administrativo
- ✅ Panel principal con estadísticas
- ✅ Accesos rápidos funcionales
- ✅ Navegación intuitiva
- ✅ Información del usuario actual

### 3. Gestión de Planes de Desarrollo
- ✅ **Crear planes** con información completa
- ✅ **Editar planes** existentes
- ✅ **Eliminar planes** con confirmación
- ✅ **Vista detallada** de cada plan
- ✅ **Estructura jerárquica** visual

### 4. Sistema Jerárquico Completo
- ✅ **Líneas Estratégicas** con códigos únicos
- ✅ **Componentes** asociados a líneas
- ✅ **Programas PDM** con responsables
- ✅ **Proyectos** con presupuesto y ubicación
- ✅ **Relaciones padre-hijo** completas

### 5. Indicadores y Seguimiento
- ✅ **Indicadores de producto** con metas
- ✅ **Seguimiento trimestral** automático
- ✅ **Cálculo de progreso** porcentual
- ✅ **Líneas base y objetivos** configurables

### 6. Gestión de Documentos
- ✅ **Subida de archivos** segura
- ✅ **Organización automática** por directorios
- ✅ **Control de permisos** por confidencialidad
- ✅ **Múltiples formatos** soportados (PDF, Word, Excel, imágenes, etc.)
- ✅ **Hasta 50MB** por archivo

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd alcaldias-final
```

### 2. Configurar entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

```bash
# Inicializar base de datos con datos de ejemplo
python init_db.py
```

### 5. Ejecutar la aplicación

```bash
python run.py
```

### 6. Acceder al sistema

- **URL**: `http://localhost:5000`
- **Usuario de prueba**: `admin`
- **Contraseña**: `admin123`

## 📋 Datos de Ejemplo Incluidos

Después de ejecutar `python init_db.py`, tendrás:

- ✅ **Usuario administrador** completo
- ✅ **Plan de Desarrollo Municipal 2024-2027** con estructura completa
- ✅ **Línea Estratégica**: Desarrollo Económico Sostenible
- ✅ **Componente**: Fortalecimiento del Sector Productivo
- ✅ **Programa PDM**: Programa de Apoyo a Emprendimientos
- ✅ **Proyecto**: Centro de Emprendimiento Municipal
- ✅ **Indicador**: Número de emprendedores capacitados
- ✅ **Ejecución trimestral** del primer trimestre

## 🎯 Cómo Usar el Sistema

### Crear un Plan de Desarrollo

1. **Accede al sistema** con tus credenciales
2. **Ve al Dashboard** y haz clic en "Crear Plan"
3. **Completa el formulario** con la información del plan
4. **Guarda el plan** y comienza a estructurarlo

### Gestionar la Estructura Jerárquica

1. **Desde la vista del plan**, usa los botones de acciones rápidas
2. **Agrega líneas estratégicas** con códigos únicos
3. **Crea componentes** asociados a cada línea
4. **Define programas PDM** con responsables
5. **Registra proyectos** con presupuesto y ubicación

### Subir Documentos

1. **En cualquier nivel** de la jerarquía, busca "Subir Documento"
2. **Selecciona el archivo** (máximo 50MB)
3. **Configura permisos** de confidencialidad
4. **El sistema** organiza automáticamente los archivos

## 🔧 Configuración Avanzada

### Variables de Entorno

```env
# Archivo: .env
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta-muy-segura
DATABASE_URL=sqlite:///alcaldias.db
```

### Configuración de Producción

Para deployment en producción:

```bash
# Usar Gunicorn
pip install gunicorn

# Ejecutar con Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
```

### Configuración Apache/Nginx

- ✅ **Apache**: Configuración incluida en `apache.conf`
- ✅ **Nginx**: Configuración incluida en `nginx.conf`
- ✅ **WSGI**: Archivo `wsgi.py` preparado

## 📈 Próximas Funcionalidades

- 🔄 **Sistema de reportes** avanzado
- 🔄 **Exportación a PDF/Excel**
- 🔄 **API REST** para integraciones
- 🔄 **Sistema de notificaciones**
- 🔄 **Backup automático** de base de datos
- 🔄 **Múltiples idiomas**

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

## 👥 Soporte

Para soporte técnico:

1. Revisa la documentación en este README
2. Verifica los logs de la aplicación
3. Contacta al equipo de desarrollo

---

**Proyecto INNOVA - Sistema de Gestión de Proyectos Innovadores** 🇻🇪

**Versión**: 1.0.0
**Última actualización**: Diciembre 2024
