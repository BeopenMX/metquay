from odoo import models, fields,api
import requests
from requests import request
from odoo.exceptions import ValidationError

import simplejson as json

class ProductVTS(models.Model):
    _inherit = "product.product"

    calibr_id = fields.Char(string="Calibr Id",copy=False,help="Indicates Server ID")
    api_message = fields.Char(string="message")
    api_request = fields.Text(copy=False,string='API Request Data', help="")
    api_response= fields.Text(copy=False,string='API Response Data', help="")
    exported_using_api= fields.Boolean(copy=False, string="Exported Using API", help="TRUE indiacate exported on server.", default=False)
    api_message = fields.Char(string="message")

    def export_product_using_cronjob(self):
        product_ids = self.search([('exported_using_api', '=', False)])
        for product_id in product_ids:
            try:
                product_id.api_structure()
            except Exception as e:
                product_id.api_message=e
        return True

    def api_structure(self):
        instance=self.env['api.configuration'].search([],limit=1)

        api_url_data = "/FlexicalERP/rest/customerInstrument/createCustomerInstrument" if self.exported_using_api else "/FlexicalERP/rest/customerInstrument/updateCustomerInstrument"
        if not instance:
            raise ValidationError("Please set appropriate API configuration, Configuration Missing!")
        request_data ={
            "username": "%s"%(instance.c_user_name),
            "model": "customerInstrument",
            "password": "%s"%(instance.c_user_password),
            "northlabCustomerInstrument": [{
                "customerInstrumentName": "%s"%(self.name),
                "instrumentRange": "",
                "serialNo": "%s"%(self.default_code),
                "instrumentModel": "",
                "tagNo": "",
                "calibrationFrequency": 365,
                "instrumentMake": "Make",
                "instrumentCategoryCalibrId": 2,
                "companyCalibrId": 1,
                "calibrId": 0,
                "odooUser": ""
            }]
        }

        data = json.dumps(request_data)
        api_url="%s%s"%(instance.c_api_url,api_url_data)
        headers= {"Accept": "application/json", "Content-Type": "application/json"}
        api_request="Request Data : %s \n URL : %s \n  Header : %s"%(data,api_url,headers)
        try:
            response_data = request(method='POST', url=api_url, data=data, headers=headers)
        except Exception as e:
            raise ValidationError(e)

        if response_data.status_code in [200, 201,700]:
            response_data = response_data.json()
            self.exported_using_api = True
            self.calibr_id="%s"%(response_data.get("calibrId",False))
            self.api_request = api_request
            self.api_response =response_data
            self.api_message=response_data
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "Yeah! Sucessfully Completed.",
                    'img_url': '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise ValidationError("%s"%(response_data))

    def delete_api_structure(self):
        instance = self.env['api.configuration'].search([], limit=1)
        api_url_data = "/FlexicalERP/rest/customerInstrument/deleteCustomerInstrument"
        if not instance:
            raise ValidationError("Please set appropriate API configuration, Configuration Missing!")
        request_data = {
            "username": "%s" % (instance.c_user_name),
            "model": "customerInstrument",
            "password": "%s" % (instance.c_user_password),
            "northlabCustomerInstrument": [{
                "customerInstrumentName": "%s" % (self.name),
                "instrumentRange": "",
                "serialNo": "%s" % (self.default_code),
                "instrumentModel": "",
                "tagNo": "",
                "calibrationFrequency": 365,
                "instrumentMake": "Make",
                "instrumentCategoryCalibrId": 2,
                "companyCalibrId": 1,
                "calibrId": 0,
                "odooUser": ""
            }]
        }

        data = json.dumps(request_data)
        api_url = "%s%s" % (instance.c_api_url, api_url_data)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        api_request = "Request Data : %s \n URL : %s \n  Header : %s" % (data, api_url, headers)
        try:
            response_data = request(method='POST', url=api_url, data=data, headers=headers)
        except Exception as e:
            raise ValidationError(e)

        if response_data.status_code in [200, 201, 700]:
            response_data = response_data.json()
            self.exported_using_api = True
            self.api_request = api_request
            self.api_response = response_data
            self.api_message = response_data
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "Yeah! Delete Operation Sucessfully Completed.",
                    'img_url': '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise ValidationError("%s" % (response_data))

