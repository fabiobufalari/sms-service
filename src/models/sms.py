from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SmsMessage(db.Model):
    """Model for storing SMS message history"""
    id = db.Column(db.Integer, primary_key=True)
    from_number = db.Column(db.String(20), nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, delivered, failed
    provider_message_id = db.Column(db.String(100))
    provider_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SmsMessage {self.id}: {self.to_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'message': self.message,
            'status': self.status,
            'provider_message_id': self.provider_message_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Contact(db.Model):
    """Model for storing contacts (clients and employees)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    contact_type = db.Column(db.String(20), nullable=False)  # client, employee
    email = db.Column(db.String(120))
    company = db.Column(db.String(100))
    position = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with groups
    groups = db.relationship('ContactGroup', secondary='contact_group_members', back_populates='contacts')
    
    def __repr__(self):
        return f'<Contact {self.name}: {self.phone_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone_number': self.phone_number,
            'contact_type': self.contact_type,
            'email': self.email,
            'company': self.company,
            'position': self.position,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'groups': [group.to_dict() for group in self.groups]
        }

class ContactGroup(db.Model):
    """Model for storing contact groups"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    group_type = db.Column(db.String(20), nullable=False)  # client_group, employee_group, mixed
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with contacts
    contacts = db.relationship('Contact', secondary='contact_group_members', back_populates='groups')
    
    def __repr__(self):
        return f'<ContactGroup {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'group_type': self.group_type,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'contact_count': len(self.contacts)
        }

# Association table for many-to-many relationship between contacts and groups
contact_group_members = db.Table('contact_group_members',
    db.Column('contact_id', db.Integer, db.ForeignKey('contact.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('contact_group.id'), primary_key=True)
)

class SmsTemplate(db.Model):
    """Model for storing SMS templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    template = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    template_type = db.Column(db.String(50))  # weather_alert, project_update, general
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SmsTemplate {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'template': self.template,
            'description': self.description,
            'template_type': self.template_type,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

