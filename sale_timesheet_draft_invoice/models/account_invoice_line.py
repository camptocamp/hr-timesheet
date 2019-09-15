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

    @api.multi
    def ail_analytic_compute_delivered_quantity(self):
        """
        Recompute qty based on analytic lines in same way as in SO
        """
        invoices = self.mapped('invoice_id')
        # The delivered quantity of Sales Lines in 'manual' mode
        # should not be erased
        self = self.filtered(
            lambda ail: ail.product_id.service_type != 'manual'
        )

        # avoid recomputation if no lines concerned
        if not self:
            return False
        for inv in invoices:
            ail_lines = self.filtered(lambda l: l.invoice_id == inv)
            so_lines = ail_lines.mapped('sale_line_ids')
            domain = (
                so_lines._timesheet_compute_delivered_quantity_domain()
            )
            domain = expression.AND(
                [domain, [('timesheet_invoice_id', '=', inv.id)]]
            )
            lines = self.env['account.analytic.line'].search(domain)
            for sol in so_lines:
                # here we expect that in one invoice invoice lines have
                # unique so_line
                qty = sum(lines.filtered(
                    lambda l: l.so_line == sol).mapped('unit_amount')
                )
                ail = self.filtered(lambda l: l.sale_line_ids == sol)
                ail.write({'quantity': qty})
        return True
