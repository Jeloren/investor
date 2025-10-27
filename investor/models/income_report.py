from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class IncomeReport(models.Model):
    _name = 'investor.income_report'
    _description = 'Отчёт о доходах инвестора'

    investor_id = fields.Many2one('investor.investor', string="Инвестор", required=True)
    account_id = fields.Many2one('investor.account', string="Счёт (опционально)")
    date_from = fields.Date(string="Дата начала", required=True)
    date_to = fields.Date(string="Дата окончания", required=True)
    
    transaction_ids = fields.Many2many('investor.transaction', string="Транзакции", compute='_compute_transactions')
    total_buy = fields.Float(string="Сумма покупок", compute='_compute_totals')
    total_sell = fields.Float(string="Сумма продаж", compute='_compute_totals')
    total_deposit = fields.Float(string="Зачисления", compute='_compute_totals')
    total_withdrawal = fields.Float(string="Списания", compute='_compute_totals')
    total_commission = fields.Float(string="Комиссии", compute='_compute_totals')
    total_income = fields.Float(string="Чистый доход", compute='_compute_totals')

    @api.depends('investor_id', 'account_id', 'date_from', 'date_to')
    def _compute_transactions(self):
        """Вычисляет транзакции по заданным параметрам"""
        for record in self:
            if not record.investor_id or not record.date_from or not record.date_to:
                record.transaction_ids = False
                continue

            domain = [
                ('transaction_datetime', '>=', record.date_from.strftime('%Y-%m-%d 00:00:00')),
                ('transaction_datetime', '<=', record.date_to.strftime('%Y-%m-%d 23:59:59')),
                ('account_id.investor_id', '=', record.investor_id.id)
            ]
            
            if record.account_id:
                domain.append(('account_id', '=', record.account_id.id))
            
            transactions = self.env['investor.transaction'].search(domain, order='transaction_datetime')
            record.transaction_ids = transactions

    @api.depends('transaction_ids')
    def _compute_totals(self):
        """Вычисляет итоговые суммы"""
        for record in self:
            record.total_buy = sum(record.transaction_ids.filtered(lambda t: t.operation_type == 'buy').mapped('amount'))
            record.total_sell = sum(record.transaction_ids.filtered(lambda t: t.operation_type == 'sell').mapped('amount'))
            record.total_deposit = sum(record.transaction_ids.filtered(lambda t: t.operation_type == 'deposit').mapped('amount'))
            record.total_withdrawal = sum(record.transaction_ids.filtered(lambda t: t.operation_type == 'withdrawal').mapped('amount'))
            record.total_commission = sum(record.transaction_ids.filtered(lambda t: t.operation_type == 'commission').mapped('amount'))
            record.total_income = record.total_sell + record.total_deposit - record.total_buy - record.total_withdrawal - record.total_commission

    def check_access_rights(self, operation, raise_exception=True):
        """Проверка прав доступа к отчёту"""
        user = self.env.user
        if user.has_group('investor.group_investor_investor') and not user.has_group('investor.group_investor_admin'):
            if self.investor_id.user_id != user:
                if raise_exception:
                    raise UserError("У вас нет доступа к отчётам других инвесторов.")
                return False
        return super().check_access_rights(operation, raise_exception)

