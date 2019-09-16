# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class AccountInvoice(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def create(self, vals):
        """
        Override to link to 'timesheet_invoice_id' the invoice
        """
        invoice_line = super().create(vals)
        if (
            invoice_line.invoice_id.type == 'out_invoice'
            and invoice_line.invoice_id.state == 'draft'
        ):
            invoice_line.link_timesheets_lines()
        return invoice_line

    def link_timesheets_lines(self):
        for line in self:
            if line.product_id.type == 'service':
                so_lines = line.sale_line_ids
                domain = (
                    so_lines._timesheet_compute_delivered_quantity_domain()
                )
                domain = line._update_domain(domain)
                uninvoiced_ts_lines = (
                    self.env['account.analytic.line'].sudo().search(domain)
                )
                if uninvoiced_ts_lines:
                    uninvoiced_ts_lines.write(
                        {'timesheet_invoice_id': line.invoice_id.id}
                    )

    def _update_domain(self, domain):
        return expression.AND(
            [domain, [('timesheet_invoice_id', '=', False)]]
        )
