class ALMException(Exception):
    """Exception คลาสฐานของแอปพลิเคชัน ALM-X-IMPACT"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class SMSGatewayException(ALMException):
    """Exception สำหรับกรณีข้อผิดพลาดจากเครือข่าย SMS Gateway ภายนอก"""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, status_code)

class SlotConflictException(ALMException):
    """Exception สำหรับกรณีมีการจองสนามในสล็อตวันเวลาดังกล่าวไปแล้ว"""
    def __init__(self, message: str = "สล็อตเวลานี้ถูกจองเต็มแล้ว"):
        super().__init__(message, 409)

class UserDuplicateBookingException(ALMException):
    """Exception สำหรับกรณีผู้เล่นพยายามจองสนามซ้ำสล็อตเดิมที่ตัวเองจองไว้"""
    def __init__(self, message: str = "คุณจองสนามในสล็อตเวลานี้ไปแล้ว"):
        super().__init__(message, 400)
