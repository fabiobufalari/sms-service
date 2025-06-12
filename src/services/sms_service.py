import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from src.models.sms import SmsMessage, db
from datetime import datetime

class SmsService:
    """Service class for handling SMS operations using Twilio"""
    
    def __init__(self):
        # Twilio configuration - these should be set as environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'your_account_sid_here')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token_here')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER', '+15551234567')
        
        # Initialize Twilio client
        if self.account_sid != 'your_account_sid_here' and self.auth_token != 'your_auth_token_here':
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            print("Warning: Twilio credentials not configured. SMS sending will be simulated.")
    
    def send_sms(self, to_number, message, template_data=None):
        """
        Send a single SMS message
        
        Args:
            to_number (str): Destination phone number
            message (str): Message content
            template_data (dict): Optional data for template substitution
            
        Returns:
            dict: Result with success status and message details
        """
        try:
            # Process template data if provided
            if template_data:
                message = self._process_template(message, template_data)
            
            # Create SMS record in database
            sms_record = SmsMessage(
                from_number=self.from_number,
                to_number=to_number,
                message=message,
                status='pending'
            )
            db.session.add(sms_record)
            db.session.commit()
            
            # Send SMS via Twilio
            if self.client:
                try:
                    twilio_message = self.client.messages.create(
                        body=message,
                        from_=self.from_number,
                        to=to_number
                    )
                    
                    # Update record with Twilio response
                    sms_record.provider_message_id = twilio_message.sid
                    sms_record.status = 'sent'
                    sms_record.provider_response = str(twilio_message.status)
                    db.session.commit()
                    
                    return {
                        'success': True,
                        'message_id': sms_record.id,
                        'provider_message_id': twilio_message.sid,
                        'status': 'sent'
                    }
                    
                except TwilioException as e:
                    # Update record with error
                    sms_record.status = 'failed'
                    sms_record.provider_response = str(e)
                    db.session.commit()
                    
                    return {
                        'success': False,
                        'message_id': sms_record.id,
                        'error': str(e),
                        'status': 'failed'
                    }
            else:
                # Simulate SMS sending for testing
                sms_record.status = 'sent'
                sms_record.provider_message_id = f'sim_{sms_record.id}'
                sms_record.provider_response = 'Simulated send - Twilio not configured'
                db.session.commit()
                
                return {
                    'success': True,
                    'message_id': sms_record.id,
                    'provider_message_id': f'sim_{sms_record.id}',
                    'status': 'sent',
                    'note': 'Simulated send - Twilio not configured'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
    
    def send_bulk_sms(self, phone_numbers, message, template_data=None):
        """
        Send SMS to multiple phone numbers
        
        Args:
            phone_numbers (list): List of destination phone numbers
            message (str): Message content
            template_data (dict): Optional data for template substitution
            
        Returns:
            dict: Result with success status and details for each message
        """
        results = []
        
        for phone_number in phone_numbers:
            result = self.send_sms(phone_number, message, template_data)
            results.append({
                'phone_number': phone_number,
                'result': result
            })
        
        # Calculate summary
        successful = sum(1 for r in results if r['result']['success'])
        failed = len(results) - successful
        
        return {
            'success': failed == 0,
            'total_sent': len(phone_numbers),
            'successful': successful,
            'failed': failed,
            'results': results
        }
    
    def send_group_sms(self, group_id, message, template_data=None):
        """
        Send SMS to all contacts in a group
        
        Args:
            group_id (int): ID of the contact group
            message (str): Message content
            template_data (dict): Optional data for template substitution
            
        Returns:
            dict: Result with success status and details
        """
        from src.models.sms import ContactGroup
        
        try:
            # Get group and its contacts
            group = ContactGroup.query.get(group_id)
            if not group:
                return {
                    'success': False,
                    'error': f'Group with ID {group_id} not found'
                }
            
            if not group.active:
                return {
                    'success': False,
                    'error': f'Group {group.name} is not active'
                }
            
            # Get active contacts from the group
            active_contacts = [contact for contact in group.contacts if contact.active]
            phone_numbers = [contact.phone_number for contact in active_contacts]
            
            if not phone_numbers:
                return {
                    'success': False,
                    'error': f'No active contacts found in group {group.name}'
                }
            
            # Send bulk SMS
            result = self.send_bulk_sms(phone_numbers, message, template_data)
            result['group_name'] = group.name
            result['group_id'] = group_id
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_message_status(self, message_id):
        """
        Get the status of a specific message
        
        Args:
            message_id (int): ID of the SMS message
            
        Returns:
            dict: Message status and details
        """
        try:
            sms_record = SmsMessage.query.get(message_id)
            if not sms_record:
                return {
                    'success': False,
                    'error': f'Message with ID {message_id} not found'
                }
            
            # If we have a Twilio message ID, try to get updated status
            if self.client and sms_record.provider_message_id and not sms_record.provider_message_id.startswith('sim_'):
                try:
                    twilio_message = self.client.messages(sms_record.provider_message_id).fetch()
                    
                    # Update status if it has changed
                    if twilio_message.status != sms_record.status:
                        sms_record.status = twilio_message.status
                        sms_record.updated_at = datetime.utcnow()
                        db.session.commit()
                        
                except TwilioException:
                    # If we can't fetch from Twilio, just return what we have
                    pass
            
            return {
                'success': True,
                'message': sms_record.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_message_history(self, limit=100, offset=0, contact_type=None):
        """
        Get SMS message history
        
        Args:
            limit (int): Maximum number of messages to return
            offset (int): Number of messages to skip
            contact_type (str): Filter by contact type (client, employee)
            
        Returns:
            dict: List of messages and pagination info
        """
        try:
            query = SmsMessage.query.order_by(SmsMessage.created_at.desc())
            
            # Apply filters if needed
            if contact_type:
                from src.models.sms import Contact
                query = query.join(Contact, SmsMessage.to_number == Contact.phone_number)
                query = query.filter(Contact.contact_type == contact_type)
            
            # Apply pagination
            total = query.count()
            messages = query.offset(offset).limit(limit).all()
            
            return {
                'success': True,
                'messages': [msg.to_dict() for msg in messages],
                'pagination': {
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_template(self, message, template_data):
        """
        Process template placeholders in message
        
        Args:
            message (str): Message with placeholders
            template_data (dict): Data to substitute
            
        Returns:
            str: Processed message
        """
        try:
            return message.format(**template_data)
        except KeyError as e:
            # If a placeholder is missing, return the original message
            print(f"Warning: Template placeholder {e} not found in data")
            return message
        except Exception:
            # If any other error occurs, return the original message
            return message

