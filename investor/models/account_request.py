from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountRequest(models.Model):
    _name = 'investor.account.request'
    _description = 'Заявка на открытие счета'

    investor_id = fields.Many2one('investor.investor', string="Инвестор", required=True, readonly=True)
    broker_id = fields.Many2one('investor.broker', string="Брокер", required=True, readonly=True)
    account_type = fields.Selection([
        ('iis', 'ИИС'),
        ('broker', 'Брокерский'),
        ('depository', 'Депозитарный')
    ], string="Тип Счёта", required=True, readonly=True)

    status = fields.Selection([
        ('draft', 'На рассмотрении'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
        ('done', 'Счёт создан'),
    ], string="Статус", default='draft', required=True, readonly=True)

    account_id = fields.Many2one('investor.account', string="Созданный счёт", readonly=True)

    def action_approve(self):
        """Одобрить заявку и создать счет через sudo"""
        self.ensure_one()
        if self.status not in ('draft', 'approved'):
            return

        account = self.env['investor.account'].sudo().create({
            'name': self.env['ir.sequence'].next_by_code('investor.account') or '/',
            'account_type': self.account_type,
            'investor_id': self.investor_id.id,
            'broker_id': self.broker_id.id,
        })

        self.write({
            'status': 'done',
            'account_id': account.id
        })

    def action_reject(self):
        self.write({'status': 'rejected'})
