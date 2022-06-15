from odoo import models, fields, api
import requests
from requests import request
from odoo.exceptions import ValidationError
import datetime, pytz
import logging
from datetime import datetime
import logging
import simplejson as json

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    metquay_status = fields.Char('Status', copy=False, help='Report type if work is finished. Close type and comment if work is closed. Status if work is not finished.')
    observations = fields.Char(copy=False, string='Observations')
    work_cal_id = fields.Char(readonly=True, copy=False, string='Work Calibration Id')
    calibracion = fields.Boolean(copy=True, string='Calibracion',help="Marcar cuando se desea Calibrar o Reparar el producto.")
    workno = fields.Char(readonly=True, copy=False, string="WorkNo")
    api_message = fields.Char(copy=False, string="Message")
    api_request = fields.Text(copy=False, string='API Request Data', help="")
    api_response = fields.Text(copy=False, string='API Response Data', help="")
    exported_using_api = fields.Boolean(string='Exported Customer Inst. Using API', copy=False)
    work_api_message = fields.Char(copy=False, string="Message")
    work_api_request = fields.Text(copy=False, string='Work API Request Data', help="")
    work_api_response = fields.Text(copy=False, string='Work API Response Data', help="")
    exported_work_order_using_api = fields.Boolean('Exported', help='Exported Work Order Using API', copy=False)

    #Campos de Metquay ---> Odoo
    certificate_no = fields.Char('Certificate No.', copy=False, help="Certificate number of the work ")
    certificate_name = fields.Char('Certificate Name', copy=False, help="Certificate issued to the company name")
    certificate_address = fields.Char('Certificate Address',copy=False, help="Certificate address of work")
    expiry_date = fields.Char('Expiry Date', copy=False, help="Recommended due date of work")
    date_of_completion = fields.Char('Completion Date', copy=False, help="Date of completion of work in CMS")
    assigned_to = fields.Char('Assigned To', copy=False, help="Technician Who calibrated")
    finished_by = fields.Char('Finished by',copy=False, help="Technician who approved")
    work_type = fields.Char('Work type', copy=False, help="At Customers Place, At Lab, Subcon")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        # self.create_workorder()
        # self.create_customer_instrument_api
        # ResUserVTS()
        res = super(SaleOrder, self).action_confirm()

        return res

    def create_workorder(self):

        instance = self.env['api.configuration'].search([], limit=1)
        line_no = ''
        work_cal_id = ''
        calibar_id = ''
        for order_line in self.order_line:

            if order_line.calibracion:
                pass
            else:
                continue

            for lot_id in order_line.lot_ids:
                api_url_data = "/FlexicalERP/rest/work/createOrUpdateWork"
                if not instance:
                    raise ValidationError("Configurar API, Configuration Missing!")
                work_api_message = []
                work_api_request = []
                work_api_response = []
                #  date_met = self.confirmation_date
                #  date_met2 = strftime('%Y-%m-%d %H:%M:%S')
                # scheduled_date += pick.scheduled_date.strftime("%Y-%m-%d %H:%M:%S")

                request_data = {
                    "username": "%s" % (instance.c_user_name),
                    "password": "%s" % (instance.c_user_password),
                    "model": "work",
                    "northlabWork": [{
                        "workNo": "",
                        "accreditation": False,
                        "salesOrderNo": "%s" % (self.name),
                        "siteJob": False,
                        "outsource": False,
                        "customerSpecificRequirements": "",
                        "certificateAddress": "",
                        "taskType": "Calibration",
                        "department": "",
                        "scope": "",
                        "certificateIssuedTo": "",
                        "complianceRequired": False,
                        "remarks": "",
                        "calibrId": 0,
                        "customerInstrumentCalibrId": lot_id.ref,
                        "odooUser": "%s" % (self.env.user.name)
                    }]

                }

                data = json.dumps(request_data)
                api_url = "%s%s" % (instance.c_api_url, api_url_data)
                headers = {"Accept": "application/json", "Content-Type": "application/json"}
                work_api_request = "%s" % ("Request Data : %s \n URL : %s \n  Header : %s" % (data, api_url, headers))
                try:
                    work_api_response_data = request(method='POST', url=api_url, data=data, headers=headers)
                except Exception as e:
                    raise ValidationError(e)
                work_api_response_data = work_api_response_data.json()
                work_api_response_code = "%s" % (work_api_response_data.get("responseCode", False))
                _logger.info("Fue exitosa la call?????  %s", work_api_response_data)
                if work_api_response_code == "700":
                    work_api_response = "%s" % (work_api_response_data)
                    work_api_message = "%s" % (work_api_response_data.get("shortMessage", False))

                    if order_line.workno:
                        order_line.workno += ", %s" % (work_api_response_data.get("response", False).get("workNo", False)) + ","
                    else:
                        order_line.workno = "%s" % (work_api_response_data.get("response", False).get("workNo", False))
                    if order_line.work_cal_id:
                        order_line.work_cal_id += ", %s" % (work_api_response_data.get("response", False).get("calibrId", False))
                    else:
                        order_line.work_cal_id = "%s" % (work_api_response_data.get("response", False).get("calibrId", False))

                    order_line.exported_work_order_using_api = True
                    order_line.work_api_request = work_api_request
                    order_line.work_api_response = work_api_response
                    order_line.work_api_message = work_api_message
                else:

                    line_no += "%s" % str(order_line.sequence2) + ","
                    work_api_response = "%s" % (work_api_response_data)
                    work_api_message = "%s" % (work_api_response_data.get("longMessage", False))
                    order_line.exported_work_order_using_api = False
                    order_line.work_api_request = work_api_request
                    order_line.work_api_response = work_api_response
                    order_line.work_api_message = work_api_message

        if line_no:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "Ocurrió un problema al generar los servicios en las siguientes líneas: %s" % line_no,
                    'img_url': '/web/static/src/img/neutral_face.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "¡Guardado exitosamente!",
                    'img_url': '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }



    def create_customer_instrument_api(self):
        instance = self.env['api.configuration'].search([], limit=1)
        if not instance:
            raise ValidationError("Please set appropriate API configuration, Configuration Missing!")
        line_no = ''
        # _logger.info(" Today DateTime (%s) " % (today_datetime))
        _logger.info("Entrando a funcion ")
        # self.mapped('move_lines').mapped('move_line_ids').mapped('lot_id')
        if not self.order_line:
            raise ValidationError("Sale Order Line Is Not Available!")
        for order_line in self.order_line:

            if order_line.calibracion:
                pass
            else:
                return

            calibr_id = ''
            message = []
            api_request = []
            api_response = []
            response_data = []
            for lot_id in order_line.lot_ids:
                api_url_data = "/FlexicalERP/rest/customerInstrument/createCustomerInstrument" if not order_line.exported_using_api else "/FlexicalERP/rest/customerInstrument/updateCustomerInstrument"
                request_data = {
                    "username": "%s" % (instance.c_user_name),
                    "model": "customerInstrument",
                    "password": "%s" % (instance.c_user_password),
                    "northlabCustomerInstrument": [{
                        "customerInstrumentName": "%s" % (lot_id.product_id and lot_id.product_id.name),
                        "instrumentRange": "",
                        "serialNo": "%s" % (lot_id.name),
                        "instrumentModel": "",
                        "tagNo": "",
                        "calibrationFrequency": 365,
                        "instrumentMake": "",
                        "instrumentCategoryCalibrId": "%s"%(order_line.category.calib_id),
                       # "instrumentCategoryCalibrId": category.calib_id,
                        "companyCalibrId": order_line.order_partner_id.calibr_id,
                        "calibrId": lot_id.ref or 0,
                        "odooUser": "%s" % (self.env.user.name)
                    }]
                }
                data = json.dumps(request_data)
                api_url = "%s%s" % (instance.c_api_url, api_url_data)
                headers = {"Accept": "application/json", "Content-Type": "application/json"}
                api_request = "%s" % ("Request Data : %s \n URL : %s \n  Header : %s" % (data, api_url, headers))
                try:
                    response_data = request(method='POST', url=api_url, data=data, headers=headers)
                except Exception as e:
                    raise ValidationError(e)

                response_data = response_data.json()
                response_code = "%s" % (response_data.get("responseCode", False))
                #  _logger.info("Fue exitosa la call?????%s", response_code)

                if response_code == "700":

                    api_response = "%s" % (response_data)
                    lot_id.ref = "%s" % (response_data.get("response", False).get("calibrId", False))
                    message.append("%s" % (response_data.get("shortMessage", False)))
                    order_line.exported_using_api = True
                    order_line.api_request = api_request
                    order_line.api_response = api_response
                    order_line.api_message = message

                else:
                    _logger.info("si entro al error")
                    line_no += "%s" % str(order_line.sequence2) + ","
                    # response_data = response_data.json()
                    api_response = "%s" % (response_data)
                    message.append("%s" % (response_data.get("longMessage", False)))
                    order_line.exported_using_api = False
                    order_line.api_request = api_request
                    order_line.api_response = api_response
                    order_line.api_message = message

        _logger.info("%s" % line_no)
        if line_no:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "Ocurrió un problema al generar los equipos en las siguientes líneas: %s" % line_no,
                    'img_url': '/web/static/src/img/neutral_face.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "¡Guardado exitosamente!",
                    'img_url': '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }

