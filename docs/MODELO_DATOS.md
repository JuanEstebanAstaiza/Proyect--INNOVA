# Modelo de datos

## La matriz del Plan de Desarrollo

Las entidades territoriales colombianas hacen el seguimiento de su Plan de
Desarrollo en una matriz de Excel con **una fila por indicador de producto** y 37
columnas. `plantilla_plan.xlsx` contiene los encabezados y
`Diccionario_de_datos.txt` el tipo de dato de cada uno.

INNOVA normaliza esa matriz en seis tablas encadenadas. Una fila del Excel es el
resultado de recorrer la cadena completa:

```
PlanDesarrollo
└── LineaEstrategica        cod_linea, nombre
    └── Componente          cod_componente, nombre
        └── Programa        cod_programa, nombre, dependencia_responsable, bpim
            └── Proyecto    nombre
                └── IndicadorProducto   cod_indicador, nombre, meta, unidad...
                    └── EjecucionTrimestral  (una por año y trimestre)
```

> **Una fila del Excel = un indicador de producto.** Un proyecto suele tener
> entre 3 y 5 indicadores, y cada uno ocupa su propia fila repitiendo los datos
> de la jerarquía superior.

## Correspondencia entre columnas y campos

| Columna del Excel | Modelo | Campo |
|---|---|---|
| `CÓD LINEA` | LineaEstrategica | `cod_linea` (entero) |
| `LINEAS ESTRATEGICAS` | LineaEstrategica | `nombre` |
| `CÓD COMPONENTE` | Componente | `cod_componente` (decimal, p. ej. 1.2) |
| `COMPONENTES` | Componente | `nombre` |
| `CÓD PROGRAMA` | Programa | `cod_programa` |
| `PROGRAMA PDM` | Programa | `nombre` |
| `DEPENDENCIA RESPOSABLE` | Programa | `dependencia_responsable` |
| `BPIM` | Programa | `bpim` |
| `NOMBRE PROYECTO` | Proyecto | `nombre` |
| `INDICADORES` | IndicadorProducto | `nombre` |
| `CÓD INDICADOR DE PRODUCTO` | IndicadorProducto | `cod_indicador` |
| `INDICADOR DE PRODUCTO` | IndicadorProducto | `nombre` |
| `TIPO DE INDICADOR` | IndicadorProducto | `tipo_indicador` |
| `LINEA BASE` | IndicadorProducto | `linea_base` |
| `SENTIDO` | IndicadorProducto | `sentido` |
| `TIPOLOGÍA` | IndicadorProducto | `tipologia` |
| `UNIDAD` | IndicadorProducto | `unidad` |
| `META CUATRIENIO (2024-2027)` | IndicadorProducto | `meta_cuatrienio` |
| `META 2024` | IndicadorProducto | `meta_2024` |
| `EJECUCIÓN I…IV TRIMESTRE` | EjecucionTrimestral | `ejecucion_trimestral` (fila por trimestre) |
| `% CUMPLIMIENTO I…IV TRIMESTRE` | EjecucionTrimestral | `cumplimiento_trimestral` |
| `POBLACIÓN IMPACTADA … I…IV TRIMESTRE` | EjecucionTrimestral | `poblacion_impactada_trimestral` |
| `OBSERVACIÓN AL CUMPLIMIENTO I…IV TRIMESTRE` | EjecucionTrimestral | `observacion_trimestral` |
| `EJECUCIÓN ACUMULADA` | — | Calculada: suma de los cuatro trimestres |
| `% CUMPLIMIENTO ACUMULADO` | — | Calculada: `ejecución acumulada / META 2024 × 100` |

Las columnas `DEPENDENCIA RESPOSABLE` y `OBSERVACIÓN AL CUMPLIMIENTO ITRIMESTRE`
llevan erratas en el Excel original (falta la `N`, falta un espacio). Se
conservan **tal cual** para que los archivos de las entidades sigan importándose
sin retoques.

Nótese que `INDICADORES` e `INDICADOR DE PRODUCTO` toman el mismo valor: en la
matriz original son dos columnas que en la práctica se duplican.

## Tablas

### Núcleo del plan

