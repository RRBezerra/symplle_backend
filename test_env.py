from sms_service import SMSService

service = SMSService()
result = service.send_sms("+5511993729656", "Teste direto do SMSService")
print(result)