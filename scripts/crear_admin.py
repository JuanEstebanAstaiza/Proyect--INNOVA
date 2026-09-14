#!/usr/bin/env python3
"""Crea un usuario administrador, o eleva a administrador uno que ya exista.

Pensado para el primer arranque de una instalación: el registro público
(`/auth/register`) crea siempre usuarios con rol `viewer`, así que el primer
administrador hay que designarlo desde aquí.

Uso:
    python scripts/crear_admin.py                 # pregunta los datos
    python scripts/crear_admin.py --usuario juan  # eleva a 'juan' a administrador
"""

import argparse
import getpass
import os
import sys

# Permite ejecutar este script desde cualquier directorio: anade la raiz del
# proyecto al sys.path para poder importar el paquete `app`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# La consola de Windows usa cp1252 y no puede imprimir acentos ni simbolos.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace')

from app import create_app, db
from app.models import Role, User, UserRole


def elevar_a_administrador(user):
    """Marca al usuario como administrador en el sistema legacy y en el de roles."""
    user.legacy_role = 'admin'

    rol_admin = Role.query.filter_by(name='Administrador').first()
    if rol_admin is None:
        print("AVISO: no existe el rol 'Administrador'. Ejecute antes "
              "'python scripts/init_roles.py'. El usuario queda como admin legacy.")
        db.session.commit()
        return

    ya_asignado = UserRole.query.filter_by(
        user_id=user.id, role_id=rol_admin.id, is_active=True
    ).first()

    if not ya_asignado:
        db.session.add(UserRole(
            user_id=user.id,
            role_id=rol_admin.id,
            assigned_by=user.id,
            notes='Administrador designado con scripts/crear_admin.py',
        ))

    db.session.commit()


def main():
    parser = argparse.ArgumentParser(description='Crea o eleva un usuario administrador.')
    parser.add_argument('--usuario', help='Nombre de usuario existente a elevar')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.usuario:
            user = User.query.filter_by(username=args.usuario).first()
            if user is None:
                print(f"ERROR: no existe el usuario '{args.usuario}'.")
                return 1
            elevar_a_administrador(user)
            print(f"Listo: '{user.username}' ya es administrador.")
            return 0

        print('Creación del usuario administrador\n')
        username = input('Usuario          : ').strip()
        if not username:
            print('ERROR: el usuario no puede quedar vacío.')
            return 1

        if User.query.filter_by(username=username).first():
            print(f"El usuario '{username}' ya existe; se elevará a administrador.")
            elevar_a_administrador(User.query.filter_by(username=username).first())
            print(f"Listo: '{username}' ya es administrador.")
            return 0

        email = input('Correo           : ').strip()
        if User.query.filter_by(email=email).first():
            print(f"ERROR: el correo '{email}' ya está registrado.")
            return 1

        first_name = input('Nombres          : ').strip()
        last_name = input('Apellidos        : ').strip()
        municipality = input('Municipio        : ').strip()
        department = input('Departamento     : ').strip()

        password = getpass.getpass('Contraseña       : ')
        if len(password) < 8:
            print('ERROR: la contraseña debe tener al menos 8 caracteres.')
            return 1
        if password != getpass.getpass('Repita contraseña: '):
            print('ERROR: las contraseñas no coinciden.')
            return 1

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            municipality=municipality,
            department=department,
            legacy_role='admin',
        )
        user.password = password
        db.session.add(user)
        db.session.commit()

        elevar_a_administrador(user)
        print(f"\nListo: administrador '{username}' creado. Ya puede entrar en /auth/login.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
