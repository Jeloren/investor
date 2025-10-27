from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Transaction(models.Model):
    _name = 'investor.transaction'
    _description = 'Транзакция'
    _order = 'transaction_datetime desc'

    name = fields.Char(string="Описание", compute='_compute_name', store=True)
    transaction_datetime = fields.Datetime(string="Дата и Время", required=True, default=fields.Datetime.now, index=True)
    operation_type = fields.Selection([
        ('buy', 'Покупка'),
        ('sell', 'Продажа'),
        ('deposit', 'Зачисление'),
        ('withdrawal', 'Списание'),
        ('commission', 'Комиссия')
    ], string="Тип Операции", required=True)
    quantity = fields.Float(string="Количество", default=1.0, required=True)
    amount = fields.Float(string="Сумма Транзакции", required=True)
    currency = fields.Selection([
        ('RUB', 'RUB'), ('USD', 'USD'), ('EUR', 'EUR')
    ], string="Валюта", required=True, default='RUB')
    
    account_id = fields.Many2one('investor.account', string="Счет", required=True, index=True)
    asset_id = fields.Many2one('investor.asset', string="Актив", index=True)
    
    description = fields.Text(string="Дополнительные детали")
    
    @api.depends('operation_type', 'asset_id.name', 'account_id.name')
    def _compute_name(self):
        for trans in self:
            name_parts = []
            if trans.operation_type:
                name_parts.append(dict(self._fields['operation_type'].selection).get(trans.operation_type))
            if trans.asset_id:
                name_parts.append(trans.asset_id.name)
            if trans.account_id:
                name_parts.append(f"({trans.account_id.name})")

            trans.name = " ".join(name_parts) if name_parts else "Транзакция"

    @api.constrains('quantity', 'amount')
    def _check_positive_values(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError("Количество должно быть положительным.")
            if record.amount <= 0:
                raise ValidationError("Сумма транзакции должна быть положительной.")
            
    @api.constrains('transaction_datetime')
    def _check_transaction_datetime(self):
        for record in self:
            if record.transaction_datetime and record.transaction_datetime > fields.Datetime.now():
                raise ValidationError("Дата и время транзакции не могут быть в будущем.")
    
    @api.constrains('operation_type', 'asset_id')
    def _check_asset_for_buy_sell(self):
        for record in self:
            if record.operation_type in ['buy', 'sell'] and not record.asset_id:
                raise ValidationError("Для операций покупки или продажи необходимо указать актив.")

    def open_account(self):
        user = self.env.user
        domain = []
        if user.has_group('investor.group_investor_investor') and not user.has_group('investor.group_investor_admin'):
            domain.append(('account_id.broker_id', '=', user.broker_id.id))
            if user.investor_id:
                domain.append(('account_id.investor_id', '=', user.investor_id.id))
            else:
                domain.append(('account_id.investor_id.user_id', '=', user.id))
        if user.has_group('investor.group_investor_broker') and not user.has_group('investor.group_investor_admin'):
            if user.broker_id:
                domain.append(('account_id.broker_id', '=', user.broker_id.id))
            else:
                domain.append(('account_id.broker_id.user_id', '=', user.id))
        return {
            'name': 'Транзакции',
            'type': 'ir.actions.act_window',
            'res_model': 'investor.transaction',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain
        }