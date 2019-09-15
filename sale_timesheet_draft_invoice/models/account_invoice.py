# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_cancel(self):
        self._unlink_timesheet_ids()
        return super().action_invoice_cancel()

    @api.multi
    def _unlink_timesheet_ids(self):
        """
        Unlink timesheet_ids and timesheet_invoice_id on the aal
        """
        self.write({'timesheet_ids': [(5, False)]})

    @api.multi
    def action_invoice_draft(self):
        res = super().action_invoice_draft()
        if res:
            out_inv = self.filtered(lambda inv: inv.type == 'out_invoice')
            out_inv.mapped('invoice_line_ids').link_timesheets_lines()
        return res
