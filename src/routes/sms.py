from flask import Blueprint, jsonify, request
from src.models.sms import SmsMessage, Contact, ContactGroup, SmsTemplate, db
from src.services.sms_service import SmsService

sms_bp = Blueprint('sms', __name__)
sms_service = SmsService()

@sms_bp.route('/sms/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for SMS service
    Endpoint de verificação de saúde do serviço SMS
    """
    try:
        # Check database connection / Verifica conexão com banco de dados
        db.session.execute('SELECT 1')
        
        return jsonify({
            'service': 'sms-service',
            'status': 'healthy',
            'database': 'connected',
            'timestamp': str(db.func.now())
        }), 200
        
    except Exception as e:
        return jsonify({
            'service': 'sms-service',
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503

@sms_bp.route('/sms/status', methods=['GET'])
def service_status():
    """
    Service status endpoint with detailed information
    Endpoint de status do serviço com informações detalhadas
    """
    try:
        # Get service statistics / Obtém estatísticas do serviço
        total_messages = SmsMessage.query.count()
        total_contacts = Contact.query.filter_by(active=True).count()
        total_groups = ContactGroup.query.filter_by(active=True).count()
        total_templates = SmsTemplate.query.filter_by(active=True).count()
        
        return jsonify({
            'service': 'sms-service',
            'status': 'operational',
            'version': '1.0.0',
            'statistics': {
                'total_messages': total_messages,
                'total_contacts': total_contacts,
                'total_groups': total_groups,
                'total_templates': total_templates
            },
            'endpoints': {
                'send_sms': '/api/sms/send',
                'bulk_sms': '/api/sms/send/bulk',
                'group_sms': '/api/sms/send/group/<group_id>',
                'history': '/api/sms/history',
                'contacts': '/api/contacts',
                'groups': '/api/groups',
                'templates': '/api/templates'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'service': 'sms-service',
            'status': 'error',
            'error': str(e)
        }), 500

@sms_bp.route('/sms/send', methods=['POST'])
def send_sms():
    """
    Send a single SMS message
    Envia uma única mensagem SMS
    """
    try:
        data = request.json
        
        # Validate required fields / Valida campos obrigatórios
        if not data.get('to'):
            return jsonify({'success': False, 'error': 'Phone number (to) is required'}), 400
        
        if not data.get('message'):
            return jsonify({'success': False, 'error': 'Message content is required'}), 400
        
        # Send SMS / Envia SMS
        result = sms_service.send_sms(
            to_number=data['to'],
            message=data['message'],
            template_data=data.get('template_data')
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/sms/send/bulk', methods=['POST'])
def send_bulk_sms():
    """
    Send SMS to multiple phone numbers
    Envia SMS para múltiplos números de telefone
    """
    try:
        data = request.json
        
        # Validate required fields / Valida campos obrigatórios
        if not data.get('to') or not isinstance(data['to'], list):
            return jsonify({'success': False, 'error': 'Phone numbers list (to) is required'}), 400
        
        if not data.get('message'):
            return jsonify({'success': False, 'error': 'Message content is required'}), 400
        
        # Send bulk SMS / Envia SMS em massa
        result = sms_service.send_bulk_sms(
            phone_numbers=data['to'],
            message=data['message'],
            template_data=data.get('template_data')
        )
        
        status_code = 200 if result['success'] else 207  # 207 for partial success
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/sms/send/group/<int:group_id>', methods=['POST'])
def send_group_sms(group_id):
    """
    Send SMS to all contacts in a group
    Envia SMS para todos os contatos de um grupo
    """
    try:
        data = request.json
        
        # Validate required fields / Valida campos obrigatórios
        if not data.get('message'):
            return jsonify({'success': False, 'error': 'Message content is required'}), 400
        
        # Send group SMS / Envia SMS para grupo
        result = sms_service.send_group_sms(
            group_id=group_id,
            message=data['message'],
            template_data=data.get('template_data')
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/sms/history', methods=['GET'])
def get_sms_history():
    """
    Get SMS message history
    Obtém histórico de mensagens SMS
    """
    try:
        # Get query parameters / Obtém parâmetros de consulta
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        contact_type = request.args.get('contact_type')
        
        # Get message history / Obtém histórico de mensagens
        result = sms_service.get_message_history(
            limit=limit,
            offset=offset,
            contact_type=contact_type
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/sms/status/<int:message_id>', methods=['GET'])
def get_message_status(message_id):
    """
    Get the status of a specific message
    Obtém o status de uma mensagem específica
    """
    try:
        result = sms_service.get_message_status(message_id)
        
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Contact management endpoints / Endpoints de gerenciamento de contatos

@sms_bp.route('/contacts', methods=['GET'])
def get_contacts():
    """
    Get all contacts
    Obtém todos os contatos
    """
    try:
        contact_type = request.args.get('type')  # client, employee
        active_only = request.args.get('active', 'true').lower() == 'true'
        
        query = Contact.query
        
        if contact_type:
            query = query.filter(Contact.contact_type == contact_type)
        
        if active_only:
            query = query.filter(Contact.active == True)
        
        contacts = query.all()
        
        return jsonify({
            'success': True,
            'contacts': [contact.to_dict() for contact in contacts]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/contacts', methods=['POST'])
def create_contact():
    """
    Create a new contact
    Cria um novo contato
    """
    try:
        data = request.json
        
        # Validate required fields / Valida campos obrigatórios
        required_fields = ['name', 'phone_number', 'contact_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Check if contact with this phone number already exists
        # Verifica se contato com este número já existe
        existing_contact = Contact.query.filter_by(phone_number=data['phone_number']).first()
        if existing_contact:
            return jsonify({'success': False, 'error': 'Contact with this phone number already exists'}), 400
        
        # Create new contact / Cria novo contato
        contact = Contact(
            name=data['name'],
            phone_number=data['phone_number'],
            contact_type=data['contact_type'],
            email=data.get('email'),
            company=data.get('company'),
            position=data.get('position')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """
    Update an existing contact
    Atualiza um contato existente
    """
    try:
        contact = Contact.query.get_or_404(contact_id)
        data = request.json
        
        # Update fields / Atualiza campos
        contact.name = data.get('name', contact.name)
        contact.phone_number = data.get('phone_number', contact.phone_number)
        contact.contact_type = data.get('contact_type', contact.contact_type)
        contact.email = data.get('email', contact.email)
        contact.company = data.get('company', contact.company)
        contact.position = data.get('position', contact.position)
        contact.active = data.get('active', contact.active)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """
    Delete a contact (soft delete by setting active=False)
    Exclui um contato (exclusão suave definindo active=False)
    """
    try:
        contact = Contact.query.get_or_404(contact_id)
        contact.active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Contact deactivated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Contact group management endpoints / Endpoints de gerenciamento de grupos de contatos

@sms_bp.route('/groups', methods=['GET'])
def get_groups():
    """
    Get all contact groups
    Obtém todos os grupos de contatos
    """
    try:
        group_type = request.args.get('type')  # client_group, employee_group, mixed
        active_only = request.args.get('active', 'true').lower() == 'true'
        
        query = ContactGroup.query
        
        if group_type:
            query = query.filter(ContactGroup.group_type == group_type)
        
        if active_only:
            query = query.filter(ContactGroup.active == True)
        
        groups = query.all()
        
        return jsonify({
            'success': True,
            'groups': [group.to_dict() for group in groups]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/groups', methods=['POST'])
def create_group():
    """
    Create a new contact group
    Cria um novo grupo de contatos
    """
    try:
        data = request.json
        
        # Validate required fields / Valida campos obrigatórios
        required_fields = ['name', 'group_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Create new group / Cria novo grupo
        group = ContactGroup(
            name=data['name'],
            description=data.get('description'),
            group_type=data['group_type']
        )
        
        db.session.add(group)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'group': group.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/groups/<int:group_id>/members', methods=['POST'])
def add_contact_to_group(group_id):
    """
    Add a contact to a group
    Adiciona um contato a um grupo
    """
    try:
        data = request.json
        contact_id = data.get('contact_id')
        
        if not contact_id:
            return jsonify({'success': False, 'error': 'contact_id is required'}), 400
        
        group = ContactGroup.query.get_or_404(group_id)
        contact = Contact.query.get_or_404(contact_id)
        
        # Check if contact is already in the group / Verifica se contato já está no grupo
        if contact in group.contacts:
            return jsonify({'success': False, 'error': 'Contact is already in this group'}), 400
        
        # Add contact to group / Adiciona contato ao grupo
        group.contacts.append(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Contact {contact.name} added to group {group.name}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/groups/<int:group_id>/members/<int:contact_id>', methods=['DELETE'])
def remove_contact_from_group(group_id, contact_id):
    """
    Remove a contact from a group
    Remove um contato de um grupo
    """
    try:
        group = ContactGroup.query.get_or_404(group_id)
        contact = Contact.query.get_or_404(contact_id)
        
        # Check if contact is in the group / Verifica se contato está no grupo
        if contact not in group.contacts:
            return jsonify({'success': False, 'error': 'Contact is not in this group'}), 404
        
        # Remove contact from group / Remove contato do grupo
        group.contacts.remove(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Contact {contact.name} removed from group {group.name}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# SMS Template management endpoints / Endpoints de gerenciamento de templates SMS

@sms_bp.route('/templates', methods=['GET'])
def get_templates():
    """
    Get all SMS templates
    Obtém todos os templates SMS
    """
    try:
        template_type = request.args.get('type')
        active_only = request.args.get('active', 'true').lower() == 'true'
        
        query = SmsTemplate.query
        
        if template_type:
            query = query.filter(SmsTemplate.template_type == template_type)
        
        if active_only:
            query = query.filter(SmsTemplate.active == True)
        
        templates = query.all()
        
        return jsonify({
            'success': True,
            'templates': [template.to_dict() for template in templates]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sms_bp.route('/templates', methods=['POST'])
def create_template():
    """
    Create a new SMS template
    Cria um novo template SMS
    """
    try:
        data = request.json
        
        # Validate required fields / Valida campos obrigatórios
        required_fields = ['name', 'template']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Create new template / Cria novo template
        template = SmsTemplate(
            name=data['name'],
            template=data['template'],
            description=data.get('description'),
            template_type=data.get('template_type', 'general')
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'template': template.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

