from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class IncomeReportWizard(models.TransientModel):
    _name = 'investor.income_report.wizard'
    _description = 'Мастер отчёта о доходах инвестора'

    investor_id = fields.Many2one('investor.investor', string="Инвестор", required=True)
    date_from = fields.Date(string="Дата начала", required=True, default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string="Дата окончания", required=True, default=fields.Date.context_today)

    def _compute_dynamic_domain(self):  
        if self.env.user.has_group('investor.group_investor_investor'):
            return [('investor_id', '=', self.env.user.investor_id.id)]
        return []

    account_id = fields.Many2one('investor.account', string="Счёт (опционально)", domain=_compute_dynamic_domain)
    
    @api.model
    def default_get(self, fields_list):
        """Автоматически выбирает инвестора для текущего пользователя"""
        res = super().default_get(fields_list)
        user = self.env.user
        
        # Если пользователь - инвестор, автоматически выбираем его инвестора
        if user.has_group('investor.group_investor_investor') and user.investor_id:
            res['investor_id'] = user.investor_id.id
        
        return res

    @api.onchange('investor_id')
    def _onchange_investor_id(self):
        """Обновляет список доступных счетов при выборе инвестора"""
        self.account_id = False  # Сбрасываем выбранный счёт
        if self.investor_id:
            domain = [('investor_id', '=', self.investor_id.id)]
            return {'domain': {'account_id': domain}}
        return {'domain': {'account_id': []}}

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from > record.date_to:
                raise UserError("Дата начала не может быть позже даты окончания.")

    def action_generate_report(self):
        """Генерация отчёта о доходах"""
        self.ensure_one()
        
        # Проверка прав доступа
        user = self.env.user
        if user.has_group('investor.group_investor_investor') and not user.has_group('investor.group_investor_admin'):
            if self.investor_id.user_id != user:
                raise UserError("У вас нет доступа к отчётам других инвесторов.")

        # Создаём запись отчёта
        report = self.env['investor.income_report'].create({
            'investor_id': self.investor_id.id,
            'account_id': self.account_id.id if self.account_id else False,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        
        # Возвращаем action для отображения отчёта
        return {
            'type': 'ir.actions.report',
            'report_name': 'investor.income_report',
            'report_type': 'qweb-html',
            'res_model': 'investor.income_report',
            'context': {'active_ids': [report.id], 'active_id': report.id},
            'res_id': report.id,
        }


