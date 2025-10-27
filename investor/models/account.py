from odoo import models, fields, api
from odoo.exceptions import ValidationError
class Account(models.Model):
    _name = 'investor.account'
    _description = 'Счет'

    name = fields.Char(string="Номер Счета", required=True, index=True)
    account_type = fields.Selection([
        ('iis', 'ИИС'),
        ('broker', 'Брокерский'),
        ('depository', 'Депозитарный')
    ], string="Тип Счета", required=True)
    open_date = fields.Date(string="Дата Открытия", required=True, default=fields.Date.context_today)
    status = fields.Selection([
        ('active', 'Активен'),
        ('closed', 'Закрыт'),
        ('blocked', 'Заблокирован')
    ], string="Статус", required=True, default='active')
    
    investor_id = fields.Many2one(comodel_name='investor.investor', string="Инвестор", required=True, index=True)
    broker_id = fields.Many2one('investor.broker', string="Брокер", required=True, index=True)
    
    transaction_ids = fields.One2many(comodel_name='investor.transaction', inverse_name='account_id', string="Транзакции")
    asset_line_ids = fields.One2many(comodel_name='investor.account.asset', inverse_name='account_id', string="Активы на счете")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Номер счета должен быть уникальным.')
    ]
    
    @api.constrains('open_date')
    def _check_open_date(self):
        for record in self:
            if record.open_date and record.open_date > fields.Date.today():
                raise ValidationError("Дата открытия не может быть в будущем.")

    def open_account(self):
        user = self.env.user
        domain = []
        if user.has_group('investor.group_investor_investor') and not user.has_group('investor.group_investor_admin'):
            domain.append(('broker_id', '=', user.broker_id.id))
            if user.investor_id:
                domain.append(('investor_id', '=', user.investor_id.id))
            else:
                domain.append(('investor_id.user_id', '=', user.id))
        if user.has_group('investor.group_investor_broker') and not user.has_group('investor.group_investor_admin'):
            if user.broker_id:
                domain.append(('broker_id', '=', user.broker_id.id))
            else:
                domain.append(('broker_id.user_id', '=', user.id))
        return {
            'name': 'Счета',
            'type': 'ir.actions.act_window',
            'res_model': 'investor.account',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain
        }