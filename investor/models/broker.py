from odoo import models, fields, api

class Broker(models.Model):
    _name = 'investor.broker'
    _description = 'Брокер'

    name = fields.Char(string="Наименование", required=True)
    license_number = fields.Char(string="Лицензия", required=True, index=True)
    contact_details = fields.Text(string="Контактные Данные")
    user_id = fields.Many2one('res.users', string='Связанный пользователь', ondelete='cascade')

    _sql_constraints = [
        ('license_number_uniq', 'unique (license_number)', 'Номер лицензии должен быть уникальным.')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Переопределяем create для установки user_id из связанного пользователя"""
        brokers = super().create(vals_list)
        for broker in brokers:
            user = self.env['res.users'].search([('broker_id', '=', broker.id)], limit=1)
            if user and not broker.user_id:
                broker.write({'user_id': user.id})
        return brokers