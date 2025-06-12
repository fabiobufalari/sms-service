#!/usr/bin/env python3
"""
SMS Microservice Initialization Script
This script initializes the SMS microservice with sample data for testing
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app
from src.models.sms import db, Contact, ContactGroup, SmsTemplate

def init_sample_data():
    """Initialize the database with sample data for testing"""
    
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        print("Creating sample contacts...")
        
        # Create sample contacts
        contacts = [
            Contact(
                name="Fabio Bufalari",
                phone_number="+17828821713",
                contact_type="employee",
                email="bufalari.fabio@gmail.com",
                company="Financial Solutions",
                position="System Administrator"
            ),
            Contact(
                name="John Smith",
                phone_number="+15551234567",
                contact_type="client",
                email="john.smith@example.com",
                company="ABC Construction",
                position="Project Manager"
            ),
            Contact(
                name="Maria Garcia",
                phone_number="+15559876543",
                contact_type="employee",
                email="maria.garcia@financialsolutions.com",
                company="Financial Solutions",
                position="Field Supervisor"
            ),
            Contact(
                name="Robert Johnson",
                phone_number="+15555555555",
                contact_type="client",
                email="robert.johnson@xyz.com",
                company="XYZ Enterprises",
                position="CEO"
            ),
            Contact(
                name="Ana Silva",
                phone_number="+15554444444",
                contact_type="employee",
                email="ana.silva@financialsolutions.com",
                company="Financial Solutions",
                position="Project Coordinator"
            )
        ]
        
        for contact in contacts:
            db.session.add(contact)
        
        db.session.commit()
        print(f"Created {len(contacts)} sample contacts")
        
        print("Creating sample groups...")
        
        # Create sample groups
        groups = [
            ContactGroup(
                name="Field Team",
                description="Field workers and supervisors",
                group_type="employee_group"
            ),
            ContactGroup(
                name="VIP Clients",
                description="High priority clients",
                group_type="client_group"
            ),
            ContactGroup(
                name="Project Managers",
                description="All project managers (clients and employees)",
                group_type="mixed"
            )
        ]
        
        for group in groups:
            db.session.add(group)
        
        db.session.commit()
        print(f"Created {len(groups)} sample groups")
        
        print("Assigning contacts to groups...")
        
        # Assign contacts to groups
        field_team = ContactGroup.query.filter_by(name="Field Team").first()
        vip_clients = ContactGroup.query.filter_by(name="VIP Clients").first()
        project_managers = ContactGroup.query.filter_by(name="Project Managers").first()
        
        # Add employees to field team
        fabio = Contact.query.filter_by(name="Fabio Bufalari").first()
        maria = Contact.query.filter_by(name="Maria Garcia").first()
        ana = Contact.query.filter_by(name="Ana Silva").first()
        
        field_team.contacts.extend([fabio, maria, ana])
        
        # Add clients to VIP clients
        john = Contact.query.filter_by(name="John Smith").first()
        robert = Contact.query.filter_by(name="Robert Johnson").first()
        
        vip_clients.contacts.extend([john, robert])
        
        # Add project managers (mixed group)
        project_managers.contacts.extend([john, ana])  # John (client PM) and Ana (employee PM)
        
        db.session.commit()
        print("Assigned contacts to groups")
        
        print("Creating SMS templates...")
        
        # Create sample SMS templates
        templates = [
            SmsTemplate(
                name="Weather Alert",
                template="WEATHER ALERT: {weather_condition} expected at {location} on {date}. Project: {project_name}. Please take necessary precautions. - Financial Solutions",
                description="Template for weather-related alerts to field workers",
                template_type="weather_alert"
            ),
            SmsTemplate(
                name="Project Update",
                template="Project Update: {project_name} - {update_message}. Next milestone: {next_milestone}. Contact: {contact_person} - Financial Solutions",
                description="Template for general project updates",
                template_type="project_update"
            ),
            SmsTemplate(
                name="Critical Weather Warning",
                template="🚨 CRITICAL WEATHER WARNING: {weather_condition} at {location}. STOP WORK IMMEDIATELY. Safety first! Contact supervisor: {supervisor_phone} - Financial Solutions",
                description="Template for critical weather warnings",
                template_type="weather_alert"
            ),
            SmsTemplate(
                name="Meeting Reminder",
                template="Reminder: {meeting_type} scheduled for {date} at {time}. Location: {location}. Topic: {topic}. - Financial Solutions",
                description="Template for meeting reminders",
                template_type="general"
            )
        ]
        
        for template in templates:
            db.session.add(template)
        
        db.session.commit()
        print(f"Created {len(templates)} SMS templates")
        
        print("\n✅ Sample data initialization completed successfully!")
        print("\nSample data created:")
        print("- 5 contacts (3 employees, 2 clients)")
        print("- 3 groups (Field Team, VIP Clients, Project Managers)")
        print("- 4 SMS templates (weather alerts, project updates, etc.)")
        print(f"\nTest phone number configured: +17828821713 (Fabio Bufalari)")
        print("\nThe SMS microservice is ready for testing!")

if __name__ == "__main__":
    init_sample_data()

