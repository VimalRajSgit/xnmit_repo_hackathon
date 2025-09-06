#!/usr/bin/env python
"""
Setup script for new installations.
Run this script to create admin user and required groups.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cms.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.core.management import call_command

def setup_database():
    print("Setting up database...")
    
    # Run migrations
    call_command('migrate')
    
    # Create required groups
    groups = ['Admin', 'Buyer', 'Customer']
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"Created group: {group_name}")
        else:
            print(f"Group already exists: {group_name}")
    
    # Create superuser if none exists
    if not User.objects.filter(is_superuser=True).exists():
        print("\nNo superuser found. Creating one...")
        call_command('createsuperuser')
    else:
        print("\nSuperuser already exists.")
    
    print("\nSetup complete!")
    print("You can now run: python manage.py runserver")

if __name__ == "__main__":
    setup_database()
