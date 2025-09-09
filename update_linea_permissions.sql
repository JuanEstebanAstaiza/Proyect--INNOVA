-- Script SQL para actualizar permisos de 'CÓD LINEA' para el rol Editor General

-- Actualizar permisos para 'CÓD LINEA' en el rol Editor General
UPDATE column_permissions
SET can_edit = 1
WHERE column_name = 'CÓD LINEA'
AND role_id = (
    SELECT id FROM roles
    WHERE name = 'Editor General'
    AND is_active = 1
);

-- Verificar que se actualizó correctamente
SELECT
    r.name as rol_name,
    cp.column_name,
    cp.can_edit,
    cp.can_view
FROM roles r
JOIN column_permissions cp ON r.id = cp.role_id
WHERE r.name = 'Editor General'
AND cp.column_name = 'CÓD LINEA';
