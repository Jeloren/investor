from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    broker_id = fields.Many2one('investor.broker', string="Брокер")
    investor_id = fields.Many2one(comodel_name='investor.investor', string="Инвестор", index=True)

    MODULE_NAME = 'investor' 

    INVESTOR_ROLE_GROUPS_MAP = {
        'admin': f'{MODULE_NAME}.group_investor_admin',
        'broker': f'{MODULE_NAME}.group_investor_broker',
        'investor': f'{MODULE_NAME}.group_investor_investor',
    }

    investor_role_type = fields.Selection(
        [
            ('admin', 'Администратор инвестиций'),
            ('broker', 'Брокер'),
            ('investor', 'Инвестор'),
        ],
        string="Роль в инвестициях",
        compute='_compute_investor_role_type',
        inverse='_inverse_investor_role_type',
        store=True,
        readonly=False,
        default=False,
    )

    @api.depends('groups_id')
    def _compute_investor_role_type(self):
        """
        Вычисляет значение 'selection' (radio) на основе групп, в которых
        состоит пользователь. Срабатывает при загрузке формы.
        """
        for user in self:
            user.investor_role_type = False
            if user.has_group(self.INVESTOR_ROLE_GROUPS_MAP['admin']):
                user.investor_role_type = 'admin'
            elif user.has_group(self.INVESTOR_ROLE_GROUPS_MAP['broker']):
                user.investor_role_type = 'broker'
            elif user.has_group(self.INVESTOR_ROLE_GROUPS_MAP['investor']):
                user.investor_role_type = 'investor'

    def _inverse_investor_role_type(self):
        """
        Обратная функция: обновляет группы пользователя при изменении
        значения 'selection' (radio). Срабатывает при сохранении.
        """
        admin_group = self.env.ref(self.INVESTOR_ROLE_GROUPS_MAP['admin'], raise_if_not_found=False)
        broker_group = self.env.ref(self.INVESTOR_ROLE_GROUPS_MAP['broker'], raise_if_not_found=False)
        investor_group = self.env.ref(self.INVESTOR_ROLE_GROUPS_MAP['investor'], raise_if_not_found=False)
        
        all_managed_groups = admin_group | broker_group | investor_group
        
        for user in self:
            user.groups_id = [(3, g.id) for g in all_managed_groups if g]
            
            selected_role = user.investor_role_type
            if selected_role == 'admin' and admin_group:
                user.groups_id = [(4, admin_group.id)]
            elif selected_role == 'broker' and broker_group:
                user.groups_id = [(4, broker_group.id)]
            elif selected_role == 'investor' and investor_group:
                user.groups_id = [(4, investor_group.id)]

    """Поля из investor"""
    inv_birth_date = fields.Date(string="Дата Рождения")
    inv_phone = fields.Char(string="Контактный Телефон")

    r_inv_name = fields.Char(related="investor_id.name")
    r_birth_date = fields.Date(related="investor_id.birth_date")
    r_phone = fields.Char(related="investor_id.phone")
    r_email = fields.Char(related="investor_id.email")

    """Поля из broker"""
    br_license_number = fields.Char(string="Лицензия")
    br_contact_details = fields.Text(string="Контактные Данные")

    r_br_name = fields.Char(related="broker_id.name")
    r_license_number = fields.Char(related="broker_id.license_number")
    r_contact_details = fields.Text(related="broker_id.contact_details")

    @api.model_create_multi
    def create(self, vals):
        users = super().create(vals)
        Broker = self.env['investor.broker']
        Investor = self.env['investor.investor']

        for user in users:
            if user.investor_role_type == 'broker' and not user.broker_id:
                user.broker_id = Broker.create({
                    'name': user.name,
                    'license_number': user.br_license_number,
                    'contact_details': user.br_contact_details,
                    'user_id': user.id,
                }).id
            elif user.investor_role_type == 'investor' and not user.investor_id:
                user.investor_id = Investor.create({
                    'name': user.name,
                    'birth_date': user.inv_birth_date,
                    'phone': user.inv_phone,
                    'email': user.email,
                    'user_id': user.id,
                }).id
        return users

    def write(self, vals):
        res = super().write(vals)
        for user in self:
            if user.has_group(self.INVESTOR_ROLE_GROUPS_MAP['investor']) and not user.broker_id:
                raise ValidationError("Инвестору необходимо назначить брокера перед сохранением.")
            
            if user.investor_id and not user.investor_id.user_id:
                user.investor_id.write({'user_id': user.id})
            
            if user.broker_id and not user.broker_id.user_id:
                user.broker_id.write({'user_id': user.id})
                
        return res

    @api.constrains('groups_id', 'broker_id')
    def _check_investor_requires_broker(self):
        for user in self:
            if user.has_group(self.INVESTOR_ROLE_GROUPS_MAP['investor']) and not user.broker_id:
                raise ValidationError("Инвестору необходимо назначить брокера.")