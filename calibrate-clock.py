print("Use this script to tell master-clock what time your slave clock displays.")
# try:
#     while 1:
#         userDC = input("Enter duty cycle 0-100: ")
#         print("Setting meter to "+str(userDC))
#         setMeter(float(userDC))
# except KeyboardInterrupt:
#     print("\r\nBye!")
# # except:
# #     print("Error")
# finally:
#     if dcLast > 20: #kill the meter softly
#         setMeter(0)
#     pwm.stop()
#     GPIO.cleanup()