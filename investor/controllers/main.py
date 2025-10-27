# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome

class Home(WebHome):
    @http.route()
    def web_login(self, redirect=None, **kw):
        response = super(Home, self).web_login(redirect=redirect, **kw)

        if request.httprequest.method == 'POST' and request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)

            if user.has_group('investor.group_investor_investor'):
                broker_id = kw.get('broker_id')
                if broker_id:
                    b_id = request.env['investor.broker'].sudo().browse(int(broker_id))
                    request.env['res.users'].sudo().browse(request.session.uid).write({'broker_id': b_id.id})
                    request.env.cr.commit()
                else:
                    request.session.logout(keep_db=True)
                    return request.redirect('/web/login?missing_broker=1')

        return response