from odoo import models, fields,api
import requests
from requests import request
from odoo.exceptions import ValidationError

import simplejson as json

class ResUserVTS(models.Model):
    _inherit = "res.partner"

    api_message = fields.Char(string="message")
    calibr_id = fields.Char(string="calibrId")
    api_request = fields.Text(copy=False,string='API Request Data', help="")
    api_response= fields.Text(copy=False,string='API Response Data', help="")
    exported_using_api= fields.Boolean(copy=False, string="Exported Using API", help="TRUE indiacate exported on server.", default=False)

    def export_customer_using_cronjob(self):
        customer_ids = self.search([('exported_using_api', '=', False)])
        for customer_id in customer_ids:
            try:
                customer_id.api_structure()
            except Exception as e:
                customer_id.api_message=e
        return True

    def api_structure(self):
        instance=self.env['api.configuration'].search([],limit=1)

        api_url_data = "/FlexicalERP/rest/customer/createCustomer" if not  self.exported_using_api else "/FlexicalERP/rest/customer/updateCustomer"
        if not instance:
            raise ValidationError("Please set appropriate API configuration, Configuration Missing!")
        request_data={
            "username": "%s"%(instance.c_user_name),
            "password": "%s"%(instance.c_user_password),
            "model": "customer",
            "northlabCustomer": [{
            "calibrId": self.calibr_id or 0 ,
            "odooUser": "%s"%(self.env.user.name),
            "companyName": "%s"%(self.name),
            "companyCode": "%s"%(self.ref),
            "companyPhone1": "%s"%(self.phone),
            "companyPhone2": "%s"%(self.mobile or ""),
            "companyPhone3": "",
            "companyEmail": "%s"%(self.email),
            "companyWebsite": "",
            "companyFax": "",
            "website": "",
            "companyStatus": True,
            "companyAddress": [{
                "addressField1": "%s"%(self.street),
                "addressField2": "%s"%(self.street2),
                "addressField3": "",
                "addressField4": "",
                "postalCode": "%s"%(self.zip),
                "city": "%s"%(self.city),
                "calibrId": self.calibr_id or 0,
              #  "location": "%s"%(self.l10n_mx_edi_colony or ""),
                "phone1": "%s"%(self.phone),
                "phone2": "",
                "fax": "",
                "email": "%s"%(self.email),
                "state": "%s"%(self.state_id.name),
                "country":"%s"%(self.country_id.name),
                "primaryAddress": True,
                "certificateAddress": True
            }]
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

        response_data = response_data.json()
        response_code = "%s" % (response_data.get("responseCode",False))
                #_logger.info("Fue exitosa la call?????  %s", response_code)
        if  response_code == "700":

            self.exported_using_api = True
            self.api_request = api_request
            self.api_response =response_data
            self.api_message=response_data
            self.calibr_id=response_data.get("response",False).get("calibrId", False)
           
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "¡Guardado exitosamente!",
                    'img_url': '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:

            self.exported_using_api = False
            self.api_request = api_request
            self.api_response =response_data
            self.api_message=response_data
        return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "Ocurrió un problema",
                    'img_url': '/web/static/src/img/neutral_face.svg',
                    'type': 'rainbow_man',
                }
            }

    def delete_api_structure(self):
        instance = self.env['api.configuration'].search([], limit=1)
        api_url_data = "/FlexicalERP/rest/customer/deleteCustomer"
        if not instance:
            raise ValidationError("Please set appropriate API configuration, Configuration Missing!")
        request_data = {
            "username": "%s"%(instance.c_user_name),
            "password": "%s"%(instance.c_user_password),
            "model": "customer",
            "northlabCustomer": [{
            "calibrId": self.calibr_id,
            "odooUser": "%s"%(self.env.user.name),
            "companyName": "%s"%(self.name),
            "companyCode": "%s"%(self.ref),
            "companyPhone1": "%s"%(self.phone),
            "companyPhone2": "%s"%(self.mobile or ""),
            "companyPhone3": "",
            "companyEmail": "%s"%(self.email),
            "companyWebsite": "",
            "companyFax": "",
            "website": "",
            "companyStatus": True,
            "companyAddress": [{
                "addressField1": "%s"%(self.street),
                "addressField2": "%s"%(self.street2),
                "addressField3": "",
                "addressField4": "",
                "postalCode": "%s"%(self.zip),
                "city": "%s"%(self.city),
                "calibrId": self.calibr_id or 0,
                "location": "%s"%(self.l10n_mx_edi_colony or ""),
                "phone1": "%s"%(self.phone),
                "phone2": "",
                "fax": "",
                "email": "%s"%(self.email),
                "state": "%s"%(self.state_id.name),
                "country":"%s"%(self.country_id.name),
                "primaryAddress": True,
                "certificateAddress": True
                }]
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

