# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.osv import expression
from ast import literal_eval
from operator import itemgetter
from datetime import datetime
from odoo.exceptions import UserError

from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


def get_numbers(start, end):
    end = end + 1
    days_range = list(range(start, end))
    formatted_list = [str(x) for x in days_range]
    days_tuples = [tuple([number] + [number]) for number in formatted_list]
    return days_tuples


class DashboardBlock(models.Model):
    _name = "dashboard.block"
    _description = "Dashboard Blocks"
    _rec_name = "name"

    def get_default_action(self):
        action_id = self.env.ref('silksoft_dashboards.action_dynamic_dashboard')
        if action_id:
            return action_id.id
        else:
            return False

    name = fields.Char(string="Name", help='Name of the block')
    field_id = fields.Many2one('ir.model.fields', 'Measured Field',
                               domain="[('store', '=', True), ('model_id', '=', model_id), "
                                      "('ttype', 'in', ['float','integer','monetary'])]")
    fa_icon = fields.Char(string="Icon")
    graph_size = fields.Selection(
        selection=[("col-lg-4", "Small"), ("col-lg-6", "Medium"), ("col-lg-12", "Large")],
        string="Graph Size", default='col-lg-4')
    operation = fields.Selection(
        selection=[("sum", "Sum"), ("avg", "Average"), ("count", "Count")],
        string="Operation", help='Tile Operation that needs to bring values for tile')

    graph_type = fields.Selection(
        selection=[("bar", "Bar"), ("radar", "Radar"), ("pie", "Pie"), ("line", "Line"), ("doughnut", "Doughnut")],
        string="Chart Type", help='Type of Chart')
    measured_field = fields.Many2one("ir.model.fields", "Measured Field")
    client_action = fields.Many2one('ir.actions.client', default=get_default_action)

    type = fields.Selection(
        selection=[("graph", "Chart"), ("tile", "Tile")], string="Type", help='Type of Block ie, Chart or Tile')
    x_axis = fields.Char(string="X-Axis")
    y_axis = fields.Char(string="Y-Axis")
    group_by = fields.Many2one("ir.model.fields", store=True, string="Group by(Y-Axis)", help='Field value for Y-Axis')
    tile_color = fields.Char(string="Tile Color", help='Primary Color of Tile')
    text_color = fields.Char(string="Text Color", help='Text Color of Tile')
    fa_color = fields.Char(string="Icon Color", help='Icon Color of Tile')
    filter = fields.Char(string="Filter")
    model_id = fields.Many2one('ir.model', 'Model')
    model_name = fields.Char(related='model_id.model', readonly=True)

    filter_by = fields.Many2one("ir.model.fields", string=" Filter By")
    filter_values = fields.Char(string="Filter Values")

    sequence = fields.Integer(string="Sequence")
    edit_mode = fields.Boolean(default=False, invisible=True)
    is_python_code = fields.Boolean(string="Code Execution")
    python_code = fields.Text(string="Python Code", default='''# Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories 
# (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days.
# inputs: object containing the computed inputs.
# Note: returned value have to be set in the variable 'result'
result = 0''')
    filter_by_user = fields.Boolean(string="Filter By User")
    filter_by_employee = fields.Boolean(string="Filter By Employee")
    user_field_id = fields.Many2one('ir.model.fields', 'User Field', domain="[('store', '=', True),"
                                                                            " ('model_id', '=', model_id),"
                                                                            " ('ttype', 'in', "
                                                                            "['one2many', 'many2one']),"
                                                                            " ('relation', '=', 'res.users')]")
    employee_field_id = fields.Many2one('ir.model.fields', 'Employee Field', domain="[('store', '=', True),"
                                                                                    " ('model_id', '=', model_id),"
                                                                                    " ('ttype', 'in', "
                                                                                    "['one2many', 'many2one']),"
                                                                                    " ('relation', '=',"
                                                                                    " 'hr.employee')]")
    filter_monthly = fields.Boolean(string="Filter Monthly")
    across_months = fields.Boolean(string="Across Months")
    from_day_monthly = fields.Selection(string="Day From", selection=get_numbers(1, 28))
    to_day_monthly = fields.Selection(string="Day to", selection=get_numbers(1, 28))
    date_field_id = fields.Many2one('ir.model.fields', 'Employee Field', domain="[('store', '=', True),"
                                                                                " ('model_id', '=', model_id),"
                                                                                " ('ttype', '=', 'datetime')]")

    def get_dashboard_vals(self, action_id):
        """Dashboard block values"""
        block_id = []
        dashboard_block = self.env['dashboard.block'].sudo().search([('client_action', '=', int(action_id))])
        for rec in dashboard_block:
            color = rec.tile_color if rec.tile_color else '#1f6abb;'
            icon_color = rec.tile_color if rec.tile_color else '#1f6abb;'
            text_color = rec.text_color if rec.text_color else '#FFFFFF;'
            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                'graph_type': rec.graph_type,
                'icon': rec.fa_icon,
                'cols': rec.graph_size,
                'color': 'background-color: %s;' % color,
                'text_color': 'color: %s;' % text_color,
                'icon_color': 'color: %s;' % icon_color,
            }
            domain = []
            employee_filter = '[]'
            user_filter = '[]'
            from_date_formatted = '[]'
            to_date_formatted = '[]'
            if rec.filter_by_employee or rec.filter or rec.filter_by_user or rec.filter_monthly:
                if rec.filter_by_employee:
                    employee_filter = str([(rec.employee_field_id.name, '=', self.env.user.employee_id.id)])
                if rec.filter_by_user:
                    user_filter = str([(rec.user_field_id.name, '=', self.env.uid)])
                if rec.filter_monthly:
                    from_month = datetime.today().month
                    to_month = datetime.today().month
                    from_year = datetime.today().year
                    to_year = datetime.today().year
                    today = datetime.today().day
                    if rec.across_months:
                        if today > int(rec.from_day_monthly):
                            to_month = to_month + 1
                            if to_month == 12:
                                to_year = to_year + 1
                        else:
                            from_month = from_month - 1
                    date_from_string = rec.from_day_monthly+"-"+str(from_month)+"-"+str(from_year)
                    from_date_datetime = datetime.combine(datetime.strptime(date_from_string, "%d-%m-%Y")
                                                          , datetime.min.time())
                    from_date_formatted = str([(rec.date_field_id.name, '>=',
                                                from_date_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])
                    date_to_string = rec.to_day_monthly+"-"+str(to_month)+"-"+str(to_year)
                    to_date_datetime = datetime.combine(datetime.strptime(date_to_string, "%d-%m-%Y")
                                                        , datetime.max.time())
                    to_date_formatted = str([(rec.date_field_id.name, '<=',
                                            to_date_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])
                domain = expression.AND([literal_eval(rec.filter),
                                         literal_eval(employee_filter),
                                         literal_eval(user_filter),
                                         literal_eval(from_date_formatted),
                                         literal_eval(to_date_formatted)])
            if rec.model_name:
                if rec.type == 'graph':
                    query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field,
                                                               group_by=rec.group_by)
                    self._cr.execute(query)
                    records = self._cr.dictfetchall()
                    records = sorted(records, key=itemgetter(rec.group_by.name))
                    x_axis = []
                    for record in records:
                        x_axis.append(record.get(rec.group_by.name))
                    y_axis = []
                    for record in records:
                        y_axis.append(record.get('value'))
                    vals.update({'x_axis': x_axis, 'y_axis': y_axis})
                else:
                    query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field)
                    self._cr.execute(query)
                    records = self._cr.dictfetchall()
                    magnitude = 0
                    total = records[0].get('value')
                    while abs(total) >= 1000:
                        magnitude += 1
                        total /= 1000.0
                    # add more suffixes if you need them
                    val = '%.2f%s' % (total, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
                    if rec.is_python_code and rec.python_code:
                        try:
                            loc = {}
                            # we need to pass all global variables
                            exec(rec.python_code, {"val": val}, loc)
                            val = loc['result']
                        except Exception as e:
                            raise UserError(_('Wrong python code written in block %s and the error (%s).')
                                            % (rec.name, e))
                    records[0]['value'] = val
                    vals.update(records[0])
            block_id.append(vals)
        return block_id


class DataSet(dict):

    def __init__(self, model, field_to_search, field_to_calculate):
        super().__init__()
        self.model = model
        self.field_to_search = field_to_search
        self.field_to_calculate = field_to_calculate

    def __getitem__(self, item):
        record = self.model.search([(self.field_to_search, '=', item)], limit=1)
        if record:
            return getattr(record, self.field_to_calculate)
        else:
            return 0


class DashboardBlockLine(models.Model):
    _name = "dashboard.block.line"

    sequence = fields.Integer(string="Sequence")
    block_size = fields.Integer(string="Block size")
