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
    
    # --- Поля данных ---
    transaction_ids = fields.Many2many('investor.transaction', string="Транзакции", 
                                       compute='_compute_transactions')
    
    # --- Вычисляемые поля итогов ---
    total_buy = fields.Float(string="Сумма покупок (расход)", compute='_compute_totals')
    total_sell = fields.Float(string="Сумма продаж (доход)", compute='_compute_totals')
    total_deposit = fields.Float(string="Зачисления", compute='_compute_totals')
    total_withdrawal = fields.Float(string="Списания", compute='_compute_totals')
    total_commission = fields.Float(string="Комиссии (расход)", compute='_compute_totals')
    
    financial_result = fields.Float(string="Финансовый результат (от сделок)", compute='_compute_totals')
    total_income_flow = fields.Float(string="Общий фин. поток (до налога)", compute='_compute_totals')

    # --- Новые поля для налога ---
    taxable_base = fields.Float(string="Налогооблагаемая база", compute='_compute_totals')
    tax_rate = fields.Float(string="Ставка налога (%)", compute='_compute_totals', default=13.0)
    estimated_tax = fields.Float(string="Расчетный НДФЛ", compute='_compute_totals')
    total_income_after_tax = fields.Float(string="Итоговый доход (после налога)", compute='_compute_totals')
    is_iis = fields.Boolean(compute='_compute_totals') # Вспомогательное поле для шаблона


    @api.depends('investor_id', 'account_id', 'date_from', 'date_to')
    def _compute_transactions(self):
        """Вычисляет транзакции по заданным параметрам"""
        for record in self:
            domain = [
                ('transaction_datetime', '>=', record.date_from.strftime('%Y-%m-%d 00:00:00')),
                ('transaction_datetime', '<=', record.date_to.strftime('%Y-%m-%d 23:59:59')),
                ('account_id.investor_id', '=', record.investor_id.id)
            ]
            
            if record.account_id:
                domain.append(('account_id', '=', record.account_id.id))
            
            transactions = self.env['investor.transaction'].search(domain, order='transaction_datetime')
            record.transaction_ids = transactions

    @api.depends('transaction_ids', 'account_id', 'account_id.account_type')
    def _compute_totals(self):
        """Вычисляет итоговые суммы и налоги"""
        for record in self:
            # Используем abs(), т.к. расходы часто хранятся с минусом
            record.total_buy = abs(sum(t.amount for t in record.transaction_ids if t.operation_type == 'buy'))
            record.total_sell = abs(sum(t.amount for t in record.transaction_ids if t.operation_type == 'sell'))
            record.total_deposit = abs(sum(t.amount for t in record.transaction_ids if t.operation_type == 'deposit'))
            record.total_withdrawal = abs(sum(t.amount for t in record.transaction_ids if t.operation_type == 'withdrawal'))
            record.total_commission = abs(sum(t.amount for t in record.transaction_ids if t.operation_type == 'commission'))

            # Финансовый результат (Доход от сделок)
            # Это база для налога
            record.financial_result = record.total_sell - record.total_buy - record.total_commission
            
            # Общий доход (включая пополнения/списания)
            record.total_income_flow = (record.total_sell + record.total_deposit) - (record.total_buy + record.total_withdrawal + record.total_commission)

            # --- Логика налога (упрощенная) ---
            record.is_iis = bool(record.account_id and record.account_id.account_type == 'iis')
            
            if record.is_iis:
                # Для ИИС (упрощенно, тип Б) доход не облагается налогом
                record.tax_rate = 0.0
                record.taxable_base = 0.0 
                record.estimated_tax = 0.0
            else:
                # Для обычного брокерского счета
                record.tax_rate = 13.0 # Упрощенно, 13% (без учета > 5 млн)
                
                # Налогооблагаемая база = фин. результат (если он положителен)
                # ПРИМЕЧАНИЕ: Реальный расчет сложнее (FIFO, дивиденды, купоны)
                record.taxable_base = record.financial_result if record.financial_result > 0 else 0
                record.estimated_tax = record.taxable_base * (record.tax_rate / 100.0)

            # Итоговый доход = Общий поток минус налог
            record.total_income_after_tax = record.total_income_flow - record.estimated_tax