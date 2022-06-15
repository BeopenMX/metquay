from odoo import models, fields,api
import requests
from requests import request
from odoo.exceptions import ValidationError

import simplejson as json

class StockPickingVTS(models.Model):
    _inherit = "stock.picking"

    api_message = fields.Char(string="message")
    api_request = fields.Text(copy=False,string='API Request Data', help="")
    api_response= fields.Text(copy=False,string='API Response Data', help="")
    exported_using_api= fields.Boolean(copy=False, string="Exported Using API", help="TRUE indiacate exported on server.", default=False)
    #calibr_id = fields.Char(string="calibrId")
    
    def api_structure(self):
        instance=self.env['api.configuration'].search([],limit=1)
        if not instance:
            raise ValidationError("Please set appropriate API configuration, Configuration Missing!")
        message = []
        api_request=[]
        api_response=[]
        # self.mapped('move_lines').mapped('move_line_ids').mapped('lot_id')
        if not self.move_lines:
            raise ValidationError("Product Is Not Available!")
        for move_line in self.move_lines:
            for move_line_id in move_line.move_line_ids:
                if not move_line_id.lot_id:
                    message.append("Serial And Lot Configuration Not Done : %s!"%(move_line_id.product_id and move_line_id.product_id.name ))
                    continue
                for lot_id in move_line_id.lot_id:
                    api_url_data = "/FlexicalERP/rest/customerInstrument/createCustomerInstrument" if self.exported_using_api else "/FlexicalERP/rest/customerInstrument/updateCustomerInstrument"
                    request_data ={
                        "username": "%s"%(instance.c_user_name),
                        "model": "customerInstrument",
                        "password": "%s"%(instance.c_user_password),
                        "northlabCustomerInstrument": [{
                            "customerInstrumentName": "%s"%(lot_id.product_id and lot_id.product_id.name),
                            "instrumentRange": "",
                            "serialNo": "%s"%(lot_id.name),
                            "instrumentModel": "",
                            "tagNo": "",
                            "calibrationFrequency": 365,
                            "instrumentMake": "Make",
                            "instrumentCategoryCalibrId": 2,
                            "companyCalibrId": 1,
                            "calibrId": 0,
                            "odooUser": "%s"%(self.env.user.name)
                        }]
                    }
                    data = json.dumps(request_data)
                    api_url="%s%s"%(instance.c_api_url,api_url_data)
                    headers= {"Accept": "application/json", "Content-Type": "application/json"}
                    api_request.append("Request Data : %s \n URL : %s \n  Header : %s"%(data,api_url,headers))
                    try:
                        response_data = request(method='POST', url=api_url, data=data, headers=headers)
                    except Exception as e:
                        message.append(e)
                        continue

                    if response_data.status_code in [200, 201,700]:
                        response_data = response_data.json()
                        api_response.append(response_data)
                        lot_id.ref = response_data.get("response",False).get("calibrId", False)
                    else:
                        message.append("%s" % (response_data))
        self.exported_using_api = True
        self.api_request = api_request
        self.api_response =api_response
        self.api_message=message
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Yeah! Sucessfully Completed.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }
