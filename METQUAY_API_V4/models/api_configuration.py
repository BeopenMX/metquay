from odoo import models, fields,api
class APIConfiguration(models.Model):
    _name = "api.configuration"
    name = fields.Char(string="Name",copy=False)
    c_user_name = fields.Char(string="User Name", help="Developer key",copy=False)
    c_user_password = fields.Char(copy=False,string='Password')
    c_api_url=fields.Char(copy=False,string='API URL')
    