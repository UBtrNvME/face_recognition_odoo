from odoo import fields, models, api


class EmployeePhotobooth (models.TransientModel):
    _name = 'employee.photobooth'
    _description = 'Photo Booth'

    employee_id = fields.Reference(selection=[('hr.employee', "Employee")], string="Employee")