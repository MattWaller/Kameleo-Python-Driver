from Kameleo_driver_base import Kameleo_cli

email = 'email'
password = 'password'
kam_driver = Kameleo_cli(email,password)
driver = kam_driver.init_profile()