| Tabla | Modelo | Notas |
|---|---|---|
| `planes_desarrollo` | `PlanDesarrollo` | `estado`: borrador, activo, finalizado, cancelado. `municipio_id` apunta al usuario dueño |
| `lineas_estrategicas` | `LineaEstrategica` | |
| `componentes` | `Componente` | `cod_componente` es decimal |
| `programas` | `Programa` | Incluye BPIM y dependencia responsable |
| `proyectos` | `Proyecto` | Presupuesto, fechas, ubicación, sector, responsables |
| `indicadores_producto` | `IndicadorProducto` | Metas, línea base, unidad, sentido |
| `ejecuciones_trimestrales` | `EjecucionTrimestral` | Clave lógica: indicador + año + trimestre |
| `actividades` | `Actividad` | Nivel opcional bajo proyecto; no aparece en la matriz |

Solo un plan por municipio puede estar `activo`: `PlanDesarrollo.activar()` pasa
a `borrador` los demás planes del mismo municipio.

`municipio_id` apunta al usuario que creó el plan, pero el plan es de la entidad
territorial: la visibilidad se resuelve por municipio y departamento mediante
`PlanDesarrollo.visibles_para(usuario)`. Ver [PERMISOS.md](PERMISOS.md).

### Usuarios y permisos

| Tabla | Modelo | Notas |
|---|---|---|
| `users` | `User` | Cada usuario pertenece a un municipio y departamento |
| `roles` | `Role` | Cinco roles por defecto; los de sistema no se pueden borrar |
| `column_permissions` | `ColumnPermission` | 37 filas por rol, una por columna |
| `user_roles` | `UserRole` | Asignación usuario ↔ rol |
| `row_permissions` | `RowPermission` | Acceso a una entidad concreta de la jerarquía |

`users.legacy_role` (`admin`/`editor`/`viewer`) es el sistema antiguo. Sigue
vivo como respaldo: si un usuario no tiene ninguna fila en `user_roles`,
`is_admin()` e `is_editor()` recurren a él.

> Cuidado al consultar: `User.role` es una **propiedad de Python**, no una
> columna. Filtrar con `User.query.filter_by(role='admin')` no da error pero
> devuelve 0 resultados. Hay que usar `legacy_role`.

### Auditoría y sesiones

| Tabla | Modelo | Notas |
|---|---|---|
| `edit_justifications` | `EditJustification` | Valor anterior, valor nuevo, motivo, autor, archivo de soporte |
| `activity_logs` | `ActivityLog` | Login, creación de planes, etc. |
| `active_sessions` | `ActiveSession` | JWT, huella del dispositivo, última actividad |
| `documentos` | `Documento` | Anexos; se cuelgan de cualquier nivel de la jerarquía |
| `smtp_configs` | `SMTPConfig` | Servidor de correo por municipio |
| `user_temp_passwords` | `UserTempPassword` | Contraseñas temporales con caducidad |

### Modelos heredados

`Objetivo`, `Meta` e `Indicador` (`app/models/objetivo.py`, `meta.py`,
`indicador.py`) son de un diseño anterior. **No se exportan en
`app/models/__init__.py` ni se usan en ninguna vista.** Se conservan solo como
referencia histórica.

Como esos modelos no se registran, la relación `PlanDesarrollo.objetivos` no
llega a existir. `PlanDesarrollo.get_progreso_general()` la usaba y lanzaba
`AttributeError`; ahora promedia el progreso de las líneas estratégicas, igual
que `LineaEstrategica.get_progreso_general()` promedia el de sus componentes.

## Documentos anexos

`Documento` tiene una clave foránea *opcional* hacia cada nivel (`plan_id`,
`linea_estrategica_id`, `componente_id`, `programa_id`, `proyecto_id`,
`indicador_id`). Se rellena solo la del nivel al que se adjunta el archivo.
El campo `confidencialidad` acepta `publico`, `interno` o `confidencial`, y el
límite de tamaño son 50 MB (`MAX_CONTENT_LENGTH`).

## Ejecución trimestral

Cada `EjecucionTrimestral` guarda un trimestre de un año para un indicador. Para
el año 2024 completo hay cuatro filas por indicador. Además de la ejecución y el
cumplimiento almacena población impactada, presupuesto ejecutado, la fuente de
la información y una marca `verificado`.

Los valores acumulados que muestra la matriz se **calculan al vuelo** en la vista
Excel y en la exportación; las columnas `*_acumulado` de la tabla existen pero no
son la fuente de verdad de esa vista.