class StockLot(models.Model):
    _inherit = "stock.production.lot"
    metquay_status = fields.Char(copy=False, string='Report type if work is finished. Close type and comment if work is closed. Status if work is not finished.')
    observations = fields.Char(copy=False, string='Observations')
    work_cal_id = fields.Char(readonly=True, copy=False, string='Work Calibration Id')
    calibration_frecuency = fields.Char(readonly=True, copy=False, string='Calibration Frecuency')
    last_calibration_date = fields.Char(readonly=True, copy=False, string='Last Calibration Date')


class ResUserVTS(models.Model):
    _inherit = "res.partner"

    api_message = fields.Char(string="message")
    calibr_id = fields.Char(string="calibrId")
    api_request = fields.Text(copy=False, string='API Request Data', help="")
    api_response = fields.Text(copy=False, string='API Response Data', help="")
    exported_using_api = fields.Boolean(copy=False, string="Exported Using API",
                                        help="TRUE indiacate exported on server.", default=False)

    def export_customer_using_cronjob(self):
        customer_ids = self.search([('exported_using_api', '=', False)])
        for customer_id in customer_ids:
            try:
                customer_id.api_structure()
            except Exception as e:
                customer_id.api_message = e
        return True

    def api_structure(self):
        instance = self.env['api.configuration'].search([], limit=1)

        api_url_data = "/FlexicalERP/rest/customer/createCustomer" if not self.exported_using_api else "/FlexicalERP/rest/customer/updateCustomer"
        if not instance:
            raise ValidationError("Please set appropriate API configuration, Configuration Missing!")
        request_data = {
            "username": "%s" % (instance.c_user_name),
            "password": "%s" % (instance.c_user_password),
            "model": "customer",
            "northlabCustomer": [{
                "calibrId": self.calibr_id or 0,
                "odooUser": "%s" % (self.env.user.name),
                "companyName": "%s" % (self.name),
                "companyCode": "%s" % (self.ref),
                "companyPhone1": "%s" % (self.phone),
                "companyPhone2": "%s" % (self.mobile or ""),
                "companyPhone3": "",
                "companyEmail": "%s" % (self.email),
                "companyWebsite": "",
                "companyFax": "",
                "website": "",
                "companyStatus": True,
                "companyAddress": [{
                    "addressField1": "%s" % (self.street),
                    "addressField2": "%s" % (self.street2),
                    "addressField3": "",
                    "addressField4": "",
                    "postalCode": "%s" % (self.zip),
                    "city": "%s" % (self.city),
                    "calibrId": self.calibr_id or 0,
                    #  "location": "%s"%(self.l10n_mx_edi_colony or ""),
                    "phone1": "%s" % (self.phone),
                    "phone2": "",
                    "fax": "",
                    "email": "%s" % (self.email),
                    "state": "%s" % (self.state_id.name),
                    "country": "%s" % (self.country_id.name),
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

        response_data = response_data.json()
        response_code = "%s" % (response_data.get("responseCode", False))
        # _logger.info("Fue exitosa la call?????  %s", response_code)
        if response_code == "700":

            self.exported_using_api = True
            self.api_request = api_request
            self.api_response = response_data
            self.api_message = response_data
            self.calibr_id = response_data.get("response", False).get("calibrId", False)

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
            self.api_response = response_data
            self.api_message = response_data
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
            "username": "%s" % (instance.c_user_name),
            "password": "%s" % (instance.c_user_password),
            "model": "customer",
            "northlabCustomer": [{
                "calibrId": self.calibr_id,
                "odooUser": "%s" % (self.env.user.name),
                "companyName": "%s" % (self.name),
                "companyCode": "%s" % (self.ref),
                "companyPhone1": "%s" % (self.phone),
                "companyPhone2": "%s" % (self.mobile or ""),
                "companyPhone3": "",
                "companyEmail": "%s" % (self.email),
                "companyWebsite": "",
                "companyFax": "",
                "website": "",
                "companyStatus": True,
                "companyAddress": [{
                    "addressField1": "%s" % (self.street),
                    "addressField2": "%s" % (self.street2),
                    "addressField3": "",
                    "addressField4": "",
                    "postalCode": "%s" % (self.zip),
                    "city": "%s" % (self.city),
                    "calibrId": self.calibr_id or 0,
                    "location": "%s" % (self.l10n_mx_edi_colony or ""),
                    "phone1": "%s" % (self.phone),
                    "phone2": "",
                    "fax": "",
                    "email": "%s" % (self.email),
                    "state": "%s" % (self.state_id.name),
                    "country": "%s" % (self.country_id.name),
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

