from odoo import models, fields

class StudyGame(models.Model):
    _name = "study.game"
    _description = "Study Game (Memory)"

    name = fields.Char("Название", default="Игра 'Найди пару'")
