# Interfaz y sistema de diseño

Toda la capa visual vive en un solo archivo: `app/static/css/style.css`. No hay
compilador, ni preprocesador, ni framework de componentes: Bootstrap 5 pone la
retícula y el comportamiento, y esta hoja reescribe su apariencia.

## A quién está dirigida

Servidores públicos de alcaldías y gobernaciones que pasan la jornada frente a
una matriz de 37 columnas. Eso fija las prioridades:

1. **Legibilidad antes que efecto.** Nada de degradados, brillos ni animaciones
   de entrada escalonadas.
2. **Tipografía grande.** El cuerpo arranca en 17 px y ningún texto auxiliar
   baja de 14 px.
3. **Contraste suficiente.** Los tres niveles de tinta y los cinco colores de
   estado cumplen WCAG AA sobre fondo claro.
4. **Objetivos amplios.** Botones de 42 px de alto mínimo, campos de 44 px.
5. **Foco siempre visible.** Un solo anillo, el mismo en toda la aplicación.

## Paleta

El fondo no es blanco puro sino un papel cálido (`#f2f0ec`): reduce el
deslumbramiento en jornadas largas y deja que las tarjetas blancas destaquen.

| Función | Variable | Valor | Contraste sobre blanco |
|---|---|---|---|
| Texto principal | `--tinta` | `#232a2f` | 13.9:1 |
| Texto secundario | `--tinta-2` | `#4f5a63` | 7.4:1 |
| Texto apagado | `--tinta-3` | `#6d777f` | 4.9:1 |
| Institucional | `--primario` | `#1d5265` | 8.7:1 |
| Correcto | `--exito` | `#3d6b52` | 5.9:1 |
| Advertencia | `--aviso` | `#8a6d21` | 5.0:1 |
| Error | `--peligro` | `#9c4630` | 6.4:1 |
| Informativo | `--info` | `#3f6483` | 6.2:1 |

Todos los tonos están desaturados a propósito. El azul petróleo sustituye al
azul saturado; el rojo es terracota; el amarillo es ocre. El color se reserva
para señalar **estado**, nunca para decorar.

Las variables de Bootstrap (`--bs-primary`, `--bs-body-color`, …) se reescriben
en `:root`, de modo que los componentes que no personalizamos heredan la paleta
en lugar del azul de fábrica.

## Tipografía

`Source Sans 3` desde Google Fonts, con respaldo en la fuente del sistema. Una
sola familia en toda la aplicación.

Las celdas numéricas usan `font-variant-numeric: tabular-nums`, para que las
cifras de la matriz queden alineadas en columna.

## Componentes propios

Clases definidas por el proyecto, más allá de las de Bootstrap:

| Clase | Para qué |
|---|---|
| `.encabezado-pagina` | Título, subtítulo y acciones de cada pantalla |
| `.barra-acciones` | Franja de botones sobre una tabla o tarjeta |
| `.atajo` | Mosaico de acceso rápido del panel de administración |
| `.tarjeta-acceso` | Tarjeta pulsable completa (inicio) |
| `.estado-vacio` | Pantalla sin datos, con su llamada a la acción |
| `.matriz-envoltura` | Contenedor con desplazamiento de la matriz del plan |
| `.matriz-ayuda`, `.matriz-leyenda` | Pista de uso y leyenda de colores |
| `.stat-card`, `.stat-valor`, `.stat-etiqueta` | Tarjetas de cifras |
| `.avatar-circle`, `.icon-circle` (`.avatar-sm`, `.avatar-md`) | Discos con inicial o icono |
| `.punto-estado` | Punto de color para activo / inactivo / alerta |
| `.salto-contenido` | Enlace de salto al contenido para teclado |

## La matriz del plan

Es la pantalla donde más tiempo se pasa, y tiene tratamiento aparte:

- **Encabezado fijo** al desplazarse en vertical.
- **Primera columna fija** al desplazarse en horizontal (desde 992 px).
- **Franja de color por grupo de columnas** —estructura, indicadores,
  ejecución, cumplimiento, acumulado, documentos— en seis tonos del mismo
  sistema, con su leyenda debajo de la tabla. Antes era un degradado
  azul-verde-naranja-rojo bajo cada encabezado.
- **Celda editable frente a celda de solo lectura**: la editable revela su
  borde al pasar el ratón; la de solo lectura queda en tinta secundaria y no
  cambia el cursor.
- **Celda en edición**: resalte ocre fijo. Antes latía con una animación
  infinita.

## Accesibilidad

- Enlace «Ir al contenido» como primer elemento enfocable.
- `:focus-visible` con anillo propio en todos los controles.
- `prefers-reduced-motion: reduce` anula transiciones y animaciones.
- Los `<h1>` de página van en tinta normal. Antes se coloreaban según la acción
  (azul crear, ámbar editar, cian ver), lo que convertía el color en ruido.

## Al modificar la interfaz

- **No agregue bloques `<style>` a las plantillas.** Se retiraron 31 de ellos
  porque repetían —y contradecían— las reglas globales. La excepción es
  `app/templates/emails/`: los clientes de correo ignoran las hojas externas y
  ese CSS tiene que ir en línea.
- **No escriba colores en línea.** Use las variables de `:root`.
- Antes de dar por buena una pantalla nueva, compruébela con el teclado y a
  400 px de ancho.
